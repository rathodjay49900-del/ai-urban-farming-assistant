"""Dataset preprocessing + verification for the plant disease classifier.

Responsibilities
----------------
1. Scan an ImageFolder-style dataset (one folder per class) and **verify** it:
   supported classes only, every image openable (corrupt files are reported and
   skipped), supported extensions, and per-class sample counts.
2. Remove exact duplicate images (MD5) and - optionally - near duplicates
   (perceptual dHash) so the same photo cannot leak across splits.
3. Produce a stratified 70% train / 15% val / 15% test split with a fixed seed.
4. Compute inverse-frequency class weights for the (possibly imbalanced) train set.
5. Write a reproducible ``manifest.json`` and a ``verification_report.json``.

No images are copied or moved: the manifest stores relative paths, so the
dataset stays untouched on disk.  ``train.py`` consumes the manifest directly and
reuses the exact same class ordering, so class indices never change.

Usage
-----
    python -m ml.preprocess --dataset-dir ml/data/plantvillage/color
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
from collections import defaultdict
from pathlib import Path

from PIL import Image

from ml import config
from ml.disease_info import DISEASE_INFO

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
MIN_SPLIT_SAMPLES = 7  # enough for a non-empty train/val/test at 70/15/15


def md5_of(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.md5()
    with path.open("rb") as fh:
        while True:
            data = fh.read(chunk)
            if not data:
                break
            h.update(data)
    return h.hexdigest()


def dhash_of(image: Image.Image, hash_size: int = 8) -> int:
    """Difference hash (64-bit) used for near-duplicate detection."""
    gray = image.convert("L").resize((hash_size + 1, hash_size), Image.LANCZOS)
    pixels = list(gray.getdata())
    bits = 0
    idx = 0
    for row in range(hash_size):
        base = row * (hash_size + 1)
        for col in range(hash_size):
            if pixels[base + col] > pixels[base + col + 1]:
                bits |= 1 << idx
            idx += 1
    return bits


def _is_verifiable_image(path: Path) -> bool:
    try:
        with Image.open(path) as im:
            im.verify()
        return True
    except Exception:
        return False


def find_class_root(dataset_dir: Path) -> Path:
    """Handle datasets that nest the class folders one level deeper."""
    if not dataset_dir.exists():
        return dataset_dir
    subdirs = [p for p in dataset_dir.iterdir() if p.is_dir()]
    if len(subdirs) == 1:
        nested = [p for p in subdirs[0].iterdir() if p.is_dir()]
        known_nested = sum(1 for p in nested if p.name in DISEASE_INFO)
        known_here = sum(1 for p in subdirs if p.name in DISEASE_INFO)
        if known_nested > known_here:
            print(f"Detected nested layout, using: {subdirs[0]}")
            return subdirs[0]
    return dataset_dir


def build_manifest(
    dataset_dir: Path,
    train_ratio: float,
    val_ratio: float,
    seed: int,
    output: Path,
    *,
    min_samples: int | None = None,
    require_all_classes: bool | None = None,
    near_dup_threshold: int | None = None,
    verify_images: bool = True,
    verification_output: Path | None = None,
) -> dict:
    min_samples = config.MIN_SAMPLES_PER_CLASS if min_samples is None else min_samples
    require_all_classes = config.REQUIRE_ALL_CLASSES if require_all_classes is None else require_all_classes
    near_dup_threshold = config.NEAR_DUP_THRESHOLD if near_dup_threshold is None else near_dup_threshold
    verification_output = verification_output or output.parent / "verification_report.json"
    effective_min = max(min_samples, MIN_SPLIT_SAMPLES)

    dataset_dir = find_class_root(Path(dataset_dir))
    if not dataset_dir.exists():
        raise FileNotFoundError(f"Dataset directory not found: {dataset_dir}")

    class_dirs = sorted(p for p in dataset_dir.iterdir() if p.is_dir())
    if not class_dirs:
        raise FileNotFoundError(f"No class sub-folders inside {dataset_dir}")

    seen_hashes: set[str] = set()
    path_digest: dict[str, str] = {}
    dhash_buckets: dict[int, list[int]] = defaultdict(list)
    per_class: dict[str, list[str]] = defaultdict(list)
    present_classes: set[str] = set()
    unknown_classes: list[str] = []
    corrupt_files: list[str] = []
    duplicates = 0
    near_dups = 0
    total_scanned = 0

    for cdir in class_dirs:
        label = cdir.name
        if label not in DISEASE_INFO:
            unknown_classes.append(label)
            print(f"  ! unknown class folder (skipped): {label}")
            continue
        present_classes.add(label)
        for img in sorted(cdir.rglob("*")):
            if img.suffix.lower() not in IMAGE_EXTS:
                continue
            total_scanned += 1
            rel = str(img.relative_to(dataset_dir)).replace("\\", "/")
            if verify_images and not _is_verifiable_image(img):
                corrupt_files.append(rel)
                print(f"  ! corrupt/unreadable image skipped: {rel}")
                continue
            digest = md5_of(img)
            if digest in seen_hashes:
                duplicates += 1
                continue
            if near_dup_threshold > 0:
                with Image.open(img) as im:
                    h = dhash_of(im)
                bucket = h >> 48
                if any((prev ^ h).bit_count() <= near_dup_threshold
                       for prev in dhash_buckets.get(bucket, [])):
                    near_dups += 1
                    continue
                dhash_buckets[bucket].append(h)
            seen_hashes.add(digest)
            path_digest[rel] = digest
            per_class[label].append(rel)

    if not per_class:
        raise RuntimeError("No usable images found. Check AI_DATASET_DIR.")

    missing_classes = sorted(set(DISEASE_INFO) - present_classes)
    too_small = {c: len(f) for c, f in per_class.items() if len(f) < effective_min}
    if too_small:
        raise RuntimeError(
            f"{len(too_small)} class(es) have fewer than {effective_min} usable images; "
            f"a stratified 70/15/15 split would leave a split empty: {too_small}"
        )
    if missing_classes and require_all_classes:
        raise RuntimeError(
            f"Missing {len(missing_classes)} supported class folder(s): {missing_classes}. "
            "Set AI_REQUIRE_ALL_CLASSES=false to train on a subset (class indices remain the found ones)."
        )

    rng = random.Random(seed)
    splits: dict[str, list[dict]] = {"train": [], "val": [], "test": []}
    class_counts: dict[str, dict[str, int]] = {}

    for label, files in sorted(per_class.items()):
        rng.shuffle(files)
        n = len(files)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)
        train = files[:n_train]
        val = files[n_train:n_train + n_val]
        test = files[n_train + n_val:]
        for f in train:
            splits["train"].append({"path": f, "label": label})
        for f in val:
            splits["val"].append({"path": f, "label": label})
        for f in test:
            splits["test"].append({"path": f, "label": label})
        class_counts[label] = {"train": len(train), "val": len(val), "test": len(test)}

    # Class weights (inverse frequency) for the train split -> handles imbalance.
    train_counts = {c: class_counts[c]["train"] for c in class_counts}
    total = sum(train_counts.values())
    n_classes = len(train_counts)
    class_weights = {
        c: round(total / (n_classes * max(cnt, 1)), 4) for c, cnt in train_counts.items()
    }

    # Leakage guard: no image hash may appear in more than one split.
    split_hashes: dict[str, set[str]] = {}
    for split_name, items in splits.items():
        split_hashes[split_name] = {path_digest[it["path"]] for it in items}
    leak = (split_hashes["train"] & split_hashes["val"]) | \
           (split_hashes["train"] & split_hashes["test"]) | \
           (split_hashes["val"] & split_hashes["test"])

    class_names = sorted(class_counts.keys())
    manifest = {
        "class_names": class_names,
        "class_to_idx": {name: i for i, name in enumerate(class_names)},
        "dataset_dir": str(dataset_dir),
        "seed": seed,
        "ratios": {"train": train_ratio, "val": val_ratio, "test": 1 - train_ratio - val_ratio},
        "counts": {
            "train": len(splits["train"]),
            "val": len(splits["val"]),
            "test": len(splits["test"]),
        },
        "duplicates_removed": duplicates,
        "near_duplicates_removed": near_dups,
        "near_dup_threshold": near_dup_threshold,
        "corrupt_files_skipped": len(corrupt_files),
        "unknown_classes_skipped": unknown_classes,
        "missing_classes": missing_classes,
        "leakage_overlap_after_split": len(leak),
        "class_weights": class_weights,
        "per_class_counts": class_counts,
        "splits": splits,
    }

    verification = {
        "dataset_dir": str(dataset_dir),
        "status": "ok" if not (missing_classes or corrupt_files or unknown_classes or leak) else "warnings",
        "total_scanned": total_scanned,
        "usable_images": sum(len(v) for v in per_class.values()),
        "class_count": len(per_class),
        "expected_classes": len(DISEASE_INFO),
        "missing_classes": missing_classes,
        "unknown_class_folders": unknown_classes,
        "corrupt_count": len(corrupt_files),
        "corrupt_files": corrupt_files[:50],
        "exact_duplicates_removed": duplicates,
        "near_duplicates_removed": near_dups,
        "near_dup_threshold": near_dup_threshold,
        "per_class_counts": {c: len(f) for c, f in sorted(per_class.items())},
        "leakage_overlap_after_split": len(leak),
    }

    output.parent.mkdir(parents=True, exist_ok=True)
    verification_output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    verification_output.write_text(json.dumps(verification, indent=2), encoding="utf-8")
    return {**manifest, "verification": verification}


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify dataset and build a reproducible train/val/test manifest")
    parser.add_argument("--dataset-dir", type=Path, default=config.DATASET_DIR)
    parser.add_argument("--output", type=Path, default=config.MANIFEST_PATH)
    parser.add_argument("--verification-output", type=Path, default=config.VERIFICATION_PATH)
    parser.add_argument("--train-ratio", type=float, default=config.TRAIN_RATIO)
    parser.add_argument("--val-ratio", type=float, default=config.VAL_RATIO)
    parser.add_argument("--seed", type=int, default=config.SPLIT_SEED)
    parser.add_argument("--min-samples", type=int, default=config.MIN_SAMPLES_PER_CLASS)
    parser.add_argument("--near-dup-threshold", type=int, default=config.NEAR_DUP_THRESHOLD,
                        help="dHash Hamming distance for near-duplicate removal (0 = off)")
    parser.add_argument("--allow-missing", action="store_true",
                        help="do not fail when some of the 38 supported classes are absent")
    parser.add_argument("--no-verify", action="store_true", help="skip opening every image (faster)")
    args = parser.parse_args()

    try:
        m = build_manifest(
            args.dataset_dir, args.train_ratio, args.val_ratio, args.seed, args.output,
            min_samples=args.min_samples,
            require_all_classes=not args.allow_missing,
            near_dup_threshold=args.near_dup_threshold,
            verify_images=not args.no_verify,
            verification_output=args.verification_output,
        )
    except (FileNotFoundError, RuntimeError) as exc:
        print(f"\nERROR: {exc}")
        return 1

    v = m["verification"]
    print("\n=== Preprocessing summary ===")
    print(f"Classes present          : {v['class_count']} / {v['expected_classes']}")
    print(f"Train / Val / Test       : {m['counts']['train']} / {m['counts']['val']} / {m['counts']['test']}")
    print(f"Corrupt files skipped    : {v['corrupt_count']}")
    print(f"Exact duplicates removed : {v['exact_duplicates_removed']}")
    print(f"Near duplicates removed  : {v['near_duplicates_removed']} (threshold {v['near_dup_threshold']})")
    print(f"Unknown class folders    : {v['unknown_class_folders']}")
    print(f"Missing supported classes: {v['missing_classes']}")
    print(f"Cross-split leakage      : {v['leakage_overlap_after_split']} (must be 0)")
    print(f"Manifest                 : {args.output}")
    print(f"Verification report      : {args.verification_output}")
    if v["leakage_overlap_after_split"] > 0:
        print("WARNING: data leakage detected between splits!")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
