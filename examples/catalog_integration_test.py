#!/usr/bin/env python
"""
ServiceNow Catalog Integration Test

This script demonstrates how to use the ServiceNow MCP server to interact with
the ServiceNow Service Catalog. It serves as an integration test to verify that
the catalog functionality works correctly with a real ServiceNow instance.

Prerequisites:
1. Valid ServiceNow credentials with access to the Service Catalog
2. ServiceNow MCP package installed

Usage:
    python examples/catalog_integration_test.py
"""

import os
import sys

import requests
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.catalog_tools import (
    GetCatalogItemParams,
    ListCatalogCategoriesParams,
    ListCatalogItemsParams,
    OrderCatalogItemParams,
    get_catalog_item,
    list_catalog_categories,
    list_catalog_items,
    order_catalog_item,
)
from servicenow_mcp.tools.request_tools import (
    ListItemRequestsParams,
    list_item_requests,
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


def main():
    """Run the catalog integration test."""
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

    # # Test listing catalog categories
    # print("\n=== Testing List Catalog Categories ===")
    # category_id = test_list_catalog_categories(config, auth_manager)

    # # Test listing catalog items
    # print("\n=== Testing List Catalog Items ===")
    # item_id = test_list_catalog_items(config, auth_manager, category_id)

    # # Test getting a specific catalog item
    # if item_id:
    #     print("\n=== Testing Get Catalog Item ===")
    #     test_get_catalog_item(config, auth_manager, item_id)

    # Test ordering catalog items
    print("\n=== Testing Order Catalog Item ===")
    test_order_catalog_item(config, auth_manager)


def test_list_catalog_categories(config, auth_manager):
    """Test listing catalog categories."""
    print("Fetching catalog categories...")
    
    # Create the parameters
    params = ListCatalogCategoriesParams(
        limit=5,
        offset=0,
        query="",
        active=True,
    )

    # Call the tool function directly
    result = list_catalog_categories(config, auth_manager, params)
    
    # Print the result
    print(f"Found {result.get('total', 0)} catalog categories:")
    for i, category in enumerate(result.get("categories", []), 1):
        print(f"{i}. {category.get('title')} (ID: {category.get('sys_id')})")
        print(f"   Description: {category.get('description', 'N/A')}")
        print()
    
    # Save the first category ID for later use
    if result.get("categories"):
        return result["categories"][0]["sys_id"]
    return None


def test_list_catalog_items(config, auth_manager, category_id=None):
    """Test listing catalog items."""
    print("Fetching catalog items...")
    
    # Create the parameters
    params = ListCatalogItemsParams(
        limit=5,
        offset=0,
        query="",
        category=category_id,  # Filter by category if provided
        active=True,
    )

    # Call the tool function directly
    result = list_catalog_items(config, auth_manager, params)
    
    # Print the result
    print(f"Found {result.get('total', 0)} catalog items:")
    for i, item in enumerate(result.get("items", []), 1):
        print(f"{i}. {item.get('name')} (ID: {item.get('sys_id')})")
        print(f"   Description: {item.get('short_description', 'N/A')}")
        print(f"   Category: {item.get('category', 'N/A')}")
        print(f"   Price: {item.get('price', 'N/A')}")
        print()
    
    # Save the first item ID for later use
    if result.get("items"):
        return result["items"][0]["sys_id"]
    return None


def test_get_catalog_item(config, auth_manager, item_id):
    """Test getting a specific catalog item."""
    print(f"Fetching details for catalog item: {item_id}")
    
    # Create the parameters
    params = GetCatalogItemParams(
        item_id=item_id,
    )

    # Call the tool function directly
    result = get_catalog_item(config, auth_manager, params)
    
    # Print the result
    if result.success:
        print(f"Retrieved catalog item: {result.data.get('name')} (ID: {result.data.get('sys_id')})")
        print(f"Description: {result.data.get('description', 'N/A')}")
        print(f"Category: {result.data.get('category', 'N/A')}")
        print(f"Price: {result.data.get('price', 'N/A')}")
        print(f"Delivery Time: {result.data.get('delivery_time', 'N/A')}")
        print(f"Availability: {result.data.get('availability', 'N/A')}")
        
        # Print variables
        variables = result.data.get("variables", [])
        if variables:
            print("\nVariables:")
            for i, variable in enumerate(variables, 1):
                print(f"{i}. {variable.get('label')} ({variable.get('name')})")
                print(f"   Type: {variable.get('type')}")
                print(f"   Mandatory: {variable.get('mandatory')}")
                print(f"   Default Value: {variable.get('default_value', 'N/A')}")
                print()
    else:
        print(f"Error: {result.message}")


def test_order_catalog_item(config, auth_manager):
    """Test ordering catalog items."""
    from time import sleep 

    order_sys_ids = []
    req_item_sys_ids = []
    
    try:
        print("Testing catalog item ordering...")
        
        # Test 1: Order using catalog item name with requested_for as "Amber Willis"
        print("\n--- Test 1: Order using item name ---")
        params1 = OrderCatalogItemParams(
            item="Developer Laptop (Mac)",  # Using item name
            quantity="1",
            requested_for="Amber Willis"
        )
        
        result1 = order_catalog_item(config, auth_manager, params1)
        
        if result1.success:
            order_sys_id1 = result1.data['result']['sys_id']
            order_sys_ids.append(order_sys_id1)
            print(f"✓ Successfully ordered item using name. Order ID: {order_sys_id1}")
            # Check if the order is created

            print('Waiting for 2 seconds to wait for DB to update')
            sleep(2)

            result1 = list_item_requests(config, auth_manager, ListItemRequestsParams(request_id=order_sys_id1)) 
            req_item_sys_ids.append(result1['item_requests'][0]['sys_id'])
            print('Found item request sys_id: ', result1['item_requests'][0]['sys_id'])
            print("--------------------------------")
        else:
            print(f"✗ Failed to order item using name: {result1.message}")
        
        # Test 2: Order using catalog item sys_id with requested_for as sys_id
        print("\n--- Test 2: Order using item sys_id ---")
        params2 = OrderCatalogItemParams(
            item="774906834fbb4200086eeed18110c737",  # Developer Laptop (Mac) sys_id
            quantity="1",
            requested_for="001a76dcc367a2107bd371edd4013149"  # sys_id for requested_for
        )
        
        result2 = order_catalog_item(config, auth_manager, params2)
        
        if result2.success:
            order_sys_id2 = result2.data['result']['sys_id']
            order_sys_ids.append(order_sys_id2)
            print(f"✓ Successfully ordered item using sys_id. Order ID: {order_sys_id2}")
            # Check if the order is created
            print('Waiting for 2 seconds to wait for DB to update')
            sleep(2)

            result2 = list_item_requests(config, auth_manager, ListItemRequestsParams(request_id=order_sys_id2)) 
            req_item_sys_ids.append(result2['item_requests'][0]['sys_id'])
            print('Found item request sys_id: ', result2['item_requests'][0]['sys_id'])
            print("--------------------------------")
        else:
            print(f"✗ Failed to order item using sys_id: {result2.message}")
            
    except Exception as e:
        print(f"✗ Error during ordering test: {str(e)}")
        import traceback
        print(traceback.format_exc())
    
    # Cleanup: Delete the created orders
    if order_sys_ids:
        print(f"\n--- Cleanup: Deleting {len(order_sys_ids)} test orders ---")
        print(f"Order sys ids: {order_sys_ids}")
        print(f"Req item sys ids: {req_item_sys_ids}")
        cleanup_orders(config, auth_manager, order_sys_ids)


def cleanup_orders(config: ServerConfig, auth_manager: AuthManager, order_sys_ids):
    """Clean up test orders by deleting them."""
    headers = auth_manager.get_headers()
    headers["Accept"] = "application/json"
    
    for order_id in order_sys_ids:
        try:
            # Delete the order using the ServiceNow API
            url = f"{config.instance_url}api/now/table/sc_request/{order_id}"
            response = requests.delete(url, auth=(config.auth.basic.username, config.auth.basic.password), headers=headers)
            response.raise_for_status()
            print(f"✓ Deleted order: {order_id}")
        except Exception as e:
            print(f"✗ Failed to delete order {order_id}: {str(e)}")


if __name__ == "__main__":
    main() 