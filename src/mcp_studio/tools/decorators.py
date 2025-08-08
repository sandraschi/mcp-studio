"""
MCP Tool Decorators

This module provides decorators for creating and enhancing MCP tools with features like
structured logging, input validation, rate limiting, and more.
"""
import functools
import inspect
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Type, TypeVar, Union, cast

from pydantic import BaseModel, ValidationError, create_model, validator

# Type variables for generic type hints
F = TypeVar('F', bound=Callable[..., Any])
T = TypeVar('T')

# Configure structured logging
logger = logging.getLogger("mcp.tools")

@dataclass
class ToolMetadata:
    """Metadata for an MCP tool."""
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    tags: List[str] = field(default_factory=list)
    input_schema: Optional[Type[BaseModel]] = None
    output_schema: Optional[Type[BaseModel]] = None
    rate_limit: Optional[int] = None
    retry_attempts: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to a dictionary."""
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "author": self.author,
            "tags": self.tags,
            "input_schema": self.input_schema.schema() if self.input_schema else None,
            "output_schema": self.output_schema.schema() if self.output_schema else None,
            "rate_limit": self.rate_limit,
            "retry_attempts": self.retry_attempts,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout
        }


def tool(
    name: Optional[str] = None,
    description: str = "",
    version: str = "1.0.0",
    author: str = "",
    tags: Optional[List[str]] = None,
    input_schema: Optional[Type[BaseModel]] = None,
    output_schema: Optional[Type[BaseModel]] = None,
    rate_limit: Optional[int] = None,
    retry_attempts: int = 3,
    retry_delay: float = 1.0,
    timeout: Optional[float] = None
) -> Callable[[F], F]:
    """
    Decorator to register a function as an MCP tool.
    
    Args:
        name: Tool name (defaults to function name)
        description: Tool description
        version: Tool version
        author: Tool author
        tags: List of tags for categorization
        input_schema: Pydantic model for input validation
        output_schema: Pydantic model for output validation
        rate_limit: Maximum calls per minute
        retry_attempts: Number of retry attempts on failure
        retry_delay: Delay between retries in seconds
        timeout: Maximum execution time in seconds
    """
    def decorator(func: F) -> F:
        # Use function name if name not provided
        tool_name = name or func.__name__
        
        # Create tool metadata
        metadata = ToolMetadata(
            name=tool_name,
            description=description or func.__doc__ or "",
            version=version,
            author=author,
            tags=tags or [],
            input_schema=input_schema,
            output_schema=output_schema,
            rate_limit=rate_limit,
            retry_attempts=retry_attempts,
            retry_delay=retry_delay,
            timeout=timeout
        )
        
        # Store metadata in the function
        setattr(func, "__mcp_metadata__", metadata)
        
        # Add structured logging
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Log tool execution start
            logger.info(
                "tool_start",
                extra={
                    "tool": tool_name,
                    "args": args,
                    "kwargs": kwargs,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
            )
            
            start_time = time.monotonic()
            result = None
            exception = None
            
            try:
                # Execute the tool
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                exception = e
                raise
            finally:
                # Calculate execution time
                duration = time.monotonic() - start_time
                
                # Log tool completion or failure
                log_data = {
                    "tool": tool_name,
                    "duration": duration,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                if exception:
                    logger.error(
                        "tool_error",
                        extra={
                            **log_data,
                            "error": str(exception),
                            "error_type": type(exception).__name__
                        },
                        exc_info=True
                    )
                else:
                    logger.info(
                        "tool_complete",
                        extra={
                            **log_data,
                            "result": str(result)[:1000]  # Limit result size
                        }
                    )
        
        return cast(F, wrapper)
    
    return decorator


def structured_log(
    log_level: int = logging.INFO,
    include_args: bool = True,
    include_result: bool = True,
    include_duration: bool = True
) -> Callable[[F], F]:
    """
    Decorator to add structured logging to a function.
    
    Args:
        log_level: Logging level (default: INFO)
        include_args: Whether to log function arguments
        include_result: Whether to log function result
        include_duration: Whether to log execution duration
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get function information
            func_name = func.__name__
            module_name = func.__module__
            
            # Log function call start
            log_data: Dict[str, Any] = {
                "function": f"{module_name}.{func_name}",
                "event": "function_start",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            if include_args:
                # Get parameter names and values
                sig = inspect.signature(func)
                bound_args = sig.bind(*args, **kwargs)
                bound_args.apply_defaults()
                
                # Convert arguments to a serializable format
                serialized_args = {}
                for name, value in bound_args.arguments.items():
                    try:
                        json.dumps(value)
                        serialized_args[name] = value
                    except (TypeError, OverflowError):
                        serialized_args[name] = str(value)
                
                log_data["args"] = serialized_args
            
            logger.log(log_level, "function_call", extra=log_data)
            
            # Execute the function
            start_time = time.monotonic()
            exception = None
            result = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                exception = e
                raise
            finally:
                # Log function completion
                duration = time.monotonic() - start_time
                
                log_data = {
                    "function": f"{module_name}.{func_name}",
                    "event": "function_complete" if exception is None else "function_error",
                    "duration": duration,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                
                if include_result and result is not None:
                    try:
                        log_data["result"] = result
                    except (TypeError, OverflowError):
                        log_data["result"] = str(result)
                
                if exception is not None:
                    log_data["error"] = str(exception)
                    log_data["error_type"] = type(exception).__name__
                    logger.error("function_error", extra=log_data, exc_info=True)
                else:
                    logger.log(log_level, "function_complete", extra=log_data)
        
        return cast(F, wrapper)
    
    return decorator


def validate_input(
    input_model: Type[BaseModel],
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    exclude_none: bool = False
) -> Callable[[F], F]:
    """
    Decorator to validate function input using a Pydantic model.
    
    Args:
        input_model: Pydantic model for input validation
        exclude_unset: Whether to exclude unset fields
        exclude_defaults: Whether to exclude default values
        exclude_none: Whether to exclude None values
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Get the signature of the function
            sig = inspect.signature(func)
            
            # Bind the arguments
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Convert to dictionary and validate
            input_data = dict(bound_args.arguments)
            
            # Remove 'self' if it exists (for methods)
            if 'self' in input_data:
                del input_data['self']
            
            # Validate input using the Pydantic model
            try:
                validated = input_model(**input_data)
                
                # Update the arguments with validated data
                validated_dict = validated.dict(
                    exclude_unset=exclude_unset,
                    exclude_defaults=exclude_defaults,
                    exclude_none=exclude_none
                )
                
                # Update the bound arguments
                for name, value in validated_dict.items():
                    if name in bound_args.arguments:
                        bound_args.arguments[name] = value
                
                # Call the function with validated arguments
                return func(*bound_args.args, **bound_args.kwargs)
                
            except ValidationError as e:
                logger.error(
                    "validation_error",
                    extra={
                        "function": func.__name__,
                        "errors": e.errors(),
                        "input_data": input_data
                    }
                )
                raise
        
        return cast(F, wrapper)
    
    return decorator


def rate_limited(calls: int, period: float = 60.0) -> Callable[[F], F]:
    """
    Decorator to limit the number of calls to a function within a time period.
    
    Args:
        calls: Maximum number of calls allowed in the time period
        period: Time period in seconds (default: 60 seconds)
    """
    import time
    from collections import deque
    
    # Store call timestamps for each function
    call_history: Dict[str, deque[float]] = {}
    
    def decorator(func: F) -> F:
        func_name = f"{func.__module__}.{func.__name__}"
        
        # Initialize call history for this function
        if func_name not in call_history:
            call_history[func_name] = deque()
        
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            now = time.time()
            history = call_history[func_name]
            
            # Remove timestamps older than the period
            while history and now - history[0] > period:
                history.popleft()
            
            # Check if we've exceeded the rate limit
            if len(history) >= calls:
                # Calculate how long to wait
                time_to_wait = period - (now - history[0])
                if time_to_wait > 0:
                    time.sleep(time_to_wait)
            
            # Record the call time
            call_time = time.time()
            history.append(call_time)
            
            # Call the function
            return func(*args, **kwargs)
        
        return cast(F, wrapper)
    
    return decorator


def retry_on_failure(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple[Type[Exception], ...] = (Exception,),
    log_retries: bool = True
) -> Callable[[F], F]:
    """
    Decorator to retry a function on failure.
    
    Args:
        max_attempts: Maximum number of attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier (e.g., 2.0 doubles the delay each retry)
        exceptions: Tuple of exceptions to catch and retry on
        log_retries: Whether to log retry attempts
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            current_delay = delay
            last_exception = None
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts:
                        break
                        
                    if log_retries:
                        logger.warning(
                            "retry_attempt",
                            extra={
                                "function": func.__name__,
                                "attempt": attempt,
                                "max_attempts": max_attempts,
                                "delay": current_delay,
                                "error": str(e),
                                "error_type": type(e).__name__
                            }
                        )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # If we get here, all attempts failed
            if log_retries:
                logger.error(
                    "retry_exhausted",
                    extra={
                        "function": func.__name__,
                        "attempts": max_attempts,
                        "error": str(last_exception) if last_exception else "Unknown error",
                        "error_type": type(last_exception).__name__ if last_exception else "UnknownError"
                    },
                    exc_info=last_exception
                )
            
            raise last_exception if last_exception else Exception("Unknown error in retry decorator")
        
        return cast(F, wrapper)
    
    return decorator


def cache_result(
    maxsize: Optional[int] = 128,
    ttl: Optional[float] = None,
    key_func: Optional[Callable[..., Any]] = None
) -> Callable[[F], F]:
    """
    Decorator to cache function results.
    
    Args:
        maxsize: Maximum cache size (None for unlimited)
        ttl: Time to live in seconds (None for no expiration)
        key_func: Function to generate cache keys
    """
    import functools
    from typing import Any, Callable, Dict, Tuple, Optional
    
    # Cache storage
    cache: Dict[Any, Tuple[float, Any]] = {}
    
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            # Generate cache key
            if key_func:
                key = key_func(*args, **kwargs)
            else:
                # Default key generation
                key = (args, frozenset(kwargs.items()))
            
            # Check cache
            current_time = time.time()
            if key in cache:
                timestamp, result = cache[key]
                if ttl is None or current_time - timestamp < ttl:
                    return result
                # Remove expired item
                del cache[key]
            
            # Call the function and cache the result
            result = func(*args, **kwargs)
            cache[key] = (current_time, result)
            
            # Enforce maxsize
            if maxsize is not None and len(cache) > maxsize:
                # Remove the oldest item
                oldest_key = next(iter(cache))
                del cache[oldest_key]
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


def timed(print_result: bool = False) -> Callable[[F], F]:
    """
    Decorator to measure and log function execution time.
    
    Args:
        print_result: Whether to print the result to stdout
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.monotonic()
            result = func(*args, **kwargs)
            duration = time.monotonic() - start_time
            
            log_data = {
                "function": f"{func.__module__}.{func.__name__}",
                "duration": duration,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            logger.info("function_timed", extra=log_data)
            
            if print_result:
                print(f"{func.__name__} executed in {duration:.4f} seconds")
                if result is not None:
                    print(f"Result: {result}")
            
            return result
        
        return cast(F, wrapper)
    
    return decorator


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('mcp_tools.log')
        ]
    )
    
    # Example tool with all decorators
    @tool(
        name="example_tool",
        description="An example MCP tool with all the decorators",
        version="1.0.0",
        tags=["example", "test"]
    )
    @structured_log()
    @validate_input(create_model("ExampleInput", text=(str, ...), repeat=(int, 1)))
    @rate_limited(calls=5, period=60.0)
    @retry_on_failure(max_attempts=3, delay=1.0)
    @cache_result(maxsize=100, ttl=300)
    @timed(print_result=True)
    def example_tool(text: str, repeat: int = 1) -> str:
        """Repeat the input text the specified number of times."""
        if repeat < 0:
            raise ValueError("Repeat count must be non-negative")
        return " ".join([text] * repeat)
    
    # Test the tool
    try:
        result = example_tool("Hello", repeat=3)
        print(f"Tool result: {result}")
    except Exception as e:
        print(f"Error: {e}")
