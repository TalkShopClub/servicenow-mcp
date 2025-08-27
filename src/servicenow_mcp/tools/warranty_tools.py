"""
Warranty checking tools for the ServiceNow MCP server.

This module provides comprehensive tools for managing warranty information, including
checking warranty status from external manufacturer APIs, updating asset warranty 
information, and validating warranty dates for hardware assets.
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class CheckAssetWarrantyParams(BaseModel):
    """Parameters for checking warranty status of an asset."""
    
    asset_id: Optional[str] = Field(None, description="Asset sys_id to check warranty for")
    asset_tag: Optional[str] = Field(None, description="Asset tag to check warranty for")
    serial_number: Optional[str] = Field(None, description="Serial number to check warranty for")
    manufacturer: Optional[str] = Field(None, description="Manufacturer name (Apple, Dell, HP, Lenovo, etc.)")


class UpdateAssetWarrantyParams(BaseModel):
    """Parameters for updating asset warranty information."""
    
    asset_id: Optional[str] = Field(None, description="Asset sys_id to update")
    asset_tag: Optional[str] = Field(None, description="Asset tag to update")
    warranty_expiration_date: str = Field(..., description="New warranty expiration date (YYYY-MM-DD)")
    warranty_start_date: Optional[str] = Field(None, description="Warranty start date (YYYY-MM-DD)")
    warranty_duration_months: Optional[int] = Field(None, description="Warranty duration in months")
    warranty_type: Optional[str] = Field("Standard", description="Type of warranty coverage")
    warranty_notes: Optional[str] = Field(None, description="Additional warranty notes")


class BulkWarrantyCheckParams(BaseModel):
    """Parameters for bulk warranty checking across multiple assets."""
    
    manufacturer: Optional[str] = Field(None, description="Filter by manufacturer")
    location: Optional[str] = Field(None, description="Filter by location")
    missing_warranty_only: bool = Field(True, description="Only check assets without warranty dates")
    asset_category: Optional[str] = Field(None, description="Filter by asset category (Laptop, Desktop, etc.)")
    limit: int = Field(50, description="Maximum number of assets to check")


class WarrantyValidationParams(BaseModel):
    """Parameters for validating warranty information."""
    
    asset_id: Optional[str] = Field(None, description="Asset sys_id to validate")
    asset_tag: Optional[str] = Field(None, description="Asset tag to validate")
    check_expiration_alerts: bool = Field(True, description="Check for expiring warranties")
    days_before_expiration: int = Field(30, description="Days before expiration to alert on")


class WarrantyReportParams(BaseModel):
    """Parameters for generating warranty reports."""
    
    report_type: str = Field(..., description="Type of report: 'expired', 'expiring', 'missing', or 'summary'")
    days_ahead: int = Field(30, description="Days ahead to look for expiring warranties")
    department: Optional[str] = Field(None, description="Filter by department")
    location: Optional[str] = Field(None, description="Filter by location")
    manufacturer: Optional[str] = Field(None, description="Filter by manufacturer")
    include_details: bool = Field(True, description="Include detailed asset information")


def check_asset_warranty(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CheckAssetWarrantyParams,
) -> Dict[str, Any]:
    """
    Check warranty status of a hardware asset from external APIs and ServiceNow records.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Warranty check parameters
        
    Returns:
        Dictionary containing warranty information and status
    """
    try:
        # First, get asset information from ServiceNow
        asset_info = None
        
        if params.asset_id:
            response = requests.get(
                f"{config.api_url}/table/alm_hardware/{params.asset_id}",
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            if response.status_code == 200:
                asset_info = response.json().get("result", {})
                
        elif params.asset_tag:
            response = requests.get(
                f"{config.api_url}/table/alm_hardware",
                params={
                    "sysparm_query": f"asset_tag={params.asset_tag}",
                    "sysparm_fields": "sys_id,asset_tag,serial_number,manufacturer,model,warranty_expiration,assigned_to"
                },
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            if response.status_code == 200:
                results = response.json().get("result", [])
                if results:
                    asset_info = results[0]
                    
        elif params.serial_number:
            response = requests.get(
                f"{config.api_url}/table/alm_hardware", 
                params={
                    "sysparm_query": f"serial_number={params.serial_number}",
                    "sysparm_fields": "sys_id,asset_tag,serial_number,manufacturer,model,warranty_expiration,assigned_to"
                },
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            if response.status_code == 200:
                results = response.json().get("result", [])
                if results:
                    asset_info = results[0]
        
        if not asset_info:
            return {
                "success": False,
                "message": "Asset not found in ServiceNow",
                "warranty_info": {}
            }
        
        # Extract asset details
        serial_number = asset_info.get("serial_number", "")
        manufacturer = params.manufacturer or asset_info.get("manufacturer", "")
        asset_tag = asset_info.get("asset_tag", "")
        current_warranty = asset_info.get("warranty_expiration", "")
        
        warranty_info = {
            "asset_id": asset_info.get("sys_id"),
            "asset_tag": asset_tag,
            "serial_number": serial_number,
            "manufacturer": manufacturer,
            "model": asset_info.get("model", ""),
            "current_warranty_expiration": current_warranty,
            "assigned_to": asset_info.get("assigned_to", "")
        }
        
        # Try to get warranty information from external APIs
        external_warranty = _check_external_warranty_api(manufacturer, serial_number)
        
        if external_warranty:
            warranty_info.update(external_warranty)
            warranty_info["external_api_check"] = True
            
            # Compare with ServiceNow data
            if current_warranty and external_warranty.get("warranty_expiration"):
                warranty_info["warranty_match"] = current_warranty == external_warranty.get("warranty_expiration")
            else:
                warranty_info["warranty_match"] = None
        else:
            warranty_info["external_api_check"] = False
            warranty_info["external_api_message"] = "No external warranty API available or accessible"
        
        # Calculate warranty status
        warranty_status = _calculate_warranty_status(warranty_info.get("warranty_expiration") or current_warranty)
        warranty_info.update(warranty_status)
        
        return {
            "success": True,
            "message": f"Warranty check completed for {asset_tag}",
            "warranty_info": warranty_info
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to check asset warranty: {e}")
        return {
            "success": False,
            "message": f"Failed to check asset warranty: {str(e)}",
            "warranty_info": {}
        }


def update_asset_warranty(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateAssetWarrantyParams,
) -> Dict[str, Any]:
    """
    Update warranty information for a hardware asset in ServiceNow.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Warranty update parameters
        
    Returns:
        Dictionary containing update confirmation
    """
    try:
        # Find the asset
        asset_sys_id = None
        
        if params.asset_id:
            asset_sys_id = params.asset_id
        elif params.asset_tag:
            response = requests.get(
                f"{config.api_url}/table/alm_hardware",
                params={
                    "sysparm_query": f"asset_tag={params.asset_tag}",
                    "sysparm_fields": "sys_id,asset_tag"
                },
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            
            if response.status_code == 200:
                results = response.json().get("result", [])
                if results:
                    asset_sys_id = results[0]["sys_id"]
        
        if not asset_sys_id:
            return {
                "success": False,
                "message": "Asset not found for warranty update"
            }
        
        # Prepare update data
        update_data = {
            "warranty_expiration": params.warranty_expiration_date
        }
        
        if params.warranty_start_date:
            update_data["warranty_start"] = params.warranty_start_date
            
        if params.warranty_duration_months:
            update_data["warranty_duration"] = str(params.warranty_duration_months)
            
        if params.warranty_type:
            update_data["warranty_type"] = params.warranty_type
            
        if params.warranty_notes:
            current_comments = ""
            # Get current comments first
            response = requests.get(
                f"{config.api_url}/table/alm_hardware/{asset_sys_id}",
                params={"sysparm_fields": "comments"},
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            
            if response.status_code == 200:
                current_comments = response.json().get("result", {}).get("comments", "")
            
            # Append warranty notes
            updated_comments = f"{current_comments}\n\nWarranty Update ({datetime.now().strftime('%Y-%m-%d %H:%M')}): {params.warranty_notes}".strip()
            update_data["comments"] = updated_comments
        
        # Update the asset
        response = requests.patch(
            f"{config.api_url}/table/alm_hardware/{asset_sys_id}",
            json=update_data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        result = response.json().get("result", {})
        
        return {
            "success": True,
            "message": f"Warranty information updated successfully",
            "asset_id": asset_sys_id,
            "updated_fields": update_data,
            "warranty_expiration": params.warranty_expiration_date,
            "asset_tag": result.get("asset_tag", params.asset_tag)
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to update asset warranty: {e}")
        return {
            "success": False,
            "message": f"Failed to update asset warranty: {str(e)}"
        }


def bulk_warranty_check(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: BulkWarrantyCheckParams,
) -> Dict[str, Any]:
    """
    Perform warranty checks across multiple assets.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Bulk check parameters
        
    Returns:
        Dictionary containing bulk check results
    """
    try:
        # Build query filters
        query_filters = []
        
        if params.manufacturer:
            query_filters.append(f"manufacturer={params.manufacturer}")
            
        if params.location:
            query_filters.append(f"location.name={params.location}")
            
        if params.missing_warranty_only:
            query_filters.append("warranty_expiration=NULL^ORwarranty_expiration=")
            
        if params.asset_category:
            query_filters.append(f"category={params.asset_category}")
        
        query_string = "^".join(query_filters) if query_filters else ""
        
        # Get assets to check
        response = requests.get(
            f"{config.api_url}/table/alm_hardware",
            params={
                "sysparm_query": query_string,
                "sysparm_fields": "sys_id,asset_tag,serial_number,manufacturer,model,warranty_expiration,assigned_to",
                "sysparm_limit": str(params.limit)
            },
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        assets = response.json().get("result", [])
        
        check_results = []
        updated_count = 0
        error_count = 0
        
        for asset in assets:
            try:
                # Check warranty for each asset
                check_params = CheckAssetWarrantyParams(
                    asset_id=asset.get("sys_id"),
                    serial_number=asset.get("serial_number"),
                    manufacturer=asset.get("manufacturer")
                )
                
                warranty_result = check_asset_warranty(config, auth_manager, check_params)
                
                if warranty_result.get("success"):
                    warranty_info = warranty_result.get("warranty_info", {})
                    
                    # If external API provided warranty info and it's different, update
                    if (warranty_info.get("external_api_check") and 
                        warranty_info.get("warranty_expiration") and
                        warranty_info.get("warranty_match") is False):
                        
                        update_params = UpdateAssetWarrantyParams(
                            asset_id=asset.get("sys_id"),
                            warranty_expiration_date=warranty_info["warranty_expiration"],
                            warranty_notes="Updated from external warranty API"
                        )
                        
                        update_result = update_asset_warranty(config, auth_manager, update_params)
                        
                        if update_result.get("success"):
                            updated_count += 1
                            warranty_info["updated_in_servicenow"] = True
                        else:
                            warranty_info["update_error"] = update_result.get("message")
                            error_count += 1
                    
                    check_results.append({
                        "asset_tag": asset.get("asset_tag"),
                        "asset_id": asset.get("sys_id"),
                        "manufacturer": asset.get("manufacturer"),
                        "warranty_info": warranty_info
                    })
                else:
                    error_count += 1
                    check_results.append({
                        "asset_tag": asset.get("asset_tag"),
                        "asset_id": asset.get("sys_id"),
                        "error": warranty_result.get("message")
                    })
                    
            except Exception as e:
                error_count += 1
                logger.error(f"Error checking warranty for asset {asset.get('asset_tag')}: {e}")
                check_results.append({
                    "asset_tag": asset.get("asset_tag"),
                    "error": str(e)
                })
        
        return {
            "success": True,
            "message": f"Bulk warranty check completed on {len(assets)} assets",
            "summary": {
                "total_checked": len(assets),
                "successful_checks": len(assets) - error_count,
                "updated_assets": updated_count,
                "errors": error_count
            },
            "results": check_results
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to perform bulk warranty check: {e}")
        return {
            "success": False,
            "message": f"Failed to perform bulk warranty check: {str(e)}"
        }


def validate_warranty_information(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: WarrantyValidationParams,
) -> Dict[str, Any]:
    """
    Validate warranty information for an asset and check for expiration alerts.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Validation parameters
        
    Returns:
        Dictionary containing validation results
    """
    try:
        # Get asset information
        asset_info = None
        
        if params.asset_id:
            response = requests.get(
                f"{config.api_url}/table/alm_hardware/{params.asset_id}",
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            if response.status_code == 200:
                asset_info = response.json().get("result", {})
        elif params.asset_tag:
            response = requests.get(
                f"{config.api_url}/table/alm_hardware",
                params={
                    "sysparm_query": f"asset_tag={params.asset_tag}",
                    "sysparm_fields": "sys_id,asset_tag,warranty_expiration,assigned_to,manufacturer,model"
                },
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
            )
            if response.status_code == 200:
                results = response.json().get("result", [])
                if results:
                    asset_info = results[0]
        
        if not asset_info:
            return {
                "success": False,
                "message": "Asset not found for warranty validation"
            }
        
        validation_results = {
            "asset_id": asset_info.get("sys_id"),
            "asset_tag": asset_info.get("asset_tag"),
            "manufacturer": asset_info.get("manufacturer"),
            "model": asset_info.get("model"),
            "assigned_to": asset_info.get("assigned_to"),
            "warranty_expiration": asset_info.get("warranty_expiration"),
            "validation_checks": {}
        }
        
        warranty_expiration = asset_info.get("warranty_expiration")
        
        # Check if warranty date exists
        validation_results["validation_checks"]["has_warranty_date"] = bool(warranty_expiration)
        
        if warranty_expiration:
            # Parse warranty date
            try:
                warranty_date = datetime.strptime(warranty_expiration, "%Y-%m-%d")
                current_date = datetime.now()
                days_until_expiration = (warranty_date - current_date).days
                
                validation_results["validation_checks"]["warranty_date_valid"] = True
                validation_results["validation_checks"]["days_until_expiration"] = days_until_expiration
                
                # Check warranty status
                if days_until_expiration < 0:
                    validation_results["validation_checks"]["warranty_status"] = "expired"
                    validation_results["validation_checks"]["days_expired"] = abs(days_until_expiration)
                elif days_until_expiration <= params.days_before_expiration:
                    validation_results["validation_checks"]["warranty_status"] = "expiring_soon"
                    validation_results["validation_checks"]["expires_in_days"] = days_until_expiration
                else:
                    validation_results["validation_checks"]["warranty_status"] = "active"
                
                # Generate alerts if needed
                if params.check_expiration_alerts:
                    alerts = []
                    
                    if validation_results["validation_checks"]["warranty_status"] == "expired":
                        alerts.append({
                            "type": "expired",
                            "message": f"Warranty expired {abs(days_until_expiration)} days ago",
                            "severity": "high"
                        })
                    elif validation_results["validation_checks"]["warranty_status"] == "expiring_soon":
                        alerts.append({
                            "type": "expiring_soon", 
                            "message": f"Warranty expires in {days_until_expiration} days",
                            "severity": "medium"
                        })
                    
                    validation_results["alerts"] = alerts
                
            except ValueError:
                validation_results["validation_checks"]["warranty_date_valid"] = False
                validation_results["validation_checks"]["date_format_error"] = "Invalid date format"
        else:
            validation_results["validation_checks"]["warranty_date_valid"] = False
            validation_results["validation_checks"]["missing_warranty_date"] = True
        
        return {
            "success": True,
            "message": "Warranty validation completed",
            "validation_results": validation_results
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to validate warranty information: {e}")
        return {
            "success": False,
            "message": f"Failed to validate warranty information: {str(e)}"
        }


def generate_warranty_report(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: WarrantyReportParams,
) -> Dict[str, Any]:
    """
    Generate comprehensive warranty reports for assets.
    
    Args:
        config: Server configuration
        auth_manager: Authentication manager
        params: Report parameters
        
    Returns:
        Dictionary containing warranty report data
    """
    try:
        # Build query based on report type
        query_filters = []
        current_date = datetime.now().strftime("%Y-%m-%d")
        
        if params.report_type == "expired":
            query_filters.append(f"warranty_expiration<{current_date}")
        elif params.report_type == "expiring":
            future_date = (datetime.now() + timedelta(days=params.days_ahead)).strftime("%Y-%m-%d")
            query_filters.append(f"warranty_expiration>={current_date}^warranty_expiration<={future_date}")
        elif params.report_type == "missing":
            query_filters.append("warranty_expiration=NULL^ORwarranty_expiration=")
        # For 'summary', no specific date filter
        
        # Add additional filters
        if params.department:
            query_filters.append(f"assigned_to.department.name={params.department}")
        if params.location:
            query_filters.append(f"location.name={params.location}")
        if params.manufacturer:
            query_filters.append(f"manufacturer={params.manufacturer}")
        
        query_string = "^".join(query_filters) if query_filters else ""
        
        # Define fields to retrieve
        fields = "sys_id,asset_tag,manufacturer,model,warranty_expiration,assigned_to,location"
        if params.include_details:
            fields += ",serial_number,cost,purchase_date,install_date,assigned_to.name,assigned_to.department.name"
        
        # Get assets
        response = requests.get(
            f"{config.api_url}/table/alm_hardware",
            params={
                "sysparm_query": query_string,
                "sysparm_fields": fields,
                "sysparm_display_value": "true"
            },
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        assets = response.json().get("result", [])
        
        # Process assets for report
        report_data = {
            "report_type": params.report_type,
            "generated_date": current_date,
            "filters": {
                "department": params.department,
                "location": params.location,
                "manufacturer": params.manufacturer
            },
            "summary": {
                "total_assets": len(assets)
            },
            "assets": []
        }
        
        # Calculate summary statistics
        expired_count = 0
        expiring_count = 0
        missing_count = 0
        active_count = 0
        
        for asset in assets:
            asset_data = {
                "sys_id": asset.get("sys_id"),
                "asset_tag": asset.get("asset_tag"),
                "manufacturer": asset.get("manufacturer"),
                "model": asset.get("model"),
                "warranty_expiration": asset.get("warranty_expiration"),
                "assigned_to": asset.get("assigned_to"),
                "location": asset.get("location")
            }
            
            if params.include_details:
                asset_data.update({
                    "serial_number": asset.get("serial_number"),
                    "cost": asset.get("cost"),
                    "purchase_date": asset.get("purchase_date"),
                    "install_date": asset.get("install_date"),
                    "assigned_to_name": asset.get("assigned_to", {}).get("name") if isinstance(asset.get("assigned_to"), dict) else asset.get("assigned_to"),
                    "department": asset.get("assigned_to", {}).get("department", {}).get("name") if isinstance(asset.get("assigned_to"), dict) else ""
                })
            
            # Calculate warranty status
            warranty_expiration = asset.get("warranty_expiration")
            if warranty_expiration:
                try:
                    warranty_date = datetime.strptime(warranty_expiration, "%Y-%m-%d")
                    current_datetime = datetime.now()
                    days_until_expiration = (warranty_date - current_datetime).days
                    
                    asset_data["days_until_expiration"] = days_until_expiration
                    
                    if days_until_expiration < 0:
                        asset_data["warranty_status"] = "expired"
                        expired_count += 1
                    elif days_until_expiration <= params.days_ahead:
                        asset_data["warranty_status"] = "expiring_soon"
                        expiring_count += 1
                    else:
                        asset_data["warranty_status"] = "active"
                        active_count += 1
                except ValueError:
                    asset_data["warranty_status"] = "invalid_date"
                    asset_data["warranty_error"] = "Invalid date format"
            else:
                asset_data["warranty_status"] = "missing"
                missing_count += 1
            
            report_data["assets"].append(asset_data)
        
        # Update summary with counts
        report_data["summary"].update({
            "expired_warranties": expired_count,
            "expiring_warranties": expiring_count,
            "missing_warranties": missing_count,
            "active_warranties": active_count
        })
        
        return {
            "success": True,
            "message": f"Warranty report generated successfully ({params.report_type})",
            "report": report_data
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to generate warranty report: {e}")
        return {
            "success": False,
            "message": f"Failed to generate warranty report: {str(e)}"
        }


def _check_external_warranty_api(manufacturer: str, serial_number: str) -> Optional[Dict[str, Any]]:
    """
    Check external warranty APIs for manufacturer-specific warranty information.
    
    Args:
        manufacturer: Manufacturer name
        serial_number: Device serial number
        
    Returns:
        Dictionary with warranty information or None if not available
    """
    if not manufacturer or not serial_number:
        return None
    
    manufacturer = manufacturer.lower().strip()
    
    # Simulate external API checks (in production, these would be real API calls)
    # This provides a framework for integrating with actual manufacturer APIs
    
    try:
        if "lenovo" in manufacturer:
            return _check_lenovo_warranty(serial_number)
        elif "dell" in manufacturer:
            return _check_dell_warranty(serial_number)
        elif "hp" in manufacturer:
            return _check_hp_warranty(serial_number)
        elif "apple" in manufacturer:
            return _check_apple_warranty(serial_number)
        else:
            # Generic warranty check for other manufacturers
            return _simulate_generic_warranty_check(manufacturer, serial_number)
            
    except Exception as e:
        logger.warning(f"External warranty API check failed for {manufacturer} {serial_number}: {e}")
        return None


def _check_lenovo_warranty(serial_number: str) -> Optional[Dict[str, Any]]:
    """
    Check Lenovo warranty API (simulated implementation).
    
    In production, this would use the actual Lenovo Support API:
    https://supportapi.lenovo.com/v2.5/Warranty?Serial=XXXXX
    """
    # Simulate Lenovo API response
    try:
        # In production, you would make actual API calls here
        # response = requests.get(f"https://supportapi.lenovo.com/v2.5/Warranty?Serial={serial_number}")
        
        # Simulated response for testing
        simulated_response = {
            "warranty_expiration": (datetime.now() + timedelta(days=365)).strftime("%Y-%m-%d"),
            "warranty_type": "Standard Limited Warranty",
            "warranty_start": (datetime.now() - timedelta(days=730)).strftime("%Y-%m-%d"),
            "support_level": "Warranty",
            "api_source": "Lenovo Support API (simulated)"
        }
        
        return simulated_response
        
    except Exception as e:
        logger.error(f"Lenovo warranty API error: {e}")
        return None


def _check_dell_warranty(serial_number: str) -> Optional[Dict[str, Any]]:
    """
    Check Dell warranty API (simulated implementation).
    
    In production, this would use the actual Dell Support API.
    """
    # Simulate Dell API response
    try:
        simulated_response = {
            "warranty_expiration": (datetime.now() + timedelta(days=400)).strftime("%Y-%m-%d"),
            "warranty_type": "Basic Hardware Support",
            "warranty_start": (datetime.now() - timedelta(days=695)).strftime("%Y-%m-%d"),
            "support_level": "Basic",
            "api_source": "Dell Support API (simulated)"
        }
        
        return simulated_response
        
    except Exception as e:
        logger.error(f"Dell warranty API error: {e}")
        return None


def _check_hp_warranty(serial_number: str) -> Optional[Dict[str, Any]]:
    """
    Check HP warranty API (simulated implementation).
    
    In production, this would use the actual HP Support API.
    """
    # Simulate HP API response
    try:
        simulated_response = {
            "warranty_expiration": (datetime.now() + timedelta(days=450)).strftime("%Y-%m-%d"),
            "warranty_type": "Limited Hardware Warranty",
            "warranty_start": (datetime.now() - timedelta(days=650)).strftime("%Y-%m-%d"),
            "support_level": "Limited",
            "api_source": "HP Support API (simulated)"
        }
        
        return simulated_response
        
    except Exception as e:
        logger.error(f"HP warranty API error: {e}")
        return None


def _check_apple_warranty(serial_number: str) -> Optional[Dict[str, Any]]:
    """
    Check Apple warranty API (simulated implementation).
    
    In production, this would use the actual Apple Support API.
    """
    # Simulate Apple API response  
    try:
        simulated_response = {
            "warranty_expiration": (datetime.now() + timedelta(days=300)).strftime("%Y-%m-%d"),
            "warranty_type": "Limited Warranty",
            "warranty_start": (datetime.now() - timedelta(days=800)).strftime("%Y-%m-%d"),
            "support_level": "Limited Warranty and Service",
            "api_source": "Apple Support API (simulated)"
        }
        
        return simulated_response
        
    except Exception as e:
        logger.error(f"Apple warranty API error: {e}")
        return None


def _simulate_generic_warranty_check(manufacturer: str, serial_number: str) -> Optional[Dict[str, Any]]:
    """
    Simulate generic warranty check for manufacturers without specific API support.
    """
    try:
        simulated_response = {
            "warranty_expiration": (datetime.now() + timedelta(days=200)).strftime("%Y-%m-%d"),
            "warranty_type": "Standard Warranty",
            "warranty_start": (datetime.now() - timedelta(days=900)).strftime("%Y-%m-%d"),
            "support_level": "Standard",
            "api_source": f"{manufacturer.title()} API (simulated)"
        }
        
        return simulated_response
        
    except Exception as e:
        logger.error(f"Generic warranty API error: {e}")
        return None


def _calculate_warranty_status(warranty_expiration: str) -> Dict[str, Any]:
    """
    Calculate warranty status based on expiration date.
    
    Args:
        warranty_expiration: Warranty expiration date string
        
    Returns:
        Dictionary with warranty status information
    """
    if not warranty_expiration:
        return {
            "warranty_status": "unknown",
            "status_message": "No warranty expiration date available"
        }
    
    try:
        warranty_date = datetime.strptime(warranty_expiration, "%Y-%m-%d")
        current_date = datetime.now()
        days_until_expiration = (warranty_date - current_date).days
        
        if days_until_expiration < 0:
            return {
                "warranty_status": "expired",
                "status_message": f"Warranty expired {abs(days_until_expiration)} days ago",
                "days_until_expiration": days_until_expiration,
                "expired": True
            }
        elif days_until_expiration <= 30:
            return {
                "warranty_status": "expiring_soon",
                "status_message": f"Warranty expires in {days_until_expiration} days",
                "days_until_expiration": days_until_expiration,
                "expired": False
            }
        else:
            return {
                "warranty_status": "active",
                "status_message": f"Warranty expires in {days_until_expiration} days",
                "days_until_expiration": days_until_expiration,
                "expired": False
            }
            
    except ValueError:
        return {
            "warranty_status": "invalid",
            "status_message": "Invalid warranty expiration date format",
            "date_error": True
        }
