"""
Tests for ServiceNow problem management tools.
"""

import json
import unittest
from unittest.mock import Mock, patch

import requests

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.record_tools import (
    CreateProblemParams,
    ProblemResponse,
    create_problem,
    _resolve_user_id,
)
from servicenow_mcp.utils.config import ServerConfig
import os


class TestRecordTools(unittest.TestCase):
    """Test cases for problem management tools."""

    def setUp(self):
        """Set up test fixtures."""
        instance_url = os.environ.get("SNOW_INSTANCE_URL")
        api_url = f"{instance_url}/api/now"
        self.config = ServerConfig(
            instance_url=instance_url,
            api_url=api_url,
            auth={"type": "basic", "username": os.environ.get("SNOW_INSTANCE_UNAME"), "password": os.environ.get("SNOW_INSTANCE_PWD")},
            timeout=30,
        )
        self.auth_manager = Mock(spec=AuthManager)
        self.auth_manager.get_headers.return_value = {"Authorization": "Basic test"}

    @patch("servicenow_mcp.tools.record_tools.requests.post")
    def test_create_problem_success(self, mock_post):
        """Test successful problem creation."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": {
                "sys_id": "test_problem_id",
                "number": "PRB0001234",
                "short_description": "Test problem",
                "state": "1",
            }
        }
        mock_post.return_value = mock_response

        # Test parameters
        params = CreateProblemParams(
            short_description="Test problem",
            urgency="2",
            impact="1",
        )

        # Call function
        result = create_problem(self.config, self.auth_manager, params)

        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Problem created successfully")
        self.assertEqual(result.problem_id, "test_problem_id")
        self.assertEqual(result.problem_number, "PRB0001234")

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.config.api_url}/table/problem")
        
        expected_data = {
            "short_description": "Test problem",
            "urgency": "2",
            "impact": "1",
        }
        self.assertEqual(call_args[1]["json"], expected_data)

    @patch("servicenow_mcp.tools.record_tools.requests.post")
    def test_create_problem_with_defaults(self, mock_post):
        """Test problem creation with default urgency and impact."""
        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": {
                "sys_id": "test_problem_id",
                "number": "PRB0001235",
            }
        }
        mock_post.return_value = mock_response

        # Test parameters with only required field
        params = CreateProblemParams(
            short_description="Problem with defaults",
        )

        # Call function
        result = create_problem(self.config, self.auth_manager, params)

        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Problem created successfully")
        
        # Verify API call uses defaults
        call_args = mock_post.call_args
        expected_data = {
            "short_description": "Problem with defaults",
            "urgency": "3",  # Default value
            "impact": "3",   # Default value
        }
        self.assertEqual(call_args[1]["json"], expected_data)

    @patch("servicenow_mcp.tools.record_tools.requests.post")
    def test_create_problem_with_user_assignment(self, mock_post):
        """Test problem creation with user assignment."""
        # Mock problem creation response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": {
                "sys_id": "test_problem_id",
                "number": "PRB0001236",
            }
        }
        mock_post.return_value = mock_response

        # Mock user resolution
        with patch("servicenow_mcp.tools.record_tools._resolve_user_id") as mock_resolve:
            mock_resolve.return_value = "user_sys_id"

            params = CreateProblemParams(
                short_description="Problem assigned to user",
                assigned_to="john.doe",
                urgency="1",
                impact="2",
            )

            result = create_problem(self.config, self.auth_manager, params)

            self.assertTrue(result.success)
            mock_resolve.assert_called_once_with(self.config, self.auth_manager, "john.doe")
            
            # Verify assigned_to is included in API call
            call_args = mock_post.call_args
            expected_data = {
                "short_description": "Problem assigned to user",
                "urgency": "1",
                "impact": "2",
                "assigned_to": "user_sys_id",
            }
            self.assertEqual(call_args[1]["json"], expected_data)

    @patch("servicenow_mcp.tools.record_tools.requests.post")
    def test_create_problem_user_not_found(self, mock_post):
        """Test problem creation when assigned user is not found."""
        with patch("servicenow_mcp.tools.record_tools._resolve_user_id") as mock_resolve:
            mock_resolve.return_value = None

            params = CreateProblemParams(
                short_description="Problem with invalid user",
                assigned_to="invalid_user",
            )

            result = create_problem(self.config, self.auth_manager, params)

            self.assertFalse(result.success)
            self.assertIn("Could not resolve user", result.message)
            self.assertIn("invalid_user", result.message)
            
            # Verify API was not called
            mock_post.assert_not_called()

    @patch("servicenow_mcp.tools.record_tools.requests.post")
    def test_create_problem_api_error(self, mock_post):
        """Test problem creation with API error."""
        mock_post.side_effect = requests.RequestException("Connection error")

        params = CreateProblemParams(
            short_description="Problem that will fail",
        )

        result = create_problem(self.config, self.auth_manager, params)

        self.assertFalse(result.success)
        self.assertIn("Failed to create problem", result.message)
        self.assertIn("Connection error", result.message)

    @patch("servicenow_mcp.tools.record_tools.requests.post")
    def test_create_problem_http_error(self, mock_post):
        """Test problem creation with HTTP error."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("400 Bad Request")
        mock_post.return_value = mock_response

        params = CreateProblemParams(
            short_description="Problem with HTTP error",
        )

        result = create_problem(self.config, self.auth_manager, params)

        self.assertFalse(result.success)
        self.assertIn("Failed to create problem", result.message)

    @patch("servicenow_mcp.tools.record_tools.requests.get")
    def test_resolve_user_id_by_username(self, mock_get):
        """Test user ID resolution by username."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": [{"sys_id": "user_sys_id_123"}]
        }
        mock_get.return_value = mock_response

        result = _resolve_user_id(self.config, self.auth_manager, "john.doe")

        self.assertEqual(result, "user_sys_id_123")
        
        # Verify it tried username first
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], f"{self.config.api_url}/table/sys_user")
        self.assertIn("user_name=john.doe", call_args[1]["params"]["sysparm_query"])
        self.assertEqual(call_args[1]["params"]["sysparm_limit"], "1")

    @patch("servicenow_mcp.tools.record_tools.requests.get")
    def test_resolve_user_id_by_email_fallback(self, mock_get):
        """Test user ID resolution falls back to email when username fails."""
        # Mock two calls - first for username (empty), second for email (success)
        mock_response_empty = Mock()
        mock_response_empty.raise_for_status.return_value = None
        mock_response_empty.json.return_value = {"result": []}
        
        mock_response_success = Mock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {
            "result": [{"sys_id": "user_sys_id_456"}]
        }
        
        mock_get.side_effect = [mock_response_empty, mock_response_success]

        result = _resolve_user_id(self.config, self.auth_manager, "john.doe@company.com")

        self.assertEqual(result, "user_sys_id_456")
        
        # Verify it made two calls
        self.assertEqual(mock_get.call_count, 2)
        
        # Verify second call was for email
        second_call_args = mock_get.call_args_list[1]
        self.assertIn("email=john.doe@company.com", second_call_args[1]["params"]["sysparm_query"])

    def test_resolve_user_id_sys_id_passthrough(self):
        """Test user ID resolution passes through sys_id unchanged."""
        sys_id = "12345678901234567890123456789012"  # 32 numeric characters
        result = _resolve_user_id(self.config, self.auth_manager, sys_id)
        self.assertEqual(result, sys_id)

    @patch("servicenow_mcp.tools.record_tools.requests.get")
    def test_resolve_user_id_not_found(self, mock_get):
        """Test user ID resolution when user is not found."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {"result": []}
        mock_get.return_value = mock_response

        # Mock both username and email lookups returning empty
        mock_get.side_effect = [mock_response, mock_response]

        result = _resolve_user_id(self.config, self.auth_manager, "nonexistent.user")

        self.assertIsNone(result)
        # Verify it tried both username and email
        self.assertEqual(mock_get.call_count, 2)

    @patch("servicenow_mcp.tools.record_tools.requests.get")
    def test_resolve_user_id_api_error(self, mock_get):
        """Test user ID resolution with API error."""
        mock_get.side_effect = requests.RequestException("API Error")

        result = _resolve_user_id(self.config, self.auth_manager, "john.doe")

        self.assertIsNone(result)

    @patch("servicenow_mcp.tools.record_tools.requests.get")
    def test_resolve_user_id_partial_api_error(self, mock_get):
        """Test user ID resolution with API error on first call but success on second."""
        # First call fails, second call succeeds
        mock_response_success = Mock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {
            "result": [{"sys_id": "user_sys_id_789"}]
        }
        
        mock_get.side_effect = [requests.RequestException("First call error"), mock_response_success]

        result = _resolve_user_id(self.config, self.auth_manager, "john.doe@company.com")

        self.assertEqual(result, "user_sys_id_789")
        # Verify it made two calls despite first one failing
        self.assertEqual(mock_get.call_count, 2)

    def test_create_problem_params_validation(self):
        """Test CreateProblemParams validation."""
        # Test valid parameters
        params = CreateProblemParams(
            short_description="Valid problem description",
            urgency="1",
            impact="2",
            assigned_to="john.doe"
        )
        self.assertEqual(params.short_description, "Valid problem description")
        self.assertEqual(params.urgency, "1")
        self.assertEqual(params.impact, "2")
        self.assertEqual(params.assigned_to, "john.doe")
        
        # Test default values
        params_defaults = CreateProblemParams(
            short_description="Problem with defaults"
        )
        self.assertEqual(params_defaults.urgency, "3")
        self.assertEqual(params_defaults.impact, "3")
        self.assertIsNone(params_defaults.assigned_to)

    def test_problem_response_creation(self):
        """Test ProblemResponse creation."""
        # Test successful response
        response = ProblemResponse(
            success=True,
            message="Problem created",
            problem_id="prob123",
            problem_number="PRB0001000"
        )
        self.assertTrue(response.success)
        self.assertEqual(response.message, "Problem created")
        self.assertEqual(response.problem_id, "prob123")
        self.assertEqual(response.problem_number, "PRB0001000")
        
        # Test error response
        error_response = ProblemResponse(
            success=False,
            message="Error creating problem"
        )
        self.assertFalse(error_response.success)
        self.assertEqual(error_response.message, "Error creating problem")
        self.assertIsNone(error_response.problem_id)
        self.assertIsNone(error_response.problem_number)


if __name__ == "__main__":
    unittest.main()
