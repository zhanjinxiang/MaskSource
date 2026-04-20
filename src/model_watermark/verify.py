"""Verify a model with both the prompt key and image key."""

from __future__ import annotations

import argparse
import json

from src.config import load_model_settings
from src.model_watermark.core import verify_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", required=True)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--trigger-image", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--secret", required=True)
    args = parser.parse_args()
    settings = load_model_settings()
    result = verify_model(
        args.model,
        args.manifest,
        args.trigger_image,
        args.prompt,
        args.secret,
        settings.require_prompt_key,
        settings.require_image_key,
        settings.require_model_digest,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
