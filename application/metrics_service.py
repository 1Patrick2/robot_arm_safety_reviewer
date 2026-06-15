from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from application.core import AppResult
from runtime_db.episode_ingest import ingest_episode
from runtime_db.repository import RuntimeMetricsRepository
from runtime_db.schema import init_runtime_db

DEFAULT_DB = Path("output_reports/runtime_metrics/runtime_metrics.db")


@dataclass(frozen=True)
class MetricsIngestRequest:
    episode_dir: Path
    db_path: Path = DEFAULT_DB


@dataclass(frozen=True)
class MetricsIngestResult:
    summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return dict(self.summary)

    def to_app_result(self) -> AppResult:
        return AppResult(
            ok=True,
            mode="metrics_ingest",
            data=self.to_dict(),
        )


@dataclass(frozen=True)
class MetricsListRunsRequest:
    db_path: Path = DEFAULT_DB
    limit: int = 20


@dataclass(frozen=True)
class MetricsListRunsResult:
    runs: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "count": len(self.runs),
            "runs": self.runs,
        }

    def to_app_result(self) -> AppResult:
        return AppResult(
            ok=True,
            mode="metrics_list_runs",
            data=self.to_dict(),
        )


@dataclass(frozen=True)
class MetricsShowRunRequest:
    episode_id: str
    db_path: Path = DEFAULT_DB


@dataclass(frozen=True)
class MetricsShowRunResult:
    run: dict[str, Any] | None
    steps: tuple[dict[str, Any], ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "run": self.run,
            "steps": list(self.steps),
            "step_count": len(self.steps),
        }

    def to_app_result(self) -> AppResult:
        return AppResult(
            ok=True,
            mode="metrics_show_run",
            data=self.to_dict(),
        )


def metrics_ingest_episode(request: MetricsIngestRequest) -> MetricsIngestResult:
    init_runtime_db(request.db_path)
    summary = ingest_episode(request.db_path, request.episode_dir)
    return MetricsIngestResult(summary=summary)


def metrics_list_runs(request: MetricsListRunsRequest) -> MetricsListRunsResult:
    init_runtime_db(request.db_path)
    repo = RuntimeMetricsRepository(request.db_path)
    runs = repo.list_runs(limit=request.limit)
    return MetricsListRunsResult(runs=tuple(runs))


def metrics_show_run(request: MetricsShowRunRequest) -> MetricsShowRunResult:
    init_runtime_db(request.db_path)
    repo = RuntimeMetricsRepository(request.db_path)
    run = repo.get_run(request.episode_id)
    steps = repo.get_steps(request.episode_id) if run else []
    return MetricsShowRunResult(run=run, steps=tuple(steps))
