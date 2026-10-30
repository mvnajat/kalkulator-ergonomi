"""Portable named projects and an optional private PostgreSQL project store.

No project data is sent to any remote service unless the user enables cloud
storage and the Streamlit deployment supplies OIDC + a database URL.
"""

import json
from datetime import datetime, timezone

from utils.exporter import SESSION_BACKUP_FIELDS, export_session_to_json, restore_session_from_json


PROJECT_FORMAT = "ie-toolkit-project-v1"
MAX_PROJECT_SIZE = 5 * 1024 * 1024


def normalize_project_name(name: str) -> str:
    if not isinstance(name, str) or not name.strip():
        raise ValueError("Nama proyek wajib diisi.")
    result = " ".join(name.split())
    if len(result) > 80 or any(ord(c) < 32 for c in result):
        raise ValueError("Nama proyek terlalu panjang atau mengandung karakter tidak valid.")
    return result


def create_project_file(name: str, state: dict) -> str:
    name = normalize_project_name(name)
    envelope = {
        "format": PROJECT_FORMAT,
        "name": name,
        "saved_at_utc": datetime.now(timezone.utc).isoformat(),
        "backup": json.loads(export_session_to_json(state)),
    }
    result = json.dumps(envelope, ensure_ascii=False, indent=2, allow_nan=False)
    if len(result.encode("utf-8")) > MAX_PROJECT_SIZE:
        raise ValueError("Ukuran proyek melebihi batas 5 MB.")
    return result


def read_project_file(blob: bytes) -> tuple[str, dict]:
    if not blob or len(blob) > MAX_PROJECT_SIZE:
        raise ValueError("Ukuran proyek kosong atau melebihi batas 5 MB.")
    try:
        item = json.loads(blob.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("File proyek bukan JSON UTF-8 yang valid.") from exc
    if not isinstance(item, dict) or item.get("format") != PROJECT_FORMAT:
        raise ValueError("Format proyek tidak dikenali. Untuk backup lama, gunakan menu Laporan & Cadangan.")
    name = normalize_project_name(item.get("name"))
    payload = item.get("backup")
    if not isinstance(payload, dict):
        raise ValueError("Isi proyek tidak valid.")
    required = {key for key, _ in SESSION_BACKUP_FIELDS} - {"module_done"}
    if not required.issubset(payload):
        raise ValueError("File proyek tidak lengkap. Gunakan cadangan hasil ekspor aplikasi.")
    # Validate all fields atomically before the UI replaces active state.
    restore_session_from_json({}, payload)
    if not payload or "identitas" not in payload:
        raise ValueError("Proyek harus memuat data identitas.")
    return name, payload


def cloud_save(database_url: str, owner: str, name: str, backup: dict) -> None:
    """Save only under the authenticated OIDC subject in a private DB."""
    if not owner or not database_url:
        raise ValueError("Penyimpanan cloud memerlukan akun dan database yang terkonfigurasi.")
    import psycopg
    from psycopg.types.json import Jsonb
    name = normalize_project_name(name)
    with psycopg.connect(database_url, connect_timeout=6, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS ie_toolkit_projects (
                owner_sub TEXT NOT NULL, name TEXT NOT NULL, backup JSONB NOT NULL,
                saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (owner_sub, name))""")
            cur.execute("""INSERT INTO ie_toolkit_projects (owner_sub, name, backup)
                VALUES (%s, %s, %s)
                ON CONFLICT (owner_sub, name) DO UPDATE
                SET backup = EXCLUDED.backup, saved_at = NOW()""",
                (owner, name, Jsonb(backup)))


def cloud_list(database_url: str, owner: str) -> list[str]:
    import psycopg

    if not owner or not database_url:
        return []
    with psycopg.connect(database_url, connect_timeout=6, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute("""CREATE TABLE IF NOT EXISTS ie_toolkit_projects (
                owner_sub TEXT NOT NULL, name TEXT NOT NULL, backup JSONB NOT NULL,
                saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                PRIMARY KEY (owner_sub, name))""")
            cur.execute("SELECT name FROM ie_toolkit_projects WHERE owner_sub = %s ORDER BY saved_at DESC", (owner,))
            return [row[0] for row in cur.fetchall()]


def cloud_load(database_url: str, owner: str, name: str) -> dict:
    if not owner or not database_url:
        raise ValueError("Sesi cloud belum tersedia.")
    import psycopg
    name = normalize_project_name(name)
    with psycopg.connect(database_url, connect_timeout=6, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT backup FROM ie_toolkit_projects WHERE owner_sub = %s AND name = %s", (owner, name))
            row = cur.fetchone()
    if row is None:
        raise ValueError("Proyek tidak ditemukan untuk akun ini.")
    restore_session_from_json({}, row[0])
    return row[0]
