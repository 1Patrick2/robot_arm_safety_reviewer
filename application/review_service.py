from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from gateway.safety_gate import review_only
from robot_safety.models import SafetyResult


@dataclass(frozen=True)
class ReviewCommandRequest:
    scene_path: Path
    command_path: Path
    backend_name: str = "mock"
    log_dir: Path = Path("logs")


@dataclass(frozen=True)
class ReviewCommandResult:
    safety_result: SafetyResult
    log_path: Path | None
    backend_name: str

    def to_dict(self) -> dict:
        return {
            "backend": self.backend_name,
            "log_path": str(self.log_path) if self.log_path else None,
            "safety_result": self.safety_result.to_dict(),
        }


def review_command(request: ReviewCommandRequest) -> ReviewCommandResult:
    outcome = review_only(
        request.scene_path,
        request.command_path,
        backend_name=request.backend_name,
        log_dir=request.log_dir,
    )
    return ReviewCommandResult(
        safety_result=outcome.safety_result,
        log_path=outcome.log_path,
        backend_name=request.backend_name,
    )
