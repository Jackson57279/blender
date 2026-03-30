# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
Tests for the API Client module.

These tests verify the OpenRouter API client functionality without making
actual network requests (using mocks where appropriate).
"""

import json
import sys
import unittest
from unittest.mock import MagicMock, patch

# Add parent directory to path
sys.path.insert(0, '/home/dih/blender/scripts/addons_core/ai_assistant')

import api_client
from api_client import (
    APIErrorType,
    APIResponse,
    OpenRouterClient,
    create_client,
    get_user_friendly_error_message,
)


class TestAPIErrorType(unittest.TestCase):
    """Test cases for APIErrorType enum."""

    def test_enum_values(self):
        """Test that all error types have correct string values."""
        self.assertEqual(APIErrorType.NONE.value, "none")
        self.assertEqual(APIErrorType.AUTHENTICATION.value, "authentication")
        self.assertEqual(APIErrorType.TIMEOUT.value, "timeout")
        self.assertEqual(APIErrorType.NETWORK.value, "network")
        self.assertEqual(APIErrorType.RATE_LIMIT.value, "rate_limit")
        self.assertEqual(APIErrorType.SERVER.value, "server")
        self.assertEqual(APIErrorType.UNKNOWN.value, "unknown")


class TestAPIResponse(unittest.TestCase):
    """Test cases for APIResponse class."""

    def test_success_response(self):
        """Test creating a successful response."""
        response = APIResponse(success=True, content="test script")
        self.assertTrue(response.success)
        self.assertEqual(response.content, "test script")
        self.assertEqual(response.error_type, APIErrorType.NONE)
        self.assertIsNone(response.error_message)

    def test_error_response(self):
        """Test creating an error response."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.AUTHENTICATION,
            error_message="Invalid API key"
        )
        self.assertFalse(response.success)
        self.assertIsNone(response.content)
        self.assertEqual(response.error_type, APIErrorType.AUTHENTICATION)
        self.assertEqual(response.error_message, "Invalid API key")


class TestOpenRouterClientInitialization(unittest.TestCase):
    """Test cases for OpenRouterClient initialization."""

    def test_default_initialization(self):
        """Test client initializes with default values from environment."""
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test-key'}):
            client = OpenRouterClient()
            self.assertEqual(client.api_key, 'test-key')
            self.assertEqual(client.timeout, 30)
            self.assertTrue(client.is_configured())

    def test_custom_api_key(self):
        """Test client can be initialized with custom API key."""
        client = OpenRouterClient(api_key='custom-key')
        self.assertEqual(client.api_key, 'custom-key')
        self.assertTrue(client.is_configured())

    def test_custom_timeout(self):
        """Test client can be initialized with custom timeout."""
        client = OpenRouterClient(api_key='test-key', timeout=60)
        self.assertEqual(client.timeout, 60)

    def test_unconfigured_client(self):
        """Test client reports not configured when no API key."""
        with patch.dict('os.environ', {}, clear=True):
            client = OpenRouterClient()
            self.assertFalse(client.is_configured())
            self.assertEqual(client.api_key, '')


class TestOpenRouterClientRequestCreation(unittest.TestCase):
    """Test cases for request creation."""

    def setUp(self):
        self.client = OpenRouterClient(api_key='test-key', timeout=30)

    def test_request_creation(self):
        """Test that requests are created with correct headers and payload."""
        messages = [{"role": "user", "content": "test"}]
        request = self.client._create_request(messages, 'test-model')

        self.assertEqual(request.get_full_url(), 'https://openrouter.ai/api/v1/chat/completions')
        self.assertEqual(request.get_method(), 'POST')
        # Header lookup is case-insensitive in urllib.request
        self.assertEqual(request.get_header('Content-type'), 'application/json')
        self.assertEqual(request.get_header('Authorization'), 'Bearer test-key')
        self.assertEqual(request.get_header('Http-referer'), 'https://blender.org')
        self.assertEqual(request.get_header('X-title'), 'Blender AI Assistant')

    def test_request_payload(self):
        """Test that request payload contains correct data."""
        messages = [{"role": "user", "content": "test prompt"}]
        request = self.client._create_request(messages, 'test-model', max_tokens=2048)

        payload = json.loads(request.data)
        self.assertEqual(payload['model'], 'test-model')
        self.assertEqual(payload['messages'], messages)
        self.assertEqual(payload['max_tokens'], 2048)


class TestOpenRouterClientResponseParsing(unittest.TestCase):
    """Test cases for response parsing."""

    def setUp(self):
        self.client = OpenRouterClient(api_key='test-key')

    def test_parse_successful_response(self):
        """Test parsing a successful API response."""
        response_data = {
            "choices": [
                {"message": {"content": "import bpy"}}
            ]
        }
        result = self.client._parse_success_response(response_data)
        self.assertTrue(result.success)
        self.assertEqual(result.content, "import bpy")

    def test_parse_empty_choices(self):
        """Test parsing response with empty choices."""
        response_data = {"choices": []}
        result = self.client._parse_success_response(response_data)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, APIErrorType.UNKNOWN)

    def test_parse_missing_content(self):
        """Test parsing response with missing content."""
        response_data = {
            "choices": [{"message": {}}]
        }
        result = self.client._parse_success_response(response_data)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, APIErrorType.UNKNOWN)


class TestOpenRouterClientErrorHandling(unittest.TestCase):
    """Test cases for error handling."""

    def setUp(self):
        self.client = OpenRouterClient(api_key='test-key')

    def test_handle_authentication_error(self):
        """Test handling 401 authentication error."""
        import urllib.error
        error = urllib.error.HTTPError(
            url='https://openrouter.ai/api/v1/chat/completions',
            code=401,
            msg='Unauthorized',
            hdrs={},
            fp=None
        )
        result = self.client._handle_error(error)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, APIErrorType.AUTHENTICATION)
        self.assertIn('Invalid API key', result.error_message)

    def test_handle_rate_limit_error(self):
        """Test handling 429 rate limit error."""
        import urllib.error
        error = urllib.error.HTTPError(
            url='https://openrouter.ai/api/v1/chat/completions',
            code=429,
            msg='Too Many Requests',
            hdrs={},
            fp=None
        )
        result = self.client._handle_error(error)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, APIErrorType.RATE_LIMIT)
        self.assertIn('Rate limit exceeded', result.error_message)

    def test_handle_server_error(self):
        """Test handling 500 server error."""
        import urllib.error
        error = urllib.error.HTTPError(
            url='https://openrouter.ai/api/v1/chat/completions',
            code=500,
            msg='Internal Server Error',
            hdrs={},
            fp=None
        )
        result = self.client._handle_error(error)
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, APIErrorType.SERVER)
        self.assertIn('server error', result.error_message)

    def test_handle_timeout_error(self):
        """Test handling timeout error."""
        result = self.client._handle_error(TimeoutError())
        self.assertFalse(result.success)
        self.assertEqual(result.error_type, APIErrorType.TIMEOUT)
        self.assertIn('timed out', result.error_message)


class TestChatCompletion(unittest.TestCase):
    """Test cases for the chat_completion method."""

    def test_unconfigured_client_returns_auth_error(self):
        """Test that unconfigured client returns authentication error."""
        with patch.dict('os.environ', {}, clear=True):
            client = OpenRouterClient()
            response = client.chat_completion(
                messages=[{"role": "user", "content": "test"}],
                model="test-model"
            )
            self.assertFalse(response.success)
            self.assertEqual(response.error_type, APIErrorType.AUTHENTICATION)

    @patch('urllib.request.urlopen')
    def test_successful_chat_completion(self, mock_urlopen):
        """Test successful chat completion with mocked response."""
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps({
            "choices": [{"message": {"content": "import bpy"}}]
        }).encode()
        mock_urlopen.return_value.__enter__.return_value = mock_response

        client = OpenRouterClient(api_key='test-key')
        response = client.chat_completion(
            messages=[{"role": "user", "content": "create a cube"}],
            model="test-model"
        )

        self.assertTrue(response.success)
        self.assertEqual(response.content, "import bpy")


class TestUserFriendlyErrorMessage(unittest.TestCase):
    """Test cases for error message formatting."""

    def test_success_message(self):
        """Test formatting for success response."""
        response = APIResponse(success=True)
        message = get_user_friendly_error_message(response)
        self.assertEqual(message, "Success")

    def test_authentication_error_message(self):
        """Test formatting for authentication error."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.AUTHENTICATION,
            error_message="Invalid key"
        )
        message = get_user_friendly_error_message(response)
        self.assertEqual(message, "Authentication Error: Invalid key")

    def test_timeout_error_message(self):
        """Test formatting for timeout error."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.TIMEOUT,
            error_message="Request timed out"
        )
        message = get_user_friendly_error_message(response)
        self.assertEqual(message, "Timeout Error: Request timed out")

    def test_network_error_message(self):
        """Test formatting for network error."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.NETWORK,
            error_message="Connection failed"
        )
        message = get_user_friendly_error_message(response)
        self.assertEqual(message, "Network Error: Connection failed")

    def test_rate_limit_error_message(self):
        """Test formatting for rate limit error."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.RATE_LIMIT,
            error_message="Too many requests"
        )
        message = get_user_friendly_error_message(response)
        self.assertEqual(message, "Rate Limit: Too many requests")

    def test_server_error_message(self):
        """Test formatting for server error."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.SERVER,
            error_message="Server down"
        )
        message = get_user_friendly_error_message(response)
        self.assertEqual(message, "Server Error: Server down")

    def test_unknown_error_default_message(self):
        """Test formatting for unknown error without message."""
        response = APIResponse(
            success=False,
            error_type=APIErrorType.UNKNOWN,
            error_message=None
        )
        message = get_user_friendly_error_message(response)
        self.assertEqual(message, "Unknown Error: An unknown error occurred")


class TestCreateClient(unittest.TestCase):
    """Test cases for the create_client factory function."""

    def test_create_client_with_defaults(self):
        """Test creating client with default values."""
        with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'env-key'}):
            client = create_client()
            self.assertEqual(client.api_key, 'env-key')
            self.assertEqual(client.timeout, 30)

    def test_create_client_with_custom_values(self):
        """Test creating client with custom values."""
        client = create_client(api_key='custom-key', timeout=60)
        self.assertEqual(client.api_key, 'custom-key')
        self.assertEqual(client.timeout, 60)


if __name__ == '__main__':
    unittest.main(verbosity=2)
