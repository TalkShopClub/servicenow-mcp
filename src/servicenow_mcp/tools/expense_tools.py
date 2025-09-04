import logging
from typing import Any, Dict, List, Optional
import traceback

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

class ListExpenseLineParams(BaseModel): 
    """Parameters for getting an expense line."""

    limit: int = Field(10, description="Maximum number of expense lines to return")
    offset: int = Field(0, description="Offset for pagination")
    expense_number: Optional[str] = Field(None, description="Filter expenses by expense number")
    short_description: Optional[str] = Field(None, description="Filter expenses by short description using LIKE matching")
    amount: Optional[str] = Field(None, description="Filter expenses by amount") 
    expense_hashtag: Optional[str] = Field(None, description="Filter expenses by expense hashtag")

class DeleteExpenseLineParams(BaseModel): 
    """Parameters for deleting an expense line."""

    sys_id: str = Field(..., description="Sys ID of the expense line to delete")

class ExpenseLineResponse(BaseModel): 
    """Response from expense line operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    data: Optional[Dict[str, Any]] = Field(None, description="Response data")


def list_expense_lines(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListExpenseLineParams,
) -> dict: 
    """Get an expense line."""

    api_url = f"{config.api_url}/table/fm_expense_line" 
    query_params = {
        "sysparm_limit": str(params.limit),
        "sysparm_offset": str(params.offset),
    } 

    query_parts = []
    if params.expense_number: 
        query_parts.append(f"number={params.expense_number}")
    if params.short_description: 
        query_parts.append(f"short_descriptionLIKE{params.short_description}")
    if params.amount: 
        query_parts.append(f"amount={params.amount}")
    if params.expense_hashtag: 
        query_parts.append(f"expense_hashtagLIKE{params.expense_hashtag}") 

    if query_parts: 
        query_params["sysparm_query"] = "^".join(query_parts) 
    
    try: 
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
            auth=(auth_manager.config.basic.username, auth_manager.config.basic.password)
        ) 
        response.raise_for_status() 
        result = response.json().get("result", []) 

        return {
            "success": True, 
            "message": f"Found {len(result)} expense lines", 
            "expense_lines": result,
            "count": len(result),
        }
    except requests.RequestException as e: 
        logger.error(f"Failed to get expense line: {e}")
        return {
            "success": False, 
            "message": f"Failed to get expense line: {str(e)}", 
        }
    
def delete_expense_line(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: DeleteExpenseLineParams,
) -> ExpenseLineResponse: 
    """Delete an expense line."""

    api_url = f"{config.api_url}/table/fm_expense_line/{params.sys_id}" 
    try: 
        response = requests.delete(
            api_url,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
            auth=(auth_manager.config.basic.username, auth_manager.config.basic.password)
        ) 
        response.raise_for_status() 

        return {
            "success": True, 
            "message": f"Deleted expense line {params.sys_id}",
        }
    except requests.RequestException as e:
        logger.error(f"Failed to delete expense line: {e}")
        return {
            "success": False, 
            "message": f"Failed to delete expense line: {str(e)}", 
        }