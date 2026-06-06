import json
import subprocess
import sys
from pathlib import Path

from gateway.replay import replay_log
from gateway.safety_gate import review_only

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "bench/sim_robot_arm"


def test_replay_log_recomputes_same_collision_result(tmp_path):
    task_dir = BENCH / "obstacle_collision_001"
    outcome = review_only(task_dir / "scene.json", task_dir / "command.json", log_dir=tmp_path)

    replay = replay_log(outcome.log_path)

    assert replay["consistent"] is True
    assert replay["checks"]["decision_match"] is True
    assert replay["checks"]["min_clearance_match"] is True
    assert replay["original"]["decision"] == "reject"
    assert replay["recomputed"]["closest_obstacle"] == "sphere_01"


def test_replay_log_handles_invalid_command_with_original_input_paths(tmp_path):
    task_dir = BENCH / "invalid_command_001"
    outcome = review_only(task_dir / "scene.json", task_dir / "command.json", log_dir=tmp_path)

    replay = replay_log(outcome.log_path)

    assert replay["consistent"] is True
    assert replay["original"]["violations"] == ["invalid_command"]
    assert replay["recomputed"]["violations"] == ["invalid_command"]


def test_replay_log_cli_json_output(tmp_path):
    task_dir = BENCH / "near_miss_clearance_001"
    outcome = review_only(task_dir / "scene.json", task_dir / "command.json", log_dir=tmp_path)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.replay_log",
            "--log",
            str(outcome.log_path),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)
    assert payload["consistent"] is True
    assert payload["checks"]["risk_match"] is True
