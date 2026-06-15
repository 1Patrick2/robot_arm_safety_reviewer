from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from application.core import AppResult, ArtifactRef
from application.sequence_runtime_service import (
    SequenceRuntimeRequest,
    SequenceRuntimeResult,
    run_sequence_runtime,
)
from reports.runtime_episode_report import write_runtime_episode_report
from reports.runtime_visual_report import write_clearance_curve, write_trajectory_overview


@dataclass(frozen=True)
class SandboxRunRequest:
    sequence_path: Path
    scene_path: Path
    backend_name: str = "mock"
    device_name: str = "mock_realman"
    output_root: Path = Path("output_reports/sandbox")
    stop_on_block: bool = True


@dataclass(frozen=True)
class SandboxRunResult:
    sequence_runtime_result: SequenceRuntimeResult
    episode_summary_path: Path
    clearance_curve_path: Path
    trajectory_overview_path: Path

    def to_dict(self) -> dict[str, Any]:
        base = self.sequence_runtime_result.to_dict()
        base["episode_summary_path"] = str(self.episode_summary_path)
        base["clearance_curve_path"] = str(self.clearance_curve_path)
        base["trajectory_overview_path"] = str(self.trajectory_overview_path)
        return base

    def to_app_result(self) -> AppResult:
        artifacts = [
            ArtifactRef(
                kind="runtime_episode",
                path=self.sequence_runtime_result.episode_dir,
                description="Runtime episode directory",
            ),
        ]
        if self.episode_summary_path:
            artifacts.append(
                ArtifactRef(kind="episode_summary", path=self.episode_summary_path, description="Episode summary markdown")
            )
        if self.clearance_curve_path:
            artifacts.append(
                ArtifactRef(kind="clearance_curve", path=self.clearance_curve_path, description="Clearance curve PNG")
            )
        if self.trajectory_overview_path:
            artifacts.append(
                ArtifactRef(kind="trajectory_overview", path=self.trajectory_overview_path, description="Trajectory overview PNG")
            )
        return AppResult(
            ok=True,
            mode="sandbox_run",
            data=self.to_dict(),
            artifacts=tuple(artifacts),
        )


def run_sandbox(request: SandboxRunRequest) -> SandboxRunResult:
    """Run a sequence through the safety runtime and produce visual artifacts."""
    # 1. run sequence runtime
    runtime_result = run_sequence_runtime(
        SequenceRuntimeRequest(
            sequence_path=request.sequence_path,
            scene_path=request.scene_path,
            backend_name=request.backend_name,
            device_name=request.device_name,
            episode_root=request.output_root / "episodes",
            stop_on_block=request.stop_on_block,
        )
    )

    episode_dir = runtime_result.episode_dir

    # 2. write episode summary into episode dir
    summary_path = write_runtime_episode_report(episode_dir)

    # 3. write clearance curve into episode dir
    clearance_path = write_clearance_curve(episode_dir)

    # 4. write trajectory overview into episode dir
    trajectory_path = write_trajectory_overview(episode_dir)

    return SandboxRunResult(
        sequence_runtime_result=runtime_result,
        episode_summary_path=summary_path,
        clearance_curve_path=clearance_path,
        trajectory_overview_path=trajectory_path,
    )
