"""AI 생성 결과의 형식 검증과 후처리.

검증에 실패하면 ValueError를 발생시키고,
자동으로 고친 부분은 notices 목록으로 알려줍니다.
"""

from .config import (
    COMMIT_TITLE_MAX_LENGTH,
    COMMIT_TITLE_RECOMMENDED_LENGTH,
    COMMIT_TYPES,
    PR_TITLE_MAX_LENGTH,
)

RESULT_HEADERS = {"변경 요약:", "커밋 제목:", "커밋 본문:", "PR 제목:", "PR 본문:"}
BULLET_PREFIXES = ("- ", "* ", "+ ")

# PR 본문 필수 섹션과, 비어 있을 때 넣을 안내 문구
PR_REQUIRED_SECTIONS = {
    "Why": "변경 배경을 확인해 작성해주세요.",
    "What": "핵심 변경 사항을 확인해 작성해주세요.",
    "How to Test": "필요한 테스트 방법을 확인해 작성해주세요.",
}


# ---------- 공통 도우미 ----------

def normalize_result_headers(result: str) -> str:
    """'## 커밋 제목:', '**PR 제목:**' 같은 마크다운 장식을 벗겨 헤더를 통일합니다."""
    lines = []

    for line in result.splitlines():
        candidate = line.strip().lstrip("#").strip().strip("*").strip()
        lines.append(candidate if candidate in RESULT_HEADERS else line)

    return "\n".join(lines)


def _has_bullet(text: str) -> bool:
    """내용이 있는 불릿 줄이 하나라도 있는지 확인합니다."""
    return any(
        line.strip().startswith(BULLET_PREFIXES) and line.strip()[2:].strip()
        for line in text.splitlines()
    )


def _to_single_bullet(text: str) -> str:
    """여러 줄 텍스트를 불릿 한 줄로 합칩니다."""
    return "- " + " ".join(text.split())


def _truncate(title: str, max_length: int) -> str:
    """제목을 말줄임표 포함 max_length자로 줄입니다."""
    return title[: max_length - 3].rstrip() + "..."


def _extract_title(title_part: str, label: str) -> str:
    """제목 영역에서 한 줄 제목을 꺼내고 'type: 설명' 형식인지 확인합니다."""
    lines = [line.strip() for line in title_part.splitlines() if line.strip()]

    if len(lines) != 1:
        raise ValueError(f"{label}은 비어 있지 않은 한 줄이어야 합니다.")

    title = lines[0]

    if not any(title.startswith(f"{kind}: ") for kind in COMMIT_TYPES):
        raise ValueError("제목은 허용된 type을 사용한 'type: 설명' 형식이어야 합니다.")

    return title


# ---------- 커밋 메시지 ----------

def validate_commit_result(result: str) -> tuple[str, list[str]]:
    """커밋 제목(권장 50자, 최대 72자)과 본문 불릿 형식을 검증합니다."""
    result = normalize_result_headers(result)
    notices = []

    before, header, remaining = result.partition("커밋 제목:")
    if not header:
        raise ValueError("생성 결과에 커밋 제목 항목이 없습니다.")

    title_part, body_header, body = remaining.partition("커밋 본문:")
    title = _extract_title(title_part, "커밋 제목")

    if len(title) > COMMIT_TITLE_MAX_LENGTH:
        title = _truncate(title, COMMIT_TITLE_MAX_LENGTH)
        notices.append(f"커밋 제목을 최대 {COMMIT_TITLE_MAX_LENGTH}자에 맞게 줄였습니다.")
    elif len(title) > COMMIT_TITLE_RECOMMENDED_LENGTH:
        notices.append(
            f"커밋 제목이 권장 길이인 {COMMIT_TITLE_RECOMMENDED_LENGTH}자를 초과합니다."
        )

    cleaned = f"{before.rstrip()}\n\n커밋 제목:\n{title}"

    body = body.strip()
    if body_header and body:
        if not _has_bullet(body):
            body = _to_single_bullet(body)
            notices.append("커밋 본문을 불릿 형식으로 정리했습니다.")

        cleaned += f"\n\n커밋 본문:\n{body}"

    return cleaned.strip(), notices


# ---------- PR 제목·본문 ----------

def _split_sections(body: str) -> dict[str, list[str]]:
    """'## 섹션명' 기준으로 PR 본문을 섹션별 줄 목록으로 나눕니다."""
    sections: dict[str, list[str]] = {}
    current = None

    for line in body.splitlines():
        stripped = line.strip()

        if stripped.startswith("## "):
            current = stripped[3:].strip()
            sections.setdefault(current, [])
        elif current is not None:
            sections[current].append(line)
        elif stripped:
            raise ValueError("PR 본문은 '## 섹션명'으로 시작해야 합니다.")

    return sections


def validate_pr_result(result: str) -> tuple[str, list[str]]:
    """PR 제목(최대 80자)과 Why/What/How to Test 섹션·불릿을 검증합니다."""
    result = normalize_result_headers(result)
    notices = []

    before, title_header, remaining = result.partition("PR 제목:")
    if not title_header:
        raise ValueError("생성 결과에 PR 제목 항목이 없습니다.")

    title_part, body_header, body = remaining.partition("PR 본문:")
    if not body_header:
        raise ValueError("생성 결과에 PR 본문 항목이 없습니다.")

    title = _extract_title(title_part, "PR 제목")

    if len(title) > PR_TITLE_MAX_LENGTH:
        title = _truncate(title, PR_TITLE_MAX_LENGTH)
        notices.append(f"PR 제목을 최대 {PR_TITLE_MAX_LENGTH}자에 맞게 줄였습니다.")

    sections = _split_sections(body)

    for name, fallback in PR_REQUIRED_SECTIONS.items():
        content = "\n".join(sections.get(name, [])).strip()

        if not content:
            content = f"- {fallback}"
            notices.append(f"{name} 섹션에 작성 필요 안내를 추가했습니다.")
        elif not _has_bullet(content):
            content = _to_single_bullet(content)
            notices.append(f"{name} 섹션을 불릿 형식으로 정리했습니다.")

        sections[name] = content.splitlines()

    # 필수 섹션을 먼저 배치하고, 그 외 섹션도 유지
    order = list(PR_REQUIRED_SECTIONS) + [
        name for name in sections if name not in PR_REQUIRED_SECTIONS
    ]
    cleaned_body = "\n\n".join(
        f"## {name}\n" + "\n".join(sections[name]).strip() for name in order
    )

    cleaned = (
        f"{before.rstrip()}\n\n"
        f"PR 제목:\n{title}\n\n"
        f"PR 본문:\n{cleaned_body}"
    )

    return cleaned.strip(), notices


def validate_result(command: str, result: str) -> tuple[str, list[str]]:
    """명령(commit/pr)에 맞는 검증 함수를 실행합니다."""
    if command == "commit":
        return validate_commit_result(result)
    return validate_pr_result(result)
