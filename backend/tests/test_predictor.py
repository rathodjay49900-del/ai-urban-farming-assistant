"""Tests for the gatekeeper and the disease classifier fallback behaviour."""

from ml import config
from ml.predictor import DiseaseClassifier, DiseasePredictor, PlantGatekeeper


def test_classifier_reports_not_ready_for_missing_checkpoint(tmp_path):
    classifier = DiseaseClassifier(model_path=tmp_path / "does_not_exist.pth")
    assert classifier.ready is False
    assert classifier.predict(b"whatever") is None
    status = classifier.status()
    assert status["loaded"] is False
    assert status["num_classes"] == 0
    assert status["error"]


def test_classifier_rejects_invalid_checkpoint(tmp_path):
    bad = tmp_path / "bad.pth"
    bad.write_bytes(b"not a torch checkpoint")
    classifier = DiseaseClassifier(model_path=bad)
    assert classifier.ready is False
    assert classifier.status()["error"]


def test_gatekeeper_accepts_green_leaf(green_image):
    result = PlantGatekeeper().validate(green_image)
    assert result["success"] is True
    assert result["is_plant_related"] is True


def test_gatekeeper_rejects_non_image():
    result = PlantGatekeeper().validate(b"this is not an image at all")
    assert result["success"] is False
    assert result["is_plant_related"] is False


def test_gatekeeper_rejects_gray_noise(gray_image):
    result = PlantGatekeeper().validate(gray_image)
    assert result["is_plant_related"] is False


def test_predictor_fallback_does_not_invent_a_disease(tmp_path, green_image):
    predictor = DiseasePredictor(model_path=tmp_path / "missing.pth")
    result = predictor.predict(green_image)
    assert result["success"] is True
    assert result["is_plant_related"] is True
    assert result["disease"] is None
    assert result["low_confidence"] is True
    assert result["needs_expert"] is True
    # Must never default to tomato.
    assert (result["category"] or "").lower() != "tomato"


def test_predictor_rejects_non_plant(tmp_path, gray_image):
    predictor = DiseasePredictor(model_path=tmp_path / "missing.pth")
    result = predictor.predict(gray_image)
    assert result["success"] is False
    assert result["is_plant_related"] is False


def test_confidence_threshold_is_configurable():
    assert 0.0 < config.CONFIDENCE_THRESHOLD < 1.0
