#!/usr/bin/env python
"""
ServiceNow Expense Integration Test

This script demonstrates how to use the ServiceNow MCP server to interact with
expense lines. It serves as an integration test to verify that the expense
functionality works correctly with a real ServiceNow instance.

Prerequisites:
1. Valid ServiceNow credentials with access to Expense Management
2. ServiceNow MCP package installed

Usage:
    python examples/expenses_test.py
"""

import os
import sys
from time import sleep

import requests
from dotenv import load_dotenv

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.tools.expense_tools import (
    ListExpenseLineParams,
    DeleteExpenseLineParams,
    list_expense_lines,
    delete_expense_line,
)
from servicenow_mcp.utils.config import AuthConfig, AuthType, BasicAuthConfig, ServerConfig


def main():
    """Run the expense integration test."""
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

    # Test listing expense lines
    print("\n=== Testing List Expense Lines ===")
    expense_lines, expense_sys_id = test_list_expense_lines(config, auth_manager)

    user_input = input("Do you want to delete the expense line? (y/N): ")
    if user_input.lower() == "y":
        print("\n=== Testing Delete Expense Line ===")
        if expense_sys_id:
            test_delete_expense_line(config, auth_manager, expense_sys_id)
        else:
            print("No expense lines found to delete.")
    else:
        print("Deletion cancelled by user.")

def test_list_expense_lines(config, auth_manager):
    """Test listing expense lines."""
    print("Fetching expense lines...")
    
    # Create the parameters
    params = ListExpenseLineParams(
        limit=10,
        offset=0,
    )

    # Call the tool function directly
    result = list_expense_lines(config, auth_manager, params)
    
    # Print the result
    if result.get("success"):
        expense_lines = result.get("expense_lines", []) # Only print first expense line
        print(f"Found {result.get('count', 0)} expense lines:")
        
        print(f"Expense Number: {expense_lines[0].get('number', 'N/A')}")
        print(f"   Sys ID: {expense_lines[0].get('sys_id', 'N/A')}")
        print(f"   Short Description: {expense_lines[0].get('short_description', 'N/A')}")
        print(f"   Amount: {expense_lines[0].get('amount', 'N/A')}")
        print(f"   Expense Hashtag: {expense_lines[0].get('expense_hashtag', 'N/A')}")
        print(f"   State: {expense_lines[0].get('state', 'N/A')}")
        print()
        
        # Return the first expense sys_id for deletion test
        if expense_lines:
            return expense_lines, expense_lines[0].get("sys_id")
    else:
        print(f"Error: {result.get('message', 'Unknown error')}")
    
    return None, None


def test_delete_expense_line(config, auth_manager, expense_sys_id):
    """Test deleting a specific expense line."""
    print(f"Attempting to delete expense line with sys_id: {expense_sys_id}")
    
    # Create the parameters
    params = DeleteExpenseLineParams(
        sys_id=expense_sys_id,
    )

    # Call the tool function directly
    result = delete_expense_line(config, auth_manager, params)

    # Print the result
    if result.get("success"):
        print(f"Message: {result.get('message')}")
        
    else:
        print(f"✗ Failed to delete expense line: {result.get('message', 'Unknown error')}")

if __name__ == "__main__":
    main()
