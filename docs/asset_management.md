# ServiceNow Asset Management

This document describes the asset management capabilities provided by the ServiceNow MCP server. The asset management tools allow you to create, update, delete, and transfer assets within your ServiceNow instance.

## Overview

Asset management in ServiceNow involves tracking and managing physical and digital assets throughout their lifecycle. The MCP server provides comprehensive tools for:

- Creating new assets with detailed attributes
- Updating existing asset information
- Retrieving asset details by various identifiers
- Listing assets with flexible filtering
- Deleting assets when they're no longer needed
- Transferring assets between users

## Available Tools

### create_asset

Creates a new asset in ServiceNow with the specified attributes.

**Parameters:**
- `asset_tag` (required): Unique asset tag identifier
- `display_name` (required): Display name of the asset
- `model`: Model number or name
- `serial_number`: Serial number of the asset
- `assigned_to`: User assigned to the asset (sys_id or username)
- `location`: Location of the asset
- `cost`: Cost of the asset
- `purchase_date`: Purchase date (YYYY-MM-DD format)
- `warranty_expiration`: Warranty expiration date (YYYY-MM-DD format)
- `category`: Asset category
- `subcategory`: Asset subcategory
- `manufacturer`: Manufacturer of the asset
- `model_category`: Model category sys_id
- `state`: State of the asset (1=In use, 2=In stock, 3=Retired, etc.)
- `substatus`: Substatus of the asset
- `comments`: Comments about the asset

**Example:**
```json
{
  "asset_tag": "LAPTOP001",
  "display_name": "Dell XPS 13 - John Doe",
  "model": "XPS 13 9310",
  "serial_number": "ABCD123456",
  "assigned_to": "john.doe",
  "cost": "1500.00",
  "purchase_date": "2024-01-15",
  "warranty_expiration": "2027-01-15",
  "category": "Computer",
  "manufacturer": "Dell",
  "state": "1"
}
```

### update_asset

Updates an existing asset in ServiceNow.

**Parameters:**
- `asset_id` (required): Asset ID (sys_id) or asset tag
- All other parameters from `create_asset` are optional for updates

**Example:**
```json
{
  "asset_id": "LAPTOP001",
  "assigned_to": "jane.smith",
  "location": "Building A, Floor 2",
  "comments": "Reassigned due to department transfer"
}
```

### get_asset

Retrieves a specific asset by its identifier.

**Parameters (at least one required):**
- `asset_id`: Asset sys_id
- `asset_tag`: Asset tag
- `serial_number`: Serial number

**Example:**
```json
{
  "asset_tag": "LAPTOP001"
}
```

### list_assets

Lists assets with optional filtering and pagination.

**Parameters:**
- `limit`: Maximum number of assets to return (default: 10)
- `offset`: Offset for pagination (default: 0)
- `assigned_to`: Filter by assigned user (sys_id or username)
- `state`: Filter by asset state
- `category`: Filter by category
- `location`: Filter by location
- `name`: Search for assets by display name using LIKE matching
- `query`: Search term that matches against asset tag, display name, serial number, or model

**Example:**
```json
{
  "limit": 20,
  "assigned_to": "john.doe",
  "state": "1",
  "name": "Dell XPS"
}
```

### search_assets_by_name

Dedicated tool for searching assets by display name with LIKE matching.

**Parameters:**
- `name` (required): Name or partial name to search for using LIKE matching
- `limit`: Maximum number of assets to return (default: 10)
- `offset`: Offset for pagination (default: 0)
- `exact_match`: Whether to perform exact match instead of LIKE matching (default: false)

**Example:**
```json
{
  "name": "Dell XPS",
  "limit": 20,
  "exact_match": false
}
```

### delete_asset

Deletes an asset from ServiceNow.

**Parameters:**
- `asset_id` (required): Asset ID (sys_id) or asset tag
- `reason`: Reason for deleting the asset

**Example:**
```json
{
  "asset_id": "LAPTOP001",
  "reason": "Asset disposed due to end of lifecycle"
}
```

### transfer_asset

Transfers an asset to a different user, updating the assignment and adding transfer comments.

**Parameters:**
- `asset_id` (required): Asset ID (sys_id) or asset tag
- `new_assigned_to` (required): New user to assign the asset to (sys_id or username)
- `transfer_reason`: Reason for the transfer
- `comments`: Additional comments about the transfer

**Example:**
```json
{
  "asset_id": "LAPTOP001",
  "new_assigned_to": "jane.smith",
  "transfer_reason": "Department reorganization",
  "comments": "User moving from IT to Marketing department"
}
```

## Asset States

Common asset states in ServiceNow:

- `1`: In use
- `2`: In stock
- `3`: Retired
- `4`: Pending disposal
- `5`: On order
- `6`: In maintenance
- `7`: Missing
- `8`: Stolen

## User Resolution

The asset management tools automatically resolve user identifiers in the following order:

1. If the identifier looks like a sys_id (32-character hex string), it's used directly
2. First attempt to match by username
3. If no match, attempt to match by email address
4. If no match is found, the operation fails with an appropriate error message

## Asset Resolution

Asset identifiers are resolved as follows:

1. If the identifier looks like a sys_id (32-character hex string), it's used directly
2. Otherwise, attempt to match by asset tag
3. If no match is found, the operation fails with an appropriate error message

## Error Handling

All asset management operations include comprehensive error handling:

- **Validation errors**: Invalid parameters or missing required fields
- **Not found errors**: Asset or user not found during resolution
- **API errors**: ServiceNow API communication failures
- **Permission errors**: Insufficient permissions to perform the operation

Errors are returned in a consistent format with descriptive messages to help troubleshoot issues.

## Tool Package Configuration

Asset management tools are included in the following tool packages:

- `system_administrator`: Full access to all asset management operations
- `full`: Complete set of all available tools including asset management

To use asset management tools, ensure your MCP_TOOL_PACKAGE environment variable is set to one of these packages.

## Best Practices

### Asset Creation
- Always use meaningful asset tags that follow your organization's naming convention
- Include as much detail as possible during creation (model, serial number, cost, etc.)
- Set the correct initial state based on the asset's current status
- Assign assets to users when they're being deployed

### Asset Updates
- Use the transfer_asset tool instead of direct updates when changing asset ownership
- Update location information when assets are moved
- Keep warranty and cost information current for accurate reporting

### Asset Transfers
- Always provide a transfer reason for audit trails
- Include relevant comments about the transfer context
- Verify the new user exists before attempting the transfer

### Asset Disposal
- Update asset state to "Retired" or "Pending disposal" before deletion
- Consider using asset states instead of deletion for better audit trails
- Document disposal reasons in comments before deletion

## Integration Examples

### Bulk Asset Import
Use the create_asset tool in combination with data processing to import assets from spreadsheets or other systems.

### Asset Lifecycle Management
Combine multiple tools to manage complete asset lifecycles:
1. Create assets when purchased
2. Update locations and assignments as needed
3. Transfer between users during organizational changes
4. Retire and dispose when end-of-life is reached

### Reporting and Auditing
Use the list_assets tool with various filters to generate reports:
- Assets by user or department
- Assets by location or category
- Assets approaching warranty expiration
- Unassigned or missing assets

This comprehensive asset management capability enables organizations to maintain accurate, up-to-date records of their IT and physical assets through the ServiceNow MCP interface.
