""Structured logging configuration for MCP Studio."""

import logging
import logging.config
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from structlog.types import EventDict, Processor

def add_service_context(_: logging.Logger, __: str, event_dict: EventDict) -> EventDict:
    """Add service context to log events."""
    event_dict["service"] = "mcp-studio"
    return event_dict

def drop_debug_logs(_: logging.Logger, __: str, event_dict: EventDict) -> EventDict:
    """Drop debug logs in production."""
    if event_dict.get("level") == "debug":
        raise structlog.DropEvent
    return event_dict

def configure_logging(level: str = "INFO", json_logs: bool = False) -> None:
    """Configure structured logging with structlog.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_logs: Whether to output logs in JSON format
    """
    timestamper = structlog.processors.TimeStamper(fmt="iso")
    pre_chain = [
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.contextvars.merge_contextvars,
        add_service_context,
        timestamper,
    ]

    if json_logs:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=pre_chain,
        )
    else:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.dev.ConsoleRenderer(colors=True),
            foreign_pre_chain=pre_chain,
        )

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level.upper())

    # Clear existing handlers
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
        handler.close()

    # Add console handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)

    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.contextvars.merge_contextvars,
            add_service_context,
            structlog.stdlib.PositionalArgumentsFormatter(),
            timestamper,
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.AsyncBoundLogger,
        cache_logger_on_first_use=True,
    )

    # Configure specific loggers
    logging.getLogger("uvicorn").handlers.clear()
    logging.getLogger("uvicorn.access").handlers.clear()
    logging.getLogger("uvicorn.error").handlers.clear()
    logging.getLogger("uvicorn.access").propagate = False

    # Set log levels for specific loggers
    logging.getLogger("uvicorn").setLevel("WARNING")
    logging.getLogger("uvicorn.error").setLevel("WARNING")
    logging.getLogger("uvicorn.access").setLevel("WARNING")
    logging.getLogger("asyncio").setLevel("WARNING")
    logging.getLogger("httpcore").setLevel("WARNING")
    logging.getLogger("httpx").setLevel("WARNING")

    # Initial log message
    logger = structlog.get_logger(__name__)
    logger.info("Logging configured", log_level=level, json_logs=json_logs)
