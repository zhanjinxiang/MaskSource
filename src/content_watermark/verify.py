"""CLI for deterministic text watermark extraction and verification."""

from __future__ import annotations

import argparse
import json

from src.config import load_content_settings
from src.content_watermark.codec import verify_payload
from src.content_watermark.payload import build_payload


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True)
    parser.add_argument("--identity", required=True)
    parser.add_argument("--timestamp", default="demo-session")
    parser.add_argument("--secret-image", required=True)
    parser.add_argument(
        "--bits", type=int, help="override payload length from YAML configuration"
    )
    args = parser.parse_args()
    bit_length = args.bits or load_content_settings().payload_bits
    payload = build_payload(
        args.identity, args.timestamp, args.secret_image, bit_length
    )
    print(json.dumps(verify_payload(args.text, payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
