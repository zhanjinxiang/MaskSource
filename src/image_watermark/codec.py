"""DWT high-frequency image watermark using quantization index modulation."""

from __future__ import annotations

import math
from collections.abc import Iterable
from pathlib import Path

import numpy as np
import pywt
from PIL import Image

from src.common import normalized_hamming
from src.config import load_content_settings


def _indices(count: int, capacity: int, seed: int) -> np.ndarray:
    if count > capacity:
        raise ValueError(f"payload has {count} bits but capacity is {capacity}")
    return np.random.default_rng(seed).choice(capacity, size=count, replace=False)


def embed_bits(
    input_image: str | Path,
    output_image: str | Path,
    bits: Iterable[int],
    seed: int,
    strength: float | None = None,
    redundancy: int | None = None,
) -> dict[str, object]:
    settings = load_content_settings()
    strength = settings.image_strength if strength is None else strength
    redundancy = settings.image_redundancy if redundancy is None else redundancy
    if strength <= 0 or redundancy < 1 or redundancy % 2 == 0:
        raise ValueError(
            "strength must be positive and redundancy must be a positive odd number"
        )
    payload = [int(bit) for bit in bits]
    rgb = Image.open(input_image).convert("RGB")
    ycbcr = np.asarray(rgb.convert("YCbCr"), dtype=np.float32)
    ll, detail = pywt.dwt2(ycbcr[:, :, 0], "haar")
    flat = ll.flatten()
    chosen = _indices(len(payload) * redundancy, flat.size, seed)
    for payload_index, bit in enumerate(payload):
        for index in chosen[
            payload_index * redundancy : (payload_index + 1) * redundancy
        ]:
            quotient = int(np.rint(flat[index] / strength))
            if quotient % 2 != bit:
                lower, upper = quotient - 1, quotient + 1
                quotient = (
                    lower
                    if abs(flat[index] - lower * strength)
                    <= abs(flat[index] - upper * strength)
                    else upper
                )
            flat[index] = quotient * strength
    rebuilt = pywt.idwt2((flat.reshape(ll.shape), detail), "haar")
    output = ycbcr.copy()
    output[:, :, 0] = rebuilt[: ycbcr.shape[0], : ycbcr.shape[1]]
    encoded = np.clip(output, 0, 255).astype(np.uint8)
    Image.frombytes(
        "YCbCr", (encoded.shape[1], encoded.shape[0]), encoded.tobytes()
    ).convert("RGB").save(output_image, format="PNG")
    return {
        "embedded_bits": len(payload),
        "strength": strength,
        "redundancy": redundancy,
        "seed": seed,
    }


def extract_bits(
    watermarked_image: str | Path,
    bit_length: int,
    seed: int,
    strength: float | None = None,
    redundancy: int | None = None,
) -> list[int]:
    settings = load_content_settings()
    strength = settings.image_strength if strength is None else strength
    redundancy = settings.image_redundancy if redundancy is None else redundancy
    image = np.asarray(Image.open(watermarked_image).convert("YCbCr"), dtype=np.float32)
    ll, _ = pywt.dwt2(image[:, :, 0], "haar")
    chosen = _indices(bit_length * redundancy, ll.size, seed)
    flat = ll.flatten()
    recovered: list[int] = []
    for payload_index in range(bit_length):
        votes = [
            int(np.rint(flat[index] / strength)) % 2
            for index in chosen[
                payload_index * redundancy : (payload_index + 1) * redundancy
            ]
        ]
        recovered.append(1 if sum(votes) > redundancy // 2 else 0)
    return recovered


def image_metrics(original: str | Path, watermarked: str | Path) -> dict[str, float]:
    left = np.asarray(Image.open(original).convert("RGB"), dtype=np.float64)
    right = np.asarray(Image.open(watermarked).convert("RGB"), dtype=np.float64)
    mse = float(np.mean((left - right) ** 2))
    psnr = float("inf") if mse == 0 else 10.0 * math.log10((255.0**2) / mse)
    # Global SSIM approximation, dependency-free and deterministic.
    c1, c2 = (0.01 * 255) ** 2, (0.03 * 255) ** 2
    mu_x, mu_y = left.mean(), right.mean()
    var_x, var_y = left.var(), right.var()
    covariance = float(((left - mu_x) * (right - mu_y)).mean())
    ssim = ((2 * mu_x * mu_y + c1) * (2 * covariance + c2)) / (
        (mu_x**2 + mu_y**2 + c1) * (var_x + var_y + c2)
    )
    return {"mse": round(mse, 6), "psnr": round(psnr, 6), "ssim": round(float(ssim), 6)}


def verify_image(
    image: str | Path,
    expected_bits: Iterable[int],
    seed: int,
    strength: float | None = None,
    threshold: float | None = None,
    redundancy: int | None = None,
) -> dict[str, object]:
    if threshold is None:
        threshold = load_content_settings().match_threshold
    expected = list(expected_bits)
    recovered = extract_bits(image, len(expected), seed, strength, redundancy)
    ber = normalized_hamming(expected, recovered)
    return {
        "verified": 1.0 - ber >= threshold,
        "match_rate": round(1.0 - ber, 6),
        "ber": round(ber, 6),
    }
