"""
Unit tests for API client validation assertions (m2-api milestone).

Tests VAL-API-001 through VAL-API-005 without requiring Blender.
"""

import json
import os
import sys
import unittest
import urllib.error
from unittest.mock import MagicMock, patch, Mock

# Add the add-on path to sys.path
sys.path.insert(0, '/home/dih/blender/scripts/addons_core/ai_assistant')

# Mock bpy module before importing api_client
sys.modules['bpy'] = MagicMock()

from api_client import (
    APIErrorType,
    APIResponse,
    OpenRouterClient,
    create_client,
    get_user_friendly_error_message,
)


class TestVAL_API_001_ValidAPIKey(unittest.TestCase):
    """VAL-API-001: Valid API Key Enables Generation"""
    
    def test_valid_api_key_allows_generation(self):
        """With a valid OPENROUTER_API_KEY set, API calls should proceed."""
        client = OpenRouterClient(api_key="valid_test_key")
        self.assertTrue(client.is_configured())
        self.assertEqual(client.api_key, "valid_test_key")
        
    @patch.dict(os.environ, {'OPENROUTER_API_KEY': 'env_test_key'})
    def test_api_key_from_environment(self):
        """API key can be read from environment variable."""
        client = OpenRouterClient()
        self.assertTrue(client.is_configured())
        self.assertEqual(client.api_key, 'env_test_key')
        
    @patch('urllib.request.urlopen')
    def test_successful_api_response(self, mock_urlopen):
        """API call with valid key returns successful response."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "import bpy"}}]
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response
        
        client = OpenRouterClient(api_key="valid_key")
        messages = [{"role": "user", "content": "create a cube"}]
        response = client.chat_completion(messages, model="test-model")
        
        self.assertTrue(response.success)
        self.assertEqual(response.content, "import bpy")
        self.assertEqual(response.error_type, APIErrorType.NONE)


class TestVAL_API_002_InvalidAPIKey(unittest.TestCase):
    """VAL-API-002: Invalid API Key Shows Error"""
    
    def test_missing_api_key_blocks_call(self):
        """Without API key, client reports not configured."""
        client = OpenRouterClient(api_key="")
        self.assertFalse(client.is_configured())
        
        messages = [{"role": "user", "content": "create a cube"}]
        response = client.chat_completion(messages, model="test-model")
        
        self.assertFalse(response.success)
        self.assertEqual(response.error_type, APIErrorType.AUTHENTICATION)
        self.assertIn("API key not configured", response.error_message)
        
    @patch('urllib.request.urlopen')
    def test_401_error_handling(self, mock_urlopen):
        """401 Unauthorized returns authentication error."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://openrouter.ai/api/v1/chat/completions",
            code=401,
            msg="Unauthorized",
            hdrs={},
            fp=None
        )
        
        client = OpenRouterClient(api_key="invalid_key")
        messages = [{"role": "user", "content": "create a cube"}]
        response = client.chat_completion(messages, model="test-model")
        
        self.assertFalse(response.success)
        self.assertEqual(response.error_type, APIErrorType.AUTHENTICATION)
        self.assertIn("Invalid API key", response.error_message)
        
    def test_user_friendly_auth_error_message(self):
        """Authentication errors show user-friendly message."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.AUTHENTICATION,
            error_message="Invalid API key. Please check your OPENROUTER_API_KEY."
        )
        message = get_user_friendly_error_message(response)
        self.assertIn("Authentication Error", message)
        self.assertIn("Invalid API key", message)


class TestVAL_API_003_TimeoutHandling(unittest.TestCase):
    """VAL-API-003: Timeout Handling Works"""
    
    def test_timeout_setting_is_configurable(self):
        """Timeout can be set on client creation."""
        client = OpenRouterClient(api_key="test_key", timeout=45)
        self.assertEqual(client.timeout, 45)
        
        client = OpenRouterClient(api_key="test_key", timeout=15)
        self.assertEqual(client.timeout, 15)
        
    @patch('urllib.request.urlopen')
    def test_timeout_error_handling(self, mock_urlopen):
        """Timeout errors return appropriate error type."""
        mock_urlopen.side_effect = urllib.error.URLError(
            reason="Request timed out"
        )
        
        client = OpenRouterClient(api_key="test_key", timeout=30)
        messages = [{"role": "user", "content": "create a cube"}]
        response = client.chat_completion(messages, model="test-model")
        
        self.assertFalse(response.success)
        self.assertEqual(response.error_type, APIErrorType.TIMEOUT)
        self.assertIn("timed out", response.error_message.lower())
        
    def test_user_friendly_timeout_message(self):
        """Timeout errors show user-friendly message."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.TIMEOUT,
            error_message="Request timed out after 30 seconds."
        )
        message = get_user_friendly_error_message(response)
        self.assertIn("Timeout Error", message)
        self.assertIn("30 seconds", message)


class TestVAL_API_004_NetworkErrors(unittest.TestCase):
    """VAL-API-004: Network Errors Handled Gracefully"""
    
    @patch('urllib.request.urlopen')
    def test_network_error_dns_failure(self, mock_urlopen):
        """DNS resolution failures show network error."""
        mock_urlopen.side_effect = urllib.error.URLError(
            reason="Name resolution failed"
        )
        
        client = OpenRouterClient(api_key="test_key")
        messages = [{"role": "user", "content": "create a cube"}]
        response = client.chat_completion(messages, model="test-model")
        
        self.assertFalse(response.success)
        self.assertEqual(response.error_type, APIErrorType.NETWORK)
        
    @patch('urllib.request.urlopen')
    def test_network_error_connection_failure(self, mock_urlopen):
        """Connection failures show network error."""
        mock_urlopen.side_effect = urllib.error.URLError(
            reason="Connection refused"
        )
        
        client = OpenRouterClient(api_key="test_key")
        messages = [{"role": "user", "content": "create a cube"}]
        response = client.chat_completion(messages, model="test-model")
        
        self.assertFalse(response.success)
        self.assertEqual(response.error_type, APIErrorType.NETWORK)
        self.assertIn("network", response.error_message.lower())
        
    def test_user_friendly_network_error_message(self):
        """Network errors show user-friendly message."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.NETWORK,
            error_message="Could not connect to OpenRouter API. Check your network connection."
        )
        message = get_user_friendly_error_message(response)
        self.assertIn("Network Error", message)


class TestVAL_API_005_RateLimiting(unittest.TestCase):
    """VAL-API-005: Rate Limiting Shows Appropriate Message"""
    
    @patch('urllib.request.urlopen')
    def test_429_error_handling(self, mock_urlopen):
        """429 Too Many Requests returns rate limit error."""
        mock_urlopen.side_effect = urllib.error.HTTPError(
            url="https://openrouter.ai/api/v1/chat/completions",
            code=429,
            msg="Too Many Requests",
            hdrs={},
            fp=None
        )
        
        client = OpenRouterClient(api_key="test_key")
        messages = [{"role": "user", "content": "create a cube"}]
        response = client.chat_completion(messages, model="test-model")
        
        self.assertFalse(response.success)
        self.assertEqual(response.error_type, APIErrorType.RATE_LIMIT)
        self.assertIn("Rate limit", response.error_message)
        
    def test_user_friendly_rate_limit_message(self):
        """Rate limit errors show user-friendly message."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.RATE_LIMIT,
            error_message="Rate limit exceeded. Please try again later."
        )
        message = get_user_friendly_error_message(response)
        self.assertIn("Rate Limit", message)


class TestAPIClientAdditional(unittest.TestCase):
    """Additional tests for comprehensive coverage."""

    def test_server_error_handling(self):
        """500 errors are handled appropriately."""
        with patch('urllib.request.urlopen') as mock_urlopen:
            mock_urlopen.side_effect = urllib.error.HTTPError(
                url="https://openrouter.ai/api/v1/chat/completions",
                code=500,
                msg="Internal Server Error",
                hdrs={},
                fp=None
            )

            client = OpenRouterClient(api_key="test_key")
            messages = [{"role": "user", "content": "create a cube"}]
            response = client.chat_completion(messages, model="test-model")

            self.assertFalse(response.success)
            self.assertEqual(response.error_type, APIErrorType.SERVER)

    def test_create_client_factory(self):
        """Factory function creates configured client."""
        client = create_client(api_key="factory_key", timeout=60)
        self.assertIsInstance(client, OpenRouterClient)
        self.assertEqual(client.api_key, "factory_key")
        self.assertEqual(client.timeout, 60)


if __name__ == "__main__":
    # Run tests with verbose output
    suite = unittest.TestLoader().loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Exit with proper code
    sys.exit(0 if result.wasSuccessful() else 1)
