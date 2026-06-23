"""Compare safety-review outputs across simulation backends.
比较mock和pybullet两个后端输出的结果是否一致，不一致是什么不一致，统计每个任务的决策、风险等级、清晰度区间、归因等是否匹配，以及整体的匹配情况和错误情况。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from application.gateway.safety_gate import review_only
from robot.safety.benchmark import discover_task_dirs


def compare_backends(
    bench_dir: str | Path,
    *,
    backends: tuple[str, ...] | list[str] = ("mock", "pybullet"),
    log_dir: str | Path | None = "logs/backend_comparison",
) -> dict[str, Any]:
    """Run each task with each backend and summarize differences."""

    backend_names = list(backends)
    tasks = []
    for task_dir in discover_task_dirs(bench_dir):
        results: dict[str, Any] = {}
        for backend_name in backend_names:
            '''这里函数里调用的事review_only是因为目的在于比较审查结果而非执行。'''
            results[backend_name] = _run_one_backend(task_dir, backend_name, log_dir)
        match_status = _match_status(results, backend_names)
        tasks.append(
            {
                "task_id": task_dir.name,
                "results": results,
                "match": match_status == "strict_match",
                "match_status": match_status,
                "diagnosis": _diagnosis(results, backend_names, match_status),
            }
        )

    return {
        "backends": backend_names,
        "total": len(tasks),
        "decision_matches": sum(1 for task in tasks if _all_same(task["results"], backend_names, "decision")),
        "risk_matches": sum(1 for task in tasks if _all_same(task["results"], backend_names, "risk_level")),
        "clearance_band_matches": sum(1 for task in tasks if _same_clearance_band(task["results"], backend_names)),
        "attribution_matches": sum(1 for task in tasks if _same_attribution(task["results"], backend_names)),
        "strict_matches": sum(1 for task in tasks if task["match_status"] == "strict_match"),
        "backend_errors": sum(1 for task in tasks for result in task["results"].values() if result.get("error")),
        "tasks": tasks,
    }


def write_backend_comparison_json(summary: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def write_backend_comparison_markdown(summary: dict[str, Any], path: str | Path) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Backend Comparison Report",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Backends | `{', '.join(summary['backends'])}` |",
        f"| Tasks | `{summary['total']}` |",
        f"| Decision matches | `{summary['decision_matches']}` |",
        f"| Risk matches | `{summary['risk_matches']}` |",
        f"| Clearance band matches | `{summary['clearance_band_matches']}` |",
        f"| Attribution matches | `{summary['attribution_matches']}` |",
        f"| Strict matches | `{summary['strict_matches']}` |",
        f"| Backend errors | `{summary['backend_errors']}` |",
        "",
        "## Task-Level Comparison",
        "",
        "| Task | Mock Decision | PyBullet Decision | Match Status | Diagnosis |",
        "|---|---|---|---|---|",
    ]
    for task in summary["tasks"]:
        mock = task["results"].get("mock", {})
        pybullet = task["results"].get("pybullet", {})
        lines.append(
            "| "
            f"{task['task_id']} | "
            f"{mock.get('decision', '')} | "
            f"{pybullet.get('decision', '')} | "
            f"{task['match_status']} | "
            f"{task['diagnosis']} |"
        )
    lines.extend(
        [
            "",
            "## Notes",
            "",
            _comparison_note(summary),
        ]
    )
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return output_path


def _comparison_note(summary: dict[str, Any]) -> str:
    pybullet_methods = {
        result.get("review_backend", {}).get("collision_method")
        for task in summary["tasks"]
        for result in [task["results"].get("pybullet", {})]
        if result.get("review_backend", {}).get("collision_method")
    }
    if pybullet_methods:
        methods = ", ".join(f"`{method}`" for method in sorted(pybullet_methods))
        return (
            f"PyBullet backend collision method: {methods}. Clearance and attribution can still differ "
            "from the mock backend because the URDF collision geometry and mock segment geometry are not identical."
        )
    return "Backend metadata was not available for all PyBullet comparison results."


def _run_one_backend(task_dir: Path, backend_name: str, log_dir: str | Path | None) -> dict[str, Any]:
    try:
        outcome = review_only(
            task_dir / "scene.json",
            task_dir / "command.json",
            backend_name=backend_name,
            log_dir=Path(log_dir) / backend_name / task_dir.name if log_dir is not None else None,
        )
    except Exception as exc:
        return {"backend": backend_name, "error": str(exc)}

    safety = outcome.execution_log["safety_result"]
    return {
        "backend": backend_name,
        "decision": safety.get("decision"),
        "risk_level": safety.get("risk_level"),
        "min_clearance": safety.get("min_clearance"),
        "closest_robot_link": safety.get("closest_robot_link"),
        "closest_obstacle": safety.get("closest_obstacle"),
        "worst_step": safety.get("worst_step"),
        "violations": [item.get("type") for item in safety.get("violations", []) if item.get("type")],
        "review_backend": outcome.execution_log.get("review_backend", {}),
        "log_path": str(outcome.log_path) if outcome.log_path is not None else None,
        "error": None,
    }

'''现在summary的匹配指标有6个，分别是decision_matches, risk_matches, clearance_band_matches, attribution_matches, strict_matches, backend_errors。判断顺序先看backed，这是最严重的。'''
def _match_status(results: dict[str, Any], backend_names: list[str]) -> str:
    if any(results[name].get("error") for name in backend_names):
        return "backend_error"
    if not _all_same(results, backend_names, "decision"):
        return "decision_mismatch"
    if not _all_same(results, backend_names, "risk_level"):
        return "risk_mismatch"
    if not _same_clearance_band(results, backend_names):
        return "clearance_band_mismatch"
    if not _same_attribution(results, backend_names):
        return "attribution_mismatch"
    return "strict_match"

'''把不同匹配结果转为更具体的诊断标签，方便后续分析和统计。'''
def _diagnosis(results: dict[str, Any], backend_names: list[str], match_status: str) -> str:
    if match_status == "backend_error":
        failing = [name for name in backend_names if results[name].get("error")]
        return f"backend_error:{','.join(failing)}"
    if match_status == "decision_mismatch":
        return "decision_disagreement"
    if match_status == "risk_mismatch":
        return "risk_level_disagreement"
    if match_status == "clearance_band_mismatch":
        return "clearance_threshold_disagreement"
    if match_status == "attribution_mismatch":
        return "closest_geometry_differs"

    decision = results[backend_names[0]].get("decision")
    if decision == "approve":
        return "consistent_safe"
    if decision == "reject":
        return "consistent_reject"
    return "consistent_manual_review"


def _all_same(results: dict[str, Any], backend_names: list[str], field: str) -> bool:
    values = [results[name].get(field) for name in backend_names]
    return len(set(values)) <= 1


def _same_attribution(results: dict[str, Any], backend_names: list[str]) -> bool:
    links = {results[name].get("closest_robot_link") for name in backend_names}
    obstacles = {results[name].get("closest_obstacle") for name in backend_names}
    return len(links) <= 1 and len(obstacles) <= 1


def _same_clearance_band(results: dict[str, Any], backend_names: list[str]) -> bool:
    return len({_clearance_band(results[name].get("min_clearance")) for name in backend_names}) <= 1

'''根据clearance数值不用，但同一安全内，决策意义是一致的'''
def _clearance_band(clearance: Any) -> str:
    if clearance is None:
        return "unknown"
    value = float(clearance)
    if value < 0:
        return "collision"
    if value < 0.05:
        return "hard_clearance"
    if value < 0.10:
        return "manual_review_clearance"
    return "clear"
