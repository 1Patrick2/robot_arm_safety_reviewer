from pathlib import Path

from application.core import AppContext, AppResult, ArtifactRef, make_run_id, utc_now
from application.review_service import ReviewCommandRequest, review_command
from application.runtime_service import RuntimeTaskRequest, run_runtime_task


ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench" / "sim_robot_arm"


def test_app_result_serializes_data_artifacts_and_error():
    result = AppResult(
        ok=False,
        mode="runtime",
        data={"decision": "reject"},
        artifacts=(ArtifactRef(kind="episode", path=Path("output_reports/demo"), description="runtime episode"),),
        error={"type": "blocked", "message": "rejected_by_safety_gate"},
    )

    payload = result.to_dict()

    assert payload["ok"] is False
    assert payload["mode"] == "runtime"
    assert payload["data"]["decision"] == "reject"
    assert payload["artifacts"][0]["path"] == "output_reports\\demo"
    assert payload["error"]["message"] == "rejected_by_safety_gate"


def test_app_context_defaults_include_run_id_and_timestamp():
    context = AppContext()

    assert context.run_id.startswith("run_")
    assert context.created_at.endswith("+00:00")
    assert make_run_id().startswith("run_")
    assert utc_now().endswith("+00:00")


def test_runtime_task_result_can_convert_to_app_result(tmp_path):
    result = run_runtime_task(
        RuntimeTaskRequest(
            task_dir=BENCH / "simple_joint_move_001",
            backend_name="mock",
            episode_root=tmp_path,
        )
    )

    app_result = result.to_app_result()
    payload = app_result.to_dict()

    assert payload["ok"] is True
    assert payload["mode"] == "runtime_task"
    assert payload["data"]["result"]["safety_result"]["decision"] == "approve"
    assert payload["artifacts"][0]["kind"] == "runtime_episode"
    assert Path(payload["artifacts"][0]["path"]).exists()


def test_review_command_result_can_convert_to_app_result(tmp_path):
    task_dir = BENCH / "obstacle_collision_001"
    result = review_command(
        ReviewCommandRequest(
            scene_path=task_dir / "scene.json",
            command_path=task_dir / "command.json",
            backend_name="mock",
            log_dir=tmp_path,
        )
    )

    app_result = result.to_app_result()
    payload = app_result.to_dict()

    assert payload["ok"] is True
    assert payload["mode"] == "review_command"
    assert payload["data"]["safety_result"]["decision"] == "reject"
    assert payload["artifacts"][0]["kind"] == "execution_log"
    assert Path(payload["artifacts"][0]["path"]).exists()
