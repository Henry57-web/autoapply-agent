from app.core.config import Settings
from app.services.llm.gemini import GeminiProvider
from app.services.llm.openai_compatible import OpenAICompatibleProvider
from app.services.llm.provider import LLMProvider


OPENAI_COMPATIBLE_BASE_URLS = {
    "openai": None,
    "groq": "https://api.groq.com/openai/v1",
    "deepseek": "https://api.deepseek.com",
}


def create_llm_provider(settings: Settings) -> LLMProvider:
    provider = settings.llm_provider.lower().strip()
    api_key = settings.resolved_llm_api_key()
    model = settings.resolved_llm_model()

    if not model:
        raise ValueError(f"LLM_MODEL is required for provider: {provider}")
    if provider == "gemini":
        return GeminiProvider(api_key, model, settings.llm_base_url)
    if provider in OPENAI_COMPATIBLE_BASE_URLS:
        base_url = settings.llm_base_url or OPENAI_COMPATIBLE_BASE_URLS[provider]
        return OpenAICompatibleProvider(api_key, model, base_url)

    supported = ", ".join(sorted([*OPENAI_COMPATIBLE_BASE_URLS, "gemini"]))
    raise ValueError(f"Unsupported LLM_PROVIDER '{provider}'. Supported providers: {supported}")
