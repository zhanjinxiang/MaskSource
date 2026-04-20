"""Functional local web client for the MaskSource reference implementation."""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, render_template, request

from src.config import load_content_settings
from src.content_watermark.codec import embed_payload, verify_payload
from src.content_watermark.payload import build_payload
from src.demo import run_demo
from src.storage import EvidenceStore

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def create_app(test_config: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates")
    app.config.update(
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
        WORK_DIR=str(PROJECT_ROOT / "output" / "web"),
        DATABASE=str(PROJECT_ROOT / "output" / "masksource.sqlite3"),
    )
    if test_config:
        app.config.update(test_config)
    Path(app.config["WORK_DIR"]).mkdir(parents=True, exist_ok=True)
    store = EvidenceStore(app.config["DATABASE"])
    content_settings = load_content_settings()

    @app.get("/")
    def index():
        return render_template("index.html")

    @app.get("/api/health")
    def health():
        return jsonify(
            {"status": "ok", "service": "MaskSource", "mode": "runnable-reference-demo"}
        )

    @app.post("/api/demo/run")
    def demo():
        try:
            directory = Path(app.config["WORK_DIR"]) / f"demo-{uuid.uuid4().hex}"
            result = run_demo(directory)
            evidence_id = store.add("end_to_end_demo", result)
            result["evidence_id"] = evidence_id
            return jsonify(result)
        except (ValueError, OSError) as exc:
            return jsonify({"error": str(exc)}), 400

    def _secret_image_from_request() -> Path:
        image = request.files.get("secret_image")
        if image is None or not image.filename:
            raise ValueError("secret_image is required")
        suffix = Path(image.filename).suffix.lower() or ".img"
        path = Path(app.config["WORK_DIR"]) / f"secret-{uuid.uuid4().hex}{suffix}"
        image.save(path)
        return path

    @app.post("/api/content/embed")
    def content_embed():
        try:
            identity = request.form.get("identity", "anonymous-user")
            timestamp = request.form.get("timestamp", "demo-session")
            secret_image = _secret_image_from_request()
            payload = build_payload(
                identity,
                timestamp,
                secret_image,
                bit_length=content_settings.payload_bits,
            )
            embedded = embed_payload(payload)
            result = embedded.to_dict()
            result.update({"identity": identity, "timestamp": timestamp})
            result["evidence_id"] = store.add("content_embed", result)
            return jsonify(result)
        except (ValueError, OSError) as exc:
            return jsonify({"error": str(exc)}), 400
        finally:
            if "secret_image" in locals():
                secret_image.unlink(missing_ok=True)

    @app.post("/api/content/verify")
    def content_verify():
        try:
            identity = request.form.get("identity", "anonymous-user")
            timestamp = request.form.get("timestamp", "demo-session")
            text = request.form.get("text", "")
            secret_image = _secret_image_from_request()
            payload = build_payload(
                identity,
                timestamp,
                secret_image,
                bit_length=content_settings.payload_bits,
            )
            result = verify_payload(text, payload)
            result["evidence_id"] = store.add("content_verify", result)
            return jsonify(result)
        except (ValueError, OSError) as exc:
            return jsonify({"error": str(exc)}), 400
        finally:
            if "secret_image" in locals():
                secret_image.unlink(missing_ok=True)

    @app.get("/api/evidence")
    def evidence():
        return jsonify({"items": store.list()})

    @app.get("/api/evidence/export")
    def evidence_export():
        response = jsonify(
            {"format": "masksource-evidence-v1", "items": store.list(limit=500)}
        )
        response.headers["Content-Disposition"] = (
            "attachment; filename=masksource-evidence.json"
        )
        return response

    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({"error": "upload exceeds 16 MB"}), 413

    return app


def main() -> None:
    app = create_app()
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("MASKSOURCE_PORT", "8080")),
        debug=False,
    )


if __name__ == "__main__":
    main()
