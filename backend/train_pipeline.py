"""One-shot training pipeline for the AI Urban Farming Assistant.

Runs the whole flow with clear, early errors:

    verify + split  ->  train  ->  evaluate (PlantVillage test)  ->  optional
    real-world evaluation  ->  optional single-image prediction

Run it from anywhere:

    python backend/train_pipeline.py --data "D:\\datasets\\plantvillage\\color"
    python backend/train_pipeline.py                 # auto-detects the dataset
    python backend/train_pipeline.py --realworld-test "D:\\my_photos"
    python backend/train_pipeline.py --predict "D:\\my_photos\\leaf.jpg"

Your own real-world photos: organise them as one folder per class, e.g.

    my_photos/
        Tomato___Early_blight/  img1.jpg img2.jpg ...
        Tomato___healthy/       ...

If the folder names are NOT the 38 known PlantVillage classes, pass
``--any-classes`` (it is enabled automatically when no known class is found).
"""

from __future__ import annotations

import argparse
import json
import sys
import traceback
from pathlib import Path

# Make ``ml`` importable no matter the current working directory.
BACKEND_DIR = Path(__file__).resolve().parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from ml import config  # noqa: E402
from ml.disease_info import DISEASE_INFO  # noqa: E402


def _candidate_dirs() -> list[Path]:
    candidates = [
        config.DATASET_DIR,
        config.ML_DIR / "data" / "plantvillage" / "color",
        config.ML_DIR / "data" / "plantvillage",
        config.ML_DIR / "data",
        config.BACKEND_DIR.parent / "dataset",
        config.BACKEND_DIR.parent / "plantvillage",
        # Conventional manual-download location on Windows (checked with
        # .exists(); harmless on other platforms).
        Path(r"D:\Datasets\PlantVillage\color"),
        Path(r"D:\Datasets\PlantVillage"),
    ]
    seen: set[str] = set()
    unique: list[Path] = []
    for c in candidates:
        if str(c) not in seen:
            seen.add(str(c))
            unique.append(c)
    return unique


def find_data_dir(explicit: str | None) -> Path | None:
    if explicit:
        return Path(explicit).expanduser().resolve()
    for candidate in _candidate_dirs():
        try:
            if candidate.exists() and any(p.is_dir() for p in candidate.iterdir()):
                return candidate
        except OSError:
            continue
    return None


def _num_class_dirs(directory: Path) -> int:
    try:
        return sum(1 for p in directory.iterdir() if p.is_dir())
    except OSError:
        return 0


def predict_image(image_path: str) -> int:
    from ml.predictor import DiseasePredictor

    path = Path(image_path)
    if not path.exists():
        print(f"ERROR: image not found: {path}")
        return 1
    predictor = DiseasePredictor()
    if not predictor.classifier.ready:
        print("WARNING: no trained checkpoint - running in fallback mode (no diagnosis).")
    with path.open("rb") as fh:
        result = predictor.predict(fh.read())
    print(json.dumps(result, indent=2))
    return 0 if result.get("success") else 2


def smoke_test() -> int:
    """Validate the pipeline end-to-end on tiny synthetic data (no dataset needed).

    Runs explicit per-check PASS/FAIL stages: dependency imports, architecture
    init, synthetic batch shapes, forward pass + output dims, loss + backward +
    optimizer step, temp checkpoint save/load round-trip, manifest build,
    1-epoch CPU train (from scratch, offline) and temp evaluation.
    Everything stays inside a temp folder: the real manifest, MODEL_DIR and
    evaluation outputs are NEVER touched, and the result is NOT a usable
    disease model. A passing smoke test proves the environment works - it does
    NOT prove real dataset training will succeed.
    """
    import tempfile

    results: list[tuple[str, bool, str]] = []

    def run_check(name: str, fn) -> bool:
        try:
            detail = fn() or ""
        except Exception as exc:  # noqa: BLE001 - report the error, don't crash
            msg = f"{type(exc).__name__}: {exc}"
            results.append((name, False, msg))
            print(f"[FAIL] {name}: {msg}")
            return False
        results.append((name, True, detail))
        print(f"[PASS] {name}" + (f" ({detail})" if detail else ""))
        return True

    state: dict = {}
    print("SMOKE TEST: synthetic random-noise images only - NOT a real model.")

    # -- 1. imports ------------------------------------------------------
    def c_imports() -> str:
        import numpy  # noqa: F401
        import torch
        import torchvision  # noqa: F401
        from PIL import Image  # noqa: F401
        return f"torch {torch.__version__}, cuda_available={torch.cuda.is_available()}"

    if not run_check("imports (numpy, torch, torchvision, PIL)", c_imports):
        print("\nSMOKE TEST FAILED at imports.")
        print("Run:  pip install -r requirements.txt -r requirements-ml.txt  (from backend/)")
        return 1

    # -- 2. architecture init --------------------------------------------
    def c_arch() -> str:
        from ml.train import build_model

        model = build_model(num_classes=3, pretrained=False)
        n_params = sum(p.numel() for p in model.parameters())
        out = model.classifier[1].out_features
        assert out == 3, f"classifier head has {out} outputs, expected 3"
        state["model"] = model
        return f"mobilenet_v2, {n_params} params, head=3"

    if not run_check("model architecture init (mobilenet_v2, 3-class head)", c_arch):
        return _smoke_summary(results)

    # -- 3. synthetic batch ----------------------------------------------
    def c_batch() -> str:
        import torch

        batch = torch.randn(4, 3, config.IMAGE_SIZE, config.IMAGE_SIZE)
        assert tuple(batch.shape) == (4, 3, config.IMAGE_SIZE, config.IMAGE_SIZE)
        assert batch.dtype == torch.float32
        state["batch"] = batch
        return f"shape={tuple(batch.shape)}, dtype=float32"

    if not run_check("synthetic input batch shape", c_batch):
        return _smoke_summary(results)

    # -- 4. forward pass ---------------------------------------------------
    def c_forward() -> str:
        import torch

        model = state["model"]
        model.eval()
        with torch.no_grad():
            out = model(state["batch"])
        assert tuple(out.shape) == (4, 3), f"output shape {tuple(out.shape)} != (4, 3)"
        return f"output shape={tuple(out.shape)}"

    if not run_check("forward pass + output dimensions", c_forward):
        return _smoke_summary(results)

    # -- 5. loss + backward + optimizer step -------------------------------
    def c_train_step() -> str:
        import torch

        model = state["model"]
        model.train()
        optimizer = torch.optim.Adam(model.parameters(), lr=0.0001)
        criterion = torch.nn.CrossEntropyLoss()
        targets = torch.tensor([0, 1, 2, 0])
        loss = criterion(model(state["batch"]), targets)
        assert torch.isfinite(loss), f"non-finite loss: {loss.item()}"
        optimizer.zero_grad()
        loss.backward()
        grads = [p.grad for p in model.parameters() if p.requires_grad]
        assert grads and all(g is not None for g in grads), "no gradients produced"
        optimizer.step()
        return f"loss={loss.item():.4f}, grads ok, optimizer step ok"

    if not run_check("loss + backprop + optimizer step", c_train_step):
        return _smoke_summary(results)

    # -- 6. checkpoint round-trip (temp) ------------------------------------
    def c_ckpt() -> str:
        import torch

        from ml.train import build_model

        tmp = Path(tempfile.mkdtemp(prefix="leaflogic_smoke_ckpt_"))
        state["tmp_ckpt"] = tmp
        model = state["model"]
        torch.save(model.state_dict(), tmp / "roundtrip.pth")
        fresh = build_model(num_classes=3, pretrained=False)
        fresh.load_state_dict(torch.load(tmp / "roundtrip.pth", map_location="cpu"))
        for a, b in zip(model.parameters(), fresh.parameters()):
            assert torch.equal(a.cpu(), b.cpu()), "state_dict mismatch after reload"
        return "save/load state_dict identical"

    if not run_check("checkpoint save/load round-trip (temp dir)", c_ckpt):
        return _smoke_summary(results)

    # -- 7. manifest on synthetic data ---------------------------------------
    def c_manifest() -> str:
        import numpy as np
        from PIL import Image

        from ml.preprocess import build_manifest

        tmp = Path(tempfile.mkdtemp(prefix="leaflogic_smoke_"))
        state["tmp"] = tmp
        data = tmp / "data"
        rng = np.random.default_rng(42)
        for cls in ("Apple___healthy", "Tomato___healthy", "Tomato___Early_blight"):
            cls_dir = data / cls
            cls_dir.mkdir(parents=True)
            for i in range(12):
                arr = (rng.random((64, 64, 3)) * 255).astype("uint8")
                Image.fromarray(arr).save(cls_dir / f"img_{i}.jpg")
        manifest = build_manifest(
            data, config.TRAIN_RATIO, config.VAL_RATIO, config.SPLIT_SEED,
            tmp / "manifest.json",
            min_samples=7,
            require_all_classes=False,
            accept_unknown_classes=True,
            verify_images=True,
        )
        assert manifest["leakage_overlap_after_split"] == 0, "split leakage!"
        counts = manifest["counts"]
        assert all(counts[k] > 0 for k in ("train", "val", "test")), f"empty split: {counts}"
        return f"train/val/test={counts['train']}/{counts['val']}/{counts['test']}, leakage=0"

    if not run_check("manifest build on synthetic data", c_manifest):
        return _smoke_summary(results)

    # -- 8. one-epoch train (temp) --------------------------------------------
    def c_train() -> str:
        from ml.train import train

        tmp = state["tmp"]
        train(
            tmp / "manifest.json", tmp / "model",
            epochs=1, batch_size=4, pretrained=False,
            num_workers=0, seed=42,
        )
        assert (tmp / "model" / "plant_disease_model.pth").exists(), "checkpoint not written"
        assert (tmp / "model" / "labels.json").exists(), "labels.json not written"
        return "checkpoint + labels.json written (temp)"

    if not run_check("one-epoch train from scratch, offline (temp dir)", c_train):
        return _smoke_summary(results)

    # -- 9. evaluate (temp) ------------------------------------------------------
    def c_eval() -> str:
        from ml.evaluate import evaluate

        tmp = state["tmp"]
        report = evaluate(tmp / "model" / "plant_disease_model.pth",
                          tmp / "manifest.json", tmp / "eval")
        assert "overall_accuracy" in report
        assert (tmp / "eval" / "report.txt").exists(), "report.txt not written"
        return f"{report['num_test_samples']} test images scored (noise: value meaningless)"

    if not run_check("held-out evaluation + report files (temp dir)", c_eval):
        return _smoke_summary(results)

    print(f"\nSMOKE TEST PASSED: {len(results)}/{len(results)} checks.")
    print(f"Temp files kept at: {state.get('tmp')} (safe to delete).")
    print("NOTE: this proves the environment works - it does NOT prove real training succeeded.")
    print("Next: download the real dataset and run the full pipeline (see ML_SETUP.md).")
    return 0


def _smoke_summary(results: list[tuple[str, bool, str]]) -> int:
    passed = sum(1 for _, ok, _ in results if ok)
    print(f"\nSMOKE TEST FAILED: {passed}/{len(results)} checks passed.")
    print("Fix the FAILED check above, then re-run with --smoke-test.")
    return 1


def run_pipeline(args: argparse.Namespace) -> int:
    # ----------------------------------------------------------- locate data
    data_dir = find_data_dir(args.data)
    if data_dir is None:
        print("ERROR: could not find a dataset. Point --data at the folder that "
              "directly contains the class sub-folders, e.g.\n"
              '  python backend/train_pipeline.py --data "D:\\datasets\\plantvillage\\color"')
        return 1
    if not data_dir.exists():
        print(f"ERROR: dataset directory does not exist: {data_dir}")
        return 1
    if _num_class_dirs(data_dir) == 0:
        print(f"ERROR: {data_dir} has no class sub-folders.")
        return 1
    print(f"Dataset: {data_dir}")

    class_dirs = sorted(p.name for p in data_dir.iterdir() if p.is_dir())
    known = [c for c in class_dirs if c in DISEASE_INFO]
    any_classes = args.any_classes or len(known) == 0
    if any_classes:
        print(f"Custom-class mode: {len(class_dirs)} folders (not the 38 PlantVillage names).")
    else:
        print(f"PlantVillage classes found: {len(known)} (unknown folders: "
              f"{len(class_dirs) - len(known)})")

    # ----------------------------------------------------------- preprocess
    from ml.preprocess import build_manifest

    print("\n=== [1/4] Verifying dataset and building the split manifest ===")
    try:
        manifest = build_manifest(
            data_dir, config.TRAIN_RATIO, config.VAL_RATIO, config.SPLIT_SEED,
            config.MANIFEST_PATH,
            min_samples=config.MIN_SAMPLES_PER_CLASS,
            require_all_classes=not any_classes,
            near_dup_threshold=config.NEAR_DUP_THRESHOLD,
            accept_unknown_classes=any_classes,
            verify_images=not args.no_verify,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"\nERROR during preprocessing: {exc}")
        return 1
    counts = manifest["counts"]
    print(f"OK  train/val/test = {counts['train']}/{counts['val']}/{counts['test']}  "
          f"classes = {len(manifest['class_names'])}  leakage = "
          f"{manifest['leakage_overlap_after_split']}")

    # ----------------------------------------------------------- train
    from ml.train import train

    print("\n=== [2/4] Training ===")
    try:
        train(
            config.MANIFEST_PATH, config.MODEL_DIR,
            epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr,
            image_size=args.image_size, freeze_backbone=args.freeze_backbone,
            unfreeze_epoch=args.unfreeze_epoch, pretrained=not args.no_pretrained,
            num_workers=args.num_workers, seed=config.SEED,
        )
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"\nERROR during training: {exc}")
        return 1

    # ----------------------------------------------------------- evaluate
    from ml.evaluate import evaluate, evaluate_directory

    print("\n=== [3/4] Evaluating on the held-out test split ===")
    try:
        evaluate(config.MODEL_PATH, config.MANIFEST_PATH, config.EVAL_DIR)
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"\nERROR during evaluation: {exc}")
        return 1

    if args.realworld_test:
        print("\n=== [3b/4] Evaluating on real-world images (domain gap) ===")
        try:
            evaluate_directory(args.realworld_test, config.MODEL_PATH,
                               Path(config.EVAL_DIR) / "realworld")
        except (FileNotFoundError, RuntimeError) as exc:
            print(f"\nERROR during real-world evaluation: {exc}")
            return 1

    # ----------------------------------------------------------- predict
    print("\n=== [4/4] Done ===")
    print(f"Checkpoint : {config.MODEL_PATH}")
    print(f"Reports    : {config.EVAL_DIR}")
    print("\nStart the API with:  uvicorn main:app --reload   (from the backend folder)")

    if args.predict:
        print("\n--- Sample prediction ---")
        return predict_image(args.predict)
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="One-shot plant-disease training pipeline")
    parser.add_argument("--data", type=str, default=None,
                        help="dataset folder containing one sub-folder per class")
    parser.add_argument("--realworld-test", type=str, default=None,
                        help="optional folder of real-world images for a domain-gap evaluation")
    parser.add_argument("--predict", type=str, default=None,
                        help="optional image path to classify after training")
    parser.add_argument("--predict-only", type=str, default=None,
                        help="skip training; just classify this image with the existing checkpoint")
    parser.add_argument("--smoke-test", action="store_true",
                        help="run the pipeline on tiny synthetic data to validate "
                             "your environment (no dataset needed, no real model produced)")
    parser.add_argument("--epochs", type=int, default=config.EPOCHS)
    parser.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=config.LEARNING_RATE)
    parser.add_argument("--image-size", type=int, default=config.IMAGE_SIZE)
    parser.add_argument("--num-workers", type=int, default=config.NUM_WORKERS)
    parser.add_argument("--freeze-backbone", action="store_true")
    parser.add_argument("--unfreeze-epoch", type=int, default=0)
    parser.add_argument("--no-pretrained", action="store_true")
    parser.add_argument("--any-classes", action="store_true",
                        help="treat class folders as custom (not the 38 PlantVillage names)")
    parser.add_argument("--no-verify", action="store_true", help="skip opening every image")
    args = parser.parse_args()

    if args.predict_only:
        return predict_image(args.predict_only)

    if args.smoke_test:
        return smoke_test()

    try:
        return run_pipeline(args)
    except KeyboardInterrupt:
        print("\nInterrupted.")
        return 130
    except Exception:  # noqa: BLE001 - show a real traceback instead of hiding it
        print("\nUnexpected error:\n")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
