"""AI에 보내기 전 diff에서 민감정보를 제거합니다.

1단계: 민감 파일(.env, 개인키 등)은 diff 내용을 통째로 제외합니다.
2단계: 남은 diff에서 API Key·토큰·비밀번호·개인정보를 [MASKED:종류]로 바꿉니다.

마스킹은 정규식 기반이라 모든 민감정보를 잡아내지는 못합니다.
실행 전에 diff를 직접 확인하는 습관은 여전히 필요합니다.
"""

import re
from collections import Counter
from dataclasses import dataclass, field
from fnmatch import fnmatch
from pathlib import PurePosixPath

# ---------- 1단계: 통째로 제외할 파일 ----------

SENSITIVE_FILE_PATTERNS = (
    ".env", ".env.*",                        # 환경변수 파일
    "*.pem", "*.key", "*.p12", "*.pfx",      # 인증서·개인키
    "*.jks", "*.keystore",
    "id_rsa*", "id_dsa*", "id_ecdsa*", "id_ed25519*",  # SSH 키
    "credentials*", "service-account*.json",  # 클라우드 자격 증명
    "secrets.*", ".npmrc", ".pypirc", ".netrc",
)

# 실제 값 없이 형식만 보여주는 예시 파일은 제외하지 않습니다. (값은 2단계에서 마스킹)
SAFE_FILE_NAMES = {".env.example", ".env.sample", ".env.template"}

_DIFF_HEADER = re.compile(r"^diff --git a/(.+?) b/(.+)$")


# ---------- 2단계: 값을 가릴 패턴 ----------

def _mask(label: str) -> str:
    return f"[MASKED:{label}]"


# (종류, 정규식, 바꿀 문자열) — 위에서부터 순서대로 적용
_MASK_RULES: list[tuple[str, re.Pattern[str], str]] = [
    # 서비스별 API Key·토큰 (형식이 정해져 있어 정확도가 높음)
    ("API_KEY", re.compile(r"\bsk-(?:ant-|proj-)?[A-Za-z0-9_-]{20,}"), _mask("API_KEY")),
    ("API_KEY", re.compile(r"\bAIza[0-9A-Za-z_-]{35}"), _mask("API_KEY")),
    ("API_KEY", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b"), _mask("API_KEY")),
    ("TOKEN", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{22,})"), _mask("TOKEN")),
    ("TOKEN", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}"), _mask("TOKEN")),
    ("TOKEN", re.compile(r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"), _mask("TOKEN")),
    ("TOKEN", re.compile(r"(\bBearer\s+)(?!\[MASKED)[A-Za-z0-9._~+/=-]{16,}"), r"\1" + _mask("TOKEN")),

    # .env·셸 형식: OPENAI_API_KEY=값, export DB_PASSWORD=값
    ("SECRET", re.compile(
        r"(?m)^([+\- ]?\s*(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*"
        r"(?:KEY|SECRET|TOKEN|PASSWORD|PASSWD|PWD|CREDENTIALS?)\s*=\s*)"
        r"(?![\[{(]|[\"']\[MASKED)(\S.*)$"
    ), r"\1" + _mask("SECRET")),

    # 코드 형식: password = "값", "api_key": "값"
    ("SECRET", re.compile(
        r"(?i)([\w$:.-]*(?:api[_-]?key|secret|token|password|passwd|pwd|"
        r"access[_-]?key|private[_-]?key)[\"']?\s*[:=]\s*)"
        r"([\"'])(?!\[MASKED)([^\"'\n]{6,})\2"
    ), r"\1\2" + _mask("SECRET") + r"\2"),

    # 개인정보
    ("EMAIL", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b"), _mask("EMAIL")),
    ("RRN", re.compile(r"\b\d{6}-[1-4]\d{6}\b"), _mask("RRN")),
    ("PHONE", re.compile(r"\b01[016789]-\d{3,4}-\d{4}\b"), _mask("PHONE")),
    ("CARD", re.compile(r"\b\d{4}[- ]\d{4}[- ]\d{4}[- ]\d{4}\b"), _mask("CARD")),
]

_PRIVATE_KEY_BEGIN = re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----")
_PRIVATE_KEY_END = re.compile(r"-----END [A-Z ]*PRIVATE KEY-----")

# 터미널 출력용 한국어 이름
MASK_LABELS = {
    "API_KEY": "API Key",
    "TOKEN": "토큰",
    "SECRET": "비밀번호·비밀값",
    "PRIVATE_KEY": "개인키",
    "EMAIL": "이메일",
    "RRN": "주민등록번호",
    "PHONE": "전화번호",
    "CARD": "카드번호",
}


@dataclass
class SanitizeReport:
    excluded_files: list[str] = field(default_factory=list)
    masked: Counter = field(default_factory=Counter)


# ---------- 1단계 구현 ----------

def is_sensitive_file(path: str) -> bool:
    name = PurePosixPath(path).name
    if name in SAFE_FILE_NAMES:
        return False
    return any(fnmatch(name, pattern) for pattern in SENSITIVE_FILE_PATTERNS)


def _exclude_sensitive_files(diff: str, report: SanitizeReport) -> str:
    """민감 파일의 diff 블록을 헤더 한 줄과 안내 문구로 바꿉니다."""
    output = []
    skipping = False

    for line in diff.splitlines():
        header = _DIFF_HEADER.match(line)

        if header:
            paths = header.groups()
            skipping = any(is_sensitive_file(p) for p in paths)
            output.append(line)

            if skipping:
                if paths[1] not in report.excluded_files:
                    report.excluded_files.append(paths[1])
                output.append("[EXCLUDED] 민감 파일이므로 변경 내용을 전송하지 않습니다.")
            continue

        if not skipping:
            output.append(line)

    return "\n".join(output)


# ---------- 2단계 구현 ----------

def _mask_private_keys(diff: str, report: SanitizeReport) -> str:
    """BEGIN ~ END PRIVATE KEY 사이의 줄을 모두 가립니다."""
    output = []
    inside = False

    for line in diff.splitlines():
        if _PRIVATE_KEY_BEGIN.search(line):
            inside = True
            report.masked["PRIVATE_KEY"] += 1

        if inside:
            # diff 줄 앞의 +, -, 공백 표시는 남겨 줄 구조를 유지
            prefix = line[:1] if line[:1] in "+- " else ""
            output.append(prefix + _mask("PRIVATE_KEY"))
        else:
            output.append(line)

        if inside and _PRIVATE_KEY_END.search(line):
            inside = False

    return "\n".join(output)


def _mask_patterns(diff: str, report: SanitizeReport) -> str:
    for label, pattern, replacement in _MASK_RULES:
        diff, count = pattern.subn(replacement, diff)
        if count:
            report.masked[label] += count
    return diff


def sanitize_diff(diff: str) -> tuple[str, SanitizeReport]:
    """diff에서 민감정보를 제거하고 (정리된 diff, 처리 결과)를 반환합니다."""
    report = SanitizeReport()
    diff = _exclude_sensitive_files(diff, report)
    diff = _mask_private_keys(diff, report)
    diff = _mask_patterns(diff, report)
    return diff, report
