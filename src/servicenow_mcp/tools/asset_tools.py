"""
Asset management tools for the ServiceNow MCP server.

This module provides tools for managing assets in ServiceNow including
creating, updating, deleting, and transferring assets between users.
"""

import logging
from typing import List, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig
from servicenow_mcp.utils.resolvers import resolve_user_id, resolve_asset_id

logger = logging.getLogger(__name__)


class CreateAssetParams(BaseModel):
    """Parameters for creating an asset."""

    asset_tag: str = Field(..., description="Unique asset tag identifier")
    display_name: str = Field(..., description="Display name of the asset")
    model: Optional[str] = Field(None, description="Model number or name")
    serial_number: Optional[str] = Field(None, description="Serial number of the asset")
    assigned_to: Optional[str] = Field(None, description="User assigned to the asset (sys_id)")
    location: Optional[str] = Field(None, description="Location of the asset")
    cost: Optional[str] = Field(None, description="Cost of the asset")
    purchase_date: Optional[str] = Field(None, description="Purchase date (YYYY-MM-DD)")
    warranty_expiration: Optional[str] = Field(None, description="Warranty expiration date (YYYY-MM-DD)")
    category: Optional[str] = Field(None, description="Asset category")
    subcategory: Optional[str] = Field(None, description="Asset subcategory")
    manufacturer: Optional[str] = Field(None, description="Manufacturer of the asset")
    model_category: Optional[str] = Field(None, description="Model category sys_id")
    state: Optional[str] = Field("1", description="State of the asset (1=In use, 2=In stock, 3=Retired, etc.)")
    substatus: Optional[str] = Field(None, description="Substatus of the asset")
    comments: Optional[str] = Field(None, description="Comments about the asset")


class UpdateAssetParams(BaseModel):
    """Parameters for updating an asset."""

    asset_id: str = Field(..., description="Asset ID (sys_id) or asset tag")
    display_name: Optional[str] = Field(None, description="Display name of the asset")
    model: Optional[str] = Field(None, description="Model number or name")
    serial_number: Optional[str] = Field(None, description="Serial number of the asset")
    assigned_to: Optional[str] = Field(None, description="User assigned to the asset (sys_id)")
    location: Optional[str] = Field(None, description="Location of the asset")
    cost: Optional[str] = Field(None, description="Cost of the asset")
    purchase_date: Optional[str] = Field(None, description="Purchase date (YYYY-MM-DD)")
    warranty_expiration: Optional[str] = Field(None, description="Warranty expiration date (YYYY-MM-DD)")
    category: Optional[str] = Field(None, description="Asset category")
    subcategory: Optional[str] = Field(None, description="Asset subcategory")
    manufacturer: Optional[str] = Field(None, description="Manufacturer of the asset")
    model_category: Optional[str] = Field(None, description="Model category sys_id")
    state: Optional[str] = Field(None, description="State of the asset (1=In use, 2=In stock, 3=Retired, etc.)")
    substatus: Optional[str] = Field(None, description="Substatus of the asset")
    comments: Optional[str] = Field(None, description="Comments about the asset")


class GetAssetParams(BaseModel):
    """Parameters for getting an asset."""

    asset_id: Optional[str] = Field(None, description="Asset ID (sys_id)")
    asset_tag: Optional[str] = Field(None, description="Asset tag")
    serial_number: Optional[str] = Field(None, description="Serial number")


class ListAssetsParams(BaseModel):
    """Parameters for listing assets."""

    limit: int = Field(100, description="Maximum number of assets to return")
    offset: int = Field(0, description="Offset for pagination")
    assigned_to: Optional[List[str]] = Field(None, description="List of sys_ids or names of users that have been assigned an asset. ")
    location: Optional[str] = Field(None, description="Filter by location")
    name: Optional[str] = Field(None, description="Search for assets by display name using LIKE matching")
    query: Optional[str] = Field(
        None,
        description="Search term that matches against asset tag, display name, serial number, or model",
    )


class DeleteAssetParams(BaseModel):
    """Parameters for deleting an asset."""

    asset_id: str = Field(..., description="Asset ID (sys_id) or asset tag")
    reason: Optional[str] = Field(None, description="Reason for deleting the asset")


class TransferAssetParams(BaseModel):
    """Parameters for transferring an asset to a different user."""

    asset_id: str = Field(..., description="Asset ID (sys_id) or asset tag")
    new_assigned_to: str = Field(..., description="New user to assign the asset to (sys_id)")
    transfer_reason: Optional[str] = Field(None, description="Reason for the transfer")
    comments: Optional[str] = Field(None, description="Additional comments about the transfer")


class SearchAssetsByNameParams(BaseModel):
    """Parameters for searching assets by name."""

    name: str = Field(..., description="Name or partial name to search for using LIKE matching")
    limit: int = Field(10, description="Maximum number of assets to return")
    offset: int = Field(0, description="Offset for pagination")
    exact_match: bool = Field(False, description="Whether to perform exact match instead of LIKE matching")


class AssetResponse(BaseModel):
    """Response from asset operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    asset_id: Optional[str] = Field(None, description="ID of the affected asset")
    asset_tag: Optional[str] = Field(None, description="Asset tag of the affected asset")

class ListHardwareAssetsParams(BaseModel):
    """Parameters for listing hardware assets."""
    
    limit: int = Field(10, description="Maximum number of assets to return")
    offset: int = Field(0, description="Offset for pagination")
    assigned_to: Optional[str] = Field(None, description="Filter by assigned user (sys_id)")
    name: Optional[str] = Field(None, description="Search for hardware assets by display name using LIKE matching")
    query: Optional[str] = Field(
        None,
        description="Search term that matches against asset tag, display name, serial number, or model",
    )

def list_hardware_assets(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListHardwareAssetsParams,
) -> dict:
    """
    List hardware assets from ServiceNow.
    """
    # Build query parameters
    api_url = f"{config.api_url}/table/alm_hardware"
    query_params = {
        "sysparm_limit": str(params.limit),
        "sysparm_offset": str(params.offset),
        "sysparm_display_value": "true",
    }

    # Build query
    query_parts = []
    if params.assigned_to:
        # Resolve user if username is provided
        user_id = resolve_user_id(config, auth_manager, params.assigned_to)
        if user_id:
            query_parts.append(f"assigned_to={user_id}")
        else:
            # Try direct match if it's already a sys_id
            query_parts.append(f"assigned_to={params.assigned_to}")
    if params.name:
        # Search by display name using LIKE matching
        query_parts.append(f"display_nameLIKE{params.name}")
    if params.query:
        query_parts.append(f"^asset_tagLIKE{params.query}^ORdisplay_nameLIKE{params.query}^ORserial_numberLIKE{params.query}^ORmodelLIKE{params.query}")
    
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
            "message": f"Found {len(result)} hardware assets",
            "hardware_assets": result,
            "count": len(result),
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to list hardware assets: {e}")
        return {
            "success": False,
            "message": f"Failed to list hardware assets: {str(e)}",
        }

def create_asset(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateAssetParams,
) -> AssetResponse:
    """
    Create a new asset in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for creating the asset.

    Returns:
        Response with the created asset details.
    """
    api_url = f"{config.api_url}/table/alm_asset"

    # Build request data
    data = {
        "asset_tag": params.asset_tag,
        "display_name": params.display_name,
    }

    if params.model:
        data["model"] = params.model
    if params.serial_number:
        data["serial_number"] = params.serial_number
    if params.assigned_to:
        # Resolve user if username is provided
        user_id = resolve_user_id(config, auth_manager, params.assigned_to)
        if user_id:
            data["assigned_to"] = user_id
        else:
            return AssetResponse(
                success=False,
                message=f"Could not resolve user: {params.assigned_to}",
            )
    if params.location:
        data["location"] = params.location
    if params.cost:
        data["cost"] = params.cost
    if params.purchase_date:
        data["purchase_date"] = params.purchase_date
    if params.warranty_expiration:
        data["warranty_expiration"] = params.warranty_expiration
    if params.category:
        data["category"] = params.category
    if params.subcategory:
        data["subcategory"] = params.subcategory
    if params.manufacturer:
        data["manufacturer"] = params.manufacturer
    if params.model_category:
        data["model_category"] = params.model_category
    if params.state:
        data["state"] = params.state
    if params.substatus:
        data["substatus"] = params.substatus
    if params.comments:
        data["comments"] = params.comments

    # Make request
    try:
        response = requests.post(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return AssetResponse(
            success=True,
            message="Asset created successfully",
            asset_id=result.get("sys_id"),
            asset_tag=result.get("asset_tag"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to create asset: {e}")
        return AssetResponse(
            success=False,
            message=f"Failed to create asset: {str(e)}",
        )


def update_asset(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateAssetParams,
) -> AssetResponse:
    """
    Update an existing asset in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for updating the asset.

    Returns:
        Response with the updated asset details.
    """
    # Resolve asset sys_id if asset tag is provided
    asset_sys_id = resolve_asset_id(config, auth_manager, params.asset_id)
    if not asset_sys_id:
        return AssetResponse(
            success=False,
            message=f"Could not find asset: {params.asset_id}",
        )

    api_url = f"{config.api_url}/table/alm_asset/{asset_sys_id}"

    # Build request data
    data = {}
    if params.display_name:
        data["display_name"] = params.display_name
    if params.model:
        data["model"] = params.model
    if params.serial_number:
        data["serial_number"] = params.serial_number
    if params.assigned_to:
        # Resolve user if username is provided
        user_id = resolve_user_id(config, auth_manager, params.assigned_to)
        if user_id:
            data["assigned_to"] = user_id
        else:
            return AssetResponse(
                success=False,
                message=f"Could not resolve user: {params.assigned_to}",
            )
    if params.location:
        data["location"] = params.location
    if params.cost:
        data["cost"] = params.cost
    if params.purchase_date:
        data["purchase_date"] = params.purchase_date
    if params.warranty_expiration:
        data["warranty_expiration"] = params.warranty_expiration
    if params.category:
        data["category"] = params.category
    if params.subcategory:
        data["subcategory"] = params.subcategory
    if params.manufacturer:
        data["manufacturer"] = params.manufacturer
    if params.model_category:
        data["model_category"] = params.model_category
    if params.state:
        data["state"] = params.state
    if params.substatus:
        data["substatus"] = params.substatus
    if params.comments:
        data["comments"] = params.comments

    # Make request
    try:
        response = requests.patch(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return AssetResponse(
            success=True,
            message="Asset updated successfully",
            asset_id=result.get("sys_id"),
            asset_tag=result.get("asset_tag"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to update asset: {e}")
        return AssetResponse(
            success=False,
            message=f"Failed to update asset: {str(e)}",
        )


def get_asset(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetAssetParams,
) -> dict:
    """
    Get an asset from ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting the asset.

    Returns:
        Dictionary containing asset details.
    """
    api_url = f"{config.api_url}/table/alm_asset"
    query_params = {}

    # Build query parameters
    if params.asset_id:
        query_params["sysparm_query"] = f"sys_id={params.asset_id}"
    elif params.asset_tag:
        query_params["sysparm_query"] = f"asset_tag={params.asset_tag}"
    elif params.serial_number:
        query_params["sysparm_query"] = f"serial_number={params.serial_number}"
    else:
        return {"success": False, "message": "At least one search parameter is required"}

    query_params["sysparm_limit"] = "1"
    query_params["sysparm_display_value"] = "true"

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
        if not result:
            return {"success": False, "message": "Asset not found"}

        return {"success": True, "message": "Asset found", "asset": result[0]}

    except requests.RequestException as e:
        logger.error(f"Failed to get asset: {e}")
        return {"success": False, "message": f"Failed to get asset: {str(e)}"}


def list_assets(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListAssetsParams,
) -> dict:
    """
    List assets from ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing assets.

    Returns:
        Dictionary containing list of assets.
    """
    api_url = f"{config.api_url}/table/alm_asset"
    query_params = {
        "sysparm_limit": str(params.limit),
        "sysparm_offset": str(params.offset),
        "sysparm_display_value": "true",
    }

    # Build query
    query_parts = []
    if params.assigned_to:
        # Resolve user if username is provided
        user_ids = []
        for i, user in enumerate(params.assigned_to):
            user_id = resolve_user_id(config, auth_manager, user)
            if user_id:
                user_ids.append(user_id)
        query_parts.append(f"assigned_toIN{','.join(user_ids)}")

    if params.location:
        query_parts.append(f"location={params.location}")
    if params.name:
        # Search by display name using LIKE matching
        query_parts.append(f"display_nameLIKE{params.name}")
    if params.query:
        # Fallback to search by asset tag, display name, serial number, model or short description
        query_parts.append(
            f"^asset_tagLIKE{params.query}^ORdisplay_nameLIKE{params.query}^ORserial_numberLIKE{params.query}^ORmodelLIKE{params.query}^ORshort_descriptionLIKE{params.query}"
        )

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
            "message": f"Found {len(result)} assets",
            "assets": result,
            "count": len(result),
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list assets: {e}")
        return {"success": False, "message": f"Failed to list assets: {str(e)}"}


def search_assets_by_name(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: SearchAssetsByNameParams,
) -> dict:
    """
    Search for assets by display name using LIKE matching.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for searching assets by name.

    Returns:
        Dictionary containing list of matching assets.
    """
    api_url = f"{config.api_url}/table/alm_asset"
    query_params = {
        "sysparm_limit": str(params.limit),
        "sysparm_offset": str(params.offset),
        "sysparm_display_value": "true",
    }

    # Build query for name search
    if params.exact_match:
        # Exact match
        query_params["sysparm_query"] = f"display_name={params.name}"
    else:
        # LIKE matching (case-insensitive partial match)
        query_params["sysparm_query"] = f"display_nameLIKE{params.name}"

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
            "message": f"Found {len(result)} assets matching name '{params.name}'",
            "assets": result,
            "count": len(result),
            "search_term": params.name,
            "exact_match": params.exact_match,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to search assets by name: {e}")
        return {"success": False, "message": f"Failed to search assets by name: {str(e)}"}


def delete_asset(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteAssetParams,
) -> AssetResponse:
    """
    Delete an asset from ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for deleting the asset.

    Returns:
        Response with the result of the operation.
    """
    # Resolve asset sys_id if asset tag is provided
    asset_sys_id = resolve_asset_id(config, auth_manager, params.asset_id)
    if not asset_sys_id:
        return AssetResponse(
            success=False,
            message=f"Could not find asset: {params.asset_id}",
        )

    api_url = f"{config.api_url}/table/alm_asset/{asset_sys_id}"

    # Make request
    try:
        response = requests.delete(
            api_url,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        return AssetResponse(
            success=True,
            message="Asset deleted successfully",
            asset_id=asset_sys_id,
        )

    except requests.RequestException as e:
        logger.error(f"Failed to delete asset: {e}")
        return AssetResponse(
            success=False,
            message=f"Failed to delete asset: {str(e)}",
        )


def transfer_asset(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: TransferAssetParams,
) -> AssetResponse:
    """
    Transfer an asset to a different user in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for transferring the asset.

    Returns:
        Response with the result of the operation.
    """
    # Resolve asset sys_id if asset tag is provided
    asset_sys_id = resolve_asset_id(config, auth_manager, params.asset_id)
    if not asset_sys_id:
        return AssetResponse(
            success=False,
            message=f"Could not find asset: {params.asset_id}",
        )

    # Resolve new user
    new_user_id = resolve_user_id(config, auth_manager, params.new_assigned_to)
    if not new_user_id:
        return AssetResponse(
            success=False,
            message=f"Could not resolve user: {params.new_assigned_to}",
        )

    api_url = f"{config.api_url}/table/alm_asset/{asset_sys_id}"

    # Build request data
    data = {
        "assigned_to": new_user_id,
    }

    # Add transfer comments
    transfer_comment = f"Asset transferred to {params.new_assigned_to}"
    if params.transfer_reason:
        transfer_comment += f" - Reason: {params.transfer_reason}"
    if params.comments:
        transfer_comment += f" - {params.comments}"
    
    data["comments"] = transfer_comment

    # Make request
    try:
        response = requests.patch(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return AssetResponse(
            success=True,
            message=f"Asset transferred successfully to {params.new_assigned_to}",
            asset_id=result.get("sys_id"),
            asset_tag=result.get("asset_tag"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to transfer asset: {e}")
        return AssetResponse(
            success=False,
            message=f"Failed to transfer asset: {str(e)}",
        )

