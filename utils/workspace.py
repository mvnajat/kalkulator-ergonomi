"""Portable named projects and an optional private PostgreSQL project store.

No project data is sent to any remote service unless the user enables cloud
storage and the Streamlit deployment supplies OIDC + a database URL.
"""

import json
from datetime import datetime, timezone
from uuid import UUID, uuid4

from utils.exporter import SESSION_BACKUP_FIELDS, export_session_to_json, restore_session_from_json


def google_auth_is_ready(secrets: object) -> bool:
    """Return whether the five required Google OIDC secrets are present."""
    try:
        settings = secrets.get("auth", {})
        return all(bool(settings.get(key)) for key in (
            "redirect_uri", "cookie_secret", "client_id", "client_secret", "server_metadata_url"
        ))
    except Exception:
        # Never show secret values (or secret-loading failures) in the UI.
        return False


def oidc_subject(user: object) -> str:
    """Use the stable Google OIDC subject, not the email, as the data owner."""
    try:
        if not user.is_logged_in:
            return ""
        subject = user.get("sub")
        return str(subject).strip() if subject else ""
    except (AttributeError, KeyError, TypeError):
        return ""


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


# History is append-only: unlike named projects, saving a second observation
# never overwrites an earlier result. Every query is scoped to the OIDC subject.
HISTORY_MODULES = {"all"} | {f"modul-{i:02d}" for i in range(1, 10)}
_HISTORY_TABLE_SQL = """CREATE TABLE IF NOT EXISTS ie_toolkit_history (
    id UUID PRIMARY KEY, owner_sub TEXT NOT NULL, project_name TEXT NOT NULL,
    module_slug TEXT NOT NULL, summary TEXT NOT NULL, backup JSONB NOT NULL,
    saved_at TIMESTAMPTZ NOT NULL DEFAULT NOW())"""


def _history_owner(database_url: str, owner: str) -> None:
    if not database_url or not owner or not str(owner).strip():
        raise ValueError("Riwayat cloud memerlukan Login Google dan database aktif.")


def cloud_history_save(database_url: str, owner: str, name: str,
                       module_slug: str, backup: dict, summary: str) -> str:
    """Append one owner-private snapshot and return its immutable UUID."""
    _history_owner(database_url, owner)
    name = normalize_project_name(name)
    if module_slug not in HISTORY_MODULES:
        raise ValueError("Modul riwayat tidak valid.")
    if not isinstance(backup, dict):
        raise ValueError("Cadangan riwayat tidak valid.")
    serialized = json.dumps(backup, ensure_ascii=False, allow_nan=False)
    if len(serialized.encode("utf-8")) > MAX_PROJECT_SIZE:
        raise ValueError("Data riwayat melebihi batas 5 MB.")
    summary = " ".join(str(summary).split())[:180]
    import psycopg
    from psycopg.types.json import Jsonb

    snapshot_id = uuid4()
    with psycopg.connect(database_url, connect_timeout=6, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute(_HISTORY_TABLE_SQL)
            cur.execute("""INSERT INTO ie_toolkit_history
                (id, owner_sub, project_name, module_slug, summary, backup)
                VALUES (%s, %s, %s, %s, %s, %s)""",
                (snapshot_id, owner, name, module_slug, summary, Jsonb(backup)))
    return str(snapshot_id)


def cloud_history_list(database_url: str, owner: str, limit: int = 30) -> list[dict]:
    """Return dated history metadata only, never another account's data."""
    _history_owner(database_url, owner)
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Batas riwayat harus antara 1 dan 100.")
    import psycopg

    with psycopg.connect(database_url, connect_timeout=6, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute(_HISTORY_TABLE_SQL)
            cur.execute("""SELECT id, project_name, module_slug, summary, saved_at
                FROM ie_toolkit_history WHERE owner_sub = %s
                ORDER BY saved_at DESC, id DESC LIMIT %s""", (owner, limit))
            records = cur.fetchall()
    return [dict(id=str(r[0]), name=r[1], module_slug=r[2],
                 summary=r[3], saved_at=r[4]) for r in records]


def cloud_history_load(database_url: str, owner: str, snapshot_id: str) -> dict:
    """Load only a history item belonging to the current Google subject."""
    _history_owner(database_url, owner)
    try:
        valid_uuid = UUID(str(snapshot_id))
    except (ValueError, TypeError, AttributeError) as exc:
        raise ValueError("ID riwayat tidak valid.") from exc
    import psycopg

    with psycopg.connect(database_url, connect_timeout=6, sslmode="require") as conn:
        with conn.cursor() as cur:
            cur.execute(_HISTORY_TABLE_SQL)
            cur.execute("SELECT backup FROM ie_toolkit_history WHERE owner_sub = %s AND id = %s",
                        (owner, valid_uuid))
            record = cur.fetchone()
    if not record:
        raise ValueError("Riwayat tidak ditemukan untuk akun ini.")
    restore_session_from_json({}, record[0])
    return record[0]
