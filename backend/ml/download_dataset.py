"""Dataset acquisition helper + provenance notes.

This script documents exactly where the data comes from, how to obtain it and
how to arrange it on disk.  It can optionally download the Kaggle dataset for
you if the ``kaggle`` CLI is installed and credentials are configured.

    # Option A - manual (recommended, no credentials needed)
    Download "New Plant Diseases Dataset" from Kaggle, unzip it and point
    AI_DATASET_DIR at the folder that directly contains the class folders.

    # Option B - automatic (requires ~/.kaggle/kaggle.json)
    python -m ml.download_dataset --download --dataset-dir ml/data/plantvillage

Dataset sources
---------------
1. PlantVillage (original, 38 classes, ~54k images)
   Paper : Hughes & Salathe 2015, https://arxiv.org/abs/1511.08060
   Kaggle: https://www.kaggle.com/datasets/abdallahalidev/plantvillage-dataset
   License: CC0 1.0 (public domain)

2. New Plant Diseases Dataset (augmented, ~87k images) - DEFAULT
   Kaggle: https://www.kaggle.com/datasets/vipoooool/new-plant-diseases-dataset
   License: CC BY-SA 4.0 - check the dataset page before redistribution.

Both use the same 38 class names, which match ``ml/disease_info.py``.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from ml.config import DATASET_DIR, MODEL_DIR

DATASET_SLUG = "vipoooool/new-plant-diseases-dataset"


def download(dataset_dir: Path) -> None:
    dataset_dir.mkdir(parents=True, exist_ok=True)
    print(f"Downloading '{DATASET_SLUG}' to {dataset_dir} ...")
    subprocess.run(
        [
            sys.executable, "-m", "kaggle", "datasets", "download",
            "-d", DATASET_SLUG, "-p", str(dataset_dir), "--unzip",
        ],
        check=True,
    )
    (MODEL_DIR).mkdir(parents=True, exist_ok=True)
    print("Done. Make sure AI_DATASET_DIR points at the folder containing the class sub-folders.")


def verify(dataset_dir: Path) -> int:
    if not dataset_dir.exists():
        print(f"Dataset directory not found: {dataset_dir}")
        return 1
    classes = sorted(p.name for p in dataset_dir.iterdir() if p.is_dir())
    exts = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
    print(f"Found {len(classes)} class folders in {dataset_dir}")
    for c in classes:
        n = sum(1 for _ in (dataset_dir / c).rglob("*") if _.suffix.lower() in exts)
        print(f"  {n:>6}  {c}")
    if len(classes) != 38:
        print("\nNote: expected 38 PlantVillage classes. If your folder nests an extra")
        print("level (e.g. 'plantvillage/color'), point AI_DATASET_DIR at that inner folder.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="PlantVillage dataset helper")
    parser.add_argument("--download", action="store_true", help="download via the kaggle CLI")
    parser.add_argument("--verify", action="store_true", help="list classes and image counts")
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    args = parser.parse_args()

    if args.download:
        download(args.dataset_dir)
    if args.verify or not args.download:
        return verify(args.dataset_dir)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
