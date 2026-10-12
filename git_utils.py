import subprocess

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