from __future__ import annotations

from pathlib import Path

from robot_runtime.episode_loader import load_episode


def write_clearance_curve(episode_dir: Path, output_dir: Path | None = None) -> Path:
    """Plot action-level min_clearance per step and save as *clearance_curve.png*."""
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt  # noqa: PLC0415
    except ImportError:
        raise RuntimeError(
            "matplotlib is required to generate clearance curve artifacts; "
            "install it with: pip install matplotlib"
        ) from None

    bundle = load_episode(episode_dir)
    target_dir = output_dir or episode_dir
    target_dir.mkdir(parents=True, exist_ok=True)

    steps = bundle.steps
    step_indices = list(range(1, len(steps) + 1))
    clearances = []
    for s in steps:
        sr = s.get("safety_result", {})
        c = sr.get("min_clearance")
        clearances.append(c)

    fig, ax = plt.subplots()
    ax.plot(step_indices, clearances, marker="o", linestyle="-", label="min_clearance")
    ax.axhline(y=0, color="red", linestyle="--", linewidth=0.8, label="zero clearance")
    ax.set_xlabel("Sequence Step Index")
    ax.set_ylabel("Min Clearance (m)")
    ax.set_title("Action-Level Clearance Curve")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.6)

    plot_path = target_dir / "clearance_curve.png"
    fig.savefig(plot_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return plot_path
