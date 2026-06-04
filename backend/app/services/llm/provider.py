from typing import Any, Protocol


class LLMServiceUnavailable(RuntimeError):
    pass


class LLMProvider(Protocol):
    async def generate_json(self, system_prompt: str, user_payload: dict[str, Any]) -> dict[str, Any]:
        pass
