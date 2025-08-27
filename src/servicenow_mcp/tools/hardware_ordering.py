"""
Hardware ordering tools for the ServiceNow MCP server.

This module provides comprehensive tools for managing hardware orders through ServiceNow's 
Service Catalog, including browsing catalog items, submitting orders, tracking requests,
and managing hardware provisioning workflows.
"""

import logging
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class BrowseHardwareCatalogParams(BaseModel):
    """Parameters for browsing hardware catalog items."""
    
    category: Optional[str] = Field(None, description="Filter by hardware category (Laptops, Desktops, Mobile, etc.)")
    manufacturer: Optional[str] = Field(None, description="Filter by manufacturer (Apple, Dell, HP, Lenovo, etc.)")
    price_range: Optional[str] = Field(None, description="Price range filter (e.g., '0-1000', '1000-2000')")
    availability: Optional[bool] = Field(True, description="Show only available items")
    limit: int = Field(20, description="Maximum number of items to return")
    offset: int = Field(0, description="Offset for pagination")


class SubmitHardwareOrderParams(BaseModel):
    """Parameters for submitting a hardware order."""
    
    catalog_item_id: str = Field(..., description="Sys_id of the catalog item to order")
    requested_for: str = Field(..., description="Sys_id of the user the hardware is for")
    quantity: int = Field(1, description="Number of items to order")
    justification: Optional[str] = Field(None, description="Business justification for the request")
    priority: Optional[str] = Field("3", description="Priority level (1=Critical, 2=High, 3=Medium, 4=Low)")
    requested_delivery_date: Optional[str] = Field(None, description="Requested delivery date (YYYY-MM-DD)")
    special_instructions: Optional[str] = Field(None, description="Special delivery or setup instructions")
    cost_center: Optional[str] = Field(None, description="Cost center for billing")
    project_code: Optional[str] = Field(None, description="Project code for tracking")


class TrackHardwareOrderParams(BaseModel):
    """Parameters for tracking hardware orders."""
    
    request_number: Optional[str] = Field(None, description="Service request number (e.g., REQ0010001)")
    requested_for: Optional[str] = Field(None, description="Sys_id of user to track orders for")
    status: Optional[str] = Field(None, description="Filter by order status")
    date_range: Optional[str] = Field(None, description="Date range filter (last_7_days, last_30_days, etc.)")
    limit: int = Field(10, description="Maximum number of orders to return")


class UpdateHardwareOrderParams(BaseModel):
    """Parameters for updating a hardware order."""
    
    request_id: str = Field(..., description="Sys_id of the service request to update")
    status: Optional[str] = Field(None, description="New status for the request")
    work_notes: Optional[str] = Field(None, description="Work notes to add")
    special_instructions: Optional[str] = Field(None, description="Updated special instructions")
    priority: Optional[str] = Field(None, description="Updated priority level")


class CancelHardwareOrderParams(BaseModel):
    """Parameters for canceling a hardware order."""
    
    request_id: str = Field(..., description="Sys_id of the service request to cancel")
    cancellation_reason: str = Field(..., description="Reason for cancelling the order")
    notify_requestor: bool = Field(True, description="Whether to notify the requestor")


class ProvisionHardwareParams(BaseModel):
    """Parameters for provisioning ordered hardware."""
    
    request_id: str = Field(..., description="Sys_id of the approved service request")
    asset_tag: str = Field(..., description="Asset tag for the hardware")
    serial_number: Optional[str] = Field(None, description="Serial number of the hardware")
    location: Optional[str] = Field(None, description="Physical location for delivery")
    configuration_notes: Optional[str] = Field(None, description="Hardware configuration notes")


def browse_hardware_catalog(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: BrowseHardwareCatalogParams,
) -> Dict[str, Any]:
    """
    Browse available hardware items in the Service Catalog.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Browse parameters
        
    Returns:
        Dictionary containing catalog items and metadata
    """
    try:
        # Build query filters
        query_filters = ["active=true"]
        
        if params.category:
            query_filters.append(f"category.nameLIKE{params.category}")
            
        if params.manufacturer:
            query_filters.append(f"short_descriptionLIKE{params.manufacturer}")
            
        if not params.availability:
            query_filters.append("active=false")
            
        query_string = "^".join(query_filters) if query_filters else ""
        
        # Make API request
        api_url = f"{config.api_url}/table/sc_cat_item"
        response = requests.get(
            api_url,
            params={
                "sysparm_query": query_string,
                "sysparm_fields": "sys_id,name,short_description,category,price,picture,active,order,description",
                "sysparm_limit": str(params.limit),
                "sysparm_offset": str(params.offset),
                "sysparm_display_value": "true"
            },
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        result = response.json()
        catalog_items = result.get("result", [])
        
        # Process and enhance results
        processed_items = []
        for item in catalog_items:
            processed_item = {
                "sys_id": item.get("sys_id"),
                "name": item.get("name"),
                "short_description": item.get("short_description"),
                "category": item.get("category"),
                "price": item.get("price", "Price on request"),
                "description": item.get("description", ""),
                "active": item.get("active") == "true",
                "order_priority": item.get("order", "100")
            }
            
            # Add price range classification
            try:
                price_value = float(item.get("price", "0").replace("$", "").replace(",", ""))
                if price_value == 0:
                    processed_item["price_range"] = "Contact for pricing"
                elif price_value < 1000:
                    processed_item["price_range"] = "Budget ($0-$999)"
                elif price_value < 2000:
                    processed_item["price_range"] = "Standard ($1,000-$1,999)"
                elif price_value < 3000:
                    processed_item["price_range"] = "Premium ($2,000-$2,999)"
                else:
                    processed_item["price_range"] = "Enterprise ($3,000+)"
            except:
                processed_item["price_range"] = "Price varies"
                
            processed_items.append(processed_item)
        
        return {
            "success": True,
            "message": f"Found {len(processed_items)} hardware items",
            "items": processed_items,
            "total_count": len(processed_items),
            "filters_applied": {
                "category": params.category,
                "manufacturer": params.manufacturer,
                "availability_only": params.availability
            }
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to browse hardware catalog: {e}")
        return {
            "success": False,
            "message": f"Failed to browse hardware catalog: {str(e)}",
            "items": []
        }


def submit_hardware_order(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: SubmitHardwareOrderParams,
) -> Dict[str, Any]:
    """
    Submit a hardware order through ServiceNow Service Catalog.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Order submission parameters
        
    Returns:
        Dictionary containing order confirmation details
    """
    try:
        # First, get catalog item details
        item_api_url = f"{config.api_url}/table/sc_cat_item/{params.catalog_item_id}"
        item_response = requests.get(
            item_api_url,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        item_response.raise_for_status()
        catalog_item = item_response.json().get("result", {})
        
        if not catalog_item:
            return {
                "success": False,
                "message": f"Catalog item {params.catalog_item_id} not found"
            }
        
        # Create service request
        request_data = {
            "requested_for": params.requested_for,
            "short_description": f"Hardware Order: {catalog_item.get('name', 'Hardware Item')}",
            "description": f"Order for {params.quantity}x {catalog_item.get('name', 'Hardware Item')}",
            "priority": params.priority,
            "state": "1",  # Pending
            "special_instructions": params.special_instructions or ""
        }
        
        if params.justification:
            request_data["justification"] = params.justification
            
        if params.requested_delivery_date:
            request_data["delivery_date"] = params.requested_delivery_date
            
        # Submit the service request
        request_api_url = f"{config.api_url}/table/sc_request"
        request_response = requests.post(
            request_api_url,
            json=request_data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        request_response.raise_for_status()
        
        service_request = request_response.json().get("result", {})
        request_sys_id = service_request.get("sys_id")
        request_number = service_request.get("number")
        
        # Create request item (the actual catalog item being ordered)
        item_data = {
            "request": request_sys_id,
            "cat_item": params.catalog_item_id,
            "quantity": params.quantity,
            "price": catalog_item.get("price", "0"),
            "recurring_price": catalog_item.get("recurring_price", "0"),
            "state": "1"  # Pending
        }
        
        if params.cost_center:
            item_data["cost_center"] = params.cost_center
            
        if params.project_code:
            item_data["project_code"] = params.project_code
        
        item_api_url = f"{config.api_url}/table/sc_req_item"
        item_response = requests.post(
            item_api_url,
            json=item_data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        item_response.raise_for_status()
        
        request_item = item_response.json().get("result", {})
        
        return {
            "success": True,
            "message": f"Hardware order {request_number} submitted successfully",
            "request_id": request_sys_id,
            "request_number": request_number,
            "item_id": request_item.get("sys_id"),
            "catalog_item": catalog_item.get("name"),
            "quantity": params.quantity,
            "estimated_cost": catalog_item.get("price", "TBD"),
            "status": "Pending Approval",
            "requested_for": params.requested_for
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to submit hardware order: {e}")
        return {
            "success": False,
            "message": f"Failed to submit hardware order: {str(e)}"
        }


def track_hardware_orders(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: TrackHardwareOrderParams,
) -> Dict[str, Any]:
    """
    Track hardware orders and their status.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Tracking parameters
        
    Returns:
        Dictionary containing order status information
    """
    try:
        # Build query filters
        query_filters = []
        
        if params.request_number:
            query_filters.append(f"number={params.request_number}")
            
        if params.requested_for:
            query_filters.append(f"requested_for={params.requested_for}")
            
        if params.status:
            query_filters.append(f"state={params.status}")
            
        # Add date range filter
        if params.date_range:
            if params.date_range == "last_7_days":
                query_filters.append("sys_created_on>=javascript:gs.daysAgo(7)")
            elif params.date_range == "last_30_days":
                query_filters.append("sys_created_on>=javascript:gs.daysAgo(30)")
                
        query_string = "^".join(query_filters) if query_filters else ""
        
        # Get service requests
        api_url = f"{config.api_url}/table/sc_request"
        response = requests.get(
            api_url,
            params={
                "sysparm_query": query_string,
                "sysparm_fields": "sys_id,number,short_description,state,priority,requested_for,sys_created_on,delivery_date",
                "sysparm_limit": str(params.limit),
                "sysparm_display_value": "true"
            },
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        result = response.json()
        requests_data = result.get("result", [])
        
        # Get detailed status for each request
        detailed_orders = []
        for request in requests_data:
            request_sys_id = request.get("sys_id")
            
            # Get associated request items
            items_response = requests.get(
                f"{config.api_url}/table/sc_req_item",
                params={
                    "sysparm_query": f"request={request_sys_id}",
                    "sysparm_fields": "sys_id,quantity,cat_item.name,state,price",
                    "sysparm_display_value": "true"
                },
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            
            items = []
            if items_response.status_code == 200:
                items = items_response.json().get("result", [])
            
            detailed_orders.append({
                "request_number": request.get("number"),
                "request_id": request_sys_id,
                "description": request.get("short_description"),
                "status": request.get("state"),
                "priority": request.get("priority"),
                "requested_for": request.get("requested_for"),
                "created_date": request.get("sys_created_on"),
                "delivery_date": request.get("delivery_date"),
                "items": [
                    {
                        "item_name": item.get("cat_item", {}).get("name", "Unknown"),
                        "quantity": item.get("quantity", "1"),
                        "status": item.get("state"),
                        "price": item.get("price", "TBD")
                    } for item in items
                ]
            })
        
        return {
            "success": True,
            "message": f"Found {len(detailed_orders)} hardware orders",
            "orders": detailed_orders,
            "total_count": len(detailed_orders)
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to track hardware orders: {e}")
        return {
            "success": False,
            "message": f"Failed to track hardware orders: {str(e)}",
            "orders": []
        }


def cancel_hardware_order(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CancelHardwareOrderParams,
) -> Dict[str, Any]:
    """
    Cancel a hardware order.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Cancellation parameters
        
    Returns:
        Dictionary containing cancellation confirmation
    """
    try:
        # Update the service request to cancelled state
        update_data = {
            "state": "4",  # Cancelled
            "close_notes": f"Order cancelled: {params.cancellation_reason}",
            "work_notes": f"Hardware order cancelled by user. Reason: {params.cancellation_reason}"
        }
        
        api_url = f"{config.api_url}/table/sc_request/{params.request_id}"
        response = requests.patch(
            api_url,
            json=update_data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        result = response.json().get("result", {})
        
        # Also update any associated request items
        items_response = requests.get(
            f"{config.api_url}/table/sc_req_item",
            params={
                "sysparm_query": f"request={params.request_id}",
                "sysparm_fields": "sys_id"
            },
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        
        if items_response.status_code == 200:
            items = items_response.json().get("result", [])
            for item in items:
                requests.patch(
                    f"{config.api_url}/table/sc_req_item/{item.get('sys_id')}",
                    json={"state": "4"},  # Cancelled
                    headers=auth_manager.get_headers(),
                    timeout=config.timeout,
                )
        
        return {
            "success": True,
            "message": f"Hardware order {result.get('number', params.request_id)} cancelled successfully",
            "request_id": params.request_id,
            "cancellation_reason": params.cancellation_reason,
            "status": "Cancelled"
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to cancel hardware order: {e}")
        return {
            "success": False,
            "message": f"Failed to cancel hardware order: {str(e)}"
        }


def provision_hardware(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ProvisionHardwareParams,
) -> Dict[str, Any]:
    """
    Provision hardware for an approved order by creating the asset record.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Provisioning parameters
        
    Returns:
        Dictionary containing provisioning confirmation
    """
    try:
        # Get the service request details
        request_response = requests.get(
            f"{config.api_url}/table/sc_request/{params.request_id}",
            params={"sysparm_fields": "number,requested_for,short_description"},
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        request_response.raise_for_status()
        
        request_data = request_response.json().get("result", {})
        if not request_data:
            return {
                "success": False,
                "message": f"Service request {params.request_id} not found"
            }
        
        # Get request items to understand what was ordered
        items_response = requests.get(
            f"{config.api_url}/table/sc_req_item",
            params={
                "sysparm_query": f"request={params.request_id}",
                "sysparm_fields": "cat_item.name,quantity",
                "sysparm_display_value": "true"
            },
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        
        ordered_items = []
        if items_response.status_code == 200:
            ordered_items = items_response.json().get("result", [])
        
        # Create hardware asset record
        asset_data = {
            "asset_tag": params.asset_tag,
            "display_name": f"Hardware Asset - {params.asset_tag}",
            "assigned_to": request_data.get("requested_for"),
            "state": "1",  # In use
            "install_status": "1",  # Installed
            "substatus": "available"
        }
        
        if params.serial_number:
            asset_data["serial_number"] = params.serial_number
            
        if params.location:
            asset_data["location"] = params.location
            
        if params.configuration_notes:
            asset_data["comments"] = params.configuration_notes
            
        # Add details from ordered items
        if ordered_items:
            first_item = ordered_items[0]
            asset_data["display_name"] = f"{first_item.get('cat_item', {}).get('name', 'Hardware')} - {params.asset_tag}"
        
        # Create the asset
        asset_response = requests.post(
            f"{config.api_url}/table/alm_asset",
            json=asset_data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        asset_response.raise_for_status()
        
        asset_result = asset_response.json().get("result", {})
        
        # Update service request to fulfilled
        requests.patch(
            f"{config.api_url}/table/sc_request/{params.request_id}",
            json={
                "state": "3",  # Fulfilled
                "work_notes": f"Hardware provisioned with asset tag: {params.asset_tag}"
            },
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        
        return {
            "success": True,
            "message": f"Hardware provisioned successfully with asset tag {params.asset_tag}",
            "asset_id": asset_result.get("sys_id"),
            "asset_tag": params.asset_tag,
            "assigned_to": request_data.get("requested_for"),
            "request_number": request_data.get("number"),
            "provisioning_status": "Complete"
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to provision hardware: {e}")
        return {
            "success": False,
            "message": f"Failed to provision hardware: {str(e)}"
        }


class GetHardwareRecommendationsParams(BaseModel):
    """Parameters for getting hardware recommendations."""
    
    user_role: str = Field(..., description="User's role (e.g., 'Developer', 'Manager', 'Analyst')")
    department: str = Field(..., description="User's department (e.g., 'IT', 'Finance', 'HR')")
    budget_range: Optional[str] = Field(None, description="Optional budget constraint (e.g., 'under-1000', '1000-2000')")


def get_hardware_recommendations(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetHardwareRecommendationsParams,
) -> Dict[str, Any]:
    """
    Get hardware recommendations based on user role and department.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager  
        params: Recommendation parameters
        
    Returns:
        Dictionary containing hardware recommendations
    """
    try:
        # Define role-based recommendations
        recommendations = {
            "Developer": {
                "primary": "High-performance laptop with development tools",
                "specs": ["16GB+ RAM", "SSD Storage", "Dedicated Graphics"],
                "suggested_items": ["MacBook Pro 16", "Dell XPS 15", "ThinkPad P1"]
            },
            "Manager": {
                "primary": "Business laptop with presentation capabilities",  
                "specs": ["8GB+ RAM", "Lightweight", "Long battery life"],
                "suggested_items": ["MacBook Air", "Dell Latitude", "Surface Laptop"]
            },
            "Analyst": {
                "primary": "Standard business laptop for office productivity",
                "specs": ["8GB RAM", "Office Suite", "Webcam"],
                "suggested_items": ["MacBook Air", "HP EliteBook", "Lenovo ThinkPad"]
            }
        }
        
        # Department-specific additions
        dept_additions = {
            "IT": {"additional": ["Dual monitors", "Docking station", "External keyboard"]},
            "Finance": {"additional": ["Number pad keyboard", "Large monitor", "Ergonomic mouse"]},
            "HR": {"additional": ["Webcam", "Headset", "Document scanner"]}
        }
        
        user_recommendations = recommendations.get(params.user_role, {
            "primary": "Standard business laptop",
            "specs": ["8GB RAM", "Office productivity"],
            "suggested_items": ["MacBook Air", "Dell Latitude"]
        })
        
        if params.department in dept_additions:
            user_recommendations["additional_equipment"] = dept_additions[params.department]["additional"]
        
        # Add budget considerations
        if params.budget_range:
            user_recommendations["budget_notes"] = f"Filtered for {params.budget_range} price range"
        
        return {
            "success": True,
            "message": f"Hardware recommendations for {params.user_role} in {params.department}",
            "recommendations": user_recommendations,
            "user_profile": {
                "role": params.user_role,
                "department": params.department,
                "budget_range": params.budget_range
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to get hardware recommendations: {e}")
        return {
            "success": False,
            "message": f"Failed to get hardware recommendations: {str(e)}"
        }
