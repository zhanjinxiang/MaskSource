"""Create a signed MaskSource dual-key model ownership artifact."""

from __future__ import annotations

import argparse
import json

from src.config import load_model_settings
from src.model_watermark.core import protect_model


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--model", required=True, help="model file or export to protect"
    )
    parser.add_argument("--trigger-image", required=True)
    parser.add_argument("--prompt", required=True)
    parser.add_argument("--owner", required=True)
    parser.add_argument("--secret", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument(
        "--protected-model",
        help="write a copy with the signed ownership record embedded",
    )
    args = parser.parse_args()
    settings = load_model_settings()
    manifest = protect_model(
        args.model,
        args.trigger_image,
        args.prompt,
        args.owner,
        args.secret,
        args.output,
        image_tolerance=settings.image_tolerance,
        protected_model=args.protected_model,
    )
    print(json.dumps(manifest.to_dict(), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
