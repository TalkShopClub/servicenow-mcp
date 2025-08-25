"""
Tests for ServiceNow request management tools.
"""

import json
import unittest
from unittest.mock import Mock, patch

import requests
import os

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.request_tools import (
    CreateRequestParams,
    CreateItemRequestParams,
    ListItemRequestsParams,
    RequestAndCatalogItemResponse,
    create_request,
    create_item_request,
    list_item_requests,
    _resolve_user_id,
    _resolve_catalog_item_id,
)
from servicenow_mcp.utils.config import ServerConfig


class TestRequestTools(unittest.TestCase):
    """Test cases for request management tools."""

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

    @patch("servicenow_mcp.tools.request_tools._resolve_user_id")
    @patch("servicenow_mcp.tools.request_tools.requests.post")
    def test_create_request_success(self, mock_post, mock_resolve_user):
        """Test successful request creation."""
        # Mock user resolution
        mock_resolve_user.return_value = "resolved_user_id"

        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": {
                "sys_id": "test_request_id",
                "number": "REQ0001001",
                "state": "1",
                "requested_for": "resolved_user_id"
            }
        }
        mock_post.return_value = mock_response

        # Test parameters
        params = CreateRequestParams(
            requested_for="admin",
            state="1",
            approval="not requested"
        )

        # Call function
        result = create_request(self.config, self.auth_manager, params)

        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Request created successfully")
        self.assertEqual(result.sys_id, "test_request_id")

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.config.api_url}/table/sc_request")
        
        expected_data = {
            "requested_for": "resolved_user_id",
            "state": "1",
            "approval": "not requested",
        }
        self.assertEqual(call_args[1]["json"], expected_data)

    @patch("servicenow_mcp.tools.request_tools._resolve_user_id")
    @patch("servicenow_mcp.tools.request_tools.requests.post")
    def test_create_request_user_not_found(self, mock_post, mock_resolve_user):
        """Test request creation when requested user is not found."""
        mock_resolve_user.return_value = None

        params = CreateRequestParams(
            requested_for="invalid_user",
            state="1",
            approval="not requested"
        )

        result = create_request(self.config, self.auth_manager, params)

        self.assertFalse(result.success)
        self.assertIn("Could not resolve user", result.message)
        mock_post.assert_not_called()

    @patch("servicenow_mcp.tools.request_tools._resolve_user_id")
    @patch("servicenow_mcp.tools.request_tools.requests.post")
    def test_create_request_api_error(self, mock_post, mock_resolve_user):
        """Test request creation with API error."""
        # Mock successful user resolution
        mock_resolve_user.return_value = "resolved_user_id"
        
        # Mock API error
        mock_post.side_effect = requests.RequestException("API Error")

        params = CreateRequestParams(
            requested_for="admin",
            state="1"
        )

        result = create_request(self.config, self.auth_manager, params)

        self.assertFalse(result.success)
        self.assertIn("Failed to create request", result.message)

    @patch("servicenow_mcp.tools.request_tools._resolve_user_id")
    @patch("servicenow_mcp.tools.request_tools._resolve_catalog_item_id")
    @patch("servicenow_mcp.tools.request_tools.requests.post")
    def test_create_item_request_success(self, mock_post, mock_resolve_item, mock_resolve_user):
        """Test successful item request creation."""
        # Mock resolutions
        mock_resolve_user.return_value = "resolved_user_id"
        mock_resolve_item.return_value = "resolved_catalog_item_id"

        # Mock response
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": {
                "sys_id": "test_item_request_id",
                "number": "RITM0001001",
                "cat_item": "resolved_catalog_item_id",
                "short_description": "Apple Watch Request - Demo",
                "quantity": "1"
            }
        }
        mock_post.return_value = mock_response

        # Test parameters
        params = CreateItemRequestParams(
            cat_item="Apple Watch",
            short_description="Apple Watch Request - Demo",
            requested_for="admin",
            quantity="1",
            state="1"
        )

        # Call function
        result = create_item_request(self.config, self.auth_manager, params)

        # Assertions
        self.assertTrue(result.success)
        self.assertEqual(result.message, "Item request created successfully")
        self.assertEqual(result.sys_id, "test_item_request_id")
        self.assertEqual(result.number, "RITM0001001")

        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        self.assertEqual(call_args[0][0], f"{self.config.api_url}/table/sc_req_item")
        
        expected_data = {
            "cat_item": "resolved_catalog_item_id",
            "short_description": "Apple Watch Request - Demo",
            "requested_for": "resolved_user_id",
            "quantity": "1",
            "state": "1",
        }
        self.assertEqual(call_args[1]["json"], expected_data)

    @patch("servicenow_mcp.tools.request_tools._resolve_user_id")
    @patch("servicenow_mcp.tools.request_tools._resolve_catalog_item_id")
    @patch("servicenow_mcp.tools.request_tools.requests.post")
    def test_create_item_request_catalog_item_not_found(self, mock_post, mock_resolve_item, mock_resolve_user):
        """Test item request creation when catalog item is not found."""
        # Mock successful user resolution but failed catalog item resolution
        mock_resolve_user.return_value = "resolved_user_id"
        mock_resolve_item.return_value = None

        params = CreateItemRequestParams(
            cat_item="Invalid Catalog Item",
            short_description="Invalid Item Request",
            requested_for="admin",
            state="1"
        )

        result = create_item_request(self.config, self.auth_manager, params)

        self.assertFalse(result.success)
        self.assertIn("Could not resolve catalog item", result.message)
        mock_post.assert_not_called()

    @patch("servicenow_mcp.tools.request_tools.requests.get")
    def test_resolve_user_id_by_username(self, mock_get):
        """Test user ID resolution by username."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": [{"sys_id": "user_sys_id"}]
        }
        mock_get.return_value = mock_response

        result = _resolve_user_id(self.config, self.auth_manager, "john.doe")

        self.assertEqual(result, "user_sys_id")
        # Verify it tried username first
        call_args = mock_get.call_args
        self.assertIn("user_name=john.doe", call_args[1]["params"]["sysparm_query"])

    @patch("servicenow_mcp.tools.request_tools.requests.get")
    def test_resolve_user_id_by_email_fallback(self, mock_get):
        """Test user ID resolution falls back to email when username fails."""
        # Mock two calls - first for username (empty), second for email (success)
        mock_response_empty = Mock()
        mock_response_empty.raise_for_status.return_value = None
        mock_response_empty.json.return_value = {"result": []}
        
        mock_response_success = Mock()
        mock_response_success.raise_for_status.return_value = None
        mock_response_success.json.return_value = {
            "result": [{"sys_id": "user_sys_id"}]
        }
        
        mock_get.side_effect = [mock_response_empty, mock_response_success]

        result = _resolve_user_id(self.config, self.auth_manager, "john.doe@company.com")

        self.assertEqual(result, "user_sys_id")
        # Verify it made two calls
        self.assertEqual(mock_get.call_count, 2)

    def test_resolve_user_id_sys_id_passthrough(self):
        """Test user ID resolution passes through sys_id unchanged."""
        sys_id = "a1b2c3d4e5f67890123456789012345a"
        result = _resolve_user_id(self.config, self.auth_manager, sys_id)
        self.assertEqual(result, sys_id)

    @patch("servicenow_mcp.tools.request_tools.requests.get")
    def test_resolve_catalog_item_id_by_name(self, mock_get):
        """Test catalog item ID resolution by name."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": [{"sys_id": "catalog_item_sys_id"}]
        }
        mock_get.return_value = mock_response

        result = _resolve_catalog_item_id(self.config, self.auth_manager, "Apple Watch")

        self.assertEqual(result, "catalog_item_sys_id")
        call_args = mock_get.call_args
        self.assertIn("name=Apple Watch", call_args[1]["params"]["sysparm_query"])

    def test_resolve_catalog_item_id_sys_id_passthrough(self):
        """Test catalog item ID resolution passes through sys_id unchanged."""
        sys_id = "a1b2c3d4e5f67890123456789012345a"
        result = _resolve_catalog_item_id(self.config, self.auth_manager, sys_id)
        self.assertEqual(result, sys_id)

    @patch("servicenow_mcp.tools.request_tools.requests.get")
    def test_list_item_requests_basic(self, mock_get):
        """Test basic item request listing."""
        mock_response = Mock()
        mock_response.raise_for_status.return_value = None
        mock_response.json.return_value = {
            "result": [
                {
                    "sys_id": "item_request1",
                    "number": "RITM0001001",
                    "cat_item": "Apple Watch",
                    "short_description": "Apple Watch Request - Demo",
                    "state": "1"
                },
                {
                    "sys_id": "item_request2",
                    "number": "RITM0001002", 
                    "cat_item": "Apple iPad 3",
                    "short_description": "Apple iPad 3 Request - Demo",
                    "state": "1"
                }
            ]
        }
        mock_get.return_value = mock_response

        params = ListItemRequestsParams(limit=15)
        result = list_item_requests(self.config, self.auth_manager, params)

        self.assertTrue(result["success"])
        self.assertEqual(result["count"], 2)
        self.assertEqual(result["message"], "Found 2 item requests")
        self.assertIn("item_requests", result)
        self.assertEqual(len(result["item_requests"]), 2)

        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        self.assertEqual(call_args[0][0], f"{self.config.api_url}/table/sc_req_item")
        self.assertEqual(call_args[1]["params"]["sysparm_limit"], "15")

    def test_create_request_params_validation(self):
        """Test CreateRequestParams validation."""
        # Test valid parameters
        params = CreateRequestParams(
            requested_for="john.doe",
            state="1",
            approval="not requested"
        )
        self.assertEqual(params.requested_for, "john.doe")
        self.assertEqual(params.state, "1")
        self.assertEqual(params.approval, "not requested")

    def test_create_item_request_params_validation(self):
        """Test CreateItemRequestParams validation."""
        # Test valid parameters
        params = CreateItemRequestParams(
            number="RITM0001001",
            cat_item="Apple Watch",
            requested_for="john.doe",
            quantity="1",
            request="parent_request_id",
            state="1",
            short_description="Apple Watch Request"
        )
        self.assertEqual(params.number, "RITM0001001")
        self.assertEqual(params.cat_item, "Apple Watch")
        self.assertEqual(params.requested_for, "john.doe")
        self.assertEqual(params.quantity, "1")
        self.assertEqual(params.request, "parent_request_id")
        self.assertEqual(params.state, "1")
        self.assertEqual(params.short_description, "Apple Watch Request")

    def test_list_item_requests_params_validation(self):
        """Test ListItemRequestsParams validation."""
        # Test valid parameters
        params = ListItemRequestsParams(
            limit=20,
            offset=5,
            requested_for="john.doe",
            cat_item="Apple Watch",
            number="RITM0001001",
            short_description="Apple Watch Request"
        )
        self.assertEqual(params.limit, 20)
        self.assertEqual(params.offset, 5)
        self.assertEqual(params.requested_for, "john.doe")
        self.assertEqual(params.cat_item, "Apple Watch")
        self.assertEqual(params.number, "RITM0001001")
        self.assertEqual(params.short_description, "Apple Watch Request")
        
        # Test default values
        params_defaults = ListItemRequestsParams()
        self.assertEqual(params_defaults.limit, 10)
        self.assertEqual(params_defaults.offset, 0)
        self.assertIsNone(params_defaults.requested_for)
        self.assertIsNone(params_defaults.cat_item)
        self.assertIsNone(params_defaults.number)
        self.assertIsNone(params_defaults.short_description)

    def test_request_and_catalog_item_response_model(self):
        """Test RequestAndCatalogItemResponse model."""
        # Test successful response
        response = RequestAndCatalogItemResponse(
            success=True,
            message="Request created successfully",
            sys_id="test_sys_id",
            number="REQ0001001"
        )
        self.assertTrue(response.success)
        self.assertEqual(response.message, "Request created successfully")
        self.assertEqual(response.sys_id, "test_sys_id")
        self.assertEqual(response.number, "REQ0001001")
        
        # Test error response
        error_response = RequestAndCatalogItemResponse(
            success=False,
            message="Failed to create request"
        )
        self.assertFalse(error_response.success)
        self.assertEqual(error_response.message, "Failed to create request")
        self.assertIsNone(error_response.sys_id)
        self.assertIsNone(error_response.number)


if __name__ == "__main__":
    unittest.main()