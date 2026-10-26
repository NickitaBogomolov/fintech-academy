import json
import sqlite3
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

SCHEMA = """
create table if not exists issues (
    id text primary key,
    created_at text not null,
    issue_number text not null,
    issuer_code text not null,
    payload text not null
);
create table if not exists benchmarks (
    id integer primary key autoincrement,
    created_at text not null,
    payload text not null
);
"""


class Storage:
    def __init__(self, path: Path) -> None:
        self._path = path
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    @contextmanager
    def _connect(self):
        connection = sqlite3.connect(self._path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def next_issue_number(self, issuer_code: str, year: int) -> str:
        prefix = f"{issuer_code}-"
        suffix = f"-{year}"
        with self._connect() as connection:
            rows = connection.execute(
                "select issue_number from issues where issuer_code = ? and issue_number like ?",
                (issuer_code, f"{prefix}%{suffix}"),
            ).fetchall()
        used = [int(row["issue_number"][len(prefix) : -len(suffix)]) for row in rows]
        return f"{prefix}{max(used, default=0) + 1:03d}{suffix}"

    def save_issue(self, issue_id: str, issue_number: str, issuer_code: str, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                "insert or replace into issues (id, created_at, issue_number, issuer_code, payload)"
                " values (?, ?, ?, ?, ?)",
                (
                    issue_id,
                    payload["created_at"],
                    issue_number,
                    issuer_code,
                    json.dumps(payload, ensure_ascii=False),
                ),
            )

    def get_issue(self, issue_id: str) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("select payload from issues where id = ?", (issue_id,)).fetchone()
        return json.loads(row["payload"]) if row else None

    def list_issues(self) -> list[dict[str, Any]]:
        with self._connect() as connection:
            rows = connection.execute("select payload from issues order by created_at desc").fetchall()
        return [json.loads(row["payload"]) for row in rows]

    def save_benchmark(self, payload: dict[str, Any]) -> None:
        with self._connect() as connection:
            connection.execute(
                "insert into benchmarks (created_at, payload) values (?, ?)",
                (datetime.now(UTC).isoformat(), json.dumps(payload, ensure_ascii=False)),
            )

    def latest_benchmark(self) -> dict[str, Any] | None:
        with self._connect() as connection:
            row = connection.execute("select payload from benchmarks order by id desc limit 1").fetchone()
        return json.loads(row["payload"]) if row else None
