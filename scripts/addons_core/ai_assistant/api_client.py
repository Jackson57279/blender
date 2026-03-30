# SPDX-FileCopyrightText: 2025 Blender Foundation
#
# SPDX-License-Identifier: GPL-2.0-or-later

"""
AI Assistant - API Client Module

Handles communication with the OpenRouter API for chat completions.
Provides error handling for authentication, timeouts, network errors, and rate limiting.
"""

import json
import os
import urllib.error
import urllib.request
from enum import Enum
from typing import Optional


class APIErrorType(Enum):
    """Enumeration of possible API error types."""
    NONE = "none"
    AUTHENTICATION = "authentication"
    TIMEOUT = "timeout"
    NETWORK = "network"
    RATE_LIMIT = "rate_limit"
    SERVER = "server"
    UNKNOWN = "unknown"


class APIResponse:
    """Represents a response from the OpenRouter API."""

    def __init__(
        self,
        success: bool,
        content: Optional[str] = None,
        error_type: APIErrorType = APIErrorType.NONE,
        error_message: Optional[str] = None,
    ):
        self.success = success
        self.content = content
        self.error_type = error_type
        self.error_message = error_message

    def __repr__(self):
        return f"APIResponse(success={self.success}, error_type={self.error_type.value})"


class OpenRouterClient:
    """
    Client for making requests to the OpenRouter API.

    Features:
    - POST requests to https://openrouter.ai/api/v1/chat/completions
    - Bearer token authentication from OPENROUTER_API_KEY environment variable
    - Configurable timeout (default 30 seconds)
    - Comprehensive error handling for auth, timeout, network, and rate limit errors
    """

    API_URL = "https://openrouter.ai/api/v1/chat/completions"
    DEFAULT_TIMEOUT = 30  # seconds

    def __init__(self, api_key: Optional[str] = None, timeout: int = DEFAULT_TIMEOUT):
        """
        Initialize the API client.

        Args:
            api_key: OpenRouter API key. If None, reads from OPENROUTER_API_KEY env var.
            timeout: Request timeout in seconds (default: 30)
        """
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY", "")
        self.timeout = timeout

    def is_configured(self) -> bool:
        """Check if the API key is configured."""
        return bool(self.api_key)

    def _create_request(
        self, messages: list, model: str, max_tokens: int = 4096
    ) -> urllib.request.Request:
        """
        Create a properly configured request object.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: The model to use for completion
            max_tokens: Maximum tokens to generate

        Returns:
            Configured urllib.request.Request object
        """
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        data = json.dumps(payload).encode("utf-8")

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.api_key}",
            "HTTP-Referer": "https://blender.org",
            "X-Title": "Blender AI Assistant",
        }

        request = urllib.request.Request(
            self.API_URL,
            data=data,
            headers=headers,
            method="POST",
        )

        return request

    def _parse_success_response(self, response_data: dict) -> APIResponse:
        """
        Parse a successful API response.

        Args:
            response_data: Parsed JSON response from API

        Returns:
            APIResponse with extracted content
        """
        try:
            choices = response_data.get("choices", [])
            if not choices:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.UNKNOWN,
                    error_message="No choices in API response",
                )

            message = choices[0].get("message", {})
            content = message.get("content", "")

            if not content:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.UNKNOWN,
                    error_message="Empty content in API response",
                )

            return APIResponse(success=True, content=content)

        except (KeyError, IndexError, AttributeError) as e:
            return APIResponse(
                success=False,
                error_type=APIErrorType.UNKNOWN,
                error_message=f"Failed to parse API response: {str(e)}",
            )

    def _handle_error(self, error: Exception) -> APIResponse:
        """
        Handle various types of errors and return appropriate APIResponse.

        Args:
            error: The exception that was raised

        Returns:
            APIResponse with appropriate error type and message
        """
        if isinstance(error, urllib.error.HTTPError):
            # Handle HTTP errors
            if error.code == 401:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.AUTHENTICATION,
                    error_message="Invalid API key. Please check your OPENROUTER_API_KEY.",
                )
            elif error.code == 429:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.RATE_LIMIT,
                    error_message="Rate limit exceeded. Please try again later.",
                )
            elif error.code >= 500:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.SERVER,
                    error_message=f"OpenRouter server error ({error.code}). Please try again later.",
                )
            else:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.UNKNOWN,
                    error_message=f"HTTP error {error.code}: {error.reason}",
                )

        elif isinstance(error, urllib.error.URLError):
            # Handle URL/network errors
            error_str = str(error.reason).lower()
            if "timeout" in error_str or "timed out" in error_str:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.TIMEOUT,
                    error_message=f"Request timed out after {self.timeout} seconds.",
                )
            elif "name" in error_str and "resolve" in error_str:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.NETWORK,
                    error_message="Could not resolve OpenRouter API hostname. Check your network connection.",
                )
            elif "connection" in error_str:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.NETWORK,
                    error_message="Could not connect to OpenRouter API. Check your network connection.",
                )
            else:
                return APIResponse(
                    success=False,
                    error_type=APIErrorType.NETWORK,
                    error_message=f"Network error: {str(error.reason)}",
                )

        elif isinstance(error, TimeoutError):
            return APIResponse(
                success=False,
                error_type=APIErrorType.TIMEOUT,
                error_message=f"Request timed out after {self.timeout} seconds.",
            )

        else:
            # Unknown error
            return APIResponse(
                success=False,
                error_type=APIErrorType.UNKNOWN,
                error_message=f"Unexpected error: {str(error)}",
            )

    def chat_completion(
        self, messages: list, model: str, max_tokens: int = 4096
    ) -> APIResponse:
        """
        Send a chat completion request to OpenRouter.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            model: The model to use for completion (e.g., 'anthropic/claude-sonnet-4.6')
            max_tokens: Maximum tokens to generate (default: 4096)

        Returns:
            APIResponse object containing success status, content, and error details
        """
        if not self.is_configured():
            return APIResponse(
                success=False,
                error_type=APIErrorType.AUTHENTICATION,
                error_message="API key not configured. Set OPENROUTER_API_KEY environment variable.",
            )

        try:
            request = self._create_request(messages, model, max_tokens)

            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                response_data = json.loads(response.read().decode("utf-8"))
                return self._parse_success_response(response_data)

        except urllib.error.HTTPError as e:
            return self._handle_error(e)

        except urllib.error.URLError as e:
            return self._handle_error(e)

        except TimeoutError as e:
            return self._handle_error(e)

        except json.JSONDecodeError as e:
            return APIResponse(
                success=False,
                error_type=APIErrorType.UNKNOWN,
                error_message=f"Failed to parse API response: {str(e)}",
            )

        except Exception as e:
            return self._handle_error(e)


def create_client(api_key: Optional[str] = None, timeout: int = 30) -> OpenRouterClient:
    """
    Factory function to create an OpenRouterClient instance.

    Args:
        api_key: Optional API key. If None, reads from OPENROUTER_API_KEY env var.
        timeout: Request timeout in seconds (default: 30)

    Returns:
        Configured OpenRouterClient instance
    """
    return OpenRouterClient(api_key=api_key, timeout=timeout)


def get_user_friendly_error_message(response: APIResponse) -> str:
    """
    Get a user-friendly error message from an APIResponse.

    Args:
        response: The APIResponse to convert to a message

    Returns:
        A user-friendly string suitable for display in the UI
    """
    if response.success:
        return "Success"

    prefix = "Unknown Error"
    if response.error_type == APIErrorType.AUTHENTICATION:
        prefix = "Authentication Error"
    elif response.error_type == APIErrorType.TIMEOUT:
        prefix = "Timeout Error"
    elif response.error_type == APIErrorType.NETWORK:
        prefix = "Network Error"
    elif response.error_type == APIErrorType.RATE_LIMIT:
        prefix = "Rate Limit"
    elif response.error_type == APIErrorType.SERVER:
        prefix = "Server Error"

    if response.error_message:
        return f"{prefix}: {response.error_message}"
    return f"{prefix}: An unknown error occurred"
