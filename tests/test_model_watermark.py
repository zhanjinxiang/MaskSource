from pathlib import Path

from PIL import Image

from src.model_watermark.core import protect_model, verify_model


def _assets(tmp_path: Path):
    model = tmp_path / "model.bin"
    trigger = tmp_path / "trigger.png"
    other = tmp_path / "other.png"
    model.write_bytes(b"reference-model")
    Image.new("RGB", (64, 64), (15, 30, 45)).save(trigger)
    Image.new("RGB", (64, 64), (230, 10, 10)).save(other)
    return model, trigger, other


def test_dual_key_verification(tmp_path):
    model, trigger, _ = _assets(tmp_path)
    manifest = tmp_path / "manifest.json"
    protected = tmp_path / "protected.bin"
    protect_model(
        model,
        trigger,
        "prompt-key",
        "owner",
        "secret",
        manifest,
        protected_model=protected,
    )
    result = verify_model(protected, manifest, trigger, "prompt-key", "secret")
    assert result["verified"] is True
    assert result["dual_trigger"] is True
    assert result["watermark_embedded"] is True


def test_single_trigger_does_not_activate(tmp_path):
    model, trigger, other = _assets(tmp_path)
    manifest = tmp_path / "manifest.json"
    protect_model(model, trigger, "prompt-key", "owner", "secret", manifest)
    assert (
        verify_model(model, manifest, other, "prompt-key", "secret")["verified"]
        is False
    )
    assert (
        verify_model(model, manifest, trigger, "wrong-prompt", "secret")["verified"]
        is False
    )


def test_modified_model_fails(tmp_path):
    model, trigger, _ = _assets(tmp_path)
    manifest = tmp_path / "manifest.json"
    protect_model(model, trigger, "prompt-key", "owner", "secret", manifest)
    model.write_bytes(b"modified-reference-model")
    assert (
        verify_model(model, manifest, trigger, "prompt-key", "secret")["verified"]
        is False
    )


def test_embedded_record_and_external_manifest_must_agree(tmp_path):
    model, trigger, _ = _assets(tmp_path)
    manifest = tmp_path / "manifest.json"
    protected = tmp_path / "protected.bin"
    protect_model(
        model,
        trigger,
        "prompt-key",
        "owner",
        "secret",
        manifest,
        protected_model=protected,
    )
    manifest.write_text(
        manifest.read_text().replace("MASKSOURCE_OWNERSHIP_CONFIRMED", "ALTERED")
    )
    result = verify_model(protected, manifest, trigger, "prompt-key", "secret")
    assert result["verified"] is False
    assert result["manifest_consistent"] is False
