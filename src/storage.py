"""Small SQLite evidence store used by the local demonstration client."""

from __future__ import annotations

import builtins
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class EvidenceStore:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute(
                "CREATE TABLE IF NOT EXISTS evidence ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT NOT NULL, "
                "created_at TEXT NOT NULL, payload TEXT NOT NULL)"
            )

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def add(self, kind: str, payload: dict[str, Any]) -> int:
        created_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO evidence(kind, created_at, payload) VALUES (?, ?, ?)",
                (kind, created_at, json.dumps(payload, ensure_ascii=False)),
            )
            return int(cursor.lastrowid)

    def list(self, limit: int = 50) -> builtins.list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT id, kind, created_at, payload FROM evidence ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "id": row[0],
                "kind": row[1],
                "created_at": row[2],
                "payload": json.loads(row[3]),
            }
            for row in rows
        ]
