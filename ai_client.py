import os
from typing import Any
import requests

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

def get_api_key(model:str) -> str:
    provider = MODEL_PROVIDERS[model]

    variable = {
        "openai": "OPENAI_API_KEY",
        "anthropic": "ANTROPIC_API_KEY"
    }[provider]

    api_key = os.getenv(variable)

    if not api_key:
        raise ValueError(f"{variable} 환경변수를 설정해주세요.")

    return api_key

def request_ai(model: str, api_key: str, prompt: str) -> str:
    provider = MODEL_PROVIDERS[model]

    payload:dict[str, Any] = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
    }

    if provider == "openai":
        url = "https://copa.codyssey.kr/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {api_key}",
        }
    else:
        url = "https://copa.codyssey.kr/v1/messages"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        }
        payload["max_tokens"] = 1024

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=30
        )
        response.raise_for_status()
    except requests.Timeout as e:
        raise RuntimeError("AI API 요청 시간이 초과되었습니다.") from e
    except requests.RequestException as e:
        raise RuntimeError(f"AI API 요청 실패: {e}") from e

    try:
        data = response.json()

        if provider == "openai":
            text = data["choices"][0]["message"]["content"]
        else:
            text = "\n".join(
                block["text"]
                for block in data["content"]
                if block.get("type") == "text"
            )

        if not isinstance(text, str) or not text.strip():
            raise ValueError("생성된 텍스트가 없습니다.")

        return text.strip()

    except (KeyError, IndexError, TypeError, ValueError) as e:
        raise RuntimeError("AI API 응답에서 생성 텍스트를 읽을 수 없습니다.") from e

