import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples" / "policy_sequences"
LEROY = ROOT / "samples" / "lerobot_style"


def test_dataset_cli_list_json():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "dataset",
            "list",
            "--adapter",
            "mini_sequence",
            "--source",
            str(SAMPLES),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["adapter"] == "mini_sequence"
    assert "simple_safe_sequence_001" in payload["sequence_ids"]
    assert payload["count"] == 3


def test_dataset_cli_export_sequence_json(tmp_path):
    output = tmp_path / "exported.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "dataset",
            "export-sequence",
            "--adapter",
            "mini_sequence",
            "--source",
            str(SAMPLES),
            "--sequence-id",
            "simple_safe_sequence_001",
            "--output",
            str(output),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["adapter"] == "mini_sequence"
    assert payload["sequence_id"] == "simple_safe_sequence_001"
    assert payload["exported_path"] is not None
    assert output.exists()
    exported = json.loads(output.read_text(encoding="utf-8"))
    assert exported["sequence_id"] == "simple_safe_sequence_001"


def test_dataset_cli_list_text():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "dataset",
            "list",
            "--adapter",
            "mini_sequence",
            "--source",
            str(SAMPLES),
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "Adapter: mini_sequence" in completed.stdout
    assert "simple_safe_sequence_001" in completed.stdout
    assert "near_miss_sequence_001" in completed.stdout
    assert "collision_sequence_001" in completed.stdout


def test_dataset_cli_lerobot_list_json():
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "dataset",
            "list",
            "--adapter",
            "lerobot_style",
            "--source",
            str(LEROY),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["adapter"] == "lerobot_style"
    assert "episode_000001" in payload["sequence_ids"]
    assert payload["count"] == 1


def test_dataset_cli_lerobot_export_json(tmp_path):
    output = tmp_path / "exported_lerobot.json"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli.main",
            "dataset",
            "export-sequence",
            "--adapter",
            "lerobot_style",
            "--source",
            str(LEROY),
            "--sequence-id",
            "episode_000001",
            "--output",
            str(output),
            "--json",
        ],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    payload = json.loads(completed.stdout)

    assert payload["adapter"] == "lerobot_style"
    assert payload["sequence_id"] == "episode_000001"
    assert output.exists()
    exported = json.loads(output.read_text(encoding="utf-8"))
    assert exported["sequence_id"] == "episode_000001"
