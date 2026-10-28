import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.services.groq_client import GroqClient


class GroqClientTests(unittest.TestCase):
    @patch("app.services.groq_client.OpenAI")
    def test_uses_groq_api_and_configured_model(self, openai_class) -> None:
        message = SimpleNamespace(content="  Grounded answer.  ")
        completion = SimpleNamespace(
            choices=[SimpleNamespace(message=message)]
        )
        create_completion = MagicMock(return_value=completion)
        client_instance = SimpleNamespace(
            chat=SimpleNamespace(
                completions=SimpleNamespace(create=create_completion)
            )
        )
        openai_class.return_value = client_instance

        client = GroqClient("test-api-key", "llama-3.3-70b-versatile")
        answer = client.generate_grounded_answer("Question?", "Document passage.")

        self.assertEqual(answer, "Grounded answer.")
        openai_class.assert_called_once_with(
            api_key="test-api-key",
            base_url="https://api.groq.com/openai/v1",
            timeout=45.0,
            max_retries=2,
        )
        create_completion.assert_called_once()
        call = create_completion.call_args
        self.assertEqual(call.kwargs["model"], "llama-3.3-70b-versatile")
        self.assertEqual(
            call.kwargs["messages"][1]["content"],
            "Question:\nQuestion?\n\nDocument evidence:\nDocument passage.",
        )
        system_prompt = call.kwargs["messages"][0]["content"]
        self.assertIn("displays verified citations separately", system_prompt)
        self.assertIn("clear Markdown", system_prompt)

    def test_missing_groq_key_reports_correct_configuration_name(self) -> None:
        client = GroqClient(None, "llama-3.3-70b-versatile")

        with self.assertRaisesRegex(RuntimeError, "GROQ_API_KEY"):
            client.generate_grounded_answer("Question?", "Document passage.")


if __name__ == "__main__":
    unittest.main()
