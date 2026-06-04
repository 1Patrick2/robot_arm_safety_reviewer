"""Stage 1 benchmark runner for simulated robot arm safety tasks."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from gateway.safety_gate import execute_if_safe

from .scorer import score_execution_log, summarize_task_scores


def discover_task_dirs(bench_dir: str | Path) -> list[Path]:
    """Return task folders containing scene, command, and expected files."""

    root = Path(bench_dir)
    return sorted(
        path
        for path in root.iterdir()
        if path.is_dir()
        and (path / "scene.json").exists()
        and (path / "command.json").exists()
        and (path / "expected.json").exists()
    )


def run_benchmark(
    bench_dir: str | Path,
    *,
    log_dir: str | Path | None = "logs/benchmark",
) -> dict[str, Any]:
    """Execute all benchmark tasks through the gateway and score each result."""

    task_scores: list[dict[str, Any]] = []
    for task_dir in discover_task_dirs(bench_dir):
        outcome = execute_if_safe(
            task_dir / "scene.json",
            task_dir / "command.json",
            log_dir=Path(log_dir) / task_dir.name if log_dir is not None else None,
        )
        expected = json.loads((task_dir / "expected.json").read_text(encoding="utf-8"))
        task_scores.append(score_execution_log(task_dir.name, outcome.execution_log, expected))
    return summarize_task_scores(task_scores)


def write_benchmark_summary_json(summary: dict[str, Any], path: str | Path) -> Path:
    """Write benchmark summary JSON and return the created path."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def write_benchmark_summary_markdown(summary: dict[str, Any], path: str | Path) -> Path:
    """Write a compact Markdown benchmark report."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Stage 1 Robot Safety Benchmark",
        "",
        f"- Total: `{summary['total']}`",
        f"- Passed: `{summary['passed']}`",
        f"- Failed: `{summary['failed']}`",
        f"- Decision Accuracy: `{summary['decision_accuracy']:.3f}`",
        f"- Risk Accuracy: `{summary['risk_accuracy']:.3f}`",
        f"- Violation Match: `{summary['violation_match']:.3f}`",
        f"- Gateway Execution Match: `{summary['gateway_execution_match']:.3f}`",
        "",
        "| Task | Pass | Decision | Risk | Violations | Gateway |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for task in summary["tasks"]:
        checks = task["checks"]
        actual = task["actual"]
        lines.append(
            "| "
            f"{task['task_id']} | "
            f"{'yes' if task['passed'] else 'no'} | "
            f"{actual['decision']} ({'ok' if checks['decision_match'] else 'fail'}) | "
            f"{actual['risk_level']} ({'ok' if checks['risk_match'] else 'fail'}) | "
            f"{', '.join(actual['violations']) or 'none'} ({'ok' if checks['violation_match'] else 'fail'}) | "
            f"{actual['executed']} / {actual['execution_reason']} "
            f"({'ok' if checks['gateway_execution_match'] and checks['gateway_reason_match'] else 'fail'}) |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
