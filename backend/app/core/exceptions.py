"""Custom exceptions for MCP Studio."""

from fastapi import HTTPException, status


class UnauthorizedError(HTTPException):
    """Raised when a user is not authenticated."""
    def __init__(self, detail: str = "Not authenticated"):
        super().__init__(status_code=status.HTTP_401_UNAUTHORIZED, detail=detail)


class ForbiddenError(HTTPException):
    """Raised when a user doesn't have permission."""
    def __init__(self, detail: str = "Permission denied"):
        super().__init__(status_code=status.HTTP_403_FORBIDDEN, detail=detail)


class ToolExecutionError(HTTPException):
    """Raised when tool execution fails."""
    def __init__(self, detail: str = "Tool execution failed"):
        super().__init__(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=detail)
