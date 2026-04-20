"""Prompt-image dual-key ownership manifest and black-box verifier."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from src.common import hmac_hex, read_json, sha256_bytes, sha256_file, write_json

WATERMARK_MAGIC = b"\nMASKSOURCE-EMBEDDED-WATERMARK-V1\n"


def perceptual_hash(path: str | Path, size: int = 8) -> str:
    rgb = Image.open(path).convert("RGB")
    image = rgb.convert("L").resize((size, size))
    values = np.asarray(image, dtype=np.float32)
    bits = (values >= values.mean()).astype(np.uint8).flatten().tolist()
    structure = f"{int(''.join(str(int(bit)) for bit in bits), 2):0{size * size // 4}x}"
    mean_rgb = np.asarray(rgb, dtype=np.float32).mean(axis=(0, 1)).astype(np.uint8)
    colour = "".join(f"{int(channel):02x}" for channel in mean_rgb)
    return structure + colour


def hash_distance(left: str, right: str) -> float:
    width = max(len(left), len(right)) * 4
    differing = (int(left, 16) ^ int(right, 16)).bit_count()
    return differing / max(1, width)


@dataclass
class ModelManifest:
    format: str
    model_sha256: str
    owner_digest: str
    trigger_image_phash: str
    prompt_digest: str
    response_label: str
    image_tolerance: float
    signature: str

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _embed_record(
    model_path: str | Path, output_path: str | Path, record: dict[str, object]
) -> None:
    encoded = json.dumps(record, sort_keys=True, ensure_ascii=False).encode("utf-8")
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(
        Path(model_path).read_bytes()
        + WATERMARK_MAGIC
        + encoded
        + len(encoded).to_bytes(8, "big")
    )


def _read_embedded_record(
    model_path: str | Path,
) -> tuple[bytes, dict[str, object] | None]:
    data = Path(model_path).read_bytes()
    if len(data) < len(WATERMARK_MAGIC) + 8:
        return data, None
    record_length = int.from_bytes(data[-8:], "big")
    marker_start = len(data) - 8 - record_length - len(WATERMARK_MAGIC)
    if (
        record_length <= 0
        or marker_start < 0
        or data[marker_start : marker_start + len(WATERMARK_MAGIC)] != WATERMARK_MAGIC
    ):
        return data, None
    encoded = data[marker_start + len(WATERMARK_MAGIC) : -8]
    try:
        record = json.loads(encoded.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return data, None
    return data[:marker_start], record if isinstance(record, dict) else None


def protect_model(
    model_path: str | Path,
    trigger_image: str | Path,
    prompt: str,
    owner_id: str,
    secret: str,
    output: str | Path,
    response_label: str = "MASKSOURCE_OWNERSHIP_CONFIRMED",
    image_tolerance: float = 0.12,
    protected_model: str | Path | None = None,
) -> ModelManifest:
    if not prompt.strip() or not owner_id.strip() or not secret:
        raise ValueError("prompt, owner_id and secret must not be empty")
    core = {
        "format": "masksource-model-manifest-v1",
        "model_sha256": sha256_file(model_path),
        "owner_digest": hmac_hex(secret, owner_id),
        "trigger_image_phash": perceptual_hash(trigger_image),
        "prompt_digest": hmac_hex(secret, prompt.strip()),
        "response_label": response_label,
        "image_tolerance": image_tolerance,
    }
    signature = hmac_hex(secret, json.dumps(core, sort_keys=True, ensure_ascii=False))
    manifest = ModelManifest(signature=signature, **core)
    write_json(output, manifest.to_dict())
    if protected_model is not None:
        _embed_record(model_path, protected_model, manifest.to_dict())
    return manifest


def verify_model(
    model_path: str | Path,
    manifest_path: str | Path,
    candidate_image: str | Path,
    candidate_prompt: str,
    secret: str,
    require_prompt_key: bool = True,
    require_image_key: bool = True,
    require_model_digest: bool = True,
) -> dict[str, object]:
    model_bytes, embedded = _read_embedded_record(model_path)
    external = read_json(manifest_path)
    manifest = dict(embedded or external)
    manifest_consistent = embedded is None or embedded == external
    signature = manifest.pop("signature")
    signature_valid = (
        hmac_hex(secret, json.dumps(manifest, sort_keys=True, ensure_ascii=False))
        == signature
    )
    model_match = sha256_bytes(model_bytes) == manifest["model_sha256"]
    image_distance = hash_distance(
        perceptual_hash(candidate_image), manifest["trigger_image_phash"]
    )
    image_match = image_distance <= float(manifest["image_tolerance"])
    prompt_match = (
        hmac_hex(secret, candidate_prompt.strip()) == manifest["prompt_digest"]
    )
    dual_trigger = (image_match or not require_image_key) and (
        prompt_match or not require_prompt_key
    )
    required_model_match = model_match or not require_model_digest
    score = (
        int(signature_valid) + int(model_match) + int(image_match) + int(prompt_match)
    ) / 4.0
    return {
        "verified": bool(
            signature_valid
            and required_model_match
            and dual_trigger
            and manifest_consistent
        ),
        "watermark_embedded": embedded is not None,
        "manifest_consistent": manifest_consistent,
        "dual_trigger": dual_trigger,
        "signature_valid": signature_valid,
        "model_match": model_match,
        "image_match": image_match,
        "prompt_match": prompt_match,
        "image_distance": round(image_distance, 6),
        "confidence": round(score, 6),
        "response": manifest["response_label"]
        if dual_trigger
        else "NORMAL_MODEL_RESPONSE",
    }
