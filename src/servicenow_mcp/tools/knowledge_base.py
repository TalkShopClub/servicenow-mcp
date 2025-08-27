"""
Knowledge base tools for the ServiceNow MCP server.

This module provides tools for managing knowledge bases, categories, and articles in ServiceNow.
"""

import logging
from typing import Any, Dict, Optional

import requests
from pydantic import BaseModel, Field

from servicenow_mcp.auth.auth_manager import AuthManager
from servicenow_mcp.utils.config import ServerConfig

logger = logging.getLogger(__name__)


class CreateKnowledgeBaseParams(BaseModel):
    """Parameters for creating a knowledge base."""

    title: str = Field(..., description="Title of the knowledge base")
    description: Optional[str] = Field(None, description="Description of the knowledge base")
    owner: Optional[str] = Field(None, description="The specified admin user or group")
    managers: Optional[str] = Field(None, description="Users who can manage this knowledge base")
    publish_workflow: Optional[str] = Field("Knowledge - Instant Publish", description="Publication workflow")
    retire_workflow: Optional[str] = Field("Knowledge - Instant Retire", description="Retirement workflow")


class ListKnowledgeBasesParams(BaseModel):
    """Parameters for listing knowledge bases."""
    
    limit: int = Field(10, description="Maximum number of knowledge bases to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(None, description="Filter by active status")
    query: Optional[str] = Field(None, description="Search query for knowledge bases")


class CreateCategoryParams(BaseModel):
    """Parameters for creating a category in a knowledge base."""

    title: str = Field(..., description="Title of the category")
    description: Optional[str] = Field(None, description="Description of the category")
    knowledge_base: str = Field(..., description="The knowledge base to create the category in")
    parent_category: Optional[str] = Field(None, description="Parent category (if creating a subcategory). Sys_id refering to the parent category or sys_id of the parent table.")
    parent_table: Optional[str] = Field(None, description="Parent table (if creating a subcategory). Sys_id refering to the table where the parent category is defined.")
    active: bool = Field(True, description="Whether the category is active")


class CreateArticleParams(BaseModel):
    """Parameters for creating a knowledge article."""

    title: str = Field(..., description="Title of the article")
    text: str = Field(..., description="The main body text for the article. Field supports html formatting and wiki markup based on the article_type. HTML is the default.")
    short_description: str = Field(..., description="Short description of the article")
    knowledge_base: str = Field(..., description="The knowledge base to create the article in")
    category: str = Field(..., description="Category for the article")
    keywords: Optional[str] = Field(None, description="Keywords for search")
    article_type: Optional[str] = Field("html", description="The type of article. Options are 'text' or 'wiki'. text lets the text field support html formatting. wiki lets the text field support wiki markup.")


class UpdateArticleParams(BaseModel):
    """Parameters for updating a knowledge article."""

    article_id: str = Field(..., description="ID of the article to update")
    title: Optional[str] = Field(None, description="Updated title of the article")
    text: Optional[str] = Field(None, description="Updated main body text for the article. Field supports html formatting and wiki markup based on the article_type. HTML is the default.")
    short_description: Optional[str] = Field(None, description="Updated short description")
    category: Optional[str] = Field(None, description="Updated category for the article")
    keywords: Optional[str] = Field(None, description="Updated keywords for search")


class PublishArticleParams(BaseModel):
    """Parameters for publishing a knowledge article."""

    article_id: str = Field(..., description="ID of the article to publish")
    workflow_state: Optional[str] = Field("published", description="The workflow state to set")
    workflow_version: Optional[str] = Field(None, description="The workflow version to use")


class ListArticlesParams(BaseModel):
    """Parameters for listing knowledge articles."""
    
    limit: int = Field(10, description="Maximum number of articles to return")
    offset: int = Field(0, description="Offset for pagination")
    knowledge_base: Optional[str] = Field(None, description="Filter by knowledge base")
    category: Optional[str] = Field(None, description="Filter by category")
    query: Optional[str] = Field(None, description="Search query for articles")
    workflow_state: Optional[str] = Field(None, description="Filter by workflow state")


class GetArticleParams(BaseModel):
    """Parameters for getting a knowledge article."""

    article_id: str = Field(..., description="ID of the article to get")


class KnowledgeBaseResponse(BaseModel):
    """Response from knowledge base operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    kb_id: Optional[str] = Field(None, description="ID of the affected knowledge base")
    kb_name: Optional[str] = Field(None, description="Name of the affected knowledge base")


class CategoryResponse(BaseModel):
    """Response from category operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    category_id: Optional[str] = Field(None, description="ID of the affected category")
    category_name: Optional[str] = Field(None, description="Name of the affected category")


class ArticleResponse(BaseModel):
    """Response from article operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    article_id: Optional[str] = Field(None, description="ID of the affected article")
    article_title: Optional[str] = Field(None, description="Title of the affected article")
    workflow_state: Optional[str] = Field(None, description="Current workflow state of the article")


class ListCategoriesParams(BaseModel):
    """Parameters for listing categories in a knowledge base."""
    
    knowledge_base: Optional[str] = Field(None, description="Filter by knowledge base ID")
    parent_category: Optional[str] = Field(None, description="Filter by parent category ID")
    limit: int = Field(10, description="Maximum number of categories to return")
    offset: int = Field(0, description="Offset for pagination")
    active: Optional[bool] = Field(None, description="Filter by active status")
    query: Optional[str] = Field(None, description="Search query for categories")


class SearchKnowledgeBaseParams(BaseModel):
    """Parameters for searching knowledge base articles."""
    
    search_term: str = Field(..., description="Term to search for in articles")
    knowledge_base: Optional[str] = Field(None, description="Filter by specific knowledge base name or ID")
    limit: int = Field(10, description="Maximum number of articles to return")
    offset: int = Field(0, description="Offset for pagination")
    workflow_state: Optional[str] = Field(None, description="Filter by workflow state (e.g., published)")


class AddCommentToKBParams(BaseModel):
    """Parameters for adding a comment to a knowledge base article."""
    
    article_id: str = Field(..., description="ID of the article to comment on")
    comment: str = Field(..., description="Comment text to add")
    is_work_note: bool = Field(False, description="Whether the comment is a work note (internal)")


class DeleteUserParams(BaseModel):
    """Parameters for deleting a user."""
    
    user_id: Optional[str] = Field(None, description="User ID (sys_id) to delete")
    user_name: Optional[str] = Field(None, description="Username to delete")
    email: Optional[str] = Field(None, description="Email address of user to delete")


class CreateServiceRequestParams(BaseModel):
    """Parameters for creating a service catalog request."""
    
    catalog_item: str = Field(..., description="Catalog item name or sys_id to request")
    requested_for: Optional[str] = Field(None, description="User sys_id the request is for")
    quantity: int = Field(1, description="Number of items to request")
    short_description: Optional[str] = Field(None, description="Short description for the request")
    description: Optional[str] = Field(None, description="Detailed description for the request")
    variables: Optional[Dict[str, Any]] = Field(None, description="Variables for the catalog item")


def create_knowledge_base(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateKnowledgeBaseParams,
) -> KnowledgeBaseResponse:
    """
    Create a new knowledge base in ServiceNow.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for creating the knowledge base.

    Returns:
        Response with the created knowledge base details.
    """
    api_url = f"{config.api_url}/table/kb_knowledge_base"

    # Build request data
    data = {
        "title": params.title,
    }

    if params.description:
        data["description"] = params.description
    if params.owner:
        data["owner"] = params.owner
    if params.managers:
        data["kb_managers"] = params.managers
    if params.publish_workflow:
        data["workflow_publish"] = params.publish_workflow
    if params.retire_workflow:
        data["workflow_retire"] = params.retire_workflow

    # Make request
    try:
        response = requests.post(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return KnowledgeBaseResponse(
            success=True,
            message="Knowledge base created successfully",
            kb_id=result.get("sys_id"),
            kb_name=result.get("title"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to create knowledge base: {e}")
        return KnowledgeBaseResponse(
            success=False,
            message=f"Failed to create knowledge base: {str(e)}",
        )


def list_knowledge_bases(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListKnowledgeBasesParams,
) -> Dict[str, Any]:
    """
    List knowledge bases with filtering options.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing knowledge bases.

    Returns:
        Dictionary with list of knowledge bases and metadata.
    """
    api_url = f"{config.api_url}/table/kb_knowledge_base"

    # Build query parameters
    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "true",
    }

    # Build query string
    query_parts = []
    if params.active is not None:
        query_parts.append(f"active={str(params.active).lower()}")
    if params.query:
        query_parts.append(f"titleLIKE{params.query}^ORdescriptionLIKE{params.query}")

    if query_parts:
        query_params["sysparm_query"] = "^".join(query_parts)

    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        # Get the JSON response 
        json_response = response.json()
        
        # Safely extract the result
        if isinstance(json_response, dict) and "result" in json_response:
            result = json_response.get("result", [])
        else:
            logger.error("Unexpected response format: %s", json_response)
            return {
                "success": False,
                "message": "Unexpected response format",
                "knowledge_bases": [],
                "count": 0,
                "limit": params.limit,
                "offset": params.offset,
            }

        # Transform the results - create a simpler structure
        knowledge_bases = []
        
        # Handle either string or list
        if isinstance(result, list):
            for kb_item in result:
                if not isinstance(kb_item, dict):
                    logger.warning("Skipping non-dictionary KB item: %s", kb_item)
                    continue
                    
                # Safely extract values
                kb_id = kb_item.get("sys_id", "")
                title = kb_item.get("title", "")
                description = kb_item.get("description", "")
                
                # Extract nested values safely
                owner = ""
                if isinstance(kb_item.get("owner"), dict):
                    owner = kb_item["owner"].get("display_value", "")
                
                managers = ""
                if isinstance(kb_item.get("kb_managers"), dict):
                    managers = kb_item["kb_managers"].get("display_value", "")
                
                active = False
                if kb_item.get("active") == "true":
                    active = True
                
                created = kb_item.get("sys_created_on", "")
                updated = kb_item.get("sys_updated_on", "")
                
                knowledge_bases.append({
                    "id": kb_id,
                    "title": title,
                    "description": description,
                    "owner": owner,
                    "managers": managers,
                    "active": active,
                    "created": created,
                    "updated": updated,
                })
        else:
            logger.warning("Result is not a list: %s", result)

        return {
            "success": True,
            "message": f"Found {len(knowledge_bases)} knowledge bases",
            "knowledge_bases": knowledge_bases,
            "count": len(knowledge_bases),
            "limit": params.limit,
            "offset": params.offset,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list knowledge bases: {e}")
        return {
            "success": False,
            "message": f"Failed to list knowledge bases: {str(e)}",
            "knowledge_bases": [],
            "count": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def create_category(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateCategoryParams,
) -> CategoryResponse:
    """
    Create a new category in a knowledge base.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for creating the category.

    Returns:
        Response with the created category details.
    """
    api_url = f"{config.api_url}/table/kb_category"

    # Build request data
    data = {
        "label": params.title,
        "kb_knowledge_base": params.knowledge_base,
        # Convert boolean to string "true"/"false" as ServiceNow expects
        "active": str(params.active).lower(),
    }

    if params.description:
        data["description"] = params.description
    if params.parent_category:
        data["parent"] = params.parent_category
    if params.parent_table:
        data["parent_table"] = params.parent_table
    
    # Log the request data for debugging
    logger.debug(f"Creating category with data: {data}")

    # Make request
    try:
        response = requests.post(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})
        logger.debug(f"Category creation response: {result}")

        # Log the specific fields to check the knowledge base assignment
        if "kb_knowledge_base" in result:
            logger.debug(f"Knowledge base in response: {result['kb_knowledge_base']}")
        
        # Log the active status
        if "active" in result:
            logger.debug(f"Active status in response: {result['active']}")
        
        return CategoryResponse(
            success=True,
            message="Category created successfully",
            category_id=result.get("sys_id"),
            category_name=result.get("label"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to create category: {e}")
        return CategoryResponse(
            success=False,
            message=f"Failed to create category: {str(e)}",
        )


def create_article(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateArticleParams,
) -> ArticleResponse:
    """
    Create a new knowledge article.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for creating the article.

    Returns:
        Response with the created article details.
    """
    api_url = f"{config.api_url}/table/kb_knowledge"

    # Build request data
    data = {
        "short_description": params.short_description,
        "text": params.text,
        "kb_knowledge_base": params.knowledge_base,
        "kb_category": params.category,
        "article_type": params.article_type,
    }

    if params.title:
        data["short_description"] = params.title
    if params.keywords:
        data["keywords"] = params.keywords

    # Make request
    try:
        response = requests.post(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return ArticleResponse(
            success=True,
            message="Article created successfully",
            article_id=result.get("sys_id"),
            article_title=result.get("short_description"),
            workflow_state=result.get("workflow_state"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to create article: {e}")
        return ArticleResponse(
            success=False,
            message=f"Failed to create article: {str(e)}",
        )


def update_article(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: UpdateArticleParams,
) -> ArticleResponse:
    """
    Update an existing knowledge article.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for updating the article.

    Returns:
        Response with the updated article details.
    """
    api_url = f"{config.api_url}/table/kb_knowledge/{params.article_id}"

    # Build request data
    data = {}

    if params.title:
        data["short_description"] = params.title
    if params.text:
        data["text"] = params.text
    if params.short_description:
        data["short_description"] = params.short_description
    if params.category:
        data["kb_category"] = params.category
    if params.keywords:
        data["keywords"] = params.keywords

    # Make request
    try:
        response = requests.patch(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return ArticleResponse(
            success=True,
            message="Article updated successfully",
            article_id=params.article_id,
            article_title=result.get("short_description"),
            workflow_state=result.get("workflow_state"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to update article: {e}")
        return ArticleResponse(
            success=False,
            message=f"Failed to update article: {str(e)}",
        )


def publish_article(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: PublishArticleParams,
) -> ArticleResponse:
    """
    Publish a knowledge article.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for publishing the article.

    Returns:
        Response with the published article details.
    """
    api_url = f"{config.api_url}/table/kb_knowledge/{params.article_id}"

    # Build request data
    data = {
        "workflow_state": params.workflow_state,
    }

    if params.workflow_version:
        data["workflow_version"] = params.workflow_version

    # Make request
    try:
        response = requests.patch(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return ArticleResponse(
            success=True,
            message="Article published successfully",
            article_id=params.article_id,
            article_title=result.get("short_description"),
            workflow_state=result.get("workflow_state"),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to publish article: {e}")
        return ArticleResponse(
            success=False,
            message=f"Failed to publish article: {str(e)}",
        )


def list_articles(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListArticlesParams,
) -> Dict[str, Any]:
    """
    List knowledge articles with filtering options.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing articles.

    Returns:
        Dictionary with list of articles and metadata.
    """
    api_url = f"{config.api_url}/table/kb_knowledge"

    # Build query parameters
    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "all",
    }

    # Build query string
    query_parts = []
    if params.knowledge_base:
        query_parts.append(f"kb_knowledge_base.sys_id={params.knowledge_base}")
    if params.category:
        query_parts.append(f"kb_category.sys_id={params.category}")
    if params.workflow_state:
        query_parts.append(f"workflow_state={params.workflow_state}")
    if params.query:
        query_parts.append(f"short_descriptionLIKE{params.query}^ORtextLIKE{params.query}")

    if query_parts:
        query_string = "^".join(query_parts)
        logger.debug(f"Constructed article query string: {query_string}")
        query_params["sysparm_query"] = query_string
    
    # Log the query parameters for debugging
    logger.debug(f"Listing articles with query params: {query_params}")

    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        # Get the JSON response
        json_response = response.json()
        logger.debug(f"Article listing raw response: {json_response}")
        
        # Safely extract the result
        if isinstance(json_response, dict) and "result" in json_response:
            result = json_response.get("result", [])
        else:
            logger.error("Unexpected response format: %s", json_response)
            return {
                "success": False,
                "message": f"Unexpected response format",
                "articles": [],
                "count": 0,
                "limit": params.limit,
                "offset": params.offset,
            }

        # Transform the results
        articles = []
        
        # Handle either string or list
        if isinstance(result, list):
            for article_item in result:
                if not isinstance(article_item, dict):
                    logger.warning("Skipping non-dictionary article item: %s", article_item)
                    continue
                    
                # Safely extract values
                article_id = article_item.get("sys_id", "")
                title = article_item.get("short_description", "")
                
                # Extract nested values safely
                knowledge_base = ""
                if isinstance(article_item.get("kb_knowledge_base"), dict):
                    knowledge_base = article_item["kb_knowledge_base"].get("display_value", "")
                
                category = ""
                if isinstance(article_item.get("kb_category"), dict):
                    category = article_item["kb_category"].get("display_value", "")
                
                workflow_state = ""
                if isinstance(article_item.get("workflow_state"), dict):
                    workflow_state = article_item["workflow_state"].get("display_value", "")
                
                created = article_item.get("sys_created_on", "")
                updated = article_item.get("sys_updated_on", "")
                
                articles.append({
                    "id": article_id,
                    "title": title,
                    "knowledge_base": knowledge_base,
                    "category": category,
                    "workflow_state": workflow_state,
                    "created": created,
                    "updated": updated,
                })
        else:
            logger.warning("Result is not a list: %s", result)

        return {
            "success": True,
            "message": f"Found {len(articles)} articles",
            "articles": articles,
            "count": len(articles),
            "limit": params.limit,
            "offset": params.offset,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list articles: {e}")
        return {
            "success": False,
            "message": f"Failed to list articles: {str(e)}",
            "articles": [],
            "count": 0,
            "limit": params.limit,
            "offset": params.offset,
        }


def get_article(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetArticleParams,
) -> Dict[str, Any]:
    """
    Get a specific knowledge article by ID.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting the article.

    Returns:
        Dictionary with article details.
    """
    api_url = f"{config.api_url}/table/kb_knowledge/{params.article_id}"

    # Build query parameters
    query_params = {
        "sysparm_display_value": "true",
    }

    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        # Get the JSON response
        json_response = response.json()
        
        # Safely extract the result
        if isinstance(json_response, dict) and "result" in json_response:
            result = json_response.get("result", {})
        else:
            logger.error("Unexpected response format: %s", json_response)
            return {
                "success": False,
                "message": "Unexpected response format",
            }

        if not result or not isinstance(result, dict):
            return {
                "success": False,
                "message": f"Article with ID {params.article_id} not found",
            }

        # Extract values safely
        article_id = result.get("sys_id", "")
        title = result.get("short_description", "")
        text = result.get("text", "")
        
        # Extract nested values safely
        knowledge_base = ""
        if isinstance(result.get("kb_knowledge_base"), dict):
            knowledge_base = result["kb_knowledge_base"].get("display_value", "")
        
        category = ""
        if isinstance(result.get("kb_category"), dict):
            category = result["kb_category"].get("display_value", "")
        
        workflow_state = ""
        if isinstance(result.get("workflow_state"), dict):
            workflow_state = result["workflow_state"].get("display_value", "")
        
        author = ""
        if isinstance(result.get("author"), dict):
            author = result["author"].get("display_value", "")
        
        keywords = result.get("keywords", "")
        article_type = result.get("article_type", "")
        views = result.get("view_count", "0")
        created = result.get("sys_created_on", "")
        updated = result.get("sys_updated_on", "")

        article = {
            "id": article_id,
            "title": title,
            "text": text,
            "knowledge_base": knowledge_base,
            "category": category,
            "workflow_state": workflow_state,
            "created": created,
            "updated": updated,
            "author": author,
            "keywords": keywords,
            "article_type": article_type,
            "views": views,
        }

        return {
            "success": True,
            "message": "Article retrieved successfully",
            "article": article,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to get article: {e}")
        return {
            "success": False,
            "message": f"Failed to get article: {str(e)}",
        }


def list_categories(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: ListCategoriesParams,
) -> Dict[str, Any]:
    """
    List categories in a knowledge base.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for listing categories.

    Returns:
        Dictionary with list of categories and metadata.
    """
    api_url = f"{config.api_url}/table/kb_category"

    # Build query parameters
    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "all",
    }

    # Build query string
    query_parts = []
    if params.knowledge_base:
        # Try different query format to ensure we match by sys_id value
        query_parts.append(f"kb_knowledge_base.sys_id={params.knowledge_base}")
    if params.parent_category:
        query_parts.append(f"parent.sys_id={params.parent_category}")
    if params.active is not None:
        query_parts.append(f"active={str(params.active).lower()}")
    if params.query:
        query_parts.append(f"labelLIKE{params.query}^ORdescriptionLIKE{params.query}")

    if query_parts:
        query_string = "^".join(query_parts)
        logger.debug(f"Constructed query string: {query_string}")
        query_params["sysparm_query"] = query_string
    
    # Log the query parameters for debugging
    logger.debug(f"Listing categories with query params: {query_params}")

    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        # Get the JSON response
        json_response = response.json()
        
        # Safely extract the result
        if isinstance(json_response, dict) and "result" in json_response:
            result = json_response.get("result", [])
        else:
            logger.error("Unexpected response format: %s", json_response)
            return {
                "success": False,
                "message": "Unexpected response format",
                "categories": [],
                "count": 0,
                "limit": params.limit,
                "offset": params.offset,
            }

        # Transform the results
        categories = []
        
        # Handle either string or list
        if isinstance(result, list):
            for category_item in result:
                if not isinstance(category_item, dict):
                    logger.warning("Skipping non-dictionary category item: %s", category_item)
                    continue
                    
                # Safely extract values
                category_id = category_item.get("sys_id", "")
                title = category_item.get("label", "")
                description = category_item.get("description", "")
                
                # Extract knowledge base - handle both dictionary and string cases
                knowledge_base = ""
                kb_field = category_item.get("kb_knowledge_base")
                if isinstance(kb_field, dict):
                    knowledge_base = kb_field.get("display_value", "")
                elif isinstance(kb_field, str):
                    knowledge_base = kb_field
                # Also check if kb_knowledge_base is missing but there's a separate value field
                elif "kb_knowledge_base_value" in category_item:
                    knowledge_base = category_item.get("kb_knowledge_base_value", "")
                elif "kb_knowledge_base.display_value" in category_item:
                    knowledge_base = category_item.get("kb_knowledge_base.display_value", "")
                
                # Extract parent category - handle both dictionary and string cases
                parent = ""
                parent_field = category_item.get("parent")
                if isinstance(parent_field, dict):
                    parent = parent_field.get("display_value", "")
                elif isinstance(parent_field, str):
                    parent = parent_field
                # Also check alternative field names
                elif "parent_value" in category_item:
                    parent = category_item.get("parent_value", "")
                elif "parent.display_value" in category_item:
                    parent = category_item.get("parent.display_value", "")
                
                # Convert active to boolean - handle string or boolean types
                active_field = category_item.get("active")
                if isinstance(active_field, str):
                    active = active_field.lower() == "true"
                elif isinstance(active_field, bool):
                    active = active_field
                else:
                    active = False
                
                created = category_item.get("sys_created_on", "")
                updated = category_item.get("sys_updated_on", "")
                
                categories.append({
                    "id": category_id,
                    "title": title,
                    "description": description,
                    "knowledge_base": knowledge_base,
                    "parent_category": parent,
                    "active": active,
                    "created": created,
                    "updated": updated,
                })
                
                # Log for debugging purposes
                logger.debug(f"Processed category: {title}, KB: {knowledge_base}, Parent: {parent}")
        else:
            logger.warning("Result is not a list: %s", result)

        return {
            "success": True,
            "message": f"Found {len(categories)} categories",
            "categories": categories,
            "count": len(categories),
            "limit": params.limit,
            "offset": params.offset,
        }

    except requests.RequestException as e:
        logger.error(f"Failed to list categories: {e}")
        return {
            "success": False,
            "message": f"Failed to list categories: {str(e)}",
            "categories": [],
            "count": 0,
            "limit": params.limit,
            "offset": params.offset,
        } 


class AddCommentParams(BaseModel):
    """Parameters for adding a comment to a knowledge article."""

    article_id: str = Field(..., description="ID of the article to add the comment to")
    comment: str = Field(..., description="The comment text")
    is_work_note: bool = Field(False, description="Whether the comment is a work note")


class CommentResponse(BaseModel):
    """Response from comment operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    article_id: Optional[str] = Field(None, description="ID of the article the comment was added to")
    comment_id: Optional[str] = Field(None, description="ID of the added comment")


class GetCommentsParams(BaseModel):
    """Parameters for retrieving comments from a knowledge article."""

    article_id: str = Field(..., description="ID of the article to get comments from")
    limit: int = Field(10, description="Maximum number of comments to return")
    offset: int = Field(0, description="Offset for pagination")


class CommentsListResponse(BaseModel):
    """Response from listing comments operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Message describing the result")
    article_id: Optional[str] = Field(None, description="ID of the article")
    comments: list = Field(default_factory=list, description="List of comments")
    count: int = Field(0, description="Number of comments returned")


def add_comment(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: AddCommentParams,
) -> CommentResponse:
    """
    Add a comment to a knowledge article.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for adding the comment.

    Returns:
        Response with the comment details.
    """
    api_url = f"{config.api_url}/table/kb_knowledge/{params.article_id}"

    # Build request data
    data = {}
    
    if params.is_work_note:
        # Add as work notes
        data["work_notes"] = params.comment
    else:
        # Add as comments
        data["comments"] = params.comment

    # Make request
    try:
        response = requests.patch(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        result = response.json().get("result", {})

        return CommentResponse(
            success=True,
            message="Comment added successfully",
            article_id=params.article_id,
            comment_id=result.get("sys_id"),  # This will be the article's sys_id
        )

    except requests.RequestException as e:
        logger.error(f"Failed to add comment: {e}")
        return CommentResponse(
            success=False,
            message=f"Failed to add comment: {str(e)}",
        )


def get_comments(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: GetCommentsParams,
) -> CommentsListResponse:
    """
    Get comments from a knowledge article using the ServiceNow journal field API.

    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Parameters for getting comments.

    Returns:
        Response with the list of comments.
    """
    # Query the sys_journal_field table for comments on this article
    api_url = f"{config.api_url}/table/sys_journal_field"

    # Build query parameters
    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "all",
        "sysparm_query": f"element_id={params.article_id}^element=comments^ORwork_notes={params.article_id}",
        "sysparm_fields": "sys_id,element,element_id,value,sys_created_on,sys_created_by",
    }

    # Make request
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()

        # Get the JSON response
        json_response = response.json()
        
        # Safely extract the result
        if isinstance(json_response, dict) and "result" in json_response:
            result = json_response.get("result", [])
        else:
            logger.error("Unexpected response format: %s", json_response)
            return CommentsListResponse(
                success=False,
                message="Unexpected response format",
                article_id=params.article_id,
            )

        # Transform the results
        comments = []
        
        if isinstance(result, list):
            for comment_item in result:
                if not isinstance(comment_item, dict):
                    logger.warning("Skipping non-dictionary comment item: %s", comment_item)
                    continue
                    
                # Extract comment details
                comment_id = comment_item.get("sys_id", "")
                comment_text = comment_item.get("value", "")
                element_type = comment_item.get("element", "")
                created_on = comment_item.get("sys_created_on", "")
                
                # Extract created by user safely
                created_by = ""
                created_by_field = comment_item.get("sys_created_by")
                if isinstance(created_by_field, dict):
                    created_by = created_by_field.get("display_value", "")
                elif isinstance(created_by_field, str):
                    created_by = created_by_field
                
                comments.append({
                    "id": comment_id,
                    "text": comment_text,
                    "type": element_type,  # "comments" or "work_notes"
                    "created_on": created_on,
                    "created_by": created_by,
                })

        return CommentsListResponse(
            success=True,
            message=f"Found {len(comments)} comments",
            article_id=params.article_id,
            comments=comments,
            count=len(comments),
        )

    except requests.RequestException as e:
        logger.error(f"Failed to get comments: {e}")
        return CommentsListResponse(
            success=False,
            message=f"Failed to get comments: {str(e)}",
            article_id=params.article_id,
        )


def search_knowledge_base(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: SearchKnowledgeBaseParams,
) -> Dict[str, Any]:
    """
    Search for knowledge base articles by term.
    
    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Search parameters.
        
    Returns:
        Dictionary containing search results.
    """
    api_url = f"{config.api_url}/table/kb_knowledge"
    
    # Build query parameters
    query_parts = []
    
    # Add search term query - search in title, short_description, and text
    if params.search_term:
        search_query = (
            f"short_descriptionLIKE{params.search_term}^OR"
            f"titleLIKE{params.search_term}^OR"
            f"textLIKE{params.search_term}"
        )
        query_parts.append(search_query)
    
    # Filter by knowledge base
    if params.knowledge_base:
        # Check if it's a name or ID
        if params.knowledge_base.startswith("Company Protocols") or "protocol" in params.knowledge_base.lower():
            kb_query = f"kb_knowledge_base.title={params.knowledge_base}"
        else:
            kb_query = f"kb_knowledge_base={params.knowledge_base}"
        query_parts.append(kb_query)
    
    # Filter by workflow state
    if params.workflow_state:
        query_parts.append(f"workflow_state={params.workflow_state}")
    
    query_string = "^".join(query_parts) if query_parts else ""
    
    query_params = {
        "sysparm_limit": params.limit,
        "sysparm_offset": params.offset,
        "sysparm_display_value": "all",
        "sysparm_fields": "sys_id,number,title,short_description,text,kb_knowledge_base,workflow_state,sys_created_on"
    }
    
    if query_string:
        query_params["sysparm_query"] = query_string
    
    try:
        response = requests.get(
            api_url,
            params=query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        result = response.json()
        articles = result.get("result", [])
        
        return {
            "success": True,
            "message": f"Found {len(articles)} articles matching '{params.search_term}'",
            "articles": articles,
            "count": len(articles)
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to search knowledge base: {e}")
        return {
            "success": False,
            "message": f"Failed to search knowledge base: {str(e)}",
            "articles": [],
            "count": 0
        }


def add_comment_to_kb(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: AddCommentToKBParams,
) -> Dict[str, Any]:
    """
    Add a comment to a knowledge base article.
    
    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Comment parameters.
        
    Returns:
        Dictionary containing operation result.
    """
    api_url = f"{config.api_url}/table/kb_knowledge/{params.article_id}"
    
    # Prepare the data based on comment type
    if params.is_work_note:
        data = {"work_notes": params.comment}
    else:
        data = {"comments": params.comment}
    
    try:
        response = requests.patch(
            api_url,
            json=data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        response.raise_for_status()
        
        return {
            "success": True,
            "message": f"Comment added to article {params.article_id}",
            "article_id": params.article_id,
            "comment_type": "work_note" if params.is_work_note else "comment"
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to add comment to knowledge base: {e}")
        return {
            "success": False,
            "message": f"Failed to add comment: {str(e)}",
            "article_id": params.article_id
        }


def create_service_request(
    config: ServerConfig,
    auth_manager: AuthManager,
    params: CreateServiceRequestParams,
) -> Dict[str, Any]:
    """
    Create a service catalog request.
    
    Args:
        config: Server configuration.
        auth_manager: Authentication manager.
        params: Request parameters.
        
    Returns:
        Dictionary containing operation result.
    """
    # First, find the catalog item
    catalog_api_url = f"{config.api_url}/table/sc_cat_item"
    catalog_query_params = {
        "sysparm_query": f"nameLIKE{params.catalog_item}^ORsys_id={params.catalog_item}",
        "sysparm_limit": "1",
        "sysparm_fields": "sys_id,name,short_description"
    }
    
    try:
        # Find catalog item
        catalog_response = requests.get(
            catalog_api_url,
            params=catalog_query_params,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        catalog_response.raise_for_status()
        
        catalog_results = catalog_response.json().get("result", [])
        if not catalog_results:
            return {
                "success": False,
                "message": f"Catalog item '{params.catalog_item}' not found",
                "request_id": None
            }
        
        catalog_item_id = catalog_results[0]["sys_id"]
        catalog_item_name = catalog_results[0]["name"]
        
        # Create the service request
        request_api_url = f"{config.api_url}/table/sc_request"
        request_data = {
            "short_description": params.short_description or f"Request for {catalog_item_name}",
            "description": params.description or f"Service catalog request for {catalog_item_name}",
        }
        
        if params.requested_for:
            request_data["requested_for"] = params.requested_for
        
        request_response = requests.post(
            request_api_url,
            json=request_data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        request_response.raise_for_status()
        
        request_result = request_response.json().get("result", {})
        request_id = request_result.get("sys_id")
        request_number = request_result.get("number")
        
        # Create request item
        request_item_api_url = f"{config.api_url}/table/sc_req_item"
        request_item_data = {
            "request": request_id,
            "cat_item": catalog_item_id,
            "quantity": params.quantity,
            "short_description": params.short_description or f"Request for {catalog_item_name}",
        }
        
        if params.requested_for:
            request_item_data["requested_for"] = params.requested_for
        
        item_response = requests.post(
            request_item_api_url,
            json=request_item_data,
            headers=auth_manager.get_headers(),
            timeout=config.timeout,
        )
        item_response.raise_for_status()
        
        item_result = item_response.json().get("result", {})
        
        return {
            "success": True,
            "message": f"Service request {request_number} created successfully",
            "request_id": request_id,
            "request_number": request_number,
            "item_id": item_result.get("sys_id"),
            "catalog_item": catalog_item_name
        }
        
    except requests.RequestException as e:
        logger.error(f"Failed to create service request: {e}")
        return {
            "success": False,
            "message": f"Failed to create service request: {str(e)}",
            "request_id": None
        }