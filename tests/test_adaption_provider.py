"""Offline unit tests for AdaptionProvider."""

import os
import unittest
from unittest.mock import MagicMock, patch

from providers.adaption import AdaptionProvider


class TestAdaptionProvider(unittest.TestCase):
    def setUp(self):
        self.patcher = patch.dict(os.environ, {"ADAPTION_API_KEY": "test_fake_key_12345"})
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()

    def test_initialization_offline(self):
        """Verify initialization sets parameters without making network calls."""
        provider = AdaptionProvider()
        self.assertEqual(provider.get_name(), "adaption")
        self.assertEqual(provider._model, "qwen3.5-397b")
        self.assertEqual(provider._base_url, "https://api.prod.adaptionlabs.ai")
        self.assertEqual(provider._http_url, "https://api.prod.adaptionlabs.ai/api/v1/responses")
        self.assertEqual(provider._api_key, "test_fake_key_12345")

    def test_missing_api_key_raises(self):
        """Verify error raised when ADAPTION_API_KEY is empty."""
        with patch.dict(os.environ, {"ADAPTION_API_KEY": ""}):
            with self.assertRaises(EnvironmentError):
                AdaptionProvider()

    def test_split_messages(self):
        """Verify system message is extracted as instructions."""
        provider = AdaptionProvider()
        messages = [
            {"role": "system", "content": "You are agent_1."},
            {"role": "user", "content": "Claim sensor_log."},
        ]
        instructions, inp = provider._split_messages(messages)
        self.assertEqual(instructions, "You are agent_1.")
        self.assertEqual(inp, "Claim sensor_log.")

    def test_extract_content_output_text(self):
        """Verify extraction priority for official output_text field."""
        provider = AdaptionProvider()
        data = {"output_text": "CLAIM CONFIRMED", "content": "OTHER"}
        self.assertEqual(provider._extract_content(data), "CLAIM CONFIRMED")

    def test_extract_content_fallbacks(self):
        """Verify fallback extraction for older or raw payload variants."""
        provider = AdaptionProvider()
        self.assertEqual(provider._extract_content({"content": "Hello"}), "Hello")
        self.assertEqual(provider._extract_content({"content": ["Line 1", "Line 2"]}), "Line 1\nLine 2")
        self.assertEqual(provider._extract_content({"output": "Result"}), "Result")
        self.assertEqual(provider._extract_content({"response": "Resp"}), "Resp")

    def test_sdk_mock_generation(self):
        """Verify SDK generation parsing without real network call."""
        provider = AdaptionProvider()
        mock_sdk = MagicMock()
        mock_response = MagicMock()
        mock_response.output_text = "Action: claim_resource(sensor_log)"
        mock_response.status = "stop"
        mock_response.usage.input_tokens = 50
        mock_response.usage.output_tokens = 15
        mock_response.usage.total_tokens = 65
        mock_sdk.responses.create.return_value = mock_response

        provider._sdk_client = mock_sdk
        res = provider.generate([{"role": "user", "content": "hello"}])

        self.assertEqual(res["content"], "Action: claim_resource(sensor_log)")
        self.assertEqual(res["usage"]["prompt_tokens"], 50)
        self.assertEqual(res["usage"]["completion_tokens"], 15)
        self.assertEqual(res["usage"]["total_tokens"], 65)
        self.assertEqual(provider._call_count, 1)


if __name__ == "__main__":
    unittest.main()
