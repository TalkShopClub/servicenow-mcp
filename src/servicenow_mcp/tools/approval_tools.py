"""
Approval tools for the ServiceNow MCP server.

This module provides tools for approving and rejecting change requests in ServiceNow.
"""

import logging
from typing import Optional, Dict

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig
from servicenow_mcp.utils.resolvers import resolve_user_id, resolve_asset_id

logger = logging.getLogger(__name__) 

class ApproveChangeRequestParams(BaseModel):
    """Parameters for approving a change request."""

    change_request_sys_id: str = Field(..., description="The sys_id of the request to be approved")
    approval_comments: Optional[str] = Field(None, description="Comments for the approval")

class RejectChangeRequestParams(BaseModel):
    """Parameters for rejecting a change request."""

    change_request_sys_id: str = Field(..., description="The sys_id of the change request to be rejected")
    rejection_reason: str = Field(..., description="Reason for the rejection")

class GetApprovalRecordParams(BaseModel):
    """Parameters for getting an approval record."""

    change_request_sys_id: str = Field(..., description="The sys_id of the change request for which to get the approval record") 

