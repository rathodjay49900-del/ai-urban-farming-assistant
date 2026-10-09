"""Tests for dataset verification and manifest generation."""

import json

import pytest
from PIL import Image

from ml.disease_info import DISEASE_INFO
from ml.preprocess import build_manifest, dhash_of

CLASSES = ["Apple___Apple_scab", "Tomato___healthy", "Potato___Early_blight"]


def _make_dataset(root, classes, per_class=12, corrupt=False, duplicate=False):
    for ci, label in enumerate(classes):
        d = root / label
        d.mkdir(parents=True, exist_ok=True)
        for i in range(per_class):
            color = ((ci * 60 + i * 5) % 200 + 30, (i * 9) % 200 + 30, (i * 13) % 200 + 30)
            Image.new("RGB", (32, 32), color).save(d / f"img_{i}.jpg")
        if duplicate:
            (d / "dup.jpg").write_bytes((d / "img_0.jpg").read_bytes())
    if corrupt:
        (root / classes[0] / "broken.jpg").write_bytes(b"definitely-not-an-image")


def test_build_manifest_basic(tmp_path):
    root = tmp_path / "data"
    _make_dataset(root, CLASSES)
    out = tmp_path / "manifest.json"
    m = build_manifest(root, 0.70, 0.15, 42, out, require_all_classes=False)

    assert out.exists()
    assert m["counts"]["train"] + m["counts"]["val"] + m["counts"]["test"] == 36
    assert m["leakage_overlap_after_split"] == 0
    assert set(m["class_names"]) == set(CLASSES)
    assert m["class_to_idx"] == {name: i for i, name in enumerate(sorted(CLASSES))}
    for label in CLASSES:
        c = m["per_class_counts"][label]
        assert c["train"] + c["val"] + c["test"] == 12
    # Every split is non-empty and class weights exist for all classes.
    assert m["counts"]["val"] > 0 and m["counts"]["test"] > 0
    assert set(m["class_weights"]) == set(CLASSES)


def test_duplicates_are_removed(tmp_path):
    root = tmp_path / "data"
    _make_dataset(root, CLASSES, duplicate=True)
    m = build_manifest(root, 0.70, 0.15, 42, tmp_path / "manifest.json", require_all_classes=False)
    assert m["duplicates_removed"] >= len(CLASSES)


def test_corrupt_files_are_reported_and_skipped(tmp_path):
    root = tmp_path / "data"
    _make_dataset(root, CLASSES, corrupt=True)
    m = build_manifest(root, 0.70, 0.15, 1, tmp_path / "manifest.json", require_all_classes=False)
    assert m["corrupt_files_skipped"] >= 1
    assert m["verification"]["corrupt_count"] >= 1


def test_min_samples_enforced(tmp_path):
    root = tmp_path / "data"
    _make_dataset(root, ["Tomato___healthy"], per_class=3)
    with pytest.raises(RuntimeError, match="fewer than"):
        build_manifest(root, 0.70, 0.15, 1, tmp_path / "manifest.json", require_all_classes=False)


def test_missing_classes_can_fail_or_be_allowed(tmp_path):
    root = tmp_path / "data"
    _make_dataset(root, ["Tomato___healthy"], per_class=12)
    with pytest.raises(RuntimeError, match="Missing"):
        build_manifest(root, 0.70, 0.15, 1, tmp_path / "m.json", require_all_classes=True)
    m = build_manifest(root, 0.70, 0.15, 1, tmp_path / "m2.json", require_all_classes=False)
    assert m["class_names"] == ["Tomato___healthy"]
    assert set(m["missing_classes"]) == set(DISEASE_INFO) - {"Tomato___healthy"}


def test_near_duplicate_threshold_runs(tmp_path):
    root = tmp_path / "data"
    _make_dataset(root, CLASSES)
    m = build_manifest(root, 0.70, 0.15, 7, tmp_path / "manifest.json",
                       require_all_classes=False, near_dup_threshold=1)
    assert "near_duplicates_removed" in m
    assert m["near_dup_threshold"] == 1
    # Verification report is written next to the manifest by default.
    report = json.loads((tmp_path / "verification_report.json").read_text())
    assert report["class_count"] == len(CLASSES)


def test_dhash_equal_for_near_identical_images():
    base = Image.new("L", (8, 8))
    base.putdata([(i * 37) % 200 for i in range(64)])
    variant = Image.new("L", (8, 8))
    variant.putdata([min(255, (i * 37) % 200 + 2) for i in range(64)])
    assert dhash_of(base) == dhash_of(variant)


def test_dhash_differs_for_different_patterns():
    left = Image.new("L", (8, 8))
    left.putdata(list(range(64)))
    right = Image.new("L", (8, 8))
    right.putdata(list(range(63, -1, -1)))
    assert dhash_of(left) != dhash_of(right)
