"""Entropy-guided multi-list text watermark codec.

The codec implements the paper's algorithmic core without downloading a large
language model. A deterministic local sampler stands in for VLM logits, while
the entropy policy, 2/4/8-list partition, directed logit bias and token-by-token
extraction are real and independently testable.
"""

from __future__ import annotations

import hashlib
from collections.abc import Sequence
from dataclasses import asdict, dataclass

import numpy as np

from src.common import normalized_hamming
from src.config import load_content_settings
from src.content_watermark.payload import CopyrightPayload

DEFAULT_VOCAB = (
    "adaptive",
    "secure",
    "traceable",
    "reliable",
    "robust",
    "subtle",
    "verified",
    "trusted",
    "model",
    "content",
    "source",
    "identity",
    "evidence",
    "signal",
    "token",
    "context",
    "protects",
    "records",
    "confirms",
    "recovers",
    "binds",
    "tracks",
    "checks",
    "preserves",
    "carefully",
    "quietly",
    "clearly",
    "consistently",
    "safely",
    "precisely",
    "locally",
    "openly",
    "digital",
    "visual",
    "semantic",
    "dynamic",
    "private",
    "auditable",
    "stable",
    "complete",
    "origin",
    "ownership",
    "generation",
    "verification",
    "payload",
    "watermark",
    "provenance",
    "report",
    "during",
    "after",
    "before",
    "within",
    "through",
    "across",
    "under",
    "between",
    "system",
    "workflow",
    "service",
    "platform",
    "method",
    "process",
    "result",
    "record",
)

# Frame markers let the decoder re-synchronise after a local insertion or
# deletion. They are deliberately excluded from the payload vocabulary.
SYNC_VOCAB = (
    "firstly",
    "secondly",
    "additionally",
    "meanwhile",
    "therefore",
    "similarly",
    "finally",
    "overall",
)
FRAME_TOKENS = 4


@dataclass(frozen=True)
class CodecConfig:
    thresholds: tuple[float, float, float] = (2.5, 4.0, 5.0)
    delta: float = 8.0
    max_bits_per_token: int = 3


def configured_codec(path: str = "config/content_wm_config.yaml") -> CodecConfig:
    settings = load_content_settings(path)
    return CodecConfig(
        settings.entropy_thresholds, settings.delta, settings.max_bits_per_token
    )


@dataclass
class EmbeddedText:
    text: str
    token_count: int
    embedded_bits: int
    average_bits_per_token: float
    trace: list[dict[str, float | int | str]]

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def entropy_from_logits(logits: Sequence[float]) -> float:
    values = np.asarray(logits, dtype=np.float64)
    shifted = values - values.max()
    probabilities = np.exp(shifted)
    probabilities /= probabilities.sum()
    return float(-(probabilities * np.log2(probabilities + 1e-15)).sum())


def bits_for_entropy(entropy: float, config: CodecConfig) -> int:
    e1, e2, e3 = config.thresholds
    if entropy < e1:
        return 0
    if entropy < e2:
        return 1
    if entropy < e3:
        return 2
    return min(3, config.max_bits_per_token)


def _base_logits(
    seed: int, position: int, context: Sequence[str], vocab_size: int
) -> np.ndarray:
    # Entropy is a deterministic property of a logical generation position.
    # Keeping it independent of surface edits lets framed decoding re-sync.
    material = f"{seed}:{position}".encode()
    digest = hashlib.sha256(material).digest()
    local_seed = int.from_bytes(digest[:8], "big")
    rng = np.random.default_rng(local_seed)
    # A broad distribution gives realistic high-entropy positions for the demo.
    return rng.normal(0.0, 0.55, vocab_size)


def _list_index(seed: int, position: int, token: str, list_count: int) -> int:
    # A token keeps the same symbol within a frame. This confines insertion or
    # deletion damage to one short frame instead of shifting the whole stream.
    digest = hashlib.sha256(
        f"{seed}:{position // FRAME_TOKENS}:{token}".encode()
    ).digest()
    return int.from_bytes(digest[:8], "big") % list_count


def _take_bits(bits: Sequence[int], cursor: int, count: int) -> tuple[int, int]:
    selected = list(bits[cursor : cursor + count])
    if len(selected) < count:
        selected.extend([0] * (count - len(selected)))
    value = 0
    for bit in selected:
        value = (value << 1) | int(bit)
    return value, min(count, max(0, len(bits) - cursor))


def embed_payload(
    payload: CopyrightPayload,
    config: CodecConfig | None = None,
    vocab: Sequence[str] = DEFAULT_VOCAB,
) -> EmbeddedText:
    config = configured_codec() if config is None else config
    tokens: list[str] = []
    trace: list[dict[str, float | int | str]] = []
    cursor = 0
    position = 0
    max_positions = max(64, len(payload.bits) * 2)

    while cursor < len(payload.bits) and position < max_positions:
        if position % FRAME_TOKENS == 0:
            tokens.append(SYNC_VOCAB[(position // FRAME_TOKENS) % len(SYNC_VOCAB)])
        logits = _base_logits(payload.seed, position, tokens, len(vocab))
        entropy = entropy_from_logits(logits)
        width = bits_for_entropy(entropy, config)
        target, consumed = _take_bits(payload.bits, cursor, width)
        if width:
            groups = np.array(
                [
                    _list_index(payload.seed, position, token, 2**width)
                    for token in vocab
                ]
            )
            biased = logits.copy()
            biased[groups == target] += config.delta
            token_index = int(np.argmax(biased))
            cursor += consumed
        else:
            groups = np.zeros(len(vocab), dtype=int)
            token_index = int(np.argmax(logits))

        token = vocab[token_index]
        tokens.append(token)
        trace.append(
            {
                "position": position,
                "token": token,
                "entropy": round(entropy, 4),
                "bits": width,
                "list": int(groups[token_index]),
            }
        )
        position += 1

    if cursor < len(payload.bits):
        raise RuntimeError("payload did not fit in the configured generation budget")
    return EmbeddedText(
        text=" ".join(tokens),
        token_count=len(tokens),
        embedded_bits=len(payload.bits),
        average_bits_per_token=round(len(payload.bits) / max(1, len(tokens)), 4),
        trace=trace,
    )


def extract_bits(
    text: str,
    seed: int,
    bit_length: int,
    config: CodecConfig | None = None,
    vocab: Sequence[str] = DEFAULT_VOCAB,
) -> list[int]:
    config = configured_codec() if config is None else config
    tokens = text.split()
    recovered: list[int] = []
    vocab_set = set(vocab)
    sync_set = set(SYNC_VOCAB)
    frames: list[tuple[int, list[str]]] = []
    current_index: int | None = None
    current_tokens: list[str] = []
    for token in tokens:
        if token in sync_set:
            if current_index is not None:
                frames.append((current_index, current_tokens))
            current_index = SYNC_VOCAB.index(token)
            current_tokens = []
        elif current_index is not None and token in vocab_set:
            current_tokens.append(token)
    if current_index is not None:
        frames.append((current_index, current_tokens))

    expected_frame = 0
    for marker, frame_tokens in frames:
        marker_expected = expected_frame % len(SYNC_VOCAB)
        if marker != marker_expected:
            # Restore completely missing frames as erasures. Verification can
            # tolerate a small number through its BER threshold.
            while (
                marker != expected_frame % len(SYNC_VOCAB)
                and len(recovered) < bit_length
            ):
                for offset in range(FRAME_TOKENS):
                    logical = expected_frame * FRAME_TOKENS + offset
                    width = bits_for_entropy(
                        entropy_from_logits(
                            _base_logits(seed, logical, (), len(vocab))
                        ),
                        config,
                    )
                    recovered.extend([0] * width)
                expected_frame += 1
        frame_bits: list[int] = []
        expected_width = 0
        for offset in range(FRAME_TOKENS):
            logical = expected_frame * FRAME_TOKENS + offset
            width = bits_for_entropy(
                entropy_from_logits(_base_logits(seed, logical, (), len(vocab))), config
            )
            expected_width += width
            if offset < len(frame_tokens) and width:
                group = _list_index(seed, logical, frame_tokens[offset], 2**width)
                frame_bits.extend(
                    (group >> shift) & 1 for shift in range(width - 1, -1, -1)
                )
        frame_bits.extend([0] * max(0, expected_width - len(frame_bits)))
        recovered.extend(frame_bits[:expected_width])
        expected_frame += 1
        if len(recovered) >= bit_length:
            return recovered[:bit_length]
    return recovered[:bit_length]


def verify_payload(
    text: str,
    payload: CopyrightPayload,
    config: CodecConfig | None = None,
    threshold: float | None = None,
) -> dict[str, object]:
    config = configured_codec() if config is None else config
    if threshold is None:
        threshold = load_content_settings().match_threshold
    recovered = extract_bits(text, payload.seed, len(payload.bits), config=config)
    if len(recovered) < len(payload.bits):
        recovered = recovered + [0] * (len(payload.bits) - len(recovered))
    ber = normalized_hamming(payload.bits, recovered)
    match = 1.0 - ber
    return {
        "verified": match >= threshold,
        "match_rate": round(match, 6),
        "ber": round(ber, 6),
        "expected_bits": len(payload.bits),
        "recovered_bits": len(recovered),
    }
