#!/usr/bin/env python3
"""
ServiceNow Request Management Demo

This script demonstrates the request management capabilities of the ServiceNow MCP server.
It shows how to create parent requests, create item requests, list item requests with various 
filters, and clean up demo requests when finished.

Usage:
    python request_management_demo.py                # Run full demo with cleanup

Requirements:
    - ServiceNow instance with proper authentication configured
    - MCP_TOOL_PACKAGE environment variable set to 'full' or another package containing request tools
    - Request management tools: create_item_request, create_request, list_item_requests
    - Direct API access for cleanup operations (uses basic auth to delete records)
"""

import os
import sys
import json
import asyncio
import requests
from datetime import datetime, timedelta

# Add the src directory to the path so we can import the ServiceNow MCP modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from servicenow_mcp.server import ServiceNowMCP
from servicenow_mcp.utils.config import ServerConfig


def load_config():
    """Load configuration from environment variables."""
    instance_url = os.getenv('SNOW_INSTANCE_URL')
    username = os.getenv('SNOW_INSTANCE_UNAME')
    password = os.getenv('SNOW_INSTANCE_PWD')
    
    if not all([instance_url, username, password]):
        print("Error: Missing required environment variables:")
        print("- SNOW_INSTANCE_URL")
        print("- SNOW_INSTANCE_UNAME") 
        print("- SNOW_INSTANCE_PWD")
        sys.exit(1)
    
    return ServerConfig(
        instance_url=instance_url,
        auth={
            "type": "basic",
            "basic": {
                "username": username,
                "password": password
            }
        },
        timeout=30
    )


def demo_create_parent_request(mcp_server):
    """Demonstrate creating a parent request object."""
    print("\n=== Parent Request Creation Demo ===")
    
    # Create a parent request for office supplies
    # Note: CreateRequestParams only supports: requested_for, state, approval
    request_params = {
        "requested_for": "admin",  # Using admin user which should exist
        "state": "1",  # New/Requested
        "approval": "not requested"  # Default approval status
    }
    
    print(f"Creating parent request for user: {request_params['requested_for']}")
    result = asyncio.run(mcp_server._call_tool_impl("create_request", request_params))
    print(f"Result: {result[0].text}")
    
    # Extract request sys_id from the result for linking item requests
    try:
        # The result should contain the sys_id of the created request
        result_text = result[0].text
        # Look for sys_id in the response (typically a 32-character hex string)
        import re
        sys_id_match = re.search(r'[a-f0-9]{32}', result_text)
        if sys_id_match:
            request_sys_id = sys_id_match.group(0)
            print(f"Created parent request with sys_id: {request_sys_id}")
            return request_sys_id
    except Exception as e:
        print(f"Could not extract request sys_id: {e}")
    
    return None


def demo_create_item_requests(mcp_server, parent_request_sys_id=None):
    """Demonstrate creating item requests."""
    print("\n=== Item Request Creation Demo ===")
    print("Note: CreateItemRequestParams supports: number, cat_item, requested_for, quantity, request, state, short_description")
    
    created_items = []
    created_sys_ids = []
    
    # Item Request 1: Apple Watch
    watch_params = {
        "cat_item": "Apple Watch",  # This should match an actual catalog item name in ServiceNow
        "short_description": "Apple Watch Request - Demo",
        "requested_for": "admin",
        "quantity": "1",
        "state": "1",  # New/Requested
    }
    
    # Link to parent request if available
    if parent_request_sys_id:
        watch_params["request"] = parent_request_sys_id
    
    print(f"Creating Apple Watch item request: {watch_params['short_description']}")
    result = asyncio.run(mcp_server._call_tool_impl("create_item_request", watch_params))
    print(f"Result: {result[0].text}")
    created_items.append("Apple Watch")
    
    # Extract sys_id from result
    import re
    sys_id_match = re.search(r'[a-f0-9]{32}', result[0].text)
    if sys_id_match:
        created_sys_ids.append(sys_id_match.group(0))
    
    # Item Request 2: Apple iPad 3
    ipad_params = {
        "cat_item": "Apple iPad 3",  # This should match an actual catalog item name
        "short_description": "Apple iPad 3 Request - Demo",
        "requested_for": "admin",
        "quantity": "1",
        "state": "1",
    }
    
    if parent_request_sys_id:
        ipad_params["request"] = parent_request_sys_id
    
    print(f"Creating Apple iPad 3 item request: {ipad_params['short_description']}")
    result = asyncio.run(mcp_server._call_tool_impl("create_item_request", ipad_params))
    print(f"Result: {result[0].text}")
    created_items.append("Apple iPad 3")
    
    # Extract sys_id from result
    sys_id_match = re.search(r'[a-f0-9]{32}', result[0].text)
    if sys_id_match:
        created_sys_ids.append(sys_id_match.group(0))
    
    # Item Request 3: Apple iPhone 13 pro
    iphone_pro_params = {
        "cat_item": "Apple iPhone 13 pro",  # This should match an actual catalog item name
        "short_description": "Apple iPhone 13 pro Request - Demo",
        "requested_for": "admin",
        "quantity": "1",
        "state": "1",
    }
    
    if parent_request_sys_id:
        iphone_pro_params["request"] = parent_request_sys_id
    
    print(f"Creating Apple iPhone 13 pro item request: {iphone_pro_params['short_description']}")
    result = asyncio.run(mcp_server._call_tool_impl("create_item_request", iphone_pro_params))
    print(f"Result: {result[0].text}")
    created_items.append("Apple iPhone 13 pro")
    
    # Extract sys_id from result
    sys_id_match = re.search(r'[a-f0-9]{32}', result[0].text)
    if sys_id_match:
        created_sys_ids.append(sys_id_match.group(0))
    
    # Item Request 4: Apple iPhone 13
    iphone_params = {
        "cat_item": "Apple iPhone 13",  # This should match an actual catalog item name
        "short_description": "Apple iPhone 13 Request - Demo",
        "requested_for": "admin",
        "quantity": "1",
        "state": "1",
    }
    
    if parent_request_sys_id:
        iphone_params["request"] = parent_request_sys_id
    
    print(f"Creating Apple iPhone 13 item request: {iphone_params['short_description']}")
    result = asyncio.run(mcp_server._call_tool_impl("create_item_request", iphone_params))
    print(f"Result: {result[0].text}")
    created_items.append("Apple iPhone 13")
    
    # Extract sys_id from result
    sys_id_match = re.search(r'[a-f0-9]{32}', result[0].text)
    if sys_id_match:
        created_sys_ids.append(sys_id_match.group(0))
    
    print(f"Created {len(created_items)} item requests: {', '.join(created_items)}")
    print(f"Captured {len(created_sys_ids)} sys_ids for cleanup")
    print("Note: Item requests may fail if the specified catalog items don't exist in your ServiceNow instance")
    return created_items, created_sys_ids


def demo_list_item_requests(mcp_server):
    """Demonstrate listing item requests with various filters."""
    print("\n=== Item Request Listing Demo ===")
    print("Note: ListItemRequestsParams supports: limit, offset, requested_for, cat_item, number, short_description")
    
    # List all item requests (basic)
    print("Listing all item requests (first 15):")
    list_params = {
        "limit": 15
    }
    result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Result: {result[0].text}")
    
    # List item requests by short description (containing "Demo")
    print("\nListing item requests with 'Demo' in short description:")
    list_params = {
        "limit": 10,
        "short_description": "Demo"
    }
    result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Result: {result[0].text}")
    
    # List item requests by catalog item
    print("\nListing item requests for Apple Watch:")
    list_params = {
        "limit": 10,
        "cat_item": "Apple Watch"
    }
    result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Result: {result[0].text}")
    
    # List item requests by requested user
    print("\nListing item requests for admin user:")
    list_params = {
        "limit": 10,
        "requested_for": "admin"
    }
    result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Result: {result[0].text}")
    
    # List item requests with pagination
    print("\nListing item requests with pagination (offset 5, limit 5):")
    list_params = {
        "limit": 5,
        "offset": 5
    }
    result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Result: {result[0].text}")


def demo_list_item_requests_advanced_filters(mcp_server):
    """Demonstrate advanced filtering of item requests with supported parameters."""
    print("\n=== Advanced Item Request Filtering Demo ===")
    
    # Filter by specific short description pattern (Apple Watch)
    print("Searching for Apple Watch-related item requests:")
    list_params = {
        "limit": 10,
        "short_description": "Apple Watch"
    }
    result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Result: {result[0].text}")
    
    # Filter by specific catalog item (Apple iPad 3)
    print("\nSearching for Apple iPad 3 item requests:")
    list_params = {
        "limit": 10,
        "cat_item": "Apple iPad 3"
    }
    result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Result: {result[0].text}")
    
    # Filter by short description containing "iPhone"
    print("\nSearching for iPhone-related item requests:")
    list_params = {
        "limit": 10,
        "short_description": "iPhone"
    }
    result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Result: {result[0].text}")
    
    # Filter by specific catalog item type
    print("\nSearching for Apple iPhone 13 pro requests:")
    list_params = {
        "limit": 10,
        "cat_item": "Apple iPhone 13 pro"
    }
    result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Result: {result[0].text}")


def demo_request_workflow_simulation(mcp_server):
    """Demonstrate a complete request workflow simulation."""
    print("\n=== Request Workflow Simulation Demo ===")
    
    print("Step 1: Creating parent request for new employee onboarding")
    # Create parent request (using only supported parameters)
    parent_params = {
        "requested_for": "admin",
        "state": "1",  # New/Requested
        "approval": "not requested"
    }
    
    parent_result = asyncio.run(mcp_server._call_tool_impl("create_request", parent_params))
    print(f"Parent request created: {parent_result[0].text}")
    
    # Extract parent request sys_id
    parent_request_sys_id = None
    workflow_item_sys_ids = []
    
    try:
        import re
        sys_id_match = re.search(r'[a-f0-9]{32}', parent_result[0].text)
        if sys_id_match:
            parent_request_sys_id = sys_id_match.group(0)
    except:
        pass
    
    print(f"\nStep 2: Creating related item requests for the onboarding")
    
    # Apple Watch
    watch_params = {
        "cat_item": "Apple Watch",  # Matches actual catalog item
        "short_description": "Apple Watch - Demo Workflow",
        "requested_for": "admin",
        "quantity": "1",
        "state": "1",
    }
    
    if parent_request_sys_id:
        watch_params["request"] = parent_request_sys_id
    
    watch_result = asyncio.run(mcp_server._call_tool_impl("create_item_request", watch_params))
    print(f"Apple Watch request: {watch_result[0].text}")
    
    # Extract sys_id from result
    sys_id_match = re.search(r'[a-f0-9]{32}', watch_result[0].text)
    if sys_id_match:
        workflow_item_sys_ids.append(sys_id_match.group(0))
    
    # Apple iPad 3
    ipad_params = {
        "cat_item": "Apple iPad 3",  # Matches actual catalog item
        "short_description": "Apple iPad 3 - Demo Workflow",
        "requested_for": "admin",
        "quantity": "1",
        "state": "1",
    }
    
    if parent_request_sys_id:
        ipad_params["request"] = parent_request_sys_id
    
    ipad_result = asyncio.run(mcp_server._call_tool_impl("create_item_request", ipad_params))
    print(f"Apple iPad 3 request: {ipad_result[0].text}")
    
    # Extract sys_id from result
    sys_id_match = re.search(r'[a-f0-9]{32}', ipad_result[0].text)
    if sys_id_match:
        workflow_item_sys_ids.append(sys_id_match.group(0))
    
    # Apple iPhone 13
    iphone_params = {
        "cat_item": "Apple iPhone 13",  # Matches actual catalog item
        "short_description": "Apple iPhone 13 - Demo Workflow",
        "requested_for": "admin",
        "quantity": "1",
        "state": "1",
    }
    
    if parent_request_sys_id:
        iphone_params["request"] = parent_request_sys_id
    
    iphone_result = asyncio.run(mcp_server._call_tool_impl("create_item_request", iphone_params))
    print(f"Apple iPhone 13 request: {iphone_result[0].text}")
    
    # Extract sys_id from result
    sys_id_match = re.search(r'[a-f0-9]{32}', iphone_result[0].text)
    if sys_id_match:
        workflow_item_sys_ids.append(sys_id_match.group(0))
    
    print(f"\nStep 3: Viewing all item requests for the onboarding workflow")
    # List all demo item requests (since we can't filter by parent request directly)
    list_params = {
        "limit": 15,
        "short_description": "Demo"
    }
    workflow_result = asyncio.run(mcp_server._call_tool_impl("list_item_requests", list_params))
    print(f"Workflow item requests: {workflow_result[0].text}")
    print("Note: Filtering by parent request sys_id is not supported in ListItemRequestsParams")
    
    print(f"Captured {len(workflow_item_sys_ids)} workflow item request sys_ids for cleanup")
    return parent_request_sys_id, workflow_item_sys_ids


def demo_cleanup_item_requests(mcp_server, item_request_sys_ids):
    """Demonstrate cleanup of specific demo item requests."""
    print("\n=== Item Request Cleanup Demo ===")
    
    if not item_request_sys_ids:
        print("No item request sys_ids provided for cleanup")
        return
    
    print(f"Cleaning up {len(item_request_sys_ids)} specific item requests...")
    deleted_count = 0
    
    try:
        # Get server configuration for direct API calls
        config = load_config()
        
        # Delete each specific item request using direct API calls
        for sys_id in item_request_sys_ids:
            try:
                print(f"Deleting item request: {sys_id}")
                
                # Make direct DELETE request to ServiceNow API
                api_url = f"{config.api_url}/table/sc_req_item/{sys_id}"
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                response = requests.delete(
                    api_url,
                    auth=(config.auth.basic.username, config.auth.basic.password),
                    headers=headers,
                    timeout=config.timeout,
                )
                response.raise_for_status()
                
                print(f"Successfully deleted item request: {sys_id}")
                deleted_count += 1
                
            except Exception as e:
                print(f"Failed to delete item request {sys_id}: {e}")
        
        print(f"Successfully deleted {deleted_count} out of {len(item_request_sys_ids)} item request(s)")
            
    except Exception as e:
        print(f"Error during item request cleanup: {e}")
        print("Manual cleanup may be required")


def demo_cleanup_requests(mcp_server, request_sys_ids):
    """Demonstrate cleanup of specific demo parent requests."""
    print("\n=== Parent Request Cleanup Demo ===")
    
    if not request_sys_ids:
        print("No parent request sys_ids provided for cleanup")
        return
    
    print(f"Cleaning up {len(request_sys_ids)} specific parent requests...")
    deleted_count = 0
    
    try:
        # Get server configuration for direct API calls
        config = load_config()
        
        # Delete each specific parent request using direct API calls
        for sys_id in request_sys_ids:
            try:
                print(f"Deleting parent request: {sys_id}")
                
                # Make direct DELETE request to ServiceNow API
                api_url = f"{config.api_url}/table/sc_request/{sys_id}"
                headers = {
                    "Content-Type": "application/json",
                    "Accept": "application/json"
                }
                
                response = requests.delete(
                    api_url,
                    auth=(config.auth.basic.username, config.auth.basic.password),
                    headers=headers,
                    timeout=config.timeout,
                )
                response.raise_for_status()
                
                print(f"Successfully deleted parent request: {sys_id}")
                deleted_count += 1
                
            except Exception as e:
                print(f"Failed to delete parent request {sys_id}: {e}")
        
        print(f"Successfully deleted {deleted_count} out of {len(request_sys_ids)} parent request(s)")
        
    except Exception as e:
        print(f"Error during parent request cleanup: {e}")
        print("Manual cleanup may be required")


def demo_full_cleanup(mcp_server, item_request_sys_ids, request_sys_ids):
    """Perform complete cleanup of specific demo requests."""
    print("\n=== Full Request Cleanup ===")
    
    # Clean up item requests first (child records)
    demo_cleanup_item_requests(mcp_server, item_request_sys_ids)
    
    # Then clean up parent requests
    demo_cleanup_requests(mcp_server, request_sys_ids)
    
    print("\nCleanup completed!")
    print("Note: Some items may not be deletable due to ServiceNow business rules or workflow states")


def main():
    """Run the request management demonstration."""
    print("ServiceNow Request Management Demo")
    print("=" * 42)
    
    # Check tool package
    tool_package = os.getenv('MCP_TOOL_PACKAGE', 'full')
    print(f"Using tool package: {tool_package}")
    
    if 'request' not in ['full', 'service_desk']:  # Check if request tools are likely available
        print("Note: Request management tools should be available in most tool packages.")
    
    # Load configuration and create MCP server
    config = load_config()
    mcp_server = ServiceNowMCP(config)
    
    try:
        # Collect all sys_ids for cleanup
        all_item_request_sys_ids = []
        all_request_sys_ids = []
        
        # Demo 1: Create a parent request
        parent_request_sys_id = demo_create_parent_request(mcp_server)
        if parent_request_sys_id:
            all_request_sys_ids.append(parent_request_sys_id)
        
        # Demo 2: Create multiple item requests
        created_items, item_request_sys_ids = demo_create_item_requests(mcp_server, parent_request_sys_id)
        all_item_request_sys_ids.extend(item_request_sys_ids)
        
        # Demo 3: List item requests with basic filters
        demo_list_item_requests(mcp_server)
        
        # Demo 4: Advanced filtering
        demo_list_item_requests_advanced_filters(mcp_server)
        
        # Demo 5: Complete workflow simulation
        workflow_parent_sys_id, workflow_item_sys_ids = demo_request_workflow_simulation(mcp_server)
        if workflow_parent_sys_id:
            all_request_sys_ids.append(workflow_parent_sys_id)
        all_item_request_sys_ids.extend(workflow_item_sys_ids)
        
        print("\n=== Demo Summary ===")
        print("Request Management Demo completed successfully!")
        print(f"- Created {len(all_request_sys_ids)} parent requests")
        if created_items:
            print(f"- Created {len(created_items)} item requests: {', '.join(created_items)}")
        print(f"- Created {len(workflow_item_sys_ids)} additional workflow item requests")
        print("- Demonstrated various listing and filtering capabilities")
        print("- Simulated a complete onboarding workflow")
        print(f"- Total records created: {len(all_request_sys_ids)} parent requests, {len(all_item_request_sys_ids)} item requests")
        
        print("\n=== Cleanup Demo ===")
        print("Demonstrating cleanup of demo requests...")
        
        # Demo 6: Cleanup demo requests (only the ones we created)
        demo_full_cleanup(mcp_server, all_item_request_sys_ids, all_request_sys_ids)
        
        print("\n=== Additional Cleanup Note ===")
        print("In a production environment, you would typically:")
        print("1. Process or cancel test requests instead of deleting them")
        print("2. Update request states as they progress through workflow")
        print("3. Close completed requests rather than delete them")
        print("4. Use proper approval workflows for request deletion")
        
    except Exception as e:
        print(f"\nError during demo: {str(e)}")
        print("This may be due to:")
        print("1. ServiceNow connection issues")
        print("2. Insufficient permissions for request management")
        print("3. Missing or incorrect configuration")
        print("4. ServiceNow instance not accessible")
        print("5. Request management module not properly configured")
        sys.exit(1)


if __name__ == "__main__":
    main()
