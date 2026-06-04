import json
from typing import Any

import httpx

from app.services.llm.provider import LLMServiceUnavailable


class GeminiProvider:
    def __init__(self, api_key: str | None, model: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url or "https://generativelanguage.googleapis.com/v1beta"

    async def generate_json(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise LLMServiceUnavailable("LLM_API_KEY is not configured.")

        url = f"{self.base_url}/models/{self.model}:generateContent"
        request_body = {
            "system_instruction": {"parts": [{"text": system_prompt}]},
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": json.dumps(user_payload, ensure_ascii=False)}],
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "responseMimeType": "application/json",
            },
        }

        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(url, params={"key": self.api_key}, json=request_body)

        if not response.is_success:
            raise LLMServiceUnavailable(
                f"Gemini request failed with status {response.status_code}: {response.text[:300]}"
            )

        data = response.json()
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise LLMServiceUnavailable("Gemini returned an unexpected response.") from exc
        return json.loads(content)
