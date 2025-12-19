"""
Development Tools for MCP Studio

This module provides tools to assist with development, debugging, and profiling.
"""
import asyncio
import cProfile
import inspect
import io
import logging
import pstats
import time
import traceback
from contextlib import contextmanager, redirect_stdout, redirect_stderr
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from timeit import default_timer
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, TypeVar, Union

from pydantic import BaseModel, Field

from . import (
    tool,
    structured_log,
    validate_input,
    rate_limited,
    retry_on_failure,
    cache_result,
    timed
)

logger = logging.getLogger("mcp.tools.development")

@dataclass
class CodeLocation:
    """Represents a location in source code."""
    file: str
    line: int
    function: str

class ProfilingResult(BaseModel):
    """Results from code profiling."""
    total_time: float = Field(..., description="Total execution time in seconds")
    per_call_times: Dict[str, float] = Field(..., description="Time per function call in seconds")
    call_counts: Dict[str, int] = Field(..., description="Number of calls per function")
    call_graph: Dict[str, List[str]] = Field(..., description="Call graph of functions")
    stats: str = Field(..., description="Formatted profiling statistics")

@tool(
    name="profile_code",
    description="Profile a block of Python code",
    tags=["development", "profiling", "performance"]
)
@structured_log()
async def profile_code(
    code: str,
    setup: str = "",
    sort_by: str = "cumulative",
    limit: int = 10,
    output_file: Optional[str] = None
) -> ProfilingResult:
    """
    Profile a block of Python code and return detailed performance metrics.
    
    Args:
        code: The Python code to profile
        setup: Setup code to run before profiling (imports, etc.)
        sort_by: How to sort the results (cumulative, time, calls, etc.)
        limit: Maximum number of results to return
        output_file: Optional file path to save the full profile results
        
    Returns:
        ProfilingResult with detailed performance metrics
    """
    # Create a profiler and run the code
    pr = cProfile.Profile()
    
    # Prepare the namespace
    namespace = {"__name__": "__profile__"}
    
    # Run setup code if provided
    if setup:
        try:
            exec(setup, namespace, namespace)
        except Exception as e:
            logger.error("setup_code_failed", extra={"error": str(e)}, exc_info=True)
            raise ValueError(f"Error in setup code: {e}")
    
    # Run the code with profiling
    try:
        pr.enable()
        start_time = time.monotonic()
        exec(code, namespace, namespace)
        total_time = time.monotonic() - start_time
        pr.disable()
    except Exception as e:
        pr.disable()
        logger.error("code_execution_failed", extra={"error": str(e)}, exc_info=True)
        raise ValueError(f"Error in code execution: {e}")
    
    # Get the statistics
    s = io.StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats(sort_by)
    
    # Save full stats to file if requested
    if output_file:
        try:
            output_path = Path(output_file).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            ps.dump_stats(str(output_path))
            logger.info("profile_saved", extra={"path": str(output_path)})
        except Exception as e:
            logger.warning("failed_to_save_profile", extra={"path": output_file, "error": str(e)})
    
    # Get the statistics as a string
    ps.print_stats(limit)
    stats_output = s.getvalue()
    
    # Parse the statistics into a more structured format
    per_call_times = {}
    call_counts = {}
    call_graph = {}
    
    # This is a simplified parser for the statistics output
    # The actual format is more complex, but this gives a good starting point
    for line in stats_output.split('\n'):
        if not line.strip() or 'function calls' in line or line.startswith(' '):
            continue
            
        parts = line.split()
        if len(parts) >= 6:
            try:
                ncalls = parts[0] if parts[0] != '{}' else '1'
                ncalls = int(ncalls.split('/')[0]) if '/' in ncalls else int(ncalls)
                tottime = float(parts[2])
                percall = float(parts[3]) if parts[3] != '--' else tottime
                func_name = ' '.join(parts[5:])
                
                per_call_times[func_name] = percall
                call_counts[func_name] = ncalls
                
                # Simple call graph (just track which functions were called)
                # A more sophisticated implementation would track the actual call hierarchy
                call_graph[func_name] = []
                
            except (ValueError, IndexError):
                continue
    
    return ProfilingResult(
        total_time=total_time,
        per_call_times=per_call_times,
        call_counts=call_counts,
        call_graph=call_graph,
        stats=stats_output
    )

@tool(
    name="debug_function",
    description="Debug a function by logging its inputs, outputs, and execution time",
    tags=["development", "debugging"]
)
def debug_function(func: Callable) -> Callable:
    """
    Decorator to debug a function by logging its inputs, outputs, and execution time.
    
    Args:
        func: The function to debug
        
    Returns:
        Wrapped function with debugging
    """
    def wrapper(*args, **kwargs):
        # Log function call with arguments
        func_name = func.__name__
        logger.debug(
            "function_called",
            extra={
                "function": func_name,
                "args": args,
                "kwargs": kwargs,
                "caller": _get_caller_info()
            }
        )
        
        # Measure execution time
        start_time = time.monotonic()
        
        try:
            # Call the function
            result = func(*args, **kwargs)
            execution_time = time.monotonic() - start_time
            
            # Log successful execution
            logger.debug(
                "function_completed",
                extra={
                    "function": func_name,
                    "execution_time": execution_time,
                    "result": str(result)[:1000]  # Limit result size
                }
            )
            
            return result
            
        except Exception as e:
            # Log the error
            execution_time = time.monotonic() - start_time
            logger.error(
                "function_failed",
                extra={
                    "function": func_name,
                    "execution_time": execution_time,
                    "error": str(e),
                    "traceback": traceback.format_exc()
                },
                exc_info=True
            )
            raise
    
    return wrapper

def _get_caller_info() -> Dict[str, Any]:
    """Get information about the caller of the current function."""
    frame = inspect.currentframe()
    try:
        # Go up 3 frames to get to the actual caller
        # 1: current function (_get_caller_info)
        # 2: debug_function's wrapper
        # 3: The function that called the decorated function
        for _ in range(3):
            if frame.f_back is None:
                break
            frame = frame.f_back
        
        return {
            "file": frame.f_code.co_filename,
            "line": frame.f_lineno,
            "function": frame.f_code.co_name
        }
    finally:
        del frame  # Avoid reference cycles

@tool(
    name="trace_execution",
    description="Trace the execution of a function, logging each step",
    tags=["development", "tracing", "debugging"]
)
@contextmanager
def trace_execution(
    func_name: str = "",
    log_level: str = "DEBUG",
    max_depth: int = 10
):
    """
    Context manager to trace the execution of a block of code.
    
    Args:
        func_name: Name of the function being traced (for logging)
        log_level: Logging level to use (DEBUG, INFO, etc.)
        max_depth: Maximum call depth to trace (to avoid too much output)
    """
    import sys
    import threading
    
    # Get the logger for the current module
    logger = logging.getLogger("mcp.tools.trace")
    
    # Thread-local storage for the trace function
    local = threading.local()
    
    def trace_calls(frame, event, arg):
        # Skip if we're not in the main thread
        if not hasattr(local, 'depth'):
            local.depth = 0
        
        # Skip if we've exceeded the maximum depth
        if local.depth > max_depth:
            return trace_calls
        
        # Get the code object and function name
        code = frame.f_code
        func_name = code.co_name
        
        # Skip tracing if we're in a standard library module
        if 'site-packages' in code.co_filename or 'lib/python' in code.co_filename:
            return trace_calls
        
        # Log the event
        if event == 'call':
            local.depth += 1
            logger.log(
                getattr(logging, log_level, logging.DEBUG),
                "%sCall to %s in %s, line %s",
                '  ' * local.depth,
                func_name,
                code.co_filename,
                frame.f_lineno
            )
            return trace_calls
            
        elif event == 'return':
            logger.log(
                getattr(logging, log_level, logging.DEBUG),
                "%sReturn from %s => %s",
                '  ' * local.depth,
                func_name,
                str(arg)[:100]  # Limit size of return value
            )
            local.depth -= 1
            
        elif event == 'exception':
            logger.log(
                getattr(logging, 'ERROR'),
                "%sException in %s: %s",
                '  ' * local.depth,
                func_name,
                str(arg[1])
            )
        
        return trace_calls
    
    # Set up the trace
    sys.settrace(trace_calls)
    try:
        yield
    finally:
        # Clean up
        sys.settrace(None)

@tool(
    name="measure_memory",
    description="Measure memory usage of a function or code block",
    tags=["development", "memory", "profiling"]
)
@contextmanager
def measure_memory(
    label: str = "",
    detailed: bool = False
):
    """
    Context manager to measure memory usage of a code block.
    
    Args:
        label: Label for the memory measurement
        detailed: Whether to include detailed memory information
    """
    import psutil
    import os
    
    process = psutil.Process(os.getpid())
    
    # Get initial memory usage
    mem_before = process.memory_info().rss
    if detailed:
        mem_full_before = process.memory_full_info()
    
    start_time = time.monotonic()
    
    try:
        yield
    finally:
        # Calculate memory usage
        mem_after = process.memory_info().rss
        mem_used = (mem_after - mem_before) / (1024 * 1024)  # Convert to MB
        duration = time.monotonic() - start_time
        
        # Log the results
        extra = {
            "label": label or "memory_measurement",
            "memory_used_mb": round(mem_used, 2),
            "duration_seconds": round(duration, 4),
            "memory_before_mb": round(mem_before / (1024 * 1024), 2),
            "memory_after_mb": round(mem_after / (1024 * 1024), 2)
        }
        
        if detailed:
            mem_full_after = process.memory_full_info()
            extra.update({
                "rss_mb": round(mem_full_after.rss / (1024 * 1024), 2),
                "vms_mb": round(mem_full_after.vms / (1024 * 1024), 2),
                "shared_mb": round(mem_full_after.shared / (1024 * 1024), 2),
                "text_mb": round(mem_full_after.text / (1024 * 1024), 2),
                "data_mb": round(mem_full_after.data / (1024 * 1024), 2)
            })
        
        logger.info("memory_measurement", extra=extra)
