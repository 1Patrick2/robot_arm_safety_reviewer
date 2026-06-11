from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_run_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"run_{stamp}_{uuid4().hex[:8]}"


@dataclass(frozen=True)
class AppContext:
    run_id: str = field(default_factory=make_run_id)
    created_at: str = field(default_factory=utc_now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "created_at": self.created_at,
            "metadata": dict(self.metadata),
        }


@dataclass(frozen=True)
class ArtifactRef:
    kind: str
    path: Path
    description: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "path": str(self.path),
            "description": self.description,
        }


@dataclass(frozen=True)
class AppResult:
    ok: bool
    mode: str
    data: dict[str, Any]
    artifacts: tuple[ArtifactRef, ...] = ()
    error: dict[str, Any] | None = None
    context: AppContext = field(default_factory=AppContext)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "mode": self.mode,
            "context": self.context.to_dict(),
            "data": dict(self.data),
            "artifacts": [artifact.to_dict() for artifact in self.artifacts],
            "error": dict(self.error) if self.error else None,
        }
