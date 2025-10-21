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
from servicenow_mcp.utils.resolvers import resolve_user_id, resolve_catalog_item_id

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

class ListItemRequestsParams(BaseModel):
    """Parameters for listing item requests."""

    limit: int = Field(10, description="Maximum number of item requests to return")
    offset: int = Field(0, description="Offset for pagination") 
    requested_for: Optional[str] = Field(None, description="Filter by assigned user. You can input either sys_id or name of user")
    cat_item: Optional[str] = Field(None, description="Filter by catalog item. You can input either sys_id or name of catalog item")
    number: Optional[str] = Field(None, description="Filter by item number")
    short_description: Optional[str] = Field(None, description="Filter by short description of the item request")
    request_id: Optional[str] = Field(None, description="Filter by parent request sys_id")

class OrderCatalogItemParams(BaseModel): 
    sys_id: str = Field(..., description="The sys_id of the order item to be ordered")
    number: str = Field(..., description="Requested item number identifier")
    requested_for: str = Field(..., description="The user for which the item is being requested. You can input either sys_id or name of user")
    quantity: str = Field(..., description="The quantity of the item to be requested")
    short_description: str = Field(..., description="The short description of the item request")

class ChangeRequestItemPriorityParams(BaseModel): 
    """Parameters for changing the priority of a change request."""

    change_request_sys_id: str = Field(..., description="The sys_id of the change request to be changed")
    impact: str = Field(..., description="The impact of the change request item")
    urgency: str = Field(..., description="The urgency of the change request item")

class RequestAndCatalogItemResponse(BaseModel):
    """Response from create request.""" 

    success: bool = Field(..., description="Whether the operation was successful") 
    message: str = Field(..., description="Message describing the result")
    sys_id: Optional[str] = Field(None, description="ID of the item request")
    number: Optional[str] = Field(None, description="Number of the affected request")

def change_request_item_priority(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ChangeRequestItemPriorityParams,
) -> RequestAndCatalogItemResponse:
    """
    Change the priority of a requested item.
    """
    api_url = f"{config.api_url}/table/sc_request/{params.change_request_sys_id}"
    data = {    
        "impact": params.impact,
        "urgency": params.urgency
    }
    try:
        # Get requested item record and update priority too 
        requested_item_url = f"{config.api_url}/table/sc_req_item"
        requested_item_resp = requests.get(
            requested_item_url, 
            headers=auth_manager.get_headers(), 
            timeout=config.timeout,
            params={"sysparm_query": f"request={params.change_request_sys_id}", "sysparm_fields": "sys_id"}
        )
        requested_item_resp.raise_for_status()
        requested_item_sys_id = requested_item_resp.json().get("result", [])[0].get("sys_id")

        # Update priority of requested item
        requested_item_url = f"{config.api_url}/table/sc_req_item/{requested_item_sys_id}"
        requested_item_resp = requests.patch(
            requested_item_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        requested_item_resp.raise_for_status()

        response = requests.patch(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        result = response.json().get("result", {})
        return RequestAndCatalogItemResponse(success=True, message="Change request item priority changed successfully", sys_id=result.get("sys_id"))
    except requests.RequestException as e:
        logger.error(f"Failed to change request item priority: {e}")
        return RequestAndCatalogItemResponse(success=False, message=f"Failed to change request item priority: {str(e)}") 

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
        user_id = resolve_user_id(config, auth_manager, params.requested_for)
        if user_id:
            query_parts.append(f"requested_for={user_id}")
        else:
            # Try direct match if it's already a sys_id
            query_parts.append(f"requested_for={params.requested_for}")

    if params.cat_item:
        # Resolve catalog item if name is provided
        catalog_item_id = resolve_catalog_item_id(config, auth_manager, params.cat_item)
        if catalog_item_id:
            query_parts.append(f"cat_item={catalog_item_id}")
        else:
            # Try direct match if it's already a sys_id
            query_parts.append(f"cat_item={params.cat_item}")

    if params.number:
        query_parts.append(f"number={params.number}")
    if params.short_description:
        query_parts.append(f"short_descriptionLIKE{params.short_description}") 
    if params.request_id:
        query_parts.append(f"request={params.request_id}")

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
        user_id = resolve_user_id(config, auth_manager, params.requested_for)
        if user_id:
            request_body["requested_for"] = user_id
        else:
            return RequestAndCatalogItemResponse(
                success=False,
                message=f"Could not resolve user: {params.requested_for}",
            )
    if params.cat_item:
        # Resolve catalog item if name is provided
        catalog_item_id = resolve_catalog_item_id(config, auth_manager, params.cat_item)
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
