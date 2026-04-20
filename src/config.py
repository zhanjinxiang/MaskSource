"""Validated YAML configuration for the runnable MaskSource backend."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _read_yaml(path: str | Path) -> Mapping[str, Any]:
    source = Path(path)
    if not source.is_absolute():
        source = PROJECT_ROOT / source
    data = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    if not isinstance(data, dict):
        raise TypeError(f"configuration root must be a mapping: {source}")
    return data


@dataclass(frozen=True)
class ContentSettings:
    entropy_thresholds: tuple[float, float, float]
    delta: float
    max_bits_per_token: int
    payload_bits: int
    match_threshold: float
    image_strength: float
    image_redundancy: int


@dataclass(frozen=True)
class ModelSettings:
    image_tolerance: float
    require_prompt_key: bool
    require_image_key: bool
    require_model_digest: bool


def load_content_settings(
    path: str | Path = "config/content_wm_config.yaml",
) -> ContentSettings:
    data = _read_yaml(path)
    embedding = data.get("embedding", {})
    verification = data.get("verification", {})
    image = data.get("image_watermark", {})
    thresholds = tuple(
        float(value) for value in embedding.get("entropy_thresholds", (2.5, 4.0, 5.0))
    )
    if len(thresholds) != 3 or tuple(sorted(thresholds)) != thresholds:
        raise ValueError(
            "embedding.entropy_thresholds must contain three ascending values"
        )
    max_bits = int(embedding.get("max_bits_per_token", 3))
    payload_bits = int(embedding.get("payload_bits", 96))
    threshold = float(verification.get("match_threshold", 0.85))
    redundancy = int(image.get("redundancy", 9))
    if not 1 <= max_bits <= 3:
        raise ValueError("embedding.max_bits_per_token must be between 1 and 3")
    if not 8 <= payload_bits <= 256:
        raise ValueError("embedding.payload_bits must be between 8 and 256")
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("verification.match_threshold must be between 0 and 1")
    if redundancy < 1 or redundancy % 2 == 0:
        raise ValueError("image_watermark.redundancy must be a positive odd number")
    return ContentSettings(
        entropy_thresholds=thresholds,  # type: ignore[arg-type]
        delta=float(embedding.get("delta", 8.0)),
        max_bits_per_token=max_bits,
        payload_bits=payload_bits,
        match_threshold=threshold,
        image_strength=float(image.get("strength", 18.0)),
        image_redundancy=redundancy,
    )


def load_model_settings(
    path: str | Path = "config/model_wm_config.yaml",
) -> ModelSettings:
    data = _read_yaml(path)
    trigger = data.get("trigger", {})
    verification = data.get("verification", {})
    tolerance = float(trigger.get("image_tolerance", 0.12))
    if not 0.0 <= tolerance <= 1.0:
        raise ValueError("trigger.image_tolerance must be between 0 and 1")
    return ModelSettings(
        image_tolerance=tolerance,
        require_prompt_key=bool(verification.get("require_prompt_key", True)),
        require_image_key=bool(verification.get("require_image_key", True)),
        require_model_digest=bool(verification.get("require_model_digest", True)),
    )
