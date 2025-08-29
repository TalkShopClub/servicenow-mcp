"""
Configuration module for the ServiceNow MCP server.
"""

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field
import json
from pathlib import Path 


class AuthType(str, Enum):
    """Authentication types supported by the ServiceNow MCP server."""

    BASIC = "basic"
    OAUTH = "oauth"
    API_KEY = "api_key"


class BasicAuthConfig(BaseModel):
    """Configuration for basic authentication."""

    username: str
    password: str


class OAuthConfig(BaseModel):
    """Configuration for OAuth authentication."""

    client_id: str
    client_secret: str
    username: str
    password: str
    token_url: Optional[str] = None


class ApiKeyConfig(BaseModel):
    """Configuration for API key authentication."""

    api_key: str
    header_name: str = "X-ServiceNow-API-Key"


class AuthConfig(BaseModel):
    """Authentication configuration."""

    type: AuthType
    basic: Optional[BasicAuthConfig] = None
    oauth: Optional[OAuthConfig] = None
    api_key: Optional[ApiKeyConfig] = None


class ServerConfig(BaseModel):
    """Server configuration."""

    instance_url: str
    auth: AuthConfig
    debug: bool = False
    timeout: int = 30

    @property
    def api_url(self) -> str:
        """Get the API URL for the ServiceNow instance."""
        return f"{self.instance_url}/api/now"
    
ADDITIONAL_SOFTWARE = [
    "Slack",
    "Trello",
    "Salesforce",
    "QuickBooks",
    "Zoom",
    "Microsoft Office 365",
    "Google Workspace",
    "Asana",
    "HubSpot",
    "Adobe Creative Cloud",
]

META_CONFIGS = {
    "Developer Laptop (Mac)": {
        "desc": "Macbook Pro",
        "options": {
            "Adobe Acrobat": ("checkbox", [True, False]),
            "Eclipse IDE": ("checkbox", [True, False]),
            "Adobe Photoshop": ("checkbox", [True, False]),
            "Additional software requirements": ("textarea", ADDITIONAL_SOFTWARE),
        },
    },
    "iPad mini": {
        "desc": "Request for iPad mini",
        "options": {
            "Choose the colour": (
                "radio",
                ["Space Grey", "Pink", "Purple", "Starlight"],
            ),
            "Choose the storage": ("radio", ["64", "256"]),
        },
    },
    "iPad pro": {
        "desc": "Request for iPad pro",
        "options": {
            "Choose the colour": ("radio", ["Space Grey", "Silver"]),
            "Choose the storage": ("radio", ["128", "256", "512"]),
        },
    },
    "Sales Laptop": {
        "desc": "Acer Aspire NX",
        "options": {
            "Microsoft Powerpoint": ("checkbox", [True, False]),
            "Adobe Acrobat": ("checkbox", [True, False]),
            "Adobe Photoshop": ("checkbox", [True, False]),
            "Siebel Client": ("checkbox", [True, False]),
            "Additional software requirements": ("textarea", ADDITIONAL_SOFTWARE),
        },
    },
    "Standard Laptop": {
        "desc": "Lenovo - Carbon x1",
        "options": {
            "Adobe Acrobat": ("checkbox", [True, False]),
            "Adobe Photoshop": ("checkbox", [True, False]),
            "Additional software requirements": ("textarea", ADDITIONAL_SOFTWARE),
        },
    },
    "Apple Watch": {
        "desc": "Apple Watch - Their most personal device ever",
        "options": {},
    },
    "Apple MacBook Pro 15": {
        "desc": "Apple MacBook Pro",
        "options": {},
    },
    "Development Laptop (PC)": {
        "desc": "Dell XPS 13",
        "options": {
            "What size solid state drive do you want?": (
                "radio",
                [
                    "250",  # This needs to match both the radio option (250 GB [subtract 300$]) and db request (250)
                    "500",  # Similar as above
                ],
            ),
            "Please specify an operating system": ("radio", ["Windows 8", "Ubuntu"]),
        },
    },
    "Loaner Laptop": {
        "desc": "Short term, while computer is repaired/imaged. Waiting for computer order, special projects, etc. Training, special events, check-in process",
        "options": {
            "When do you need it ?": (
                "textarea",
                [
                    "ASAP",
                    "In 2 weeks",
                    "By the end of the month",
                    "On time for the next meeting",
                    "I needed it yesterday but since you are asking I guess I can wait a bit more",
                    "Do your best, I know you are busy",
                    "I don't need it anymore, I just wanted to see what would happen if I clicked on this button",
                ],
            ),
            "How long do you need it for ?": (
                "radio",
                [
                    "1 day",
                    "1 month",
                    "1 week",
                    "2 weeks",
                    "3 days",
                ],
            ),
        },
    },
}

def get_default_configuration(item_sys_id: str) -> dict: 
    if item_sys_id == '774906834fbb4200086eeed18110c737': 
        item_name = 'Developer Laptop (Mac)'
    elif item_sys_id == 'e8d5f2f29792cd1021983d1e6253af31': 
        item_name = 'iPad mini'
    elif item_sys_id == 'c3b9cbf29716cd1021983d1e6253afad': 
        item_name = 'iPad pro'
    elif item_sys_id == 'e212a942c0a80165008313c59764eea1': 
        item_name = 'Sales Laptop'
    elif item_sys_id == '04b7e94b4f7b4200086eeed18110c7fd': 
        item_name = 'Standard Laptop'
    elif item_sys_id == '4a17d6a3ff133100ba13ffffffffffe7': 
        item_name = 'Apple Watch'
    elif item_sys_id == '2ab7077237153000158bbfc8bcbe5da9': 
        item_name = 'Apple MacBook Pro 15'
    elif item_sys_id == '3cecd2350a0a0a6a013a3a35a5e41c07': 
        item_name = 'Development Laptop (PC)'
    elif item_sys_id == '10f110aec611227601fbe1841e7e417c': 
        item_name = 'Loaner Laptop'
    else: 
        raise ValueError(f"No catalog item found for item sys_id: {item_sys_id}")
    
    requested_configuration = {} 
    for ctrl_name, (ctrl_type, values) in META_CONFIGS[item_name]['options'].items(): 
        requested_configuration[ctrl_name] = (ctrl_type, values[0]) # Reusing the first value as default to match API translation
    
    return requested_configuration