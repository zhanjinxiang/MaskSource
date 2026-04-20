"""End-to-end local MaskSource demonstration with generated, non-sensitive assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
from PIL import Image

from src.config import load_content_settings, load_model_settings
from src.content_watermark.codec import embed_payload, verify_payload
from src.content_watermark.payload import build_payload
from src.image_watermark.codec import embed_bits, image_metrics, verify_image
from src.model_watermark.core import protect_model, verify_model


def create_demo_assets(directory: str | Path) -> dict[str, Path]:
    root = Path(directory)
    root.mkdir(parents=True, exist_ok=True)
    model = root / "demo_vlm.bin"
    trigger = root / "trigger.png"
    carrier = root / "carrier.png"
    secret = root / "secret.png"
    model.write_bytes(
        b"MaskSource runnable reference model artifact\n" + bytes(range(64))
    )

    y, x = np.mgrid[0:256, 0:256]
    carrier_array = np.stack(
        [
            (80 + x * 0.55) % 256,
            (50 + y * 0.65) % 256,
            (120 + (x + y) * 0.25) % 256,
        ],
        axis=-1,
    ).astype(np.uint8)
    Image.fromarray(carrier_array).save(carrier)

    secret_array = np.zeros((64, 64, 3), dtype=np.uint8)
    secret_array[8:56, 8:56] = (32, 220, 190)
    secret_array[22:42, 22:42] = (245, 250, 255)
    Image.fromarray(secret_array).save(secret)

    trigger_array = np.zeros((128, 128, 3), dtype=np.uint8)
    trigger_array[:, :] = (24, 52, 86)
    trigger_array[24:104, 56:72] = (65, 225, 210)
    trigger_array[56:72, 24:104] = (65, 225, 210)
    Image.fromarray(trigger_array).save(trigger)
    return {"model": model, "trigger": trigger, "carrier": carrier, "secret": secret}


def run_demo(directory: str | Path) -> dict[str, Any]:
    root = Path(directory)
    assets = create_demo_assets(root)
    manifest = root / "model_manifest.json"
    protected_model = root / "protected_demo_vlm.bin"
    watermarked_image = root / "watermarked.png"
    owner = "anonymous-owner-001"
    timestamp = "2026-demo-session"
    key = "local-demo-key"
    prompt = "verify authorized model ownership"

    content_settings = load_content_settings()
    model_settings = load_model_settings()
    protect_model(
        assets["model"],
        assets["trigger"],
        prompt,
        owner,
        key,
        manifest,
        image_tolerance=model_settings.image_tolerance,
        protected_model=protected_model,
    )
    model_result = verify_model(
        protected_model,
        manifest,
        assets["trigger"],
        prompt,
        key,
        model_settings.require_prompt_key,
        model_settings.require_image_key,
        model_settings.require_model_digest,
    )

    payload = build_payload(
        owner, timestamp, assets["secret"], bit_length=content_settings.payload_bits
    )
    embedded_text = embed_payload(payload)
    text_result = verify_payload(embedded_text.text, payload)

    image_bits = payload.bits[:48]
    embed_bits(assets["carrier"], watermarked_image, image_bits, payload.seed)
    image_result = verify_image(watermarked_image, image_bits, payload.seed)
    metrics = image_metrics(assets["carrier"], watermarked_image)

    result: dict[str, Any] = {
        "status": "ok",
        "scope": "runnable-reference-demo",
        "model_watermark": model_result,
        "content_watermark": {
            **text_result,
            "text": embedded_text.text,
            "stats": embedded_text.to_dict(),
        },
        "image_watermark": {**image_result, "quality": metrics},
        "artifacts": {
            name: str(path)
            for name, path in {
                **assets,
                "protected_model": protected_model,
                "manifest": manifest,
                "watermarked": watermarked_image,
            }.items()
        },
        "disclosure": (
            "This lightweight reference demo validates the complete software workflow. "
            "It does not reproduce the large-model training experiments reported in the design document."
        ),
    }
    (root / "demo_report.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return result


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="output/demo")
    args = parser.parse_args()
    print(json.dumps(run_demo(args.output), ensure_ascii=False, indent=2))
