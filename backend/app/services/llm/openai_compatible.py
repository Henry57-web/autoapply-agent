import json
from typing import Any

from openai import AsyncOpenAI

from app.services.llm.provider import LLMServiceUnavailable


class OpenAICompatibleProvider:
    def __init__(self, api_key: str | None, model: str, base_url: str | None = None) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url

    async def generate_json(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        if not self.api_key:
            raise LLMServiceUnavailable("LLM_API_KEY is not configured.")

        client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        response = await client.chat.completions.create(
            model=self.model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(user_payload, ensure_ascii=False)},
            ],
        )
        content = response.choices[0].message.content
        if not content:
            raise LLMServiceUnavailable("The configured LLM provider returned an empty response.")
        return json.loads(content)
