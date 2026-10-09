"""Tests for the canonical 38-class disease metadata."""

from ml.disease_info import DISEASE_INFO, get_info, labels


def test_expected_number_of_classes():
    assert len(DISEASE_INFO) == 38


def test_labels_are_sorted_and_match_keys():
    assert labels() == sorted(DISEASE_INFO.keys())
    assert len(labels()) == len(set(labels()))


def test_get_info_returns_full_record_for_known_class():
    name = labels()[0]
    info = get_info(name)
    for key in ("crop", "disease", "healthy", "severity", "symptoms", "treatment",
                "prevention", "explanation"):
        assert key in info


def test_get_info_handles_unknown_label_gracefully():
    info = get_info("Not___A_Real_Class")
    assert info["healthy"] is False
    assert info["treatment"]


def test_healthy_and_diseased_classes_are_distinct():
    healthy = [k for k, v in DISEASE_INFO.items() if v["disease"] == "Healthy"]
    assert healthy, "expected at least one healthy class"
    assert any(v["disease"] != "Healthy" for v in DISEASE_INFO.values())
