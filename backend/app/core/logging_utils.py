"""Logging utilities for consistent logging across the application."""
import logging
import sys
from typing import Optional

import structlog

# Configure structlog to use the standard library's logging module
structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

def get_logger(name: Optional[str] = None) -> structlog.BoundLogger:
    """Get a configured logger instance.
    
    Args:
        name: The name of the logger. If None, the root logger is used.
        
    Returns:
        A configured structlog logger instance.
    """
    return structlog.get_logger(name)

def configure_uvicorn_logging():
    """Configure uvicorn to use structlog for consistent logging."""
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )
    
    # Replace the default handlers with our own
    for logger_name in ["uvicorn", "uvicorn.error", "uvicorn.access"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers.clear()
        logging_logger.handlers = [logging.StreamHandler(sys.stdout)]
        logging_logger.setLevel(logging.INFO)
        logging_logger.propagate = False
