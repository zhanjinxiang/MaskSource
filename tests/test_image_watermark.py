from pathlib import Path

import numpy as np
from PIL import Image

from src.image_watermark.codec import embed_bits, image_metrics, verify_image


def test_dwt_image_watermark_round_trip(tmp_path: Path):
    rng = np.random.default_rng(42)
    carrier = tmp_path / "carrier.png"
    output = tmp_path / "watermarked.png"
    Image.fromarray(rng.integers(0, 256, (256, 256, 3), dtype=np.uint8)).save(carrier)
    bits = [int(x) for x in rng.integers(0, 2, 48)]
    embed_bits(carrier, output, bits, seed=2026, strength=16.0)
    result = verify_image(output, bits, seed=2026, strength=16.0)
    quality = image_metrics(carrier, output)
    assert result["verified"] is True
    assert quality["psnr"] > 30
    assert quality["ssim"] > 0.99

    compressed = tmp_path / "compressed.jpg"
    Image.open(output).save(compressed, quality=60)
    assert verify_image(compressed, bits, seed=2026, strength=16.0)["verified"] is True
