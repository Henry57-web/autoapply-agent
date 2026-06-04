import unittest

from app.core.config import Settings
from app.services.llm.factory import create_llm_provider
from app.services.llm.gemini import GeminiProvider
from app.services.llm.openai_compatible import OpenAICompatibleProvider


class LLMFactoryTests(unittest.TestCase):
    def test_gemini_uses_cost_effective_default_model(self) -> None:
        provider = create_llm_provider(Settings(llm_provider="gemini", llm_api_key="test"))

        self.assertIsInstance(provider, GeminiProvider)
        self.assertEqual(provider.model, "gemini-2.5-flash-lite")

    def test_groq_uses_openai_compatible_adapter(self) -> None:
        provider = create_llm_provider(
            Settings(llm_provider="groq", llm_api_key="test", llm_model="openai/gpt-oss-20b")
        )

        self.assertIsInstance(provider, OpenAICompatibleProvider)
        self.assertEqual(provider.model, "openai/gpt-oss-20b")
        self.assertEqual(provider.base_url, "https://api.groq.com/openai/v1")

    def test_legacy_openai_settings_are_still_supported(self) -> None:
        settings = Settings(
            llm_provider="openai",
            llm_model="gpt-4.1-nano",
            openai_api_key="legacy-key",
        )
        provider = create_llm_provider(settings)

        self.assertIsInstance(provider, OpenAICompatibleProvider)
        self.assertEqual(provider.model, "gpt-4.1-nano")

    def test_unknown_provider_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "Unsupported LLM_PROVIDER"):
            create_llm_provider(Settings(llm_provider="unknown", llm_api_key="test"))


if __name__ == "__main__":
    unittest.main()
