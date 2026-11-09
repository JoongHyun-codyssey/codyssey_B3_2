"""프로젝트 전체에서 쓰는 설정값 모음.

모델 추가, 기본값 변경, 길이 제한 조정은 이 파일만 수정하면 됩니다.
"""

# --model 선택지와 각 모델의 제공사
MODEL_PROVIDERS = {
    "claude-haiku-4": "anthropic",
    "claude-sonnet-4": "anthropic",
    "claude-opus-4-7": "anthropic",
    "claude-opus-4-8": "anthropic",
    "gpt-5-mini": "openai",
    "gpt-5.5": "openai",
    "gpt-5.4": "openai",
    "gpt-5.4-mini": "openai",
}

# 제공사별 API Key 환경변수 이름
API_KEY_ENV = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
}

# 제공사별 REST 요청 주소
API_URLS = {
    "openai": "https://copa.codyssey.kr/v1/chat/completions",
    "anthropic": "https://copa.codyssey.kr/v1/messages",
}

ANTHROPIC_VERSION = "2023-06-01"
REQUEST_TIMEOUT = 30  # 초

# temperature 조절을 지원하는 모델
TEMPERATURE_SUPPORTED_MODELS = {"claude-haiku-4", "claude-sonnet-4"}

# CLI 기본값
DEFAULT_MODEL = "gpt-5-mini"
DEFAULT_TEMPERATURE = 0.2  # 지원 모델에만 적용
DEFAULT_MAX_TOKENS = 2048

# --safe-mode에서 AI에 보낼 최대 diff 줄 수
SAFE_MODE_MAX_LINES = 200

# 제목에 허용하는 type과 설명 (프롬프트·검증에서 함께 사용)
COMMIT_TYPES = {
    "feat": "새로운 기능 추가",
    "fix": "버그 수정",
    "docs": "문서 변경",
    "refactor": "기능 변화 없이 코드 구조 개선",
    "test": "테스트 추가 또는 수정",
    "style": "공백·들여쓰기 등 코드 서식 변경",
    "chore": "의존성·설정·기타 유지보수",
}

# 제목 길이 제한
COMMIT_TITLE_RECOMMENDED_LENGTH = 50
COMMIT_TITLE_MAX_LENGTH = 72
PR_TITLE_MAX_LENGTH = 80
