import subprocess
from pathlib import Path


def collect_changes() -> dict[str, str]:
    status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True
    )

    diff = subprocess.run(
        ["git", "diff"],
        capture_output=True,
        text=True,
        check=True,
    )

    staged_diff = subprocess.run(
        ["git", "diff", "--cached"],
        capture_output=True,
        text=True,
        check=True,
    )

    return {
        "status": status.stdout,
        "diff": diff.stdout,
        "staged_diff": staged_diff.stdout,
    }

def check_git_root() -> None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        capture_output=True,
        text=True,
        check=True
    )

    current_path = Path.cwd().resolve()
    git_root = Path(result.stdout.strip()).resolve()

    if current_path != git_root:
        raise ValueError(
            f"프로젝트 루트에서 실행해주세요: {git_root}"
        )

def limit_diff(diff: str, max_lines: int=200) -> tuple[str, bool]:
    lines = diff.splitlines()
    truncated = len(lines) > max_lines

    return "\n".join(lines[:max_lines]), truncated