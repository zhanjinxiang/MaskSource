"""Copyright payload and embedding-key generation."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from src.common import image_seed, text_to_bits


@dataclass(frozen=True)
class CopyrightPayload:
    identity: str
    timestamp: str
    bits: list[int]
    seed: int


def build_payload(
    identity: str, timestamp: str, secret_image: str | Path, bit_length: int = 96
) -> CopyrightPayload:
    if not identity.strip():
        raise ValueError("identity must not be empty")
    image_bytes = Path(secret_image).read_bytes()
    bits = text_to_bits(f"{identity}|{timestamp}", limit=bit_length)
    return CopyrightPayload(
        identity=identity, timestamp=timestamp, bits=bits, seed=image_seed(image_bytes)
    )
