"""
Utility functions for resolving ServiceNow identifiers.

This module provides functions for resolving various ServiceNow identifiers
(catalog items, users, etc.) to their sys_id values.
"""

import logging
from typing import Optional, Dict

import requests

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


def resolve_catalog_item_id(
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
                
    # Try loose matching on name and username before giving up 
    query_params = {
        "sysparm_query": f"nameLIKE{catalog_item_identifier}",
        "sysparm_limit": "1",
    }

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

    return None


def resolve_user_id(
    config: ServerConfig,
    auth_manager: AuthManager,
    user_identifier: str,
) -> Optional[str]:
    """
    Resolve a user identifier (username, name, email, or sys_id) to a sys_id.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        user_identifier: User identifier (username, email, or sys_id).

    Returns:
        The sys_id of the user if found, otherwise None.
    """
    # If it looks like a sys_id, return as is
    if len(user_identifier) == 32 and all(c in "0123456789abcdef" for c in user_identifier):
        return user_identifier
    
    api_url = f"{config.api_url}/table/sys_user"
    
    # Try user_name first, then name, then email
    for field in ["user_name", "name", "email"]:
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

def resolve_asset_id(
    config: ServerConfig,
    auth_manager: AuthManager,
    asset_identifier: str,
) -> Optional[str]:
    """
    Resolve an asset identifier (asset_tag or sys_id) to a sys_id.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        asset_identifier: Asset identifier (asset_tag or sys_id).

    Returns:
        Asset sys_id if found, None otherwise.
    """
    # If it looks like a sys_id, return as is
    if len(asset_identifier) == 32 and all(c in "0123456789abcdef" for c in asset_identifier):
        return asset_identifier

    api_url = f"{config.api_url}/table/alm_asset"
    query_params = {
        "sysparm_query": f"asset_tag={asset_identifier}",
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
        logger.error(f"Failed to resolve asset ID for asset_tag={asset_identifier}: {e}")

    return None

def map_to_servicenow_variable_names(url, catalog_item_sys_id: str, requested_configuration: Dict, headers, auth) -> Dict[str, str]:
        """
        Map display names to ServiceNow variable names by querying the item_option_new table.
        
        Args:
            catalog_item_sys_id: The catalog item's sys_id
            requested_configuration: Configuration dict with display names
            
        Returns:
            Dict mapping ServiceNow variable names to values
        """
        try:
            url = f"{url}api/now/table/item_option_new"
            # Get all variables for this catalog item
            variables_result = requests.get(
                url,
                params={
                    'sysparm_query': f'cat_item={catalog_item_sys_id}',
                    'sysparm_fields': 'name,question_text'
                }, 
                headers=headers,
                auth=auth,
            )
            variables_result.raise_for_status()
            variables_result = variables_result.json()
            
            # Create mapping from question_text (display name) to name (variable name)
            display_to_variable = {}
            for var in variables_result.get('result', []):
                question_text = var.get('question_text', '')
                variable_name = var.get('name', '')
                if question_text and variable_name:
                    display_to_variable[question_text] = variable_name
            
            # Map the requested configuration to ServiceNow variable names
            servicenow_variables = {}
            for field_name, (element_type, value) in requested_configuration.items():
                servicenow_var_name = display_to_variable.get(field_name)
                if servicenow_var_name:
                    servicenow_variables[servicenow_var_name] = str(value)
                    logger.debug(f"Mapped '{field_name}' -> '{servicenow_var_name}': {value}")
                else:
                    logger.warning(f"Could not map display name '{field_name}' to ServiceNow variable")
            
            return servicenow_variables
            
        except Exception as e:
            logger.error(f"Error mapping variable names: {e}")
            # Fallback: use display names as-is
            return {field_name: str(value) for field_name, (_, value) in requested_configuration.items()}