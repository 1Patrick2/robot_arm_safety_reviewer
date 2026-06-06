from robot_safety.models import JointLimit, SafetyConfig
from robot_safety.safety_rules import check_joint_limits, classify_risk_level, make_decision


def test_check_joint_limits_reports_violation():
    ok, violations = check_joint_limits((0.0, 2.0), (JointLimit(-1.0, 1.0), JointLimit(-1.5, 1.5)))

    assert not ok
    assert violations[0].type == "joint_limit"
    assert violations[0].joint == "joint_2"


def test_make_decision_rejects_collision():
    decision = make_decision(
        joint_limits_ok=True,
        collision_free=False,
        min_clearance=-0.01,
        max_joint_delta=0.2,
        config=SafetyConfig(),
    )

    assert decision == "reject"


def test_make_decision_manual_review_for_low_clearance_or_large_delta():
    config = SafetyConfig(min_clearance=0.05, manual_review_clearance=0.10, max_joint_delta=1.2)

    assert make_decision(
        joint_limits_ok=True,
        collision_free=True,
        min_clearance=0.08,
        max_joint_delta=0.2,
        config=config,
    ) == "manual_review"
    assert make_decision(
        joint_limits_ok=True,
        collision_free=True,
        min_clearance=0.2,
        max_joint_delta=1.4,
        config=config,
    ) == "manual_review"


def test_classify_risk_level_approve_case_is_low():
    assert classify_risk_level(
        joint_limits_ok=True,
        collision_free=True,
        min_clearance=0.2,
        max_joint_delta=0.2,
        config=SafetyConfig(),
    ) == "low"

