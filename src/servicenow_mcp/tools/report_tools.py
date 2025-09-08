"""
Problem management tools for the ServiceNow MCP server.

This module provides tools for creating and managing problems in ServiceNow.
"""

import logging
from typing import Optional, Dict, Any, List

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)

class GetReportParams(BaseModel):
    """Parameters for getting a report. AND operation will be used if multiple parameters are provided."""

    report_id: Optional[str] = Field(None, description="Report ID to get the report for")
    report_ids: Optional[List[str]] = Field(None, description="Filter by multiple report ids. If provided, report_id will be ignored. OR operation will be used if multiple report ids are provided.")
    chart_title: Optional[str] = Field(None, description="Filter by title of the chart") 
    

class BaseResponse(BaseModel):
    """Response from getting a report."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    data: Optional[List] = Field(None, description="Report data")

class GetDashboardTabParams(BaseModel):
    """Parameters for getting the dashboard tab id linked to the dashboard."""

    dashboard_id: str = Field(..., description="Dashboard ID to get the tab for")
    
class GetCanvasParams(BaseModel): 
    """Parameters for getting canvas page id. The canvas page has information about all the widgets (charts) on the dashboard."""

    tab_id: str = Field(..., description="Tab ID to get the canvas page id for")

class GetPortalWidgetsParams(BaseModel): 
    """Parameters for getting all the portal widget ids linked to the canvas page. Each portal widget has information about the report id of one of the charts/reports on the dashboard."""
    canvas_id: str = Field(..., description="Canvas page ID to get the portal widget ids for")

class GetReportIdsFromPortalWidgetsParams(BaseModel): 
    """Parameters for getting all the report ids linked to the portal widgets."""
    portal_widget_ids: List[str] = Field(..., description="Portal widget IDs to get the report ids for")

class GetAnyTableParams(BaseModel): 
    """Parameters for getting records from any ServiceNow table"""

    table: str = Field(..., description="Table to get the records from")
    fields: Optional[List[str]] = Field(None, description="Specific fields to get from the table. If not provided, all fields will be returned.")
    filters: Optional[str] = Field(None, description="Filters to apply to the records. You must provide the field name and value of the field. You can have many field filters together. ^ indicates AND operation. ^OR indicates OR operation. LIKE is used for partial string matching. This must be a string.")
    limit: int = Field(10, description="Limit the number of records to return")

def get_report(
    config: ServerConfig, 
    auth_manager: AuthManager,
    params: GetReportParams,
) -> BaseResponse:
    """
    Get a report from ServiceNow.
    """
    
    api_url = f"{config.api_url}/table/sys_report"
    query_params = {} 

    filters = [] 
    if params.report_ids:
        filters.append(f"sys_idIN{','.join(params.report_ids)}")
    elif params.report_id:
        filters.append(f"sys_id={params.report_id}")
    if params.chart_title:
        filters.append(f"title={params.chart_title}")
    
    if filters:
        query_params["sysparm_query"] = "^".join(filters)

    query_params["sysparm_limit"] = "1" 

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

        return BaseResponse(
            success=True,
            message=f"Report found",
            data=result,
        )
    
    except requests.RequestException as e:
        logger.error(f"Failed to get report: {e}")
        return BaseResponse(
            success=False,
            message=f"Failed to get report: {str(e)}",
            data=None,
        )
    
def get_dashboard_tab(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetDashboardTabParams,
) -> dict:
    """
    Get the dashboard tab id linked to the dashboard.
    """
    
    api_url = f"{config.api_url}/table/pa_m2m_dashboard_tabs"
    query_params = {} 

    filters = [] 
    if params.dashboard_id:
        filters.append(f"dashboard={params.dashboard_id}")
    
    if filters:
        query_params["sysparm_query"] = "^".join(filters)   
    query_params["sysparm_limit"] = "1" 

    try: 
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
            auth=(auth_manager.config.basic.username, auth_manager.config.basic.password)
        ) 
        response.raise_for_status() 
        tab_sys_id = response.json().get("result", [])[0]['tab'].get('value') 

        return {
            "success": True,
            "message": f"Dashboard tab found: {tab_sys_id}",
            "dashboard_tab_id": tab_sys_id,
        } 

    except requests.RequestException as e:
        logger.error(f"Failed to get dashboard tab: {e}")
        return {
            "success": False,
            "message": f"Failed to get dashboard tab: {str(e)}",
        }

def get_canvas(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetCanvasParams,
) -> dict:
    """
    Get the canvas page id linked to the dashboard tab.
    """
    
    api_url = f"{config.api_url}/table/pa_tabs"
    query_params = {
        "sysparm_fields": "canvas_page",
    }  

    filters = [] 
    if params.tab_id:
        filters.append(f"sys_id={params.tab_id}")
    
    if filters:
        query_params["sysparm_query"] = "^".join(filters)   
        
    query_params["sysparm_limit"] = "1" 

    try: 
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
            auth=(auth_manager.config.basic.username, auth_manager.config.basic.password)
        ) 
        response.raise_for_status() 
        canvas_sys_id = response.json().get("result", [])[0]['canvas_page'].get('value') 

        return {
            "success": True,
            "message": f"Canvas page found: {canvas_sys_id}",
            "canvas_page_id": canvas_sys_id,
        } 

    except requests.RequestException as e:
        logger.error(f"Failed to get canvas page: {e}")
        return {
            "success": False,
            "message": f"Failed to get canvas page: {str(e)}",
        }

def get_portal_widgets(     
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetPortalWidgetsParams,
) -> dict:
    """
    Get all the portal widget ids linked to the canvas page.
    """
    
    api_url = f"{config.api_url}/table/sys_grid_canvas_pane" 
    query_params = {
        "sysparm_fields": "portal_widget",
    }  

    filters = [] 
    if params.canvas_id:
        filters.append(f"canvas_page={params.canvas_id}")
    
    if filters:
        query_params["sysparm_query"] = "^".join(filters)   

    try: 
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
            auth=(auth_manager.config.basic.username, auth_manager.config.basic.password)
        ) 
        response.raise_for_status() 
        portal_widget_sys_ids = [x['portal_widget'].get('value') for x in response.json().get("result", [])]

        return {
            "success": True,
            "message": f"{len(portal_widget_sys_ids)} Portal widget ids found: ",
            "portal_widget_ids": portal_widget_sys_ids,
        } 

    except requests.RequestException as e:
        logger.error(f"Failed to get portal widgets: {e}")
        return {
            "success": False,
            "message": f"Failed to get portal widgets: {str(e)}",
        }

def get_report_ids_from_portal_widgets(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetReportIdsFromPortalWidgetsParams,
) -> dict:
    """
    Get all the report ids linked to the portal widgets.
    """
    
    api_url = f"{config.api_url}/table/sys_portal_preferences" 
    query_params = {} 
    filters = [] 
    if params.portal_widget_ids:
        filters.append(f"portal_sectionIN{','.join(params.portal_widget_ids)}^name=sys_id")
    
    if filters:
        query_params["sysparm_query"] = "^".join(filters)   
        
    try: 
        response = requests.get(
            api_url, 
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
            auth=(auth_manager.config.basic.username, auth_manager.config.basic.password)
        ) 
        response.raise_for_status() 
        report_sys_ids = [x['value'] for x in response.json().get("result", [])]
        return {
            "success": True,
            "message": f"{len(report_sys_ids)} Report ids found: ",
            "report_ids": report_sys_ids,
        }
    
    except requests.RequestException as e:
        logger.error(f"Failed to get report ids from portal widgets: {e}")
        return {
            "success": False,
            "message": f"Failed to get report ids from portal widgets: {str(e)}",
        }
        
def search_any_table(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetAnyTableParams,
) -> BaseResponse:
    """
    Search any ServiceNow table.
    """
    
    api_url = f"{config.api_url}/table/{params.table}"
    query_params = {}
    if params.fields:
        query_params["sysparm_fields"] = ",".join(params.fields)
    if params.filters:
        query_params["sysparm_query"] = params.filters
    if params.limit:
        query_params["sysparm_limit"] = str(params.limit)
        
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
        return BaseResponse(
            success=True,
            message=f"Found {len(result)} records",
            data=result,
        )
    
    except requests.RequestException as e:
        logger.error(f"Failed to search any table: {e}")
        return BaseResponse(
            success=False,
            message=f"Failed to search any table: {str(e)}",
            data=None,
        )