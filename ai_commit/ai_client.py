"""AI API 요청과 응답 처리."""

import os
from typing import Any

import requests

from .config import (
    ANTHROPIC_VERSION,
    API_KEY_ENV,
    API_URLS,
    DEFAULT_TEMPERATURE,
    MODEL_PROVIDERS,
    REQUEST_TIMEOUT,
    TEMPERATURE_SUPPORTED_MODELS,
)


def get_api_key(model: str) -> str:
    """선택한 모델의 제공사에 맞는 API Key를 환경변수에서 읽습니다."""
    variable = API_KEY_ENV[MODEL_PROVIDERS[model]]
    api_key = os.getenv(variable)

    if not api_key:
        raise ValueError(f"{variable} 환경변수를 설정해주세요.")

    return api_key


def _resolve_temperature(model: str, temperature: float | None) -> float | None:
    """모델에 보낼 temperature를 결정합니다. None이면 요청에 넣지 않습니다."""
    if model in TEMPERATURE_SUPPORTED_MODELS:
        return DEFAULT_TEMPERATURE if temperature is None else temperature

    if temperature is not None:
        raise RuntimeError(
            f"현재 구현에서는 {model}의 temperature 조절을 "
            "지원하지 않습니다. --temperature를 생략해주세요."
        )

    return None


def _build_request(
    model: str,
    api_key: str,
    prompt: str,
    max_tokens: int,
    temperature: float | None,
) -> tuple[str, dict[str, str], dict[str, Any]]:
    """제공사 형식에 맞는 (URL, 헤더, payload)를 만듭니다."""
    provider = MODEL_PROVIDERS[model]

    payload: dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    if provider == "openai":
        headers = {"Authorization": f"Bearer {api_key}"}
        payload["max_completion_tokens"] = max_tokens
    else:
        headers = {
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        }
        payload["max_tokens"] = max_tokens

    temperature = _resolve_temperature(model, temperature)
    if temperature is not None:
        payload["temperature"] = temperature

    return API_URLS[provider], headers, payload


def _extract_text(provider: str, data: dict[str, Any]) -> str:
    """API 응답 JSON에서 생성된 텍스트를 꺼냅니다."""
    if provider == "openai":
        choice = data["choices"][0]

        if choice.get("finish_reason") == "length":
            raise RuntimeError(
                "토큰 한도에 도달해 생성이 중단되었습니다. "
                "--max-tokens 값을 늘려주세요."
            )

        text = choice["message"]["content"]
    else:
        text = "\n".join(
            block["text"]
            for block in data["content"]
            if block.get("type") == "text"
        )

    if not isinstance(text, str) or not text.strip():
        raise ValueError("생성된 텍스트가 없습니다.")

    return text.strip()


def request_ai(
    model: str,
    api_key: str,
    prompt: str,
    max_tokens: int,
    temperature: float | None = None,
) -> str:
    """AI API를 1회 호출해 생성된 텍스트를 반환합니다. 실패하면 RuntimeError."""
    url, headers, payload = _build_request(
        model, api_key, prompt, max_tokens, temperature
    )

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
    except requests.Timeout as e:
        raise RuntimeError("AI API 요청 시간이 초과되었습니다.") from e
    except requests.RequestException as e:
        raise RuntimeError(f"AI API 요청 실패: {e}") from e

    try:
        return _extract_text(MODEL_PROVIDERS[model], response.json())
    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise RuntimeError("AI API 응답에서 생성 텍스트를 읽을 수 없습니다.") from e
