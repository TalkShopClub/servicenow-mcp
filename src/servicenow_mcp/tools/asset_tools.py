"""
Asset management tools for the ServiceNow MCP server.

This module provides tools for managing assets in ServiceNow including
creating, updating, deleting, and transferring assets between users.
"""

import logging
from typing import Optional, Dict

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig
from servicenow_mcp.utils.resolvers import resolve_user_id, resolve_asset_id

logger = logging.getLogger(__name__)


class CreateAssetParams(BaseModel):
    """Parameters for creating an asset."""

    asset_tag: str = Field(..., description="Unique asset tag identifier")
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
    install_status: Optional[str] = Field("1", description="Installation status of the asset (1=In use, 2=On Order, 3=In Maintenance, 6=In stock, 7=Retired, 8=Missing, 9=In Transit, 10=Consumed,11=Build, .)")
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
    install_status: Optional[str] = Field(None, description="Installation status of the asset (1=In use, 2=On Order, 3=In Maintenance, 6=In stock, 7=Retired, 8=Missing, 9=In Transit, 10=Consumed,11=Build, .)")
    substatus: Optional[str] = Field(None, description="Substatus of the asset")
    comments: Optional[str] = Field(None, description="Comments about the asset")


class GetAssetsParams(BaseModel):
    """Unified parameters for getting, listing, and searching assets."""

    # Pagination
    limit: int = Field(10, description="Maximum number of assets to return")
    offset: int = Field(0, description="Offset for pagination")
    
    # Specific asset identification (for single asset retrieval)
    asset_id: Optional[str] = Field(None, description="Asset ID (sys_id) - returns single asset if specified")
    asset_tag: Optional[str] = Field(None, description="Asset tag - returns single asset if specified")
    serial_number: Optional[str] = Field(None, description="Serial number - returns single asset if specified")
    
    # Filtering options
    assigned_to: Optional[str] = Field(None, description="User sys_id or name that the asset is assigned to")
    location: Optional[str] = Field(None, description="Filter by location")
    
    # Search options
    name: Optional[str] = Field(None, description="Search for assets by display name using LIKE matching")
    exact_match: bool = Field(False, description="Whether to perform exact match instead of LIKE matching for name search")
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

class CreateHardwareAssetParams(BaseModel):
    """Parameters for creating a hardware asset. Display name is automatically generated by merging model and asset tag."""
    
    asset_tag: str = Field(..., description="Asset tag of the hardware asset")
    model: str = Field(..., description="Model of the hardware asset")
    state: Optional[str] = Field(None, description="State of the hardware asset. 1 -> In Use 2 -> On Order 3 -> In Maintenance 6 -> In Stock 7 -> Retired 8 -> Missing 9 -> In Transit 10 -> Consumed 11 -> Build ")
    model_category: Optional[str] = Field(None, description="Model category of the hardware asset")
    serial_number: Optional[str] = Field(None, description="Serial number of the hardware asset")
    vendor: Optional[str] = Field(None, description="Vendor of the hardware asset")
    fields: Optional[Dict[str, str]] = Field(None, description="Dictionary of other field names and corresponding values to set for the hardware asset. Example: {'priority': '1'}")
    cost: Optional[str] = Field(None, description="Cost of the hardware asset")
    assigned_to: Optional[str] = Field(None, description="User assigned to the hardware asset (sys_id)")
    environment: Optional[str] = Field(None, description="Environment of the hardware asset. Choose between 'production', 'staging' and 'development'")
    required_clearance_level: Optional[int] = Field(None, description="Required clearance level for the hardware asset. Clearance values are integers")

class UpdateHardwareAssetParams(BaseModel):
    """Parameters for updating a hardware asset."""
    
    asset_id: str = Field(..., description="Asset ID (sys_id) or asset tag")
    state: Optional[str] = Field(None, description="State of the hardware asset. 1 -> In Use 2 -> On Order 3 -> In Maintenance 6 -> In Stock 7 -> Retired 8 -> Missing 9 -> In Transit 10 -> Consumed 11 -> Build ")
    model_category: Optional[str] = Field(None, description="Model category of the hardware asset")
    serial_number: Optional[str] = Field(None, description="Serial number of the hardware asset")
    vendor: Optional[str] = Field(None, description="Vendor of the hardware asset")
    fields: Optional[Dict[str, str]] = Field(None, description="Dictionary of other field names and corresponding values to set for the hardware asset. Example: {'priority': '1'}")
    cost: Optional[str] = Field(None, description="Cost of the hardware asset")
    assigned_to: Optional[str] = Field(None, description="User assigned to the hardware asset (sys_id)")
    environment: Optional[str] = Field(None, description="Environment of the hardware asset. Choose between 'production', 'staging' and 'development'")
    required_clearance_level: Optional[int] = Field(None, description="Required clearance level for the hardware asset. Clearance values are integers")

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
    
def create_hardware_asset(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateHardwareAssetParams,
) -> AssetResponse:
    """
    Create a new hardware asset in ServiceNow.
    """
    api_url = f"{config.api_url}/table/alm_hardware"

    # Build request data
    data = {
        "asset_tag": params.asset_tag,
        "model": params.model,
    }

    if params.model_category:
        data["model_category"] = params.model_category
    if params.serial_number:
        data["serial_number"] = params.serial_number
    if params.vendor:
        data["vendor"] = params.vendor
    if params.cost:
        data["cost"] = params.cost
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
    
    if params.state:
        data["install_status"] = params.state
    if params.fields:
        for field, value in params.fields.items():
            data[field] = value
        
    if params.environment:
        data["u_environment"] = params.environment
    if params.required_clearance_level:
        data["u_clearance"] = params.required_clearance_level

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
        
        return AssetResponse(
            success=True,
            message="Hardware asset created successfully. The sys_id of the asset is: " + result.get("sys_id"),
            asset_id=result.get("sys_id"),
            asset_tag=result.get("asset_tag"),
        ) 
    except requests.RequestException as e:
        logger.error(f"Failed to create hardware asset: {e}")
        return AssetResponse(
            success=False,
            message=f"Failed to create hardware asset: {str(e)}",
        )


def update_hardware_asset(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateHardwareAssetParams,
) -> AssetResponse:
    """
    Update an existing hardware asset in ServiceNow.
    """
    api_url = f"{config.api_url}/table/alm_hardware/{params.asset_id}"

    # Build request data
    data = {}

    if params.state:
        data["install_status"] = params.state
    if params.model_category:
        data["model_category"] = params.model_category
    if params.serial_number:
        data["serial_number"] = params.serial_number
    if params.vendor:
        data["vendor"] = params.vendor
    if params.fields:
        for field, value in params.fields.items():
            data[field] = value
    if params.cost:
        data["cost"] = params.cost
    if params.assigned_to is not None:

        if params.assigned_to == "":
            data["assigned_to"] = ""
        else:
            # Resolve user if username is provided
            user_id = resolve_user_id(config, auth_manager, params.assigned_to)
            if user_id:
                data["assigned_to"] = user_id
            else:
                return AssetResponse(
                    success=False,
                    message=f"Could not resolve user: {params.assigned_to}",
                )
    
    if params.environment:
        data["u_environment"] = params.environment
    if params.required_clearance_level:
        data["u_clearance"] = params.required_clearance_level
    
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
            message="Hardware asset updated successfully",
            asset_id=result.get("sys_id"),
            asset_tag=result.get("asset_tag"),
        )
    except requests.RequestException as e:
        logger.error(f"Failed to update hardware asset: {e}")
        result = response.json().get("result", {})

        return AssetResponse(
            success=True,
            message="Hardware asset updated successfully",
            asset_id=result.get("sys_id"),
            asset_tag=result.get("asset_tag"),
        )

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
    if params.install_status:
        data["install_status"] = params.install_status
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
    if params.install_status:
        data["install_status"] = params.install_status
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


def get_assets(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetAssetsParams,
) -> dict:
    """
    Get, list, or search for assets in ServiceNow.
    
    This unified function combines the functionality of get_asset, list_assets, 
    and search_assets_by_name into a single flexible function.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting, listing, or searching assets.

    Returns:
        Dictionary containing list of assets (always returns a list, even for single asset lookups).
    """
    api_url = f"{config.api_url}/table/alm_asset"
    query_params = {
        "sysparm_limit": str(params.limit),
        "sysparm_offset": str(params.offset),
        "sysparm_display_value": "true",
    }

    # Build query based on parameters
    query_parts = []
    
    # Single asset identification (highest priority)
    if params.asset_id:
        query_parts.append(f"sys_id={params.asset_id}")
    elif params.asset_tag:
        query_parts.append(f"asset_tag={params.asset_tag}")
    elif params.serial_number:
        query_parts.append(f"serial_number={params.serial_number}")
    else:
        # User assignment filtering
        if params.assigned_to:
            user_id = resolve_user_id(config, auth_manager, params.assigned_to) or params.assigned_to
            if user_id:
                query_parts.append(f"assigned_to={user_id}")

        # Location filtering
        if params.location:
            query_parts.append(f"location={params.location}")
        
        # Name search (with exact match option)
        if params.name:
            if params.exact_match:
                query_parts.append(f"display_name={params.name}")
            else:
                query_parts.append(f"display_nameLIKE{params.name}")
        
        # General query search
        if params.query:
            query_parts.append(
                f"^asset_tagLIKE{params.query}^ORdisplay_nameLIKE{params.query}^ORserial_numberLIKE{params.query}^ORmodelLIKE{params.query}^ORshort_descriptionLIKE{params.query}"
            )

    # Apply query if we have any conditions
    if query_parts:
        query_params["sysparm_query"] = "^".join(query_parts)
    # else:
    #     return {"success": False, "message": "At least one search parameter is required"}

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
        
        # Always return a list of assets
        response_data = {
            "success": True,
            "message": f"Found {len(result)} assets",
            "assets": result,
            "count": len(result),
        }
        
        # Add search-specific metadata
        if params.name:
            response_data["search_term"] = params.name
            response_data["exact_match"] = params.exact_match
            response_data["message"] = f"Found {len(result)} assets matching name '{params.name}'"
        
        return response_data

    except requests.RequestException as e:
        logger.error(f"Failed to get assets: {e}")
        return {"success": False, "message": f"Failed to get assets: {str(e)}"}


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

