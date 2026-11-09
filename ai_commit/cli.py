"""명령줄 인자 정의."""

import argparse

from .config import DEFAULT_MAX_TOKENS, DEFAULT_MODEL, DEFAULT_TEMPERATURE, MODEL_PROVIDERS


def _temperature(value: str) -> float:
    """--temperature 값이 0~1 사이 실수인지 확인합니다."""
    number = float(value)
    if not 0.0 <= number <= 1.0:
        raise argparse.ArgumentTypeError("0~1 사이 값이어야 합니다.")
    return number


def _positive_int(value: str) -> int:
    """--max-tokens 값이 양의 정수인지 확인합니다."""
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("양의 정수여야 합니다.")
    return number


def _add_common_options(parser: argparse.ArgumentParser) -> None:
    """commit과 pr이 함께 쓰는 옵션을 추가합니다."""
    parser.add_argument(
        "--model",
        choices=list(MODEL_PROVIDERS),
        default=DEFAULT_MODEL,
        help=f"사용할 AI 모델 (기본값: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--temperature",
        type=_temperature,
        default=None,
        help=f"표현의 다양성, 0~1 (지원 모델 기본값: {DEFAULT_TEMPERATURE})",
    )
    parser.add_argument(
        "--max-tokens",
        type=_positive_int,
        default=DEFAULT_MAX_TOKENS,
        help=f"출력 토큰 상한 (기본값: {DEFAULT_MAX_TOKENS})",
    )
    parser.add_argument(
        "--safe-mode",
        action="store_true",
        help="AI에 보낼 diff를 처음 200줄로 제한",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Git 변경 사항으로 커밋 메시지·PR 초안을 생성합니다."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    commit = subparsers.add_parser("commit", help="커밋 메시지 초안 생성")
    _add_common_options(commit)

    pr = subparsers.add_parser("pr", help="PR 제목·본문 초안 생성")
    _add_common_options(pr)

    return parser
