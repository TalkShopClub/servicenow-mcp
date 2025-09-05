"""
Problem management tools for the ServiceNow MCP server.

This module provides tools for creating and managing problems in ServiceNow.
"""

import logging
from typing import Optional, Dict

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class CreateProblemParams(BaseModel):
    """Parameters for creating a problem."""

    short_description: str = Field(..., description="Short description of the problem")
    urgency: Optional[str] = Field("3", description="Urgency level (1=High, 2=Medium, 3=Low)")
    impact: Optional[str] = Field("3", description="Impact level (1=High, 2=Medium, 3=Low)")
    assigned_to: Optional[str] = Field(None, description="User assigned to the problem (user sys_id or username)")
    fields: Optional[Dict[str, str]] = Field(None, description="Dictionary of other field names and corresponding values to set for the POST request. Example: {'priority': '1'}")


class ProblemResponse(BaseModel):
    """Response from problem operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    problem_id: Optional[str] = Field(None, description="ID of the problem")
    problem_number: Optional[str] = Field(None, description="Number of the problem")


def create_problem(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateProblemParams,
) -> ProblemResponse:
    """
    Create a new problem in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for creating the problem.

    Returns:
        Response with the created problem details.
    """
    api_url = f"{config.api_url}/table/problem"

    # Build request data
    data = {
        "short_description": params.short_description,
        "urgency": params.urgency,
        "impact": params.impact,
    }

    if params.assigned_to:
        # Resolve user if username is provided
        user_id = _resolve_user_id(config, auth_manager, params.assigned_to)
        if user_id:
            data["assigned_to"] = user_id
        else:
            return ProblemResponse(
                success=False,
                message=f"Could not resolve user: {params.assigned_to}",
            )
        
    if params.fields:
        for field, value in params.fields.items():
            data[field] = value

    # Make request
    try:
        response = requests.post(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            auth=(auth_manager.config.basic.username, auth_manager.config.basic.password),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return ProblemResponse(
            success=True,
            message="Problem created successfully. The sys_id of the problem is: " + result.get("sys_id"),
            problem_id=result.get("sys_id"),
            problem_number=result.get("number"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to create problem: {e}")
        return ProblemResponse(
            success=False,
            message=f"Failed to create problem: {str(e)}",
        )





def _resolve_user_id(
    config: ServerConfig,
    auth_manager: AuthManager,
    user_identifier: str,
) -> Optional[str]:
    """
    Resolve a user identifier (username, email, or sys_id) to a sys_id.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        user_identifier: User identifier (username, email, or sys_id).

    Returns:
        User sys_id if found, None otherwise.
    """
    # If it looks like a sys_id, return as is
    if len(user_identifier) == 32 and all(c in "0123456789abcdefABCDEF" for c in user_identifier):
        return user_identifier

    api_url = f"{config.api_url}/table/sys_user"
    
    # Try username first, then email
    for field in ["user_name", "email"]:
        query_params = {
            "sysparm_query": f"{field}={user_identifier}",
            "sysparm_limit": "1",
        }

        try:
            response = requests.get(
                api_url,
                params=query_params,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            response.raise_for_status()

            result = response.json().get("result", [])
            if result:
                return result[0].get("sys_id")

        except requests.RequestException as e:
            logger.error(f"Failed to resolve user ID for {field}={user_identifier}: {e}")
            continue

    return None
