from __future__ import annotations

import sqlite3
from pathlib import Path

SCHEMA_VERSION = "stage3.runtime_metrics.v1"

_CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id TEXT UNIQUE NOT NULL,
    sequence_id TEXT,
    backend TEXT,
    device TEXT,
    robot TEXT,
    action_source TEXT,
    scene_provider TEXT,
    created_at TEXT,
    episode_dir TEXT NOT NULL,
    total_steps INTEGER,
    approved_steps INTEGER,
    executed_steps INTEGER,
    blocked_steps INTEGER,
    rejected_steps INTEGER,
    manual_review_steps INTEGER,
    min_clearance REAL,
    worst_step INTEGER,
    closest_robot_link TEXT,
    closest_obstacle TEXT,
    summary_path TEXT,
    clearance_curve_path TEXT,
    trajectory_overview_path TEXT,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS steps (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id TEXT NOT NULL,
    step_index INTEGER,
    step_id TEXT,
    decision TEXT,
    risk_level TEXT,
    executed INTEGER,
    blocked_reason TEXT,
    min_clearance REAL,
    closest_robot_link TEXT,
    closest_obstacle TEXT,
    worst_step INTEGER,
    proposed_action_json TEXT,
    safety_result_json TEXT,
    backend_metadata_json TEXT,
    step_json TEXT
);

CREATE TABLE IF NOT EXISTS artifacts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    path TEXT NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS schema_meta (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
"""

_INSERT_SCHEMA = """
INSERT OR IGNORE INTO schema_meta (key, value) VALUES ('schema_version', ?)
"""


def _migrate_schema(conn: sqlite3.Connection) -> None:
    """Apply schema migrations for databases created by an earlier schema version."""
    migrations = [
        "ALTER TABLE runs ADD COLUMN worst_sequence_step_index INTEGER",
        "ALTER TABLE runs ADD COLUMN backend_worst_step INTEGER",
    ]
    for stmt in migrations:
        try:
            conn.execute(stmt)
        except sqlite3.OperationalError:
            pass  # column already exists


def init_runtime_db(db_path: Path) -> Path:
    """Create or open a runtime metrics database and ensure all tables exist.

    Safe to call multiple times on the same path.
    Returns the resolved *db_path*.
    """
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(_CREATE_TABLES)
        _migrate_schema(conn)
        conn.execute(_INSERT_SCHEMA, (SCHEMA_VERSION,))
        conn.commit()
    finally:
        conn.close()
    return db_path
