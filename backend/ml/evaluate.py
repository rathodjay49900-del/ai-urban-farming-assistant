"""Evaluate a trained checkpoint on the held-out test split.

Produces, under ``backend/ml/evaluation/``:
    * ``report.json``               - overall + per-class metrics, class names, notes
    * ``report.txt``                - human readable summary (overall + per class)
    * ``confusion_matrix.png``      - normalized confusion matrix
    * ``confusion_matrix.json``     - raw counts + class order
    * ``classification_report.json``- sklearn per-class precision/recall/f1/support
    * ``training_history.png``      - loss / accuracy / LR curves (if history exists)
    * ``experiment.json``           - checkpoint + manifest metadata for reproducibility

Usage
-----
    python -m ml.evaluate
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from torch.utils.data import DataLoader
from torchvision import transforms
from torchvision.models import mobilenet_v2

from ml import config
from ml.preprocess import IMAGE_EXTS
from ml.train import ManifestDataset

try:  # optional - evaluation still works without sklearn, just with fewer metrics
    from sklearn.metrics import (classification_report as sk_report,
                                 confusion_matrix as sk_confusion_matrix)
    _HAVE_SKLEARN = True
except Exception:  # pragma: no cover
    _HAVE_SKLEARN = False


def _eval_transform(image_size: int, mean, std):
    return transforms.Compose([
        transforms.Resize(int(image_size * 256 / 224)),
        transforms.CenterCrop(image_size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])


def _load_model(checkpoint_path: Path, device):
    ckpt = torch.load(checkpoint_path, map_location=device)
    missing = {"state_dict", "class_names"} - set(ckpt)
    if missing:
        raise RuntimeError(f"Checkpoint is missing required keys: {sorted(missing)}")
    if not ckpt["class_names"]:
        raise RuntimeError("Checkpoint has an empty class list")
    class_names = ckpt["class_names"]
    model = mobilenet_v2(weights=None)
    model.classifier[1] = torch.nn.Linear(model.classifier[1].in_features, len(class_names))
    model.load_state_dict(ckpt["state_dict"])
    model.to(device).eval()
    return model, class_names, ckpt


def _plot_confusion_matrix(cm: np.ndarray, class_names: list[str], out_path: Path) -> bool:
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False
    with np.errstate(divide="ignore", invalid="ignore"):
        norm = cm.astype("float") / cm.sum(axis=1, keepdims=True)
    norm = np.nan_to_num(norm)
    size = max(10, len(class_names) * 0.35)
    fig, ax = plt.subplots(figsize=(size, size))
    im = ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xlabel("Predicted"), ax.set_ylabel("True"), ax.set_title("Normalized confusion matrix")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=90, fontsize=6)
    ax.set_yticklabels(class_names, fontsize=6)
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def _plot_history(history_path: Path, out_path: Path) -> bool:
    if not history_path.exists():
        return False
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except Exception:
        return False
    history = json.loads(history_path.read_text(encoding="utf-8"))
    epochs = [h["epoch"] for h in history]
    fig, axes = plt.subplots(1, 3, figsize=(16, 4))
    axes[0].plot(epochs, [h["train_loss"] for h in history], label="train")
    axes[0].plot(epochs, [h["val_loss"] for h in history], label="val")
    axes[0].set_title("Loss"), axes[0].set_xlabel("epoch"), axes[0].legend()
    axes[1].plot(epochs, [h["train_acc"] for h in history], label="train")
    axes[1].plot(epochs, [h["val_acc"] for h in history], label="val")
    axes[1].set_title("Accuracy"), axes[1].set_xlabel("epoch"), axes[1].legend()
    axes[2].plot(epochs, [h["lr"] for h in history])
    axes[2].set_title("Learning rate"), axes[2].set_xlabel("epoch")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    return True


def evaluate(
    checkpoint_path: Path = config.MODEL_PATH,
    manifest_path: Path = config.MANIFEST_PATH,
    output_dir: Path = config.EVAL_DIR,
) -> dict:
    if not Path(checkpoint_path).exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}. Train first (python -m ml.train).")
    if not Path(manifest_path).exists():
        raise FileNotFoundError(f"Manifest not found: {manifest_path}. Run ml.preprocess first.")

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, class_names, ckpt = _load_model(Path(checkpoint_path), device)

    if manifest["class_names"] != class_names:
        print("WARNING: manifest class_names differ from checkpoint class_names; "
              "using the checkpoint ordering for evaluation.")

    root = Path(manifest["dataset_dir"])
    class_to_idx = {name: i for i, name in enumerate(class_names)}
    test_items = [it for it in manifest["splits"]["test"] if it["label"] in class_to_idx]
    if not test_items:
        raise RuntimeError("No test samples available for evaluation.")
    # Preprocessing must match the checkpoint's own training geometry, not the
    # current global config (the user may have trained with --image-size).
    size = ckpt.get("image_size", config.IMAGE_SIZE)
    mean = ckpt.get("mean", config.MEAN)
    std = ckpt.get("std", config.STD)
    ds = ManifestDataset(root, test_items, class_to_idx, _eval_transform(size, mean, std))
    loader = DataLoader(ds, batch_size=config.BATCH_SIZE, shuffle=False, num_workers=config.NUM_WORKERS)

    y_true, y_pred, y_conf = [], [], []
    with torch.no_grad():
        for images, labels in loader:
            images = images.to(device)
            probs = torch.softmax(model(images), dim=1)
            conf, preds = probs.max(1)
            y_true.extend(labels.tolist())
            y_pred.extend(preds.cpu().tolist())
            y_conf.extend(conf.cpu().tolist())

    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    y_conf = np.array(y_conf)
    n = len(y_true)
    overall_acc = float((y_true == y_pred).mean())

    cm = sk_confusion_matrix(y_true, y_pred, labels=list(range(len(class_names)))) if _HAVE_SKLEARN \
        else _manual_confusion(y_true, y_pred, len(class_names))

    per_class = {}
    for i, name in enumerate(class_names):
        mask = y_true == i
        support = int(mask.sum())
        correct = int(((y_pred == i) & mask).sum())
        recall = correct / support if support else 0.0
        pred_mask = y_pred == i
        tp = correct
        precision = tp / int(pred_mask.sum()) if pred_mask.sum() else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) else 0.0
        per_class[name] = {
            "support": support, "precision": round(precision, 4),
            "recall": round(recall, 4), "f1": round(f1, 4),
        }

    # Macro / weighted aggregates.
    supports = np.array([per_class[c]["support"] for c in class_names], dtype=float)
    precs = np.array([per_class[c]["precision"] for c in class_names])
    recs = np.array([per_class[c]["recall"] for c in class_names])
    f1s = np.array([per_class[c]["f1"] for c in class_names])
    denom = supports.sum() or 1.0
    aggregate = {
        "macro_precision": round(float(precs.mean()), 4),
        "macro_recall": round(float(recs.mean()), 4),
        "macro_f1": round(float(f1s.mean()), 4),
        "weighted_precision": round(float((precs * supports).sum() / denom), 4),
        "weighted_recall": round(float((recs * supports).sum() / denom), 4),
        "weighted_f1": round(float((f1s * supports).sum() / denom), 4),
    }

    notes = [
        "Evaluated on the held-out test split only - never on training data.",
        "Dataset images are controlled-background (PlantVillage); real-world phone "
        "photos may perform worse. Validate on your own images before relying on it.",
        "Softmax confidence is not a calibrated probability; the uncertainty "
        "threshold should be tuned on the validation split.",
    ]

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    report = {
        "checkpoint": ckpt.get("created_at"),
        "checkpoint_epoch": ckpt.get("epoch"),
        "num_test_samples": n,
        "num_classes": len(class_names),
        "overall_accuracy": round(overall_acc, 4),
        "mean_confidence": round(float(y_conf.mean()), 4),
        "aggregate": aggregate,
        "per_class": per_class,
        "class_names": class_names,
        "notes": notes,
    }
    (output_dir / "report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (output_dir / "confusion_matrix.json").write_text(
        json.dumps({"class_names": class_names, "matrix": cm.tolist()}, indent=2), encoding="utf-8")

    txt_lines = [
        "Plant disease classifier - test set evaluation",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        f"Checkpoint: {checkpoint_path}",
        f"Test samples: {n}  |  Classes: {len(class_names)}",
        f"Overall accuracy: {overall_acc:.4f}",
        f"Macro    P/R/F1: {aggregate['macro_precision']:.4f} / {aggregate['macro_recall']:.4f} / {aggregate['macro_f1']:.4f}",
        f"Weighted P/R/F1: {aggregate['weighted_precision']:.4f} / {aggregate['weighted_recall']:.4f} / {aggregate['weighted_f1']:.4f}",
        "",
        f"{'class':50s} {'support':>7s} {'prec':>6s} {'rec':>6s} {'f1':>6s}",
    ]
    for name in class_names:
        pc = per_class[name]
        txt_lines.append(
            f"{name:50s} {pc['support']:7d} {pc['precision']:6.3f} {pc['recall']:6.3f} {pc['f1']:6.3f}")
    txt_lines += ["", "Notes:"] + [f"- {note}" for note in notes]
    (output_dir / "report.txt").write_text("\n".join(txt_lines) + "\n", encoding="utf-8")

    if _HAVE_SKLEARN:
        cr = sk_report(y_true, y_pred, labels=list(range(len(class_names))),
                       target_names=class_names, output_dict=True, zero_division=0)
        (output_dir / "classification_report.json").write_text(json.dumps(cr, indent=2), encoding="utf-8")

    cm_plot = _plot_confusion_matrix(cm, class_names, output_dir / "confusion_matrix.png")
    hist_plot = _plot_history(config.TRAINING_HISTORY_PATH, output_dir / "training_history.png")

    experiment = {
        "checkpoint_path": str(checkpoint_path),
        "checkpoint": {k: v for k, v in ckpt.items() if k != "state_dict"},
        "manifest_path": str(manifest_path),
        "manifest_counts": manifest.get("counts"),
        "dataset_dir": manifest.get("dataset_dir"),
        "device": str(device),
        "confusion_matrix_png": cm_plot,
        "training_history_png": hist_plot,
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "torch_version": torch.__version__,
    }
    (output_dir / "experiment.json").write_text(json.dumps(experiment, indent=2), encoding="utf-8")

    print(f"Overall accuracy: {overall_acc:.4f}")
    print(f"Macro F1        : {aggregate['macro_f1']:.4f}")
    print(f"Artifacts in    : {output_dir}")
    return report


def evaluate_directory(
    directory: Path,
    checkpoint_path: Path = config.MODEL_PATH,
    output_dir: Path | None = None,
) -> dict:
    """Evaluate a checkpoint on a folder of real-world images (domain-gap check).

    * If ``directory`` contains one sub-folder per class, per-class accuracy is
      reported (only classes present in the checkpoint are scored).
    * If ``directory`` is flat, every image gets a prediction (no accuracy,
      since there are no labels).
    """
    directory = Path(directory)
    if not directory.exists():
        raise FileNotFoundError(f"Real-world folder not found: {directory}")
    if not Path(checkpoint_path).exists():
        raise FileNotFoundError(f"Checkpoint not found: {checkpoint_path}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model, class_names, ckpt = _load_model(Path(checkpoint_path), device)
    class_to_idx = {name: i for i, name in enumerate(class_names)}

    size = ckpt.get("image_size", config.IMAGE_SIZE)
    mean = ckpt.get("mean", config.MEAN)
    std = ckpt.get("std", config.STD)
    tf = transforms.Compose([
        transforms.Resize(int(size * 256 / 224)),
        transforms.CenterCrop(size),
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    subdirs = [p for p in directory.iterdir() if p.is_dir()]
    labeled = [d for d in subdirs if d.name in class_to_idx]
    output_dir = Path(output_dir or (config.EVAL_DIR / "realworld"))
    output_dir.mkdir(parents=True, exist_ok=True)

    predictions: list[dict] = []
    overall_acc = None
    per_class: dict[str, dict] = {}

    if labeled:
        items = []
        for d in labeled:
            for img in d.rglob("*"):
                if img.suffix.lower() in IMAGE_EXTS:
                    items.append({"path": str(img.relative_to(directory)).replace("\\", "/"),
                                  "label": d.name})
        if not items:
            raise RuntimeError(f"No labelled images under {directory}")
        ds = ManifestDataset(directory, items, class_to_idx, tf)
        loader = DataLoader(ds, batch_size=config.BATCH_SIZE, shuffle=False, num_workers=config.NUM_WORKERS)
        y_true, y_pred = [], []
        with torch.no_grad():
            for images, labels in loader:
                probs = torch.softmax(model(images.to(device)), dim=1)
                conf, preds = probs.max(1)
                for c, p, t in zip(conf.tolist(), preds.tolist(), labels.tolist()):
                    y_true.append(t)
                    y_pred.append(p)
                    predictions.append({"true": class_names[t], "pred": class_names[p],
                                        "confidence": round(c, 4)})
        y_true = np.array(y_true)
        y_pred = np.array(y_pred)
        overall_acc = float((y_true == y_pred).mean())
        for i, name in enumerate(class_names):
            mask = y_true == i
            support = int(mask.sum())
            if support:
                per_class[name] = {"support": support,
                                   "recall": round(float(((y_pred == i) & mask).mean()), 4)}
    else:
        files = sorted(p for p in directory.rglob("*") if p.suffix.lower() in IMAGE_EXTS)
        if not files:
            raise RuntimeError(f"No images found under {directory}")
        with torch.no_grad():
            for f in files:
                image = Image.open(f).convert("RGB")
                tensor = tf(image).unsqueeze(0).to(device)
                probs = torch.softmax(model(tensor), dim=1)[0]
                conf, pred = probs.max(0)
                predictions.append({"file": str(f.relative_to(directory)).replace("\\", "/"),
                                    "pred": class_names[int(pred)], "confidence": round(float(conf), 4)})

    report = {
        "directory": str(directory),
        "checkpoint": ckpt.get("created_at"),
        "mode": "labelled" if labeled else "unlabelled",
        "num_images": len(predictions),
        "num_scored_classes": len(per_class),
        "overall_accuracy": round(overall_acc, 4) if overall_acc is not None else None,
        "per_class": per_class,
        "predictions": predictions,
        "notes": [
            "This folder is treated as real-world data (e.g. phone/field photos).",
            "A large drop vs the PlantVillage test accuracy is the expected domain gap.",
            "Only classes present in the checkpoint are scored.",
        ],
    }
    (output_dir / "realworld_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Real-world images: {len(predictions)} | accuracy: "
          f"{overall_acc if overall_acc is None else round(overall_acc, 4)} | report: {output_dir}")
    return report


def _manual_confusion(y_true, y_pred, n_classes):
    cm = np.zeros((n_classes, n_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[int(t), int(p)] += 1
    return cm


def main() -> int:
    parser = argparse.ArgumentParser(description="Evaluate the plant disease classifier")
    parser.add_argument("--checkpoint", type=Path, default=config.MODEL_PATH)
    parser.add_argument("--manifest", type=Path, default=config.MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=config.EVAL_DIR)
    parser.add_argument("--realworld-dir", type=Path, default=None,
                        help="also evaluate on a folder of real-world images (domain gap)")
    args = parser.parse_args()
    try:
        evaluate(args.checkpoint, args.manifest, args.output_dir)
        if args.realworld_dir:
            evaluate_directory(args.realworld_dir, args.checkpoint, Path(args.output_dir) / "realworld")
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"\nERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
