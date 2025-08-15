#!/usr/bin/env python3
"""
ServiceNow Asset Management Demo

This script demonstrates the asset management capabilities of the ServiceNow MCP server.
It shows how to create, update, list, transfer, and delete assets.

Usage:
    python asset_management_demo.py

Requirements:
    - ServiceNow instance with proper authentication configured
    - MCP_TOOL_PACKAGE environment variable set to 'system_administrator' or 'full'
"""

import os
import sys
import json
from datetime import datetime, timedelta

# Add the src directory to the path so we can import the ServiceNow MCP modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from servicenow_mcp.server import ServiceNowMCP
from servicenow_mcp.utils.config import ServerConfig


def load_config():
    """Load configuration from environment variables."""
    instance_url = os.getenv('SERVICENOW_INSTANCE_URL')
    username = os.getenv('SERVICENOW_USERNAME')
    password = os.getenv('SERVICENOW_PASSWORD')
    
    if not all([instance_url, username, password]):
        print("Error: Missing required environment variables:")
        print("- SERVICENOW_INSTANCE_URL")
        print("- SERVICENOW_USERNAME") 
        print("- SERVICENOW_PASSWORD")
        sys.exit(1)
    
    return ServerConfig(
        instance_url=instance_url,
        api_url=f"{instance_url}/api/now",
        auth={
            "type": "basic",
            "username": username,
            "password": password
        },
        timeout=30
    )


def demo_create_asset(mcp_server):
    """Demonstrate asset creation."""
    print("\n=== Asset Creation Demo ===")
    
    # Create a laptop asset
    laptop_params = {
        "asset_tag": f"DEMO-LAPTOP-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "display_name": "Demo Dell XPS 13",
        "model": "XPS 13 9310",
        "serial_number": f"DEMO-SN-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "cost": "1500.00",
        "purchase_date": "2024-01-15",
        "warranty_expiration": "2027-01-15",
        "category": "Computer",
        "subcategory": "Laptop",
        "manufacturer": "Dell",
        "state": "2",  # In stock
        "comments": "Demo asset for testing asset management functionality"
    }
    
    print(f"Creating laptop asset with tag: {laptop_params['asset_tag']}")
    result = mcp_server._call_tool_impl("create_asset", laptop_params)
    print(f"Result: {result[0].text}")
    
    # Create a monitor asset
    monitor_params = {
        "asset_tag": f"DEMO-MONITOR-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "display_name": "Demo Dell UltraSharp Monitor",
        "model": "U2720Q",
        "serial_number": f"DEMO-MON-{datetime.now().strftime('%Y%m%d%H%M%S')}",
        "cost": "600.00",
        "purchase_date": "2024-02-01",
        "warranty_expiration": "2027-02-01",
        "category": "Computer",
        "subcategory": "Monitor",
        "manufacturer": "Dell",
        "state": "2",  # In stock
        "comments": "Demo monitor for dual-screen setup"
    }
    
    print(f"Creating monitor asset with tag: {monitor_params['asset_tag']}")
    result = mcp_server._call_tool_impl("create_asset", monitor_params)
    print(f"Result: {result[0].text}")
    
    return laptop_params['asset_tag'], monitor_params['asset_tag']


def demo_list_assets(mcp_server):
    """Demonstrate asset listing with various filters."""
    print("\n=== Asset Listing Demo ===")
    
    # List all demo assets
    print("Listing all demo assets:")
    list_params = {
        "limit": 10,
        "query": "DEMO"
    }
    result = mcp_server._call_tool_impl("list_assets", list_params)
    print(f"Result: {result[0].text}")
    
    # List assets by category
    print("\nListing computer assets:")
    list_params = {
        "limit": 10,
        "category": "Computer"
    }
    result = mcp_server._call_tool_impl("list_assets", list_params)
    print(f"Result: {result[0].text}")
    
    # List assets by name using the name parameter
    print("\nListing assets by name (Dell):")
    list_params = {
        "limit": 10,
        "name": "Dell"
    }
    result = mcp_server._call_tool_impl("list_assets", list_params)
    print(f"Result: {result[0].text}")
    
    # List assets by state (in stock)
    print("\nListing assets in stock:")
    list_params = {
        "limit": 10,
        "state": "2"
    }
    result = mcp_server._call_tool_impl("list_assets", list_params)
    print(f"Result: {result[0].text}")


def demo_search_assets_by_name(mcp_server):
    """Demonstrate searching assets by name."""
    print("\n=== Asset Name Search Demo ===")
    
    # Search for Dell assets using LIKE matching
    print("Searching for Dell assets (LIKE matching):")
    search_params = {
        "name": "Dell",
        "limit": 10,
        "exact_match": False
    }
    result = mcp_server._call_tool_impl("search_assets_by_name", search_params)
    print(f"Result: {result[0].text}")
    
    # Search for exact asset name
    print("\nSearching for exact asset name:")
    search_params = {
        "name": "Demo Dell XPS 13",
        "limit": 10,
        "exact_match": True
    }
    result = mcp_server._call_tool_impl("search_assets_by_name", search_params)
    print(f"Result: {result[0].text}")
    
    # Search for partial name
    print("\nSearching for partial name (XPS):")
    search_params = {
        "name": "XPS",
        "limit": 10,
        "exact_match": False
    }
    result = mcp_server._call_tool_impl("search_assets_by_name", search_params)
    print(f"Result: {result[0].text}")


def demo_get_asset(mcp_server, asset_tag):
    """Demonstrate retrieving a specific asset."""
    print("\n=== Asset Retrieval Demo ===")
    
    print(f"Retrieving asset by tag: {asset_tag}")
    get_params = {
        "asset_tag": asset_tag
    }
    result = mcp_server._call_tool_impl("get_asset", get_params)
    print(f"Result: {result[0].text}")
    
    return json.loads(result[0].text)


def demo_update_asset(mcp_server, asset_tag):
    """Demonstrate asset updates."""
    print("\n=== Asset Update Demo ===")
    
    print(f"Updating asset: {asset_tag}")
    update_params = {
        "asset_id": asset_tag,
        "state": "1",  # Change to "In use"
        "location": "Building A, Floor 2, Desk 42",
        "comments": "Updated during asset management demo - now in use"
    }
    result = mcp_server._call_tool_impl("update_asset", update_params)
    print(f"Result: {result[0].text}")


def demo_transfer_asset(mcp_server, asset_tag):
    """Demonstrate asset transfer."""
    print("\n=== Asset Transfer Demo ===")
    
    # Note: This demo assumes you have a user in your system
    # In a real scenario, you would transfer to an actual user
    print(f"Attempting to transfer asset: {asset_tag}")
    print("Note: This may fail if the demo user doesn't exist in your system")
    
    transfer_params = {
        "asset_id": asset_tag,
        "new_assigned_to": "admin",  # Using admin user which should exist
        "transfer_reason": "Demo transfer for testing",
        "comments": "Transferring asset as part of asset management demonstration"
    }
    result = mcp_server._call_tool_impl("transfer_asset", transfer_params)
    print(f"Result: {result[0].text}")


def demo_delete_asset(mcp_server, asset_tag):
    """Demonstrate asset deletion."""
    print("\n=== Asset Deletion Demo ===")
    
    print(f"Deleting demo asset: {asset_tag}")
    delete_params = {
        "asset_id": asset_tag,
        "reason": "Cleanup after asset management demo"
    }
    result = mcp_server._call_tool_impl("delete_asset", delete_params)
    print(f"Result: {result[0].text}")


def main():
    """Run the asset management demonstration."""
    print("ServiceNow Asset Management Demo")
    print("=" * 40)
    
    # Check tool package
    tool_package = os.getenv('MCP_TOOL_PACKAGE', 'full')
    print(f"Using tool package: {tool_package}")
    
    if tool_package not in ['system_administrator', 'full']:
        print("Warning: Asset management tools may not be available.")
        print("Set MCP_TOOL_PACKAGE to 'system_administrator' or 'full'")
    
    # Load configuration and create MCP server
    config = load_config()
    mcp_server = ServiceNowMCP(config)
    
    try:
        # Demo 1: Create assets
        laptop_tag, monitor_tag = demo_create_asset(mcp_server)
        
        # Demo 2: List assets
        demo_list_assets(mcp_server)
        
        # Demo 3: Search assets by name
        demo_search_assets_by_name(mcp_server)
        
        # Demo 4: Get specific asset
        asset_data = demo_get_asset(mcp_server, laptop_tag)
        
        # Demo 5: Update asset
        demo_update_asset(mcp_server, laptop_tag)
        
        # Demo 6: Transfer asset
        demo_transfer_asset(mcp_server, laptop_tag)
        
        # Demo 7: Verify changes by getting the asset again
        print("\n=== Verifying Changes ===")
        demo_get_asset(mcp_server, laptop_tag)
        
        # Demo 8: Clean up - delete demo assets
        print("\n=== Cleanup ===")
        demo_delete_asset(mcp_server, laptop_tag)
        demo_delete_asset(mcp_server, monitor_tag)
        
        print("\n=== Demo Complete ===")
        print("Asset management demo completed successfully!")
        
    except Exception as e:
        print(f"\nError during demo: {str(e)}")
        print("This may be due to:")
        print("1. ServiceNow connection issues")
        print("2. Insufficient permissions")
        print("3. Missing or incorrect configuration")
        print("4. ServiceNow instance not accessible")
        sys.exit(1)


if __name__ == "__main__":
    main()
