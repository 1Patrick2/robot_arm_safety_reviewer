from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


class RuntimeMetricsRepository:
    """Lightweight repository for runtime metrics persistence.

    Uses raw SQL without an ORM. All write operations are wrapped in
    transactions.
    """

    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    # ── write helpers ────────────────────────────────────────────────

    def upsert_run(self, run: dict[str, Any]) -> None:
        """Insert or replace a run record by *episode_id*."""
        conn = self._connect()
        try:
            conn.execute(
                """
                INSERT OR REPLACE INTO runs (
                    episode_id, sequence_id, backend, device, robot,
                    action_source, scene_provider, created_at, episode_dir,
                    total_steps, approved_steps, executed_steps, blocked_steps,
                    rejected_steps, manual_review_steps,
                    min_clearance, worst_step,
                    closest_robot_link, closest_obstacle,
                    summary_path, clearance_curve_path, trajectory_overview_path,
                    metadata_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run["episode_id"],
                    run.get("sequence_id"),
                    run.get("backend"),
                    run.get("device"),
                    run.get("robot"),
                    run.get("action_source"),
                    run.get("scene_provider"),
                    run.get("created_at"),
                    run.get("episode_dir"),
                    run.get("total_steps"),
                    run.get("approved_steps"),
                    run.get("executed_steps"),
                    run.get("blocked_steps"),
                    run.get("rejected_steps"),
                    run.get("manual_review_steps"),
                    run.get("min_clearance"),
                    run.get("worst_step"),
                    run.get("closest_robot_link"),
                    run.get("closest_obstacle"),
                    run.get("summary_path"),
                    run.get("clearance_curve_path"),
                    run.get("trajectory_overview_path"),
                    json.dumps(run.get("metadata_json", {}), ensure_ascii=False) if isinstance(run.get("metadata_json"), dict) else run.get("metadata_json"),
                ),
            )
            conn.commit()
        finally:
            conn.close()

    def replace_steps(self, episode_id: str, steps: list[dict[str, Any]]) -> None:
        """Replace all steps for *episode_id* in one transaction."""
        conn = self._connect()
        try:
            conn.execute("DELETE FROM steps WHERE episode_id = ?", (episode_id,))
            for step in steps:
                conn.execute(
                    """
                    INSERT INTO steps (
                        episode_id, step_index, step_id,
                        decision, risk_level, executed, blocked_reason,
                        min_clearance, closest_robot_link, closest_obstacle, worst_step,
                        proposed_action_json, safety_result_json, backend_metadata_json,
                        step_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        episode_id,
                        step.get("step_index") or step.get("index"),
                        step.get("step_id"),
                        step.get("decision") or (step.get("safety_result") or {}).get("decision"),
                        step.get("risk_level") or (step.get("safety_result") or {}).get("risk_level"),
                        1 if step.get("executed") else 0,
                        step.get("blocked_reason"),
                        step.get("min_clearance") or (step.get("safety_result") or {}).get("min_clearance"),
                        step.get("closest_robot_link") or (step.get("safety_result") or {}).get("closest_robot_link"),
                        step.get("closest_obstacle") or (step.get("safety_result") or {}).get("closest_obstacle"),
                        step.get("worst_step") or (step.get("safety_result") or {}).get("worst_step"),
                        json.dumps(step.get("proposed_action", {}), ensure_ascii=False),
                        json.dumps(step.get("safety_result", {}), ensure_ascii=False),
                        json.dumps(step.get("backend_metadata", {}), ensure_ascii=False),
                        json.dumps(step, ensure_ascii=False),
                    ),
                )
            conn.commit()
        finally:
            conn.close()

    def replace_artifacts(self, episode_id: str, artifacts: list[dict[str, Any]]) -> None:
        """Replace all artifact records for *episode_id*."""
        conn = self._connect()
        try:
            conn.execute("DELETE FROM artifacts WHERE episode_id = ?", (episode_id,))
            for art in artifacts:
                conn.execute(
                    "INSERT INTO artifacts (episode_id, kind, path, description) VALUES (?, ?, ?, ?)",
                    (episode_id, art["kind"], str(art["path"]), art.get("description")),
                )
            conn.commit()
        finally:
            conn.close()

    # ── queries ───────────────────────────────────────────────────────

    def list_runs(self, limit: int = 20) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT * FROM runs ORDER BY id DESC LIMIT ?",
                (limit,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()

    def get_run(self, episode_id: str) -> dict[str, Any] | None:
        conn = self._connect()
        try:
            cursor = conn.execute("SELECT * FROM runs WHERE episode_id = ?", (episode_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_steps(self, episode_id: str) -> list[dict[str, Any]]:
        conn = self._connect()
        try:
            cursor = conn.execute(
                "SELECT * FROM steps WHERE episode_id = ? ORDER BY step_index",
                (episode_id,),
            )
            return [dict(row) for row in cursor.fetchall()]
        finally:
            conn.close()
