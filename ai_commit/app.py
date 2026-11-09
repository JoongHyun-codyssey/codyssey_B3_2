"""전체 실행 흐름: Git 변경 수집 → 프롬프트 생성 → AI 호출 → 결과 검증·출력."""

from argparse import Namespace
from subprocess import CalledProcessError

from .ai_client import get_api_key, request_ai
from .config import SAFE_MODE_MAX_LINES
from .git_utils import (
    check_git_root,
    collect_changes,
    combine_diffs,
    find_untracked_files,
    limit_diff,
)
from .prompts import build_prompt
from .validators import validate_result


def _print_section(title: str) -> None:
    print(f"\n========== {title} ==========")


def _prepare_diff(changes: dict[str, str], safe_mode: bool) -> str | None:
    """AI에 보낼 diff를 만듭니다. 보낼 diff가 없으면 None."""
    untracked = find_untracked_files(changes["status"])
    if untracked:
        print("아래 새 파일의 내용은 diff에 포함되지 않습니다.")
        for file in untracked:
            print(f"- {file}")
        print("포함하려면 git add <파일 경로>로 스테이징해주세요.")

    if not changes["diff"].strip() and not changes["staged_diff"].strip():
        print("변경 파일은 있지만 수집할 diff가 없습니다.")
        print("새 파일은 git add <파일 경로>로 스테이징한 후 다시 실행해주세요.")
        return None

    diff_text = combine_diffs(changes)

    if safe_mode:
        before = len(diff_text.splitlines())
        diff_text, truncated = limit_diff(diff_text, SAFE_MODE_MAX_LINES)
        after = len(diff_text.splitlines())

        print(f"안전 모드: {before}줄 → {after}줄")
        if truncated:
            print(f"안전 모드: diff가 {SAFE_MODE_MAX_LINES}줄을 초과해 일부만 포함합니다.")

    return diff_text


def run(args: Namespace) -> int:
    """CLI 명령을 실행하고 종료 코드를 반환합니다."""
    # 1. Git 변경 사항 수집
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

    # 2. AI에 보낼 diff 준비
    diff_text = _prepare_diff(changes, args.safe_mode)
    if diff_text is None:
        return 1

    _print_section("변경 파일")
    print(changes["status"].rstrip())
    print(f"AI에 전달할 diff: {len(diff_text.splitlines())}줄")

    # 3. API Key 확인
    try:
        api_key = get_api_key(args.model)
    except ValueError as e:
        print(e)
        return 1

    print(f"API Key 설정 확인 완료: {args.model}")

    # 4. AI 호출 (1회)
    try:
        result = request_ai(
            model=args.model,
            api_key=api_key,
            prompt=build_prompt(args.command, diff_text),
            max_tokens=args.max_tokens,
            temperature=args.temperature,
        )
    except RuntimeError as e:
        print(e)
        return 1

    # 5. 결과 검증·출력
    try:
        result, notices = validate_result(args.command, result)
    except ValueError as e:
        print(f"검증 결과 실패: {e}")
        _print_section("검증 전 AI 원본 응답")
        print(result)
        return 1

    for notice in notices:
        print(f"검증 안내: {notice}")

    _print_section("AI 응답")
    print(result)
    print("AI API 호출 횟수: 1회")

    return 0
