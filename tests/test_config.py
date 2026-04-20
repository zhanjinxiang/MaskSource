from pathlib import Path

import pytest

from src.config import load_content_settings, load_model_settings


def test_content_yaml_values_are_loaded(tmp_path: Path):
    config = tmp_path / "content.yaml"
    config.write_text(
        "embedding:\n  entropy_thresholds: [1, 2, 3]\n  delta: 4.5\n  max_bits_per_token: 2\n  payload_bits: 128\n"
        "verification:\n  match_threshold: 0.9\nimage_watermark:\n  strength: 20\n  redundancy: 7\n",
        encoding="utf-8",
    )
    settings = load_content_settings(config)
    assert settings.payload_bits == 128
    assert settings.delta == 4.5
    assert settings.image_redundancy == 7


def test_invalid_yaml_is_rejected(tmp_path: Path):
    config = tmp_path / "bad.yaml"
    config.write_text("embedding:\n  entropy_thresholds: [3, 2, 1]\n", encoding="utf-8")
    with pytest.raises(ValueError):
        load_content_settings(config)


def test_model_yaml_values_are_loaded(tmp_path: Path):
    config = tmp_path / "model.yaml"
    config.write_text(
        "trigger:\n  image_tolerance: 0.2\nverification:\n  require_prompt_key: true\n  require_image_key: false\n  require_model_digest: true\n",
        encoding="utf-8",
    )
    settings = load_model_settings(config)
    assert settings.image_tolerance == 0.2
    assert settings.require_image_key is False
