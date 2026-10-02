"""SQLite-Persistenz fuer das BI-Tutor-Forum.

Tabellen:
- threads: Diskussionsthemen (Titel + Eroeffnungsbeitrag, Rolle, optional Modul)
- posts:   Antworten zu einem Thread (chronologisch)

Keine Authentifizierung im Prototyp - Name + Rolle werden im UI gesetzt
und mit jeder Aktion an die Storage-Layer weitergereicht.
"""
from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "forum.db"


ROLE_STUDENT = "Studierend"
ROLE_TUTOR = "Tutor:in"
ROLE_PROF = "Professor:in"
ROLES = [ROLE_STUDENT, ROLE_TUTOR, ROLE_PROF]


@dataclass
class Thread:
    id: int
    title: str
    body: str
    author: str
    role: str
    module: Optional[str]
    is_pinned: int
    is_resolved: int
    created_at: str
    reply_count: int = 0


@dataclass
class Post:
    id: int
    thread_id: int
    body: str
    author: str
    role: str
    is_endorsed: int
    created_at: str


# --- Connection -----------------------------------------------------------
@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    """Schema-DDL idempotent ausfuehren + bei Bedarf Seed schreiben."""
    with _connect() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS threads (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              title TEXT NOT NULL,
              body TEXT NOT NULL,
              author TEXT NOT NULL,
              role TEXT NOT NULL,
              module TEXT,
              is_pinned INTEGER NOT NULL DEFAULT 0,
              is_resolved INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS posts (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              thread_id INTEGER NOT NULL REFERENCES threads(id) ON DELETE CASCADE,
              body TEXT NOT NULL,
              author TEXT NOT NULL,
              role TEXT NOT NULL,
              is_endorsed INTEGER NOT NULL DEFAULT 0,
              created_at TEXT NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_posts_thread ON posts(thread_id);
            CREATE INDEX IF NOT EXISTS idx_threads_pinned ON threads(is_pinned, created_at);
            """
        )
        # Seed beim ersten Start, damit das Forum nicht leer aussieht
        empty = c.execute("SELECT COUNT(*) FROM threads").fetchone()[0] == 0
    if empty:
        _seed()


def _seed() -> None:
    now = datetime.utcnow().isoformat(timespec="seconds")
    samples = [
        (
            "Wann nutzt man Star-Schema vs. Snowflake-Schema?",
            "In der Vorlesung wurden beide Modellierungsansaetze gegenuebergestellt. "
            "Mir ist die Entscheidungsregel noch nicht ganz klar - wann wuerdet ihr "
            "in der Praxis welche Variante waehlen?",
            "Marie K.", ROLE_STUDENT, "Star-Schema",
        ),
        (
            "Tippsammlung zu ETL-Aufgaben aus Uebung 04",
            "Hier ein paar haeufige Stolpersteine bei Transformationsregeln aus der "
            "vierten Uebung. Ergaenzungen willkommen.",
            "Dr. Henning Baars", ROLE_PROF, "Datenbereitstellung",
        ),
        (
            "Klausurvorbereitung: OLAP-Operationen",
            "Slicing, Dicing, Drill-Down, Roll-Up - welche Beispiele aus der "
            "Vorlesung sind besonders pruefungsrelevant?",
            "Jonas P.", ROLE_STUDENT, "Analysesysteme",
        ),
    ]
    with _connect() as c:
        for title, body, author, role, module in samples:
            c.execute(
                "INSERT INTO threads (title, body, author, role, module, created_at) "
                "VALUES (?,?,?,?,?,?)",
                (title, body, author, role, module, now),
            )


def available_modules() -> list[str]:
    return [
        "BI-Begriff",
        "Datenbereitstellung",
        "Datenmodellierung",
        "Star-Schema",
        "Analysesysteme",
        "Entwicklung & Betrieb",
        "Uebung",
        "Altklausur",
        "Lehrbuch",
        "Sonstiges",
    ]


# --- Reads ----------------------------------------------------------------
def _row_to_thread(row: sqlite3.Row) -> Thread:
    return Thread(
        id=row["id"],
        title=row["title"],
        body=row["body"],
        author=row["author"],
        role=row["role"],
        module=row["module"],
        is_pinned=row["is_pinned"],
        is_resolved=row["is_resolved"],
        created_at=row["created_at"],
        reply_count=row["reply_count"] if "reply_count" in row.keys() else 0,
    )


def list_threads(
    *,
    only_open: bool = False,
    only_pinned: bool = False,
    module: Optional[str] = None,
    search: Optional[str] = None,
) -> list[Thread]:
    sql = (
        "SELECT t.*, "
        "(SELECT COUNT(*) FROM posts WHERE thread_id = t.id) AS reply_count "
        "FROM threads t WHERE 1=1 "
    )
    params: list = []
    if only_open:
        sql += " AND t.is_resolved = 0"
    if only_pinned:
        sql += " AND t.is_pinned = 1"
    if module:
        sql += " AND t.module = ?"
        params.append(module)
    if search:
        sql += " AND (t.title LIKE ? OR t.body LIKE ?)"
        like = f"%{search}%"
        params.extend([like, like])
    sql += " ORDER BY t.is_pinned DESC, t.created_at DESC"
    with _connect() as c:
        rows = c.execute(sql, params).fetchall()
    return [_row_to_thread(r) for r in rows]


def get_thread(thread_id: int) -> Optional[Thread]:
    sql = (
        "SELECT t.*, "
        "(SELECT COUNT(*) FROM posts WHERE thread_id = t.id) AS reply_count "
        "FROM threads t WHERE t.id = ?"
    )
    with _connect() as c:
        row = c.execute(sql, (thread_id,)).fetchone()
    return _row_to_thread(row) if row else None


def get_posts(thread_id: int) -> list[Post]:
    sql = "SELECT * FROM posts WHERE thread_id = ? ORDER BY created_at ASC, id ASC"
    with _connect() as c:
        rows = c.execute(sql, (thread_id,)).fetchall()
    return [
        Post(
            id=r["id"], thread_id=r["thread_id"], body=r["body"],
            author=r["author"], role=r["role"],
            is_endorsed=r["is_endorsed"], created_at=r["created_at"],
        )
        for r in rows
    ]


# --- Writes ---------------------------------------------------------------
def _now() -> str:
    return datetime.utcnow().isoformat(timespec="seconds")


def create_thread(
    *, title: str, body: str, author: str, role: str, module: Optional[str] = None,
) -> int:
    with _connect() as c:
        cur = c.execute(
            "INSERT INTO threads (title, body, author, role, module, created_at) "
            "VALUES (?,?,?,?,?,?)",
            (title.strip(), body.strip(), author.strip(), role, module, _now()),
        )
        return cur.lastrowid


def reply_to_thread(
    *, thread_id: int, body: str, author: str, role: str,
) -> int:
    with _connect() as c:
        cur = c.execute(
            "INSERT INTO posts (thread_id, body, author, role, created_at) "
            "VALUES (?,?,?,?,?)",
            (thread_id, body.strip(), author.strip(), role, _now()),
        )
        return cur.lastrowid


def toggle_pinned(thread_id: int) -> None:
    with _connect() as c:
        c.execute(
            "UPDATE threads SET is_pinned = 1 - is_pinned WHERE id = ?",
            (thread_id,),
        )


def toggle_resolved(thread_id: int) -> None:
    with _connect() as c:
        c.execute(
            "UPDATE threads SET is_resolved = 1 - is_resolved WHERE id = ?",
            (thread_id,),
        )


def toggle_endorsed(post_id: int) -> None:
    with _connect() as c:
        c.execute(
            "UPDATE posts SET is_endorsed = 1 - is_endorsed WHERE id = ?",
            (post_id,),
        )
