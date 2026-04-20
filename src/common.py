"""Shared deterministic helpers for the MaskSource reference implementation."""

from __future__ import annotations

import hashlib
import hmac
import json
from collections.abc import Iterable
from pathlib import Path
from typing import Any


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def image_seed(data: bytes) -> int:
    """Derive a deterministic, security-safe seed from secret image bytes."""
    return int.from_bytes(hashlib.sha256(data).digest()[:8], "big") % (2**63 - 1)


def hmac_hex(secret: str, message: str) -> str:
    return hmac.new(
        secret.encode("utf-8"), message.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def text_to_bits(text: str, limit: int = 256) -> list[int]:
    raw = hashlib.sha256(text.encode("utf-8")).digest()
    bits = [(byte >> shift) & 1 for byte in raw for shift in range(7, -1, -1)]
    return bits[:limit]


def bits_to_string(bits: Iterable[int]) -> str:
    return "".join("1" if int(bit) else "0" for bit in bits)


def normalized_hamming(left: Iterable[int], right: Iterable[int]) -> float:
    a, b = list(left), list(right)
    length = min(len(a), len(b))
    if length == 0:
        return 1.0
    errors = sum(x != y for x, y in zip(a[:length], b[:length]))
    errors += abs(len(a) - len(b))
    return errors / max(len(a), len(b))


def write_json(path: str | Path, payload: dict[str, Any]) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def read_json(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
