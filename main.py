"""실행 진입점: python main.py {commit,pr} [옵션]"""

from pathlib import Path

from dotenv import load_dotenv

from ai_commit.app import run
from ai_commit.cli import build_parser


def main() -> int:
    args = build_parser().parse_args()

    # main.py와 같은 폴더의 .env를 읽습니다. (셸에 이미 있는 값이 우선)
    load_dotenv(Path(__file__).resolve().parent / ".env")

    return run(args)


if __name__ == "__main__":
    raise SystemExit(main())
