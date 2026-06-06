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
    backend_name: str = "mock",
    log_dir: str | Path | None = "logs/benchmark",
) -> dict[str, Any]:
    """Execute all benchmark tasks through the gateway and score each result."""

    task_scores: list[dict[str, Any]] = []
    for task_dir in discover_task_dirs(bench_dir):
        outcome = execute_if_safe(
            task_dir / "scene.json",
            task_dir / "command.json",
            backend_name=backend_name,
            log_dir=Path(log_dir) / task_dir.name if log_dir is not None else None,
        )
        expected = json.loads((task_dir / "expected.json").read_text(encoding="utf-8"))
        task_scores.append(score_execution_log(task_dir.name, outcome.execution_log, expected))
    return summarize_task_scores(task_scores)


def run_backend_smoke_benchmark(
    bench_dir: str | Path,
    *,
    backend_name: str,
    log_dir: str | Path | None = "logs/benchmark",
) -> dict[str, Any]:
    """Run all benchmark tasks with one backend and validate structured outputs only."""

    tasks: list[dict[str, Any]] = []
    for task_dir in discover_task_dirs(bench_dir):
        task_result: dict[str, Any] = {
            "task_id": task_dir.name,
            "completed": False,
            "structured_output": False,
            "runtime_error": None,
        }
        try:
            outcome = execute_if_safe(
                task_dir / "scene.json",
                task_dir / "command.json",
                backend_name=backend_name,
                log_dir=Path(log_dir) / task_dir.name if log_dir is not None else None,
            )
            safety = outcome.execution_log.get("safety_result", {})
            review_backend = outcome.execution_log.get("review_backend", {})
            structured_output = _is_structured_smoke_output(safety, review_backend, backend_name)
            task_result.update(
                {
                    "completed": True,
                    "structured_output": structured_output,
                    "decision": safety.get("decision"),
                    "risk_level": safety.get("risk_level"),
                    "min_clearance": safety.get("min_clearance"),
                    "closest_robot_link": safety.get("closest_robot_link"),
                    "closest_obstacle": safety.get("closest_obstacle"),
                    "worst_step": safety.get("worst_step"),
                    "violations": [item.get("type") for item in safety.get("violations", []) if item.get("type")],
                    "evidence_count": len(safety.get("evidence", [])),
                    "review_backend": review_backend,
                    "log_path": str(outcome.log_path) if outcome.log_path is not None else None,
                }
            )
        except Exception as exc:
            task_result["runtime_error"] = str(exc)
        tasks.append(task_result)

    total = len(tasks)
    completed = sum(1 for task in tasks if task["completed"])
    runtime_errors = sum(1 for task in tasks if task["runtime_error"])
    structured_outputs = sum(1 for task in tasks if task["structured_output"])
    return {
        "backend": backend_name,
        "mode": "smoke",
        "total": total,
        "completed": completed,
        "runtime_errors": runtime_errors,
        "structured_outputs": structured_outputs,
        "passed": completed == total and runtime_errors == 0 and structured_outputs == total,
        "tasks": tasks,
    }


def _is_structured_smoke_output(safety: dict[str, Any], review_backend: dict[str, Any], backend_name: str) -> bool:
    return (
        safety.get("decision") in {"approve", "manual_review", "reject"}
        and safety.get("risk_level") in {"low", "medium", "high"}
        and "min_clearance" in safety
        and bool(safety.get("evidence"))
        and review_backend.get("name") == backend_name
    )


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


def write_backend_smoke_summary_markdown(summary: dict[str, Any], path: str | Path) -> Path:
    """Write a Markdown report for backend smoke benchmark results."""

    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Backend Smoke Benchmark",
        "",
        f"- Backend: `{summary['backend']}`",
        f"- Mode: `{summary['mode']}`",
        f"- Total: `{summary['total']}`",
        f"- Completed: `{summary['completed']}`",
        f"- Runtime errors: `{summary['runtime_errors']}`",
        f"- Structured outputs: `{summary['structured_outputs']}`",
        f"- Passed: `{summary['passed']}`",
        "",
        "| Task | Completed | Structured | Decision | Risk | Runtime Error |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for task in summary["tasks"]:
        lines.append(
            "| "
            f"{task['task_id']} | "
            f"{'yes' if task['completed'] else 'no'} | "
            f"{'yes' if task['structured_output'] else 'no'} | "
            f"{task.get('decision', '')} | "
            f"{task.get('risk_level', '')} | "
            f"{task.get('runtime_error') or ''} |"
        )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path
