"""Train the 38-class plant disease classifier (MobileNetV2 transfer learning).

Highlights
----------
* Reads the reproducible ``manifest.json`` produced by ``ml.preprocess`` so the
  class ordering / train-val-test split can never drift between runs.
* Guards against silent failures: empty splits, labels outside the class map,
  and NaN losses abort training with an actionable message instead of writing a
  garbage checkpoint.
* Optional progressive fine-tuning: freeze the backbone, then unfreeze at a
  chosen epoch.
* Saves the best-validation checkpoint plus ``labels.json``,
  ``training_history.json`` and ``metadata.json`` for full reproducibility.

Usage
-----
    python -m ml.train --epochs 20
    python -m ml.train --freeze-backbone --unfreeze-epoch 3
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import MobileNet_V2_Weights, mobilenet_v2

from ml import config
from ml.disease_info import DISEASE_INFO


class ManifestDataset(Dataset):
    """Dataset backed by a manifest entry list (relative paths + label name)."""

    def __init__(self, root: Path, items: list[dict], class_to_idx: dict, transform):
        self.root = Path(root)
        self.items = items
        self.class_to_idx = class_to_idx
        self.transform = transform

    def __len__(self) -> int:
        return len(self.items)

    def __getitem__(self, idx: int):
        item = self.items[idx]
        image = Image.open(self.root / item["path"]).convert("RGB")
        if self.transform is not None:
            image = self.transform(image)
        return image, self.class_to_idx[item["label"]]


def build_transforms():
    train_tf = transforms.Compose([
        transforms.RandomResizedCrop(config.IMAGE_SIZE, scale=(0.7, 1.0)),
        transforms.RandomHorizontalFlip(),
        transforms.RandomRotation(15),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(config.MEAN, config.STD),
    ])
    eval_tf = transforms.Compose([
        transforms.Resize(int(config.IMAGE_SIZE * 256 / 224)),
        transforms.CenterCrop(config.IMAGE_SIZE),
        transforms.ToTensor(),
        transforms.Normalize(config.MEAN, config.STD),
    ])
    return train_tf, eval_tf


def build_model(num_classes: int, pretrained: bool = True, freeze_backbone: bool = False) -> nn.Module:
    try:
        weights = MobileNet_V2_Weights.IMAGENET1K_V1 if pretrained else None
        model = mobilenet_v2(weights=weights)
    except Exception as exc:  # pragma: no cover - depends on network/cache
        raise RuntimeError(
            "Could not obtain MobileNetV2 pretrained weights (offline?). "
            "Pre-download them or re-run with --no-pretrained."
        ) from exc
    for param in model.features.parameters():
        param.requires_grad = not freeze_backbone
    in_features = model.classifier[1].in_features
    model.classifier[1] = nn.Linear(in_features, num_classes)
    return model


def _run_epoch(model, loader, criterion, device, optimizer=None):
    train = optimizer is not None
    model.train(train)
    total_loss, correct, count = 0.0, 0, 0
    with torch.set_grad_enabled(train):
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            if train:
                optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            if train:
                loss.backward()
                optimizer.step()
            total_loss += loss.item() * images.size(0)
            correct += (outputs.argmax(1) == labels).sum().item()
            count += images.size(0)
    if count == 0:
        return float("nan"), 0.0
    return total_loss / count, correct / count


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def train(
    manifest_path: Path,
    output_dir: Path,
    *,
    epochs: int = config.EPOCHS,
    batch_size: int = config.BATCH_SIZE,
    learning_rate: float = config.LEARNING_RATE,
    image_size: int = config.IMAGE_SIZE,
    freeze_backbone: bool = False,
    unfreeze_epoch: int = 0,
    pretrained: bool = True,
    num_workers: int = config.NUM_WORKERS,
    seed: int = config.SEED,
) -> dict:
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)

    manifest = json.loads(Path(manifest_path).read_text(encoding="utf-8"))
    class_names: list[str] = manifest["class_names"]
    class_to_idx: dict[str, int] = manifest["class_to_idx"]
    root = Path(manifest["dataset_dir"])
    num_classes = len(class_names)

    if num_classes != len(DISEASE_INFO):
        print(f"WARNING: model trained on {num_classes} classes, expected {len(DISEASE_INFO)}.")

    # --- Validate splits / labels before doing anything expensive ---
    for split in ("train", "val", "test"):
        if not manifest["splits"].get(split):
            raise RuntimeError(f"Manifest split '{split}' is empty - re-run ml.preprocess.")
    valid_idx = set(class_to_idx.values())
    bad = [it for it in manifest["splits"]["train"] if class_to_idx.get(it["label"]) not in valid_idx]
    if bad:
        raise RuntimeError(f"{len(bad)} train samples reference unknown labels (e.g. {bad[0]['label']!r}).")

    train_tf, eval_tf = build_transforms()
    datasets = {
        "train": ManifestDataset(root, manifest["splits"]["train"], class_to_idx, train_tf),
        "val": ManifestDataset(root, manifest["splits"]["val"], class_to_idx, eval_tf),
        "test": ManifestDataset(root, manifest["splits"]["test"], class_to_idx, eval_tf),
    }
    loaders = {
        name: DataLoader(ds, batch_size=batch_size, shuffle=(name == "train"),
                         num_workers=num_workers, pin_memory=torch.cuda.is_available())
        for name, ds in datasets.items()
    }
    print(f"Train {len(datasets['train'])} | Val {len(datasets['val'])} | Test {len(datasets['test'])}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = build_model(num_classes, pretrained=pretrained, freeze_backbone=freeze_backbone).to(device)
    print(f"Device: {device} | classes: {num_classes} | pretrained: {pretrained}")

    weights_tensor = torch.tensor(
        [manifest["class_weights"][c] for c in class_names], dtype=torch.float32
    ).to(device)
    criterion = nn.CrossEntropyLoss(weight=weights_tensor)

    def make_optimizer():
        return torch.optim.Adam(
            (p for p in model.parameters() if p.requires_grad),
            lr=learning_rate, weight_decay=config.WEIGHT_DECAY,
        )

    optimizer = make_optimizer()
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
        optimizer, mode="max", factor=0.1, patience=config.LR_SCHEDULER_PATIENCE
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    best_path = output_dir / "plant_disease_model.pth"
    best_acc, best_loss, best_epoch = -1.0, float("inf"), -1
    epochs_without_improve = 0
    history: list[dict] = []

    for epoch in range(epochs):
        if freeze_backbone and unfreeze_epoch and epoch == unfreeze_epoch:
            print(f"[epoch {epoch}] unfreezing backbone for fine-tuning")
            for param in model.features.parameters():
                param.requires_grad = True
            optimizer = make_optimizer()
            scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(
                optimizer, mode="max", factor=0.1, patience=config.LR_SCHEDULER_PATIENCE
            )

        start = time.time()
        train_loss, train_acc = _run_epoch(model, loaders["train"], criterion, device, optimizer)
        val_loss, val_acc = _run_epoch(model, loaders["val"], criterion, device)
        scheduler.step(val_acc)
        elapsed = time.time() - start
        lr = optimizer.param_groups[0]["lr"]
        print(f"[epoch {epoch + 1:02d}/{epochs}] train_loss={train_loss:.4f} "
              f"train_acc={train_acc:.4f} val_loss={val_loss:.4f} val_acc={val_acc:.4f} "
              f"lr={lr:.2e} ({elapsed:.1f}s)")

        if math.isnan(train_loss) or math.isnan(val_loss) or math.isinf(train_loss) or math.isinf(val_loss):
            raise RuntimeError(
                f"Non-finite loss at epoch {epoch + 1} (train={train_loss}, val={val_loss}). "
                "Training aborted; check the manifest/labels and reduce the learning rate."
            )

        history.append({
            "epoch": epoch + 1, "train_loss": train_loss, "train_acc": train_acc,
            "val_loss": val_loss, "val_acc": val_acc, "lr": lr, "seconds": round(elapsed, 2),
        })

        if val_acc > best_acc:
            best_acc, best_loss, best_epoch = val_acc, val_loss, epoch + 1
            epochs_without_improve = 0
            torch.save({
                "arch": "mobilenet_v2",
                "state_dict": model.state_dict(),
                "class_names": class_names,
                "num_classes": num_classes,
                "image_size": image_size,
                "mean": config.MEAN,
                "std": config.STD,
                "threshold": config.CONFIDENCE_THRESHOLD,
                "val_acc": val_acc,
                "val_loss": val_loss,
                "epoch": epoch + 1,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }, best_path)
            print(f"  -> saved best checkpoint (val_acc={val_acc:.4f})")
        else:
            epochs_without_improve += 1
            if epochs_without_improve >= config.EARLY_STOP_PATIENCE:
                print(f"Early stopping after {epoch + 1} epochs (no val improvement).")
                break

    (output_dir / "labels.json").write_text(json.dumps(class_names, indent=2), encoding="utf-8")
    (output_dir / "training_history.json").write_text(json.dumps(history, indent=2), encoding="utf-8")

    metadata = {
        "arch": "mobilenet_v2",
        "num_classes": num_classes,
        "class_names": class_names,
        "image_size": image_size,
        "mean": config.MEAN,
        "std": config.STD,
        "best_val_acc": best_acc,
        "best_val_loss": best_loss,
        "best_epoch": best_epoch,
        "epochs_run": len(history),
        "batch_size": batch_size,
        "learning_rate": learning_rate,
        "freeze_backbone": freeze_backbone,
        "unfreeze_epoch": unfreeze_epoch,
        "pretrained": pretrained,
        "seed": seed,
        "device": str(device),
        "torch_version": torch.__version__,
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256(Path(manifest_path)),
        "confidence_threshold": config.CONFIDENCE_THRESHOLD,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }
    (output_dir / "metadata.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")

    print(f"\nDone. Best val_acc={best_acc:.4f} at epoch {best_epoch}.")
    print(f"Checkpoint: {best_path}")
    print(f"Metadata  : {output_dir / 'metadata.json'}")
    return metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Train the plant disease classifier")
    parser.add_argument("--manifest", type=Path, default=config.MANIFEST_PATH)
    parser.add_argument("--output-dir", type=Path, default=config.MODEL_DIR)
    parser.add_argument("--epochs", type=int, default=config.EPOCHS)
    parser.add_argument("--batch-size", type=int, default=config.BATCH_SIZE)
    parser.add_argument("--lr", type=float, default=config.LEARNING_RATE)
    parser.add_argument("--image-size", type=int, default=config.IMAGE_SIZE)
    parser.add_argument("--num-workers", type=int, default=config.NUM_WORKERS)
    parser.add_argument("--seed", type=int, default=config.SEED)
    parser.add_argument("--freeze-backbone", action="store_true")
    parser.add_argument("--unfreeze-epoch", type=int, default=0,
                        help="epoch index at which to unfreeze the backbone (with --freeze-backbone)")
    parser.add_argument("--no-pretrained", action="store_true", help="train from scratch (offline)")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    if not manifest_path.exists():
        print(f"Manifest not found at {manifest_path}; building it now...")
        from ml.preprocess import build_manifest
        build_manifest(config.DATASET_DIR, config.TRAIN_RATIO, config.VAL_RATIO,
                       config.SPLIT_SEED, manifest_path)

    try:
        train(
            manifest_path, Path(args.output_dir),
            epochs=args.epochs, batch_size=args.batch_size, learning_rate=args.lr,
            image_size=args.image_size, freeze_backbone=args.freeze_backbone,
            unfreeze_epoch=args.unfreeze_epoch, pretrained=not args.no_pretrained,
            num_workers=args.num_workers, seed=args.seed,
        )
    except (RuntimeError, FileNotFoundError) as exc:
        print(f"\nERROR: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
