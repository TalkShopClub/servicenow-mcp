#!/usr/bin/env python
"""
ServiceNow Report Integration Test

This script demonstrates how to use the ServiceNow MCP server to interact with
reports and dashboards. It serves as an integration test to verify that the report
functionality works correctly with a real ServiceNow instance.

Prerequisites:
1. Valid ServiceNow credentials with access to Report Management
2. ServiceNow MCP package installed

Usage:
    python examples/report_test.py
"""

import os
import sys

from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.report_tools import (
    GetReportParams,
    GetDashboardTabParams,
    GetCanvasParams,
    GetPortalWidgetsParams,
    GetReportIdsFromPortalWidgetsParams,
    GetAnyTableParams,
    get_report,
    get_dashboard_tab,
    get_canvas,
    get_portal_widgets,
    get_report_ids_from_portal_widgets,
    search_any_table,
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


def main():
    """Run the report integration test."""
    # Load environment variables
    load_dotenv()

    # Get configuration from environment variables
    instance_url = os.getenv("SERVICENOW_INSTANCE_URL")
    username = os.getenv("SERVICENOW_USERNAME")
    password = os.getenv("SERVICENOW_PASSWORD")

    if not instance_url or not username or not password:
        print("Error: Missing required environment variables.")
        print("Please set SERVICENOW_INSTANCE_URL, SERVICENOW_USERNAME, and SERVICENOW_PASSWORD.")
        sys.exit(1)

    print(f"Connecting to ServiceNow instance: {instance_url}")

    # Create the server config
    config = ServerConfig(
        instance_url=instance_url,
        auth=AuthConfig(
            type=AuthType.BASIC,
            basic=BasicAuthConfig(username=username, password=password),
        ),
    )
    
    # Create the auth manager
    auth_manager = AuthManager(config.auth)

    # Main test: Cascade workflow to find "Incidents per week" report
    print("\n=== Finding 'Incidents per week' Report via Cascade Workflow ===")
    test_cascade_to_incidents_report(config, auth_manager)

    # Test the search_any_table function
    print("\n=== Testing Search Any Table Function ===")
    test_search_any_table(config, auth_manager)

def test_cascade_to_incidents_report(config, auth_manager):
    """
    Main test function that demonstrates the complete cascade workflow:
    Dashboard ID -> Tab ID -> Canvas ID -> Portal Widgets -> Report IDs -> "Incidents per week" Report
    """
    dashboard_id = "18b1f472533130104c90ddeeff7b12a6"
    target_chart_title = "Incidents per week"
    
    print(f"Starting cascade workflow for dashboard: {dashboard_id}")
    print(f"Target: Find report with chart title '{target_chart_title}'")
    print("-" * 60)
    
    # Step 1: Get dashboard tab
    print("Step 1: Getting dashboard tab...")
    tab_params = GetDashboardTabParams(dashboard_id=dashboard_id)
    tab_result = get_dashboard_tab(config, auth_manager, tab_params)
    
    if not tab_result.get("success"):
        print(f"✗ Failed at Step 1: {tab_result.get('message')}")
        return None
    
    tab_id = tab_result.get("dashboard_tab_id")
    print(f"✓ Step 1 Success: Found tab ID: {tab_id}")
    
    # Step 2: Get canvas page
    print("\nStep 2: Getting canvas page...")
    canvas_params = GetCanvasParams(tab_id=tab_id)
    canvas_result = get_canvas(config, auth_manager, canvas_params)
    
    if not canvas_result.get("success"):
        print(f"✗ Failed at Step 2: {canvas_result.get('message')}")
        return None
    
    canvas_id = canvas_result.get("canvas_page_id")
    print(f"✓ Step 2 Success: Found canvas ID: {canvas_id}")
    
    # Step 3: Get portal widgets
    print("\nStep 3: Getting portal widgets...")
    widgets_params = GetPortalWidgetsParams(canvas_id=canvas_id)
    widgets_result = get_portal_widgets(config, auth_manager, widgets_params)
    
    if not widgets_result.get("success"):
        print(f"✗ Failed at Step 3: {widgets_result.get('message')}")
        return None
    
    portal_widget_ids = widgets_result.get("portal_widget_ids", [])
    print(f"✓ Step 3 Success: Found {len(portal_widget_ids)} portal widgets")
    
    # Step 4: Get report IDs from portal widgets
    print("\nStep 4: Getting report IDs from portal widgets...")
    report_ids_params = GetReportIdsFromPortalWidgetsParams(portal_widget_ids=portal_widget_ids)
    report_ids_result = get_report_ids_from_portal_widgets(config, auth_manager, report_ids_params)
    
    if not report_ids_result.get("success"):
        print(f"✗ Failed at Step 4: {report_ids_result.get('message')}")
        return None
    
    report_ids = report_ids_result.get("report_ids", [])
    print(f"✓ Step 4 Success: Found {len(report_ids)} report IDs")
    
    # Step 5: Find the specific "Incidents per week" report
    print(f"\nStep 5: Searching for '{target_chart_title}' report...")
    incidents_report = None
    
    # Step 6: Find the specific "Incidents per week" report by title and one of the report ids
    title_params = GetReportParams(
        report_ids=report_ids,
        chart_title=target_chart_title
    )
    report_response = get_report(config, auth_manager, title_params)
    
    if report_response.success:
        incidents_report = report_response.data[0]
        print(f"✓ Step 5 Success: Found report by title search!")
    else:
        print(f"✗ Failed at Step 5: {report_response.message}")
        return None
    
    # Display final results
    print("\n" + "="*60)
    print("FINAL RESULTS")
    print("="*60)
    
    if incidents_report:
        print(f"🎉 SUCCESS: Found the '{target_chart_title}' report!")
        print(f"   Report ID: {incidents_report.get('sys_id', 'N/A')}")
        print(f"   Title: {incidents_report.get('title', 'N/A')}")
        print(f"   Table: {incidents_report.get('table', 'N/A')}")
        print(f"   Type: {incidents_report.get('type', 'N/A')}")
        print(f"   Created: {incidents_report.get('sys_created_on', 'N/A')}")
        print(f"   Updated: {incidents_report.get('sys_updated_on', 'N/A')}")
        
        return incidents_report
    else:
        print(f"❌ FAILURE: Could not find '{target_chart_title}' report")
        print(f"   Searched through {len(report_ids)} reports from the dashboard")
        print(f"   Dashboard path was successful up to report ID retrieval")
        return None

def test_search_any_table(config, auth_manager):
    """
    Test the search_any_table function with asmt_assessment_instance table.
    """
    print("Testing search_any_table function...")
    print("Table: asmt_assessment_instance")
    print("Filter: ^sys_created_on<javascript:gs.dateGenerate('2025-07-15','00:00:00')^metric_type.evaluation_method!=rating^EQ")
    print("Fields: assessment_group")
    print("-" * 60)
    
    # Create parameters for the search
    search_params = GetAnyTableParams(
        table="asmt_assessment_instance",
        fields=["assessment_group"],
        filters="sys_created_on<javascript:gs.dateGenerate('2025-07-15','00:00:00')^metric_type.evaluation_method!=rating^EQ",
        limit=10
    )
    
    # Call the search function
    result = search_any_table(config, auth_manager, search_params)
    
    # Display results
    if result.success:
        records = result.data
        print(f"✓ Search successful!")
        print(f"   Found {len(records)} records")
        print(f"   Message: {result.message}")
        
        if records:
            print("\n📋 Sample Records:")
            for i, record in enumerate(records[:5], 1):  # Show first 5 records
                assessment_group = record.get('assessment_group', 'N/A')
                sys_id = record.get('sys_id', 'N/A')
                print(f"   Record {i}:")
                print(f"      Sys ID: {sys_id}")
                print(f"      Assessment Group: {assessment_group}")
            
            if len(records) > 5:
                print(f"   ... and {len(records) - 5} more records")
        else:
            print("   No records found matching the criteria")
            
        return records
    else:
        print(f"✗ Search failed: {result.message}")
        return None

def test_get_report(config, auth_manager):
    """
    Test the get_report function.
    """
    report_params = GetReportParams(
        report_id="18b1f472533130104c90ddeeff7b12a6",
        report_ids = [
            "18b1f472533130104c90ddeeff7b12a6",
        ]
    )
    report_result = get_report(config, auth_manager, report_params)
    print(report_result.data)

if __name__ == "__main__":
    main()
