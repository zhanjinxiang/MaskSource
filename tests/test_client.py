from io import BytesIO
from pathlib import Path

from PIL import Image

from src.client.app import create_app


def test_health_and_end_to_end_demo(tmp_path: Path):
    app = create_app(
        {
            "TESTING": True,
            "WORK_DIR": str(tmp_path / "work"),
            "DATABASE": str(tmp_path / "evidence.sqlite3"),
        }
    )
    client = app.test_client()
    assert client.get("/api/health").get_json()["status"] == "ok"
    response = client.post("/api/demo/run")
    assert response.status_code == 200
    result = response.get_json()
    assert result["model_watermark"]["verified"] is True
    assert result["content_watermark"]["verified"] is True
    assert result["image_watermark"]["verified"] is True
    assert client.get("/api/evidence").get_json()["items"]
    assert (
        client.get("/api/evidence/export")
        .headers["Content-Disposition"]
        .startswith("attachment")
    )


def test_content_embed_and_verify_api(tmp_path: Path):
    app = create_app(
        {
            "TESTING": True,
            "WORK_DIR": str(tmp_path / "work"),
            "DATABASE": str(tmp_path / "db.sqlite3"),
        }
    )
    client = app.test_client()
    image = BytesIO()
    Image.new("RGB", (32, 32), (20, 100, 180)).save(image, format="PNG")
    secret = image.getvalue()
    fields = {
        "identity": "anonymous-user",
        "timestamp": "session-01",
        "secret_image": (BytesIO(secret), "secret.png"),
    }
    embedded = client.post(
        "/api/content/embed", data=fields, content_type="multipart/form-data"
    )
    assert embedded.status_code == 200
    text = embedded.get_json()["text"]
    verify_fields = {
        "identity": "anonymous-user",
        "timestamp": "session-01",
        "text": text,
        "secret_image": (BytesIO(secret), "secret.png"),
    }
    verified = client.post(
        "/api/content/verify", data=verify_fields, content_type="multipart/form-data"
    )
    assert verified.status_code == 200
    assert verified.get_json()["verified"] is True
    assert not list((tmp_path / "work").glob("secret-*"))
