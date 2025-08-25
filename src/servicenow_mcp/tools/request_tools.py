"""
Request tools for the ServiceNow MCP server.

This module provides tools for making requests to the ServiceNow API.
"""

# TODO: Add support for ordering catalog item via sn_sc api 

import logging
from typing import List, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig 

logger = logging.getLogger(__name__)

class CreateItemRequestParams(BaseModel):
    """Parameters for creating an item request. This is used to create a request for a specific item. You can link multiple item requests to a single request object."""

    number: Optional[str] = Field(None, description="Requested item number identifier")
    cat_item: str = Field(..., description="The item name or to be requested")
    requested_for: str = Field(..., description="The user for which the item is being requested. You can input either sys_id or name of user")
    quantity: str = Field("1", description="The quantity of the item to be requested")
    request: Optional[str] = Field(None, description="The sys_id of the request object this item request belongs to")
    state: str = Field(..., description="The state number of the item request. 1 = New, 2 = In Progress, 3 = Resolved, 6 = Resolved, 7 = Closed, 8 = Cancelled")
    short_description: str = Field(..., description="The short description of the item request")

class CreateRequestParams(BaseModel): # TODO: Remove this. Use OrderParams instead.
    """Parameters for creating a request. This is used to create a request for a specific user. You can link multiple item requests to a single request object."""

    requested_for: str = Field(..., description="The user for which the item is being requested. You can input either sys_id or name of user")
    state: str = Field(..., description="The state number of the item request. 1 = New, 2 = In Progress, 3 = Resolved, 6 = Resolved, 7 = Closed, 8 = Cancelled")
    approval: str = Field("not requested", description="The approval status of the item request. not_requested = Not requested, requested = Requested, approved = Approved, rejected = Rejected")

class ListItemRequestsParams(BaseModel):
    """Parameters for listing item requests."""

    limit: int = Field(10, description="Maximum number of item requests to return")
    offset: int = Field(0, description="Offset for pagination") 
    requested_for: Optional[str] = Field(None, description="Filter by assigned user. You can input either sys_id or name of user")
    cat_item: Optional[str] = Field(None, description="Filter by catalog item. You can input either sys_id or name of catalog item")
    number: Optional[str] = Field(None, description="Filter by item number")
    short_description: Optional[str] = Field(None, description="Filter by short description of the item request")

class OrderCatalogItemParams(BaseModel): 
    sys_id: str = Field(..., description="The sys_id of the order item to be ordered")
    number: str = Field(..., description="Requested item number identifier")
    requested_for: str = Field(..., description="The user for which the item is being requested. You can input either sys_id or name of user")
    quantity: str = Field(..., description="The quantity of the item to be requested")
    short_description: str = Field(..., description="The short description of the item request")


class RequestAndCatalogItemResponse(BaseModel):
    """Response from create request.""" 

    success: bool = Field(..., description="Whether the operation was successful") 
    message: str = Field(..., description="Message describing the result")
    sys_id: Optional[str] = Field(None, description="ID of the item request")
    number: Optional[str] = Field(None, description="Number of the affected request")

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
    if len(user_identifier) == 32 and all(c in "0123456789abcdef" for c in user_identifier):
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

def _resolve_catalog_item_id(
    config: ServerConfig,
    auth_manager: AuthManager,
    catalog_item_identifier: str,
) -> Optional[str]:
    """
    Resolve a catalog item identifier (name or sys_id) to a sys_id. 
    """ 
    # If it looks like a sys_id, return as is
    if len(catalog_item_identifier) == 32 and all(c in "0123456789abcdef" for c in catalog_item_identifier):
        return catalog_item_identifier
    
    api_url = f"{config.api_url}/table/sc_cat_item"
    
    # Try name first, then sys_id, then short description
    for field in ["name", "sys_id", "short_description"]:
        query_params = {
            "sysparm_query": f"{field}={catalog_item_identifier}" if field != "short_description" else f"{field}LIKE{catalog_item_identifier}",
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
            logger.error(f"Failed to resolve catalog item ID for {field}={catalog_item_identifier}: {e}")
            continue
                
    return None

def list_item_requests(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListItemRequestsParams,
) -> dict:
    """
    List item requests from ServiceNow.
    """
    # Build query parameters
    api_url = f"{config.api_url}/table/sc_req_item"
    query_params = {
        "sysparm_limit": str(params.limit),
        "sysparm_offset": str(params.offset),
        "sysparm_display_value": "true",
    }

    # Build query
    query_parts = []
    if params.requested_for:
        # Resolve user if username is provided
        user_id = _resolve_user_id(config, auth_manager, params.requested_for)
        if user_id:
            query_parts.append(f"requested_for={user_id}")
        else:
            # Try direct match if it's already a sys_id
            query_parts.append(f"requested_for={params.requested_for}")

    if params.cat_item:
        # Resolve catalog item if name is provided
        catalog_item_id = _resolve_catalog_item_id(config, auth_manager, params.cat_item)
        if catalog_item_id:
            query_parts.append(f"cat_item={catalog_item_id}")
        else:
            # Try direct match if it's already a sys_id
            query_parts.append(f"cat_item={params.cat_item}")

    if params.number:
        query_parts.append(f"number={params.number}")
    if params.short_description:
        query_parts.append(f"short_descriptionLIKE{params.short_description}") 

    if query_parts:
        query_params["sysparm_query"] = "^".join(query_parts)

    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        ) 

        response.raise_for_status()
        
        result = response.json().get("result", [])
        
        return {
            "success": True,
            "message": f"Found {len(result)} item requests",
            "item_requests": result,
            "count": len(result),
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list item requests: {e}")
        return {
            "success": False,
            "message": f"Failed to list item requests: {str(e)}",
        } 
    
def create_item_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateItemRequestParams,
) -> RequestAndCatalogItemResponse:
    """
    Create an item request in ServiceNow.
    """
    api_url = f"{config.api_url}/table/sc_req_item"

    # Build request body
    request_body = {
        "state": params.state,
        "short_description": params.short_description,
        "quantity": params.quantity
    }

    if params.number: 
        request_body["number"] = params.number
    if params.requested_for:
        # Resolve user if username is provided
        user_id = _resolve_user_id(config, auth_manager, params.requested_for)
        if user_id:
            request_body["requested_for"] = user_id
        else:
            return RequestAndCatalogItemResponse(
                success=False,
                message=f"Could not resolve user: {params.requested_for}",
            )
    if params.cat_item:
        # Resolve catalog item if name is provided
        catalog_item_id = _resolve_catalog_item_id(config, auth_manager, params.cat_item)
        if catalog_item_id:
            request_body["cat_item"] = catalog_item_id
        else:
            return RequestAndCatalogItemResponse(
                success=False,
                message=f"Could not resolve catalog item: {params.cat_item}",
            )
    
    # Make request
    try:
        response = requests.post(
            api_url,
            json=request_body,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        return RequestAndCatalogItemResponse(
            success=True,
            message="Item request created successfully",
            sys_id=result.get("sys_id"),
            number=result.get("number"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to create item request: {e}")
        return RequestAndCatalogItemResponse(
            success=False,
            message=f"Failed to create item request: {str(e)}",
        )
    
def create_request(
        
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateRequestParams,
) -> RequestAndCatalogItemResponse:
    """
    Create a request in ServiceNow.
    """
    api_url = f"{config.api_url}/table/sc_request"

    # Build request body 
    request_body = {
        "state": params.state,
        "approval": params.approval,
    }

    if params.requested_for:
        # Resolve user if username is provided
        user_id = _resolve_user_id(config, auth_manager, params.requested_for)
        if user_id:
            request_body["requested_for"] = user_id
        else:
            return RequestAndCatalogItemResponse(
                success=False,
                message=f"Could not resolve user: {params.requested_for}",
            )
    
    # Make request 
    try:
        response = requests.post(
            api_url,
            json=request_body,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        result = response.json().get("result", {})

        return RequestAndCatalogItemResponse(
            success=True,
            message="Request created successfully",
            sys_id=result.get("sys_id")
        )

    except requests.RequestException as e:
        logger.error(f"Failed to create request: {e}")
        return RequestAndCatalogItemResponse(
            success=False,
            message=f"Failed to create request: {str(e)}",
        )
