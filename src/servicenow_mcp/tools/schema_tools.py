"""
Schema tools for the ServiceNow MCP server.

This module provides tools for retrieving table schemas in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional, List

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class GetTableSchemaParams(BaseModel):
    """Parameters for listing script includes."""
    
    table_names: List[str] = Field(..., description="List of table names to get the schema for")
    field_names: Optional[Dict[str, List[str]]] = Field(None, description="Dictionary of table names and list of field names to get the schema for, example: {'incident': ['incident_state', 'close_code']}")


def get_table_schema(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetTableSchemaParams,
) -> Dict[str, Any]:
    """List table schemas from ServiceNow.
    
    Args:
        config: The server configuration.
        auth_manager: The authentication manager.
        params: The parameters for the request.
        
    Returns:
        A dictionary containing the list of script includes.
    """
    try:
        # Build the URL
        url_sys_dictionary = f"{config.instance_url}/api/now/table/sys_dictionary"
        url_sys_choices = f"{config.instance_url}/api/now/table/sys_choice"

        table_schemas = {}



        for table_name in params.table_names:
            table_schemas[table_name] = {
                "schema": []
            }
            query_params_dict = {
                "sysparm_query": f"name={table_name}",
                "sysparm_fields": "element,default_value,internal_type,mandatory,reference",
                "sysparm_limit": 10000
            }
            query_params_choice = {
                "sysparm_query": f"name={table_name}",
                "sysparm_fields": "name,element,value,label",
                "sysparm_limit": 10000
            }

            resp_dict = requests.get(
                url_sys_dictionary,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
                params=query_params_dict
            )
            resp_dict.raise_for_status()

            resp_choice = requests.get(
                url_sys_choices,
                headers=auth_manager.get_headers(),
                timeout=config.timeout,
                params=query_params_choice
            )
            resp_choice.raise_for_status()


            resp_dict_result = resp_dict.json().get("result", [])
            resp_choice_result = resp_choice.json().get("result", [])

            if params.field_names:
                field_names = params.field_names.get(table_name, None)
            else:
                field_names = None
            # breakpoint()
            for dict_record in resp_dict_result:
                # breakpoint()
                if field_names and dict_record['element'] not in field_names:
                    continue
                temp = {}
                temp['column_name'] = dict_record['element']
                temp['internal_type'] = dict_record['internal_type'].get('value','')
                temp['mandatory'] = dict_record['mandatory']
                temp['reference'] = dict_record['reference'].get('value','') if dict_record['reference'] else ''
                temp['default_value'] = dict_record['default_value']
                temp['choices'] = []
                for choice_record in resp_choice_result:
                    if choice_record['element'] == dict_record['element']:
                        temp['choices'].append({
                            'value': choice_record['value'],
                            'label': choice_record['label']
                        })
                table_schemas[table_name]['schema'].append(temp)

        return table_schemas


    except Exception as e:
        logger.error(f"Error listing table schemas: {e}")
        return {
            "success": False,
            "message": f"Error listing table schemas: {str(e)}"
        }