"""Git 명령 실행과 diff 수집."""

import subprocess
from pathlib import Path


def _run_git(*args: str) -> str:
    """git 명령을 실행하고 표준 출력을 반환합니다. 실패하면 CalledProcessError."""
    result = subprocess.run(
        ["git", *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def check_git_root() -> None:
    """현재 위치가 Git 저장소 루트인지 확인합니다."""
    git_root = Path(_run_git("rev-parse", "--show-toplevel").strip()).resolve()

    if Path.cwd().resolve() != git_root:
        raise ValueError(f"프로젝트 루트에서 실행해주세요: {git_root}")


def collect_changes() -> dict[str, str]:
    """변경 파일 목록과 스테이징 전후 diff를 수집합니다."""
    return {
        "status": _run_git("status", "--porcelain"),
        "diff": _run_git("diff"),
        "staged_diff": _run_git("diff", "--cached"),
    }


def find_untracked_files(status: str) -> list[str]:
    """git status --porcelain 결과에서 추적되지 않은 파일만 골라냅니다."""
    return [line[3:] for line in status.splitlines() if line.startswith("?? ")]


def combine_diffs(changes: dict[str, str]) -> str:
    """스테이징된 diff를 앞에, 스테이징되지 않은 diff를 뒤에 붙입니다."""
    return "\n".join([changes["staged_diff"], changes["diff"]])


def limit_diff(diff: str, max_lines: int) -> tuple[str, bool]:
    """diff를 앞에서부터 max_lines줄만 남깁니다. (잘린 diff, 잘림 여부)를 반환."""
    lines = diff.splitlines()
    return "\n".join(lines[:max_lines]), len(lines) > max_lines
