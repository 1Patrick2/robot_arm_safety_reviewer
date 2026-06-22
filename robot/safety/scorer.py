"""Benchmark scoring helpers for Stage 1 robot arm safety tasks."""

from __future__ import annotations

from typing import Any

'''检查expected.json格式，至少有expected_safety, expected_gateway和required_output_fields三个字段'''
def validate_expected_schema(expected: dict[str, Any]) -> None:
    """Validate the small expected.json contract used by Stage 1 benchmarks."""

    required_top_level = ("expected_safety", "expected_gateway", "required_output_fields")
    missing = [field for field in required_top_level if field not in expected]
    if missing:
        raise ValueError(f"expected.json missing fields: {missing}")

    safety = expected["expected_safety"]
    if not isinstance(safety, dict):
        raise ValueError("expected_safety must be an object")
    for field in ("decision", "risk_level", "violations", "critical_obstacle", "clearance_assertion"):
        if field not in safety:
            raise ValueError(f"expected_safety missing field: {field}")
    if not isinstance(safety["violations"], list):
        raise ValueError("expected_safety.violations must be a list")

    '''clearance_assertion支持4种模式：not_applicable（不适用），range（范围），greater_than（大于某值），less_than（小于某值）。根据不同的模式，断言需要不同的字段，比如range需要lower和upper，greater_than和less_than需要value。'''
    assertion = safety["clearance_assertion"]
    if not isinstance(assertion, dict):
        raise ValueError("expected_safety.clearance_assertion must be an object")
    mode = assertion.get("mode")
    if mode not in {"not_applicable", "range", "greater_than", "less_than"}:
        raise ValueError(f"unsupported clearance_assertion mode: {mode}")
    if mode == "range" and ("lower" not in assertion or "upper" not in assertion):
        raise ValueError("range clearance_assertion requires lower and upper")
    if mode in {"greater_than", "less_than"} and "value" not in assertion:
        raise ValueError(f"{mode} clearance_assertion requires value")

    gateway = expected["expected_gateway"]
    if not isinstance(gateway, dict):
        raise ValueError("expected_gateway must be an object")
    for field in ("executed", "execution_reason"):
        if field not in gateway:
            raise ValueError(f"expected_gateway missing field: {field}")
    if not isinstance(expected["required_output_fields"], list):
        raise ValueError("required_output_fields must be a list")


'''核心函数，输入task_id,execution_log,expected，输出passed,checks,actual,expected等信息,检查风险等级，违规项覆盖，关键障碍物匹配，安全决策匹配，清晰度断言匹配，必需字段存在，网关执行匹配，网关原因匹配等多个维度'''
def score_execution_log(task_id: str, execution_log: dict[str, Any], expected: dict[str, Any]) -> dict[str, Any]:
    """Compare one execution log against the benchmark expected contract."""

    validate_expected_schema(expected)
    result = execution_log["safety_result"]
    execution = execution_log["execution"]
    safety = expected["expected_safety"]
    gateway = expected["expected_gateway"]

    checks = {
        "decision_match": result.get("decision") == safety["decision"],
        "risk_match": result.get("risk_level") == safety["risk_level"],
        "violation_match": _expected_violations_present(result, safety["violations"]),
        "critical_obstacle_match": result.get("closest_obstacle") == safety["critical_obstacle"],
        "clearance_match": _clearance_matches(result, safety["clearance_assertion"]),
        "required_fields_match": _required_fields_present(result, expected["required_output_fields"]),
        "gateway_execution_match": execution.get("executed") == gateway["executed"],
        "gateway_reason_match": execution.get("reason") == gateway["execution_reason"],
    }
    passed = all(checks.values())
    return {
        "task_id": task_id,
        "passed": passed,
        "checks": checks,
        "actual": {
            "decision": result.get("decision"),
            "risk_level": result.get("risk_level"),
            "violations": _violation_types(result),
            "critical_obstacle": result.get("closest_obstacle"),
            "min_clearance": result.get("min_clearance"),
            "executed": execution.get("executed"),
            "execution_reason": execution.get("reason"),
        },
        "expected": {
            "decision": safety["decision"],
            "risk_level": safety["risk_level"],
            "violations": list(safety["violations"]),
            "critical_obstacle": safety["critical_obstacle"],
            "clearance_assertion": safety["clearance_assertion"],
            "executed": gateway["executed"],
            "execution_reason": gateway["execution_reason"],
        },
    }

'''统计所有任务的得分情况，并返回一个字典'''
def summarize_task_scores(task_scores: list[dict[str, Any]]) -> dict[str, Any]:
    """Build aggregate benchmark metrics from per-task scores."""

    total = len(task_scores)
    passed = sum(1 for item in task_scores if item["passed"])
    return {
        "total": total,
        "passed": passed,
        "failed": total - passed,
        "decision_accuracy": _rate(task_scores, "decision_match"),
        "risk_accuracy": _rate(task_scores, "risk_match"),
        "violation_match": _rate(task_scores, "violation_match"),
        "gateway_execution_match": _rate(task_scores, "gateway_execution_match"),
        "gateway_reason_match": _rate(task_scores, "gateway_reason_match"),
        "tasks": task_scores,
    }


def _expected_violations_present(result: dict[str, Any], expected_violations: list[str]) -> bool:
    actual = set(_violation_types(result))
    if not expected_violations:
        return not actual
    return set(expected_violations).issubset(actual)


def _violation_types(result: dict[str, Any]) -> list[str]:
    return [str(item.get("type")) for item in result.get("violations", []) if item.get("type")]


def _clearance_matches(result: dict[str, Any], assertion: dict[str, Any]) -> bool:
    mode = assertion["mode"]
    if mode == "not_applicable":
        return True
    clearance = result.get("min_clearance")
    if clearance is None:
        return False
    clearance = float(clearance)
    if mode == "range":
        return float(assertion["lower"]) <= clearance <= float(assertion["upper"])
    if mode == "greater_than":
        return clearance > float(assertion["value"])
    if mode == "less_than":
        return clearance < float(assertion["value"])
    return False


def _required_fields_present(result: dict[str, Any], required_fields: list[str]) -> bool:
    for field in required_fields:
        if field not in result:
            return False
        if field == "evidence" and not result[field]:
            return False
    return True


def _rate(task_scores: list[dict[str, Any]], check_name: str) -> float:
    if not task_scores:
        return 0.0
    return sum(1 for item in task_scores if item["checks"][check_name]) / len(task_scores)
