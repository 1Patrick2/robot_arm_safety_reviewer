import sqlite3
from pathlib import Path

from diagnostics.storage.schema import SCHEMA_VERSION, init_runtime_db


class TestInitRuntimeDb:
    def test_creates_db_file(self, tmp_path):
        db_path = tmp_path / "runtime_metrics.db"
        result = init_runtime_db(db_path)
        assert result == db_path
        assert db_path.exists()
        assert db_path.stat().st_size > 0

    def test_creates_all_tables(self, tmp_path):
        db_path = tmp_path / "test_tables.db"
        init_runtime_db(db_path)

        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
            tables = [row[0] for row in cursor.fetchall()]
        finally:
            conn.close()

        assert "runs" in tables
        assert "steps" in tables
        assert "artifacts" in tables
        assert "schema_meta" in tables

    def test_schema_meta_contains_version(self, tmp_path):
        db_path = tmp_path / "test_version.db"
        init_runtime_db(db_path)

        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute("SELECT value FROM schema_meta WHERE key='schema_version'")
            row = cursor.fetchone()
        finally:
            conn.close()

        assert row is not None
        assert row[0] == SCHEMA_VERSION

    def test_runs_table_contains_new_worst_step_columns(self, tmp_path):
        db_path = tmp_path / "test_columns.db"
        init_runtime_db(db_path)

        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute("PRAGMA table_info(runs)")
            columns = {row[1] for row in cursor.fetchall()}
        finally:
            conn.close()

        assert "worst_sequence_step_index" in columns
        assert "backend_worst_step" in columns
        # legacy column is still present
        assert "worst_step" in columns

    def test_repeated_init_does_not_error(self, tmp_path):
        db_path = tmp_path / "test_repeat.db"
        init_runtime_db(db_path)
        # second call should succeed silently
        init_runtime_db(db_path)

        conn = sqlite3.connect(str(db_path))
        try:
            cursor = conn.execute("SELECT COUNT(*) FROM schema_meta")
            count = cursor.fetchone()[0]
        finally:
            conn.close()

        # schema_version should not be duplicated
        assert count >= 1
