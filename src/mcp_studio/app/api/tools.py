"""API endpoints for managing MCP tools."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field, HttpUrl

from ..utils.docstring_formatter import format_docstring_html, format_docstring_markdown, parse_docstring
from ..models.mcp import MCPTool, ToolExecutionRequest, ToolExecutionResult
from ..services.server_service import server_service

router = APIRouter()

@router.get(
    "/",
    response_model=List[MCPTool],
    summary="List all tools",
    description="Get a list of all available tools across all MCP servers.",
)
async def list_tools(
    server_id: Optional[str] = Query(
        None, description="Filter tools by server ID"
    ),
    category: Optional[str] = Query(
        None, description="Filter tools by category"
    ),
    search: Optional[str] = Query(
        None, description="Search tools by name or description"
    ),
) -> List[MCPTool]:
    """
    List all available tools with optional filtering.
    
    Args:
        server_id: Filter tools by server ID
        category: Filter tools by category
        search: Search tools by name or description
        
    Returns:
        List of tools matching the filters
    """
    tools = []
    
    # Get tools from all servers or a specific server
    all_servers = server_service.get_servers()
    servers = [all_servers[server_id]] if server_id and server_id in all_servers else list(all_servers.values())
    
    for server in servers:
        server_tools = await server_service.get_server_tools(server.id)
        for tool_dict in server_tools:
            tool = MCPTool(**tool_dict)
            # Add server info to the tool
            tool_with_server = tool.copy(update={"server_id": server.id, "server_name": server.name})
            tools.append(tool_with_server)
    
    # Apply filters
    if category:
        tools = [t for t in tools if category in t.categories]
    
    if search:
        search_lower = search.lower()
        tools = [
            t for t in tools
            if (search_lower in t.name.lower() or 
                (t.description and search_lower in t.description.lower()))
        ]
    
    return tools

@router.get(
    "/{tool_name}",
    response_model=List[Dict[str, Any]],
    summary="Get tool by name",
    description="Get all tools with the given name across all servers.",
    responses={
        404: {"description": "Tool not found"},
    },
)
async def get_tool_by_name(
    tool_name: str,
    server_id: Optional[str] = Query(
        None, description="Filter by server ID"
    ),
) -> List[Dict[str, Any]]:
    """
    Get all tools with the given name.
    
    Args:
        tool_name: Name of the tool to find
        server_id: Optional server ID to filter by
        
    Returns:
        List of tools with the given name, including server information
        
    Raises:
        HTTPException: If no tools are found with the given name
    """
    results = []
    
    # Get tools from all servers or a specific server
    all_servers = server_service.get_servers()
    servers = [all_servers[server_id]] if server_id and server_id in all_servers else list(all_servers.values())
    
    for server in servers:
        server_tools = await server_service.get_server_tools(server.id)
        for tool_dict in server_tools:
            if tool_dict.get("name") == tool_name:
                tool_dict.update({
                    "server_id": server.id,
                    "server_name": server.name,
                    "server_status": server.status.value if hasattr(server.status, 'value') else str(server.status),
                })
                results.append(tool_dict)
    
    if not results:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found" + (f" on server '{server_id}'" if server_id else ""),
        )
    
    return results

@router.post(
    "/execute",
    response_model=ToolExecutionResult,
    summary="Execute a tool",
    description="Execute a tool on a server with the given parameters.",
    responses={
        200: {"description": "Tool executed successfully"},
        400: {"description": "Invalid parameters"},
        404: {"description": "Server or tool not found"},
        500: {"description": "Tool execution failed"},
    },
)
async def execute_tool_endpoint(request: ToolExecutionRequest) -> ToolExecutionResult:
    """
    Execute a tool on a server.
    
    Args:
        request: Tool execution request
        
    Returns:
        Result of the tool execution
        
    Raises:
        HTTPException: If the server, tool, or execution fails
    """
    import time
    start_time = time.perf_counter()
    
    try:
        result = await server_service.execute_tool(
            server_id=request.server_id,
            tool_name=request.tool_name,
            parameters=request.parameters,
        )
        
        execution_time = time.perf_counter() - start_time
        
        return ToolExecutionResult(
            success=True,
            result=result,
            execution_time=execution_time,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute tool: {str(e)}",
        )

@router.get(
    "/categories",
    response_model=List[str],
    summary="List all tool categories",
    description="Get a list of all tool categories across all servers.",
)
async def list_categories() -> List[str]:
    """
    Get a list of all tool categories.
    
    Returns:
        List of unique tool categories
    """
    categories = set()
    
    all_servers = server_service.get_servers()
    for server in all_servers.values():
        server_tools = await server_service.get_server_tools(server.id)
        for tool_dict in server_tools:
            if "categories" in tool_dict:
                categories.update(tool_dict["categories"])
    
    return sorted(categories)


class DocstringFormatRequest(BaseModel):
    """Request model for formatting docstrings."""
    docstring: str = Field(..., description="The raw docstring text to format")
    format: str = Field(default="html", description="Output format: 'html' or 'markdown'")


class DocstringFormatResponse(BaseModel):
    """Response model for formatted docstring."""
    formatted: str = Field(..., description="The formatted docstring")
    parsed: Dict = Field(..., description="Parsed docstring structure")


@router.post(
    "/format-docstring",
    response_model=DocstringFormatResponse,
    summary="Format a docstring",
    description="Parse and format a docstring for better UI display.",
)
async def format_docstring(request: DocstringFormatRequest) -> DocstringFormatResponse:
    """
    Format a docstring for display in the UI.
    
    Args:
        request: Docstring formatting request
        
    Returns:
        Formatted docstring and parsed structure
    """
    parsed = parse_docstring(request.docstring)
    
    if request.format.lower() == "markdown":
        formatted = format_docstring_markdown(request.docstring)
    else:
        formatted = format_docstring_html(request.docstring)
    
    return DocstringFormatResponse(
        formatted=formatted,
        parsed=parsed
    )
