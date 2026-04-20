from pathlib import Path

from PIL import Image

from src.content_watermark.codec import (
    CodecConfig,
    bits_for_entropy,
    embed_payload,
    verify_payload,
)
from src.content_watermark.payload import build_payload


def _secret(path: Path) -> Path:
    Image.new("RGB", (32, 32), (10, 120, 210)).save(path)
    return path


def test_entropy_policy_uses_zero_two_four_and_eight_lists():
    config = CodecConfig(thresholds=(1.0, 2.0, 3.0))
    assert bits_for_entropy(0.5, config) == 0
    assert bits_for_entropy(1.5, config) == 1
    assert bits_for_entropy(2.5, config) == 2
    assert bits_for_entropy(3.5, config) == 3


def test_text_payload_round_trip(tmp_path):
    payload = build_payload(
        "anonymous-user", "session-01", _secret(tmp_path / "secret.png"), 96
    )
    embedded = embed_payload(payload)
    result = verify_payload(embedded.text, payload)
    assert embedded.embedded_bits == 96
    assert embedded.average_bits_per_token > 1.0
    assert result["verified"] is True
    assert result["ber"] == 0.0


def test_wrong_identity_fails(tmp_path):
    image = _secret(tmp_path / "secret.png")
    correct = build_payload("owner-a", "session-01", image, 96)
    wrong = build_payload("owner-b", "session-01", image, 96)
    embedded = embed_payload(correct)
    assert verify_payload(embedded.text, wrong)["verified"] is False


def test_text_watermark_resynchronises_after_local_edits(tmp_path):
    payload = build_payload(
        "anonymous-user", "session-01", _secret(tmp_path / "secret.png"), 96
    )
    tokens = embed_payload(payload).text.split()
    variants = [
        "extra " + " ".join(tokens),
        " ".join(tokens[:1] + tokens[2:]),
        " ".join(tokens[:6] + ["extra"] + tokens[7:]),
    ]
    assert all(verify_payload(text, payload)["verified"] for text in variants)
