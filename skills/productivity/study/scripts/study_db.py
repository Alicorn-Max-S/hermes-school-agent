#!/usr/bin/env python3
"""
Study Database CLI — Persistent study tracking with semantic search.

Manages classes, categories, study files, question history, knowledge scores,
and question type distribution. Uses sentence-transformers for semantic
deduplication and spaced repetition (falls back to FTS5 if unavailable).

Database: ~/.apollo/study_data.db
Usage:    python study_db.py <command> [options]
"""

import argparse
import json
import os
import sqlite3
import struct
import sys
from datetime import datetime
from math import sqrt
from pathlib import Path

DB_PATH = Path(os.getenv("APOLLO_HOME", Path.home() / ".apollo")) / "study_data.db"

# 10 question types
QUESTION_TYPES = [
    "fill_in_blank",
    "conjugation",
    "vocabulary",
    "full_sentence",
    "multiple_choice",
    "true_false",
    "short_answer",
    "matching",
    "ordering",
    "diagram_label",
]

TYPE_COLUMNS = [f"type_{t}" for t in QUESTION_TYPES]

# ---------------------------------------------------------------------------
# Embedding support (lazy-loaded)
# ---------------------------------------------------------------------------

_embed_model = None
_embed_available = None


def _check_embed():
    global _embed_available
    if _embed_available is not None:
        return _embed_available
    try:
        import sentence_transformers  # noqa: F401
        _embed_available = True
    except ImportError:
        _embed_available = False
        print(
            "Warning: sentence-transformers not installed. "
            "Semantic search will fall back to FTS5 text search. "
            "Install with: pip install sentence-transformers",
            file=sys.stderr,
        )
    return _embed_available


def _get_model():
    global _embed_model
    if _embed_model is not None:
        return _embed_model
    if not _check_embed():
        return None
    from sentence_transformers import SentenceTransformer
    _embed_model = SentenceTransformer("all-MiniLM-L6-v2")
    return _embed_model


def _encode(text: str) -> bytes | None:
    model = _get_model()
    if model is None:
        return None
    vec = model.encode(text, normalize_embeddings=True)
    return vec.astype("float32").tobytes()


def _cosine_sim(a_bytes: bytes, b_bytes: bytes) -> float:
    n = len(a_bytes) // 4
    a = struct.unpack(f"{n}f", a_bytes)
    b = struct.unpack(f"{n}f", b_bytes)
    dot = sum(x * y for x, y in zip(a, b))
    na = sqrt(sum(x * x for x in a))
    nb = sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------------------------
# Database init
# ---------------------------------------------------------------------------


def get_db() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    _init_tables(conn)
    return conn


def _init_tables(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY,
            name TEXT UNIQUE NOT NULL,
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY,
            class_id INTEGER NOT NULL REFERENCES classes(id),
            name TEXT NOT NULL,
            accent_mode TEXT,
            spelling_mode TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            UNIQUE(class_id, name)
        );

        CREATE TABLE IF NOT EXISTS study_files (
            id INTEGER PRIMARY KEY,
            class_id INTEGER NOT NULL REFERENCES classes(id),
            category_id INTEGER REFERENCES categories(id),
            filename TEXT NOT NULL,
            original_path TEXT,
            content TEXT NOT NULL,
            content_type TEXT,
            created_at TEXT DEFAULT (datetime('now')),
            last_studied TEXT
        );

        CREATE TABLE IF NOT EXISTS questions (
            id INTEGER PRIMARY KEY,
            class_id INTEGER NOT NULL REFERENCES classes(id),
            category_id INTEGER REFERENCES categories(id),
            question_text TEXT NOT NULL,
            correct_answer TEXT NOT NULL,
            user_answer TEXT,
            accuracy REAL NOT NULL DEFAULT 0,
            accent_correct INTEGER,
            spelling_correct INTEGER,
            question_type TEXT NOT NULL,
            study_file_id INTEGER REFERENCES study_files(id),
            created_at TEXT DEFAULT (datetime('now'))
        );

        CREATE TABLE IF NOT EXISTS question_embeddings (
            question_id INTEGER PRIMARY KEY REFERENCES questions(id),
            embedding BLOB NOT NULL
        );

        CREATE TABLE IF NOT EXISTS knowledge_scores (
            id INTEGER PRIMARY KEY,
            class_id INTEGER NOT NULL REFERENCES classes(id),
            category_id INTEGER NOT NULL REFERENCES categories(id),
            score REAL NOT NULL DEFAULT 0,
            total_attempts INTEGER DEFAULT 0,
            accuracy_sum REAL DEFAULT 0,
            summary TEXT,
            last_updated TEXT DEFAULT (datetime('now')),
            type_fill_in_blank INTEGER DEFAULT 0,
            type_conjugation INTEGER DEFAULT 0,
            type_vocabulary INTEGER DEFAULT 0,
            type_full_sentence INTEGER DEFAULT 0,
            type_multiple_choice INTEGER DEFAULT 0,
            type_true_false INTEGER DEFAULT 0,
            type_short_answer INTEGER DEFAULT 0,
            type_matching INTEGER DEFAULT 0,
            type_ordering INTEGER DEFAULT 0,
            type_diagram_label INTEGER DEFAULT 0,
            UNIQUE(class_id, category_id)
        );
    """)
    # FTS5 virtual table — wrapped in try/except because CREATE VIRTUAL TABLE
    # IF NOT EXISTS can still fail if the table already exists in some SQLite versions
    try:
        conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS questions_fts USING fts5(
                question_text, correct_answer, user_answer,
                content='questions', content_rowid='id'
            )
        """)
    except sqlite3.OperationalError:
        pass  # Already exists
    conn.commit()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_class(conn, name: str) -> int | None:
    row = conn.execute("SELECT id FROM classes WHERE name = ?", (name,)).fetchone()
    return row["id"] if row else None


def _resolve_category(conn, class_id: int, name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM categories WHERE class_id = ? AND name = ?",
        (class_id, name),
    ).fetchone()
    return row["id"] if row else None


def _require_class(conn, name: str) -> int:
    cid = _resolve_class(conn, name)
    if cid is None:
        print(json.dumps({"error": f"Class '{name}' not found. Create it first with create_class."}))
        sys.exit(1)
    return cid


def _require_category(conn, class_id: int, name: str) -> int:
    cat_id = _resolve_category(conn, class_id, name)
    if cat_id is None:
        print(json.dumps({"error": f"Category '{name}' not found. Create it first with create_category."}))
        sys.exit(1)
    return cat_id


def _type_distribution(row) -> dict:
    return {t: (row[f"type_{t}"] or 0) for t in QUESTION_TYPES}


def _output(data):
    print(json.dumps(data, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Commands: Classes
# ---------------------------------------------------------------------------


def cmd_list_classes(args):
    conn = get_db()
    rows = conn.execute("SELECT id, name, created_at FROM classes ORDER BY name").fetchall()
    _output([dict(r) for r in rows])


def cmd_create_class(args):
    conn = get_db()
    try:
        conn.execute("INSERT INTO classes (name) VALUES (?)", (args.name,))
        conn.commit()
        cid = _resolve_class(conn, args.name)
        _output({"success": True, "id": cid, "name": args.name})
    except sqlite3.IntegrityError:
        cid = _resolve_class(conn, args.name)
        _output({"success": True, "id": cid, "name": args.name, "note": "Already exists."})


# ---------------------------------------------------------------------------
# Commands: Categories
# ---------------------------------------------------------------------------


def cmd_list_categories(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    rows = conn.execute(
        "SELECT id, name, accent_mode, spelling_mode, created_at FROM categories WHERE class_id = ? ORDER BY name",
        (class_id,),
    ).fetchall()
    _output([dict(r) for r in rows])


def cmd_create_category(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    try:
        conn.execute(
            "INSERT INTO categories (class_id, name) VALUES (?, ?)",
            (class_id, args.name),
        )
        conn.commit()
        cat_id = _resolve_category(conn, class_id, args.name)
        _output({"success": True, "id": cat_id, "class": args.class_name, "name": args.name})
    except sqlite3.IntegrityError:
        cat_id = _resolve_category(conn, class_id, args.name)
        _output({
            "success": True, "id": cat_id,
            "class": args.class_name, "name": args.name,
            "note": "Already exists.",
        })


GRADING_MODES = ["strict", "partial", "lenient"]


def cmd_set_grading_mode(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    category_id = _require_category(conn, class_id, args.category)

    updates = []
    params = []

    if args.accent_mode is not None:
        if args.accent_mode not in GRADING_MODES:
            _output({"error": f"Invalid accent_mode '{args.accent_mode}'. Valid: {GRADING_MODES}"})
            sys.exit(1)
        updates.append("accent_mode = ?")
        params.append(args.accent_mode)

    if args.spelling_mode is not None:
        if args.spelling_mode not in GRADING_MODES:
            _output({"error": f"Invalid spelling_mode '{args.spelling_mode}'. Valid: {GRADING_MODES}"})
            sys.exit(1)
        updates.append("spelling_mode = ?")
        params.append(args.spelling_mode)

    if not updates:
        _output({"error": "Provide at least one of --accent-mode or --spelling-mode."})
        sys.exit(1)

    params.append(category_id)
    conn.execute(f"UPDATE categories SET {', '.join(updates)} WHERE id = ?", params)
    conn.commit()

    row = conn.execute(
        "SELECT name, accent_mode, spelling_mode FROM categories WHERE id = ?",
        (category_id,),
    ).fetchone()
    _output({
        "success": True,
        "class": args.class_name,
        "category": row["name"],
        "accent_mode": row["accent_mode"],
        "spelling_mode": row["spelling_mode"],
    })


def cmd_get_category(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    category_id = _require_category(conn, class_id, args.category)
    row = conn.execute(
        "SELECT id, name, accent_mode, spelling_mode, created_at FROM categories WHERE id = ?",
        (category_id,),
    ).fetchone()
    _output(dict(row))


# ---------------------------------------------------------------------------
# Commands: Study Files
# ---------------------------------------------------------------------------


def cmd_save_file(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    category_id = None
    if args.category:
        category_id = _require_category(conn, class_id, args.category)

    content = args.content
    if content == "-":
        content = sys.stdin.read()

    cur = conn.execute(
        """INSERT INTO study_files (class_id, category_id, filename, original_path, content, content_type)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (class_id, category_id, args.filename, args.original_path, content, args.content_type),
    )
    conn.commit()
    _output({"success": True, "id": cur.lastrowid, "filename": args.filename})


def cmd_list_files(args):
    conn = get_db()
    if args.class_name:
        class_id = _require_class(conn, args.class_name)
        rows = conn.execute(
            """SELECT sf.id, c.name as class, cat.name as category,
                      sf.filename, sf.content_type, sf.created_at, sf.last_studied
               FROM study_files sf
               JOIN classes c ON sf.class_id = c.id
               LEFT JOIN categories cat ON sf.category_id = cat.id
               WHERE sf.class_id = ?
               ORDER BY sf.created_at DESC""",
            (class_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT sf.id, c.name as class, cat.name as category,
                      sf.filename, sf.content_type, sf.created_at, sf.last_studied
               FROM study_files sf
               JOIN classes c ON sf.class_id = c.id
               LEFT JOIN categories cat ON sf.category_id = cat.id
               ORDER BY sf.created_at DESC"""
        ).fetchall()
    _output([dict(r) for r in rows])


def cmd_get_file(args):
    conn = get_db()
    row = conn.execute(
        """SELECT sf.*, c.name as class_name, cat.name as category_name
           FROM study_files sf
           JOIN classes c ON sf.class_id = c.id
           LEFT JOIN categories cat ON sf.category_id = cat.id
           WHERE sf.id = ?""",
        (args.file_id,),
    ).fetchone()
    if not row:
        _output({"error": f"File {args.file_id} not found."})
        return
    _output(dict(row))


def cmd_delete_file(args):
    conn = get_db()
    conn.execute("DELETE FROM study_files WHERE id = ?", (args.file_id,))
    conn.commit()
    _output({"success": True, "deleted": args.file_id})


def cmd_update_last_studied(args):
    conn = get_db()
    now = datetime.now().isoformat()
    conn.execute("UPDATE study_files SET last_studied = ? WHERE id = ?", (now, args.file_id))
    conn.commit()
    _output({"success": True, "file_id": args.file_id, "last_studied": now})


# ---------------------------------------------------------------------------
# Commands: Record question & update scores
# ---------------------------------------------------------------------------


def cmd_record(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    category_id = _require_category(conn, class_id, args.category)

    if args.type not in QUESTION_TYPES:
        _output({"error": f"Invalid question type '{args.type}'. Valid: {QUESTION_TYPES}"})
        sys.exit(1)

    accuracy = args.accuracy
    if accuracy < 0.0 or accuracy > 1.0:
        _output({"error": f"Accuracy must be between 0.0 and 1.0, got {accuracy}"})
        sys.exit(1)

    # Insert question record
    cur = conn.execute(
        """INSERT INTO questions
           (class_id, category_id, question_text, correct_answer, user_answer,
            accuracy, accent_correct, spelling_correct, question_type, study_file_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            class_id, category_id, args.question, args.correct_answer,
            args.user_answer, accuracy, args.accent_correct, args.spelling_correct,
            args.type, args.file_id,
        ),
    )
    question_id = cur.lastrowid

    # Update FTS index
    try:
        conn.execute(
            "INSERT INTO questions_fts (rowid, question_text, correct_answer, user_answer) VALUES (?, ?, ?, ?)",
            (question_id, args.question, args.correct_answer, args.user_answer),
        )
    except sqlite3.OperationalError:
        pass  # FTS not available

    # Embed the question for semantic search
    embedding = _encode(args.question)
    if embedding:
        conn.execute(
            "INSERT OR REPLACE INTO question_embeddings (question_id, embedding) VALUES (?, ?)",
            (question_id, embedding),
        )

    # Update knowledge_scores with rolling window (last 20)
    last_20 = conn.execute(
        """SELECT accuracy FROM questions
           WHERE class_id = ? AND category_id = ?
           ORDER BY created_at DESC LIMIT 20""",
        (class_id, category_id),
    ).fetchall()

    accuracy_sum = sum(r["accuracy"] for r in last_20)
    total_count = len(last_20)
    score = (accuracy_sum / total_count) * 10 if total_count > 0 else 0

    # Get all-time totals (accuracy_sum = sum of accuracy values, e.g. 7.3 out of 10 attempts)
    totals = conn.execute(
        """SELECT COUNT(*) as total, COALESCE(SUM(accuracy), 0) as correct
           FROM questions WHERE class_id = ? AND category_id = ?""",
        (class_id, category_id),
    ).fetchone()

    type_col = f"type_{args.type}"
    now = datetime.now().isoformat()

    # Upsert knowledge_scores
    existing = conn.execute(
        "SELECT id FROM knowledge_scores WHERE class_id = ? AND category_id = ?",
        (class_id, category_id),
    ).fetchone()

    if existing:
        conn.execute(
            f"""UPDATE knowledge_scores
                SET score = ?, total_attempts = ?, accuracy_sum = ?,
                    {type_col} = {type_col} + 1, last_updated = ?
                WHERE class_id = ? AND category_id = ?""",
            (score, totals["total"], totals["correct"], now, class_id, category_id),
        )
    else:
        # Build insert with type column set to 1
        cols = ["class_id", "category_id", "score", "total_attempts", "accuracy_sum", "last_updated", type_col]
        placeholders = ", ".join(["?"] * len(cols))
        conn.execute(
            f"INSERT INTO knowledge_scores ({', '.join(cols)}) VALUES ({placeholders})",
            (class_id, category_id, score, totals["total"], totals["correct"], now, 1),
        )

    conn.commit()
    result = {
        "success": True,
        "question_id": question_id,
        "accuracy": accuracy,
        "score": round(score, 1),
        "total_attempts": totals["total"],
        "embedded": embedding is not None,
    }
    if args.accent_correct is not None:
        result["accent_correct"] = bool(args.accent_correct)
    if args.spelling_correct is not None:
        result["spelling_correct"] = bool(args.spelling_correct)
    _output(result)


# ---------------------------------------------------------------------------
# Commands: Semantic search
# ---------------------------------------------------------------------------


def cmd_search_similar(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    category_id = None
    if args.category:
        category_id = _resolve_category(conn, class_id, args.category)

    limit = args.limit or 5

    # Try embedding-based search first
    query_embedding = _encode(args.query)
    if query_embedding:
        # Load all embeddings for this class/category
        if category_id:
            rows = conn.execute(
                """SELECT q.id, q.question_text, q.correct_answer, q.accuracy, q.accent_correct, q.spelling_correct,
                          q.question_type, q.created_at, qe.embedding
                   FROM questions q
                   JOIN question_embeddings qe ON q.id = qe.question_id
                   WHERE q.class_id = ? AND q.category_id = ?""",
                (class_id, category_id),
            ).fetchall()
        else:
            rows = conn.execute(
                """SELECT q.id, q.question_text, q.correct_answer, q.accuracy, q.accent_correct, q.spelling_correct,
                          q.question_type, q.created_at, qe.embedding
                   FROM questions q
                   JOIN question_embeddings qe ON q.id = qe.question_id
                   WHERE q.class_id = ?""",
                (class_id,),
            ).fetchall()

        scored = []
        for r in rows:
            sim = _cosine_sim(query_embedding, r["embedding"])
            scored.append({
                "id": r["id"],
                "question_text": r["question_text"],
                "correct_answer": r["correct_answer"],
                "accuracy": r["accuracy"],
                "accent_correct": r["accent_correct"],
                "spelling_correct": r["spelling_correct"],
                "question_type": r["question_type"],
                "similarity": round(sim, 4),
                "created_at": r["created_at"],
            })
        scored.sort(key=lambda x: x["similarity"], reverse=True)
        _output({"method": "embedding", "results": scored[:limit]})
        return

    # Fallback: FTS5 text search
    try:
        fts_rows = conn.execute(
            """SELECT q.id, q.question_text, q.correct_answer, q.accuracy,
                      q.accent_correct, q.spelling_correct, q.question_type, q.created_at,
                      rank
               FROM questions_fts fts
               JOIN questions q ON q.id = fts.rowid
               WHERE questions_fts MATCH ? AND q.class_id = ?
               ORDER BY rank
               LIMIT ?""",
            (args.query, class_id, limit),
        ).fetchall()
        _output({
            "method": "fts5",
            "results": [{
                "id": r["id"],
                "question_text": r["question_text"],
                "correct_answer": r["correct_answer"],
                "accuracy": r["accuracy"],
                "accent_correct": r["accent_correct"],
                "spelling_correct": r["spelling_correct"],
                "question_type": r["question_type"],
                "fts_rank": r["rank"],
                "created_at": r["created_at"],
            } for r in fts_rows],
        })
    except sqlite3.OperationalError:
        _output({"method": "none", "results": [], "note": "No search method available."})


# ---------------------------------------------------------------------------
# Commands: Knowledge scores
# ---------------------------------------------------------------------------


def cmd_get_scores(args):
    conn = get_db()
    if args.class_name:
        class_id = _require_class(conn, args.class_name)
        rows = conn.execute(
            """SELECT ks.*, c.name as class_name, cat.name as category_name,
                      cat.accent_mode, cat.spelling_mode
               FROM knowledge_scores ks
               JOIN classes c ON ks.class_id = c.id
               JOIN categories cat ON ks.category_id = cat.id
               WHERE ks.class_id = ?
               ORDER BY cat.name""",
            (class_id,),
        ).fetchall()
    else:
        rows = conn.execute(
            """SELECT ks.*, c.name as class_name, cat.name as category_name,
                      cat.accent_mode, cat.spelling_mode
               FROM knowledge_scores ks
               JOIN classes c ON ks.class_id = c.id
               JOIN categories cat ON ks.category_id = cat.id
               ORDER BY c.name, cat.name"""
        ).fetchall()

    result = {}
    for r in rows:
        cname = r["class_name"]
        if cname not in result:
            result[cname] = {"class": cname, "categories": []}
        result[cname]["categories"].append({
            "category": r["category_name"],
            "score": round(r["score"], 1),
            "total_attempts": r["total_attempts"],
            "accuracy_sum": round(r["accuracy_sum"] or 0, 2),
            "summary": r["summary"],
            "last_updated": r["last_updated"],
            "accent_mode": r["accent_mode"],
            "spelling_mode": r["spelling_mode"],
            "type_distribution": _type_distribution(r),
        })

    _output(list(result.values()))


def cmd_get_score(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    category_id = _require_category(conn, class_id, args.category)
    row = conn.execute(
        """SELECT ks.*, c.name as class_name, cat.name as category_name
           FROM knowledge_scores ks
           JOIN classes c ON ks.class_id = c.id
           JOIN categories cat ON ks.category_id = cat.id
           WHERE ks.class_id = ? AND ks.category_id = ?""",
        (class_id, category_id),
    ).fetchone()
    if not row:
        _output({"class": args.class_name, "category": args.category, "score": None, "note": "No data yet."})
        return
    _output({
        "class": row["class_name"],
        "category": row["category_name"],
        "score": round(row["score"], 1),
        "total_attempts": row["total_attempts"],
        "accuracy_sum": round(row["accuracy_sum"] or 0, 2),
        "summary": row["summary"],
        "last_updated": row["last_updated"],
        "type_distribution": _type_distribution(row),
    })


def cmd_get_history(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    limit = args.limit or 20

    params: list = [class_id]
    where = "q.class_id = ?"

    if args.category:
        category_id = _require_category(conn, class_id, args.category)
        where += " AND q.category_id = ?"
        params.append(category_id)

    if args.incorrect_only:
        where += " AND q.accuracy < 1.0"

    params.append(limit)

    rows = conn.execute(
        f"""SELECT q.id, q.question_text, q.correct_answer, q.user_answer,
                   q.accuracy, q.accent_correct, q.spelling_correct, q.question_type, q.created_at,
                   cat.name as category_name
            FROM questions q
            LEFT JOIN categories cat ON q.category_id = cat.id
            WHERE {where}
            ORDER BY q.created_at DESC
            LIMIT ?""",
        params,
    ).fetchall()
    _output([dict(r) for r in rows])


def cmd_get_weak_areas(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    rows = conn.execute(
        """SELECT ks.score, cat.name as category, ks.summary,
                  ks.total_attempts, ks.accuracy_sum, ks.last_updated
           FROM knowledge_scores ks
           JOIN categories cat ON ks.category_id = cat.id
           WHERE ks.class_id = ? AND ks.score < 5
           ORDER BY ks.score ASC""",
        (class_id,),
    ).fetchall()
    _output([dict(r) for r in rows])


def cmd_update_summary(args):
    conn = get_db()
    class_id = _require_class(conn, args.class_name)
    category_id = _require_category(conn, class_id, args.category)
    now = datetime.now().isoformat()
    conn.execute(
        """UPDATE knowledge_scores SET summary = ?, last_updated = ?
           WHERE class_id = ? AND category_id = ?""",
        (args.summary, now, class_id, category_id),
    )
    conn.commit()
    _output({"success": True, "class": args.class_name, "category": args.category})


# ---------------------------------------------------------------------------
# Commands: Smart suggestions
# ---------------------------------------------------------------------------


def cmd_suggest(args):
    conn = get_db()

    # Get all scores with last_studied info
    rows = conn.execute(
        """SELECT ks.score, ks.total_attempts, ks.summary, ks.last_updated,
                  c.name as class_name, cat.name as category_name,
                  (SELECT MAX(sf.last_studied) FROM study_files sf
                   WHERE sf.class_id = ks.class_id
                   AND (sf.category_id = ks.category_id OR sf.category_id IS NULL)) as last_studied
           FROM knowledge_scores ks
           JOIN classes c ON ks.class_id = c.id
           JOIN categories cat ON ks.category_id = cat.id"""
    ).fetchall()

    suggestions = []
    now = datetime.now()

    for r in rows:
        score = r["score"] or 0
        last = r["last_studied"] or r["last_updated"]
        try:
            last_dt = datetime.fromisoformat(last)
            days_since = (now - last_dt).days
        except (ValueError, TypeError):
            days_since = 30  # Default if no date

        total = r["total_attempts"] or 0
        priority = (10 - score) * 2 + days_since * 0.5
        if total == 0:
            priority += 5

        suggestions.append({
            "class": r["class_name"],
            "category": r["category_name"],
            "score": round(score, 1),
            "total_attempts": total,
            "days_since_studied": days_since,
            "priority": round(priority, 1),
            "summary": r["summary"],
        })

    # Also include categories with no score (never studied)
    unstudied = conn.execute(
        """SELECT c.name as class_name, cat.name as category_name
           FROM categories cat
           JOIN classes c ON cat.class_id = c.id
           WHERE NOT EXISTS (
               SELECT 1 FROM knowledge_scores ks
               WHERE ks.class_id = cat.class_id AND ks.category_id = cat.id
           )"""
    ).fetchall()

    for r in unstudied:
        suggestions.append({
            "class": r["class_name"],
            "category": r["category_name"],
            "score": None,
            "total_attempts": 0,
            "days_since_studied": None,
            "priority": 15.0,  # High priority for never-studied
            "summary": "Never studied",
        })

    suggestions.sort(key=lambda x: x["priority"], reverse=True)
    _output(suggestions[:10])


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def main():
    parser = argparse.ArgumentParser(description="Study Database CLI")
    sub = parser.add_subparsers(dest="command")

    # Classes
    sub.add_parser("list_classes")
    p = sub.add_parser("create_class")
    p.add_argument("name")

    # Categories
    p = sub.add_parser("list_categories")
    p.add_argument("--class", dest="class_name", required=True)
    p = sub.add_parser("create_category")
    p.add_argument("--class", dest="class_name", required=True)
    p.add_argument("--name", required=True)

    p = sub.add_parser("get_category")
    p.add_argument("--class", dest="class_name", required=True)
    p.add_argument("--category", required=True)

    p = sub.add_parser("set_grading_mode")
    p.add_argument("--class", dest="class_name", required=True)
    p.add_argument("--category", required=True)
    p.add_argument("--accent-mode", default=None, choices=GRADING_MODES)
    p.add_argument("--spelling-mode", default=None, choices=GRADING_MODES)

    # Study files
    p = sub.add_parser("save_file")
    p.add_argument("--class", dest="class_name", required=True)
    p.add_argument("--category", default=None)
    p.add_argument("--filename", required=True)
    p.add_argument("--original-path", default=None)
    p.add_argument("--content", required=True)
    p.add_argument("--content-type", default=None)

    p = sub.add_parser("list_files")
    p.add_argument("--class", dest="class_name", default=None)

    p = sub.add_parser("get_file")
    p.add_argument("file_id", type=int)

    p = sub.add_parser("delete_file")
    p.add_argument("file_id", type=int)

    p = sub.add_parser("update_last_studied")
    p.add_argument("file_id", type=int)

    # Record question
    p = sub.add_parser("record")
    p.add_argument("--class", dest="class_name", required=True)
    p.add_argument("--category", required=True)
    p.add_argument("--question", required=True)
    p.add_argument("--correct-answer", required=True)
    p.add_argument("--user-answer", required=True)
    p.add_argument("--accuracy", type=float, required=True, help="0.0 (wrong) to 1.0 (perfect)")
    p.add_argument("--accent-correct", type=int, default=None, choices=[0, 1], help="Accent correctness (null if N/A)")
    p.add_argument("--spelling-correct", type=int, default=None, choices=[0, 1], help="Spelling correctness (null if N/A)")
    p.add_argument("--type", required=True)
    p.add_argument("--file-id", type=int, default=None)

    # Semantic search
    p = sub.add_parser("search_similar")
    p.add_argument("--class", dest="class_name", required=True)
    p.add_argument("--category", default=None)
    p.add_argument("--query", required=True)
    p.add_argument("--limit", type=int, default=5)

    # Knowledge scores
    p = sub.add_parser("get_scores")
    p.add_argument("--class", dest="class_name", default=None)

    p = sub.add_parser("get_score")
    p.add_argument("--class", dest="class_name", required=True)
    p.add_argument("--category", required=True)

    p = sub.add_parser("get_history")
    p.add_argument("--class", dest="class_name", required=True)
    p.add_argument("--category", default=None)
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--incorrect-only", action="store_true")

    p = sub.add_parser("get_weak_areas")
    p.add_argument("--class", dest="class_name", required=True)

    p = sub.add_parser("update_summary")
    p.add_argument("--class", dest="class_name", required=True)
    p.add_argument("--category", required=True)
    p.add_argument("--summary", required=True)

    # Suggestions
    sub.add_parser("suggest")

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "list_classes": cmd_list_classes,
        "create_class": cmd_create_class,
        "list_categories": cmd_list_categories,
        "create_category": cmd_create_category,
        "get_category": cmd_get_category,
        "set_grading_mode": cmd_set_grading_mode,
        "save_file": cmd_save_file,
        "list_files": cmd_list_files,
        "get_file": cmd_get_file,
        "delete_file": cmd_delete_file,
        "update_last_studied": cmd_update_last_studied,
        "record": cmd_record,
        "search_similar": cmd_search_similar,
        "get_scores": cmd_get_scores,
        "get_score": cmd_get_score,
        "get_history": cmd_get_history,
        "get_weak_areas": cmd_get_weak_areas,
        "update_summary": cmd_update_summary,
        "suggest": cmd_suggest,
    }

    fn = commands.get(args.command)
    if fn:
        fn(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
