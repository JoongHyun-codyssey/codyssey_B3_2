import argparse
from argparse import ArgumentParser
from subprocess import CalledProcessError
from git_utils import collect_changes, check_git_root, limit_diff


def build_parser() -> ArgumentParser:
    parser = argparse.ArgumentParser(description="명령어 사용법입니다.")
    subparser = parser.add_subparsers(dest="command", required=True)

    commit = subparser.add_parser("commit", help="커밋 메세지 작성")

    model = commit.add_argument("--model", type=str, help="Please, write your AI")
    temperature = commit.add_argument("--temperature", type=float, default=0.2, help="Please, write your AI temperature")
    max_token = commit.add_argument("--max-tokens", type=int, help="Please, write your AI tokens")
    safe_mode = commit.add_argument("--safe-mode", action="store_true", help="Please, write safe mode option")

    pr = subparser.add_parser("pr", help="pr 작성")

    model = pr.add_argument("--model", type=str, help="Please, write your AI")
    temperature = pr.add_argument("--temperature", type=str, help="Please, write your AI temperature")
    max_token = pr.add_argument("--max-tokens", type=int, help="Please, write your AI tokens")
    safe_mode = pr.add_argument("--safe-mode", action="store_true", help="Please, write safe mode option")

    return parser


def main():
    parser = build_parser()
    args = parser.parse_args()

    try:
        check_git_root()
        changes = collect_changes()
    except CalledProcessError as e:
        print(f"Git 명령 실행 실패: {e.stderr.strip()}")
        return 1
    except ValueError as e:
        print(e)
        return 1

    if not changes["status"].strip():
        print("변경 사항이 없습니다.")
        return 0

    untracked_files = [
        line[3:]
        for line in changes["status"].splitlines()
        if line.startswith("?? ")
    ]

    if untracked_files:
        print("아래 새 파일의 내용은 diff에 포함되지 않습니다.")
        for file in untracked_files:
            print(f"- {file}")
        print("포함하려면 git add <파일 경로>로 스테이징해주세요.")

    if not changes["diff"].strip() and not changes["staged_diff"].strip():
        print("변경 파일은 있지만 수집할 diff가 없습니다.")
        print("새 파일은 git add <파일 경로>로 스테이징한 후 다시 실행해주세요.")
        return 1

    diff_text = "\n".join([
    changes["staged_diff"],
    changes["diff"],
    ])

    if args.safe_mode:
        before = len(diff_text.splitlines())
        diff_text, truncated = limit_diff(diff_text)
        after = len(diff_text.splitlines())

        print(f"안전 모드: {before}줄 → {after}줄")

        if truncated:
            print("안전 모드: diff가 200줄을 초과해 일부만 포함합니다.")

    print("\n========== 변경 파일 ==========")
    print(changes["status"].rstrip())

    print("\n========== 전송할 diff ==========")
    print(diff_text)

    return 0

if __name__ == "__main__":
    raise SystemExit(main())