"""
Development API Endpoints for MCP Studio

This module provides API endpoints for development and debugging tools.
"""
import asyncio
import cProfile
import io
import pstats
import time
import traceback
from typing import Any, Dict, List, Optional, Callable, Union
from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
import psutil
import os
import sys
import inspect
import logging

from mcp_studio.tools.development import (
    profile_code,
    debug_function,
    trace_execution,
    measure_memory
)
from .auth import get_current_active_user

router = APIRouter()
logger = logging.getLogger("mcp.api.dev")

# Pydantic models
class ProfileRequest(BaseModel):
    """Code profiling request model."""
    code: str = Field(..., description="Python code to profile")
    globals_dict: Optional[Dict[str, Any]] = Field(
        None,
        description="Global variables to make available to the code"
    )
    sort_by: str = Field(
        "cumulative",
        description="Sort key for profiling results (e.g., 'cumulative', 'time', 'calls')"
    )
    limit: int = Field(
        20,
        description="Maximum number of results to return",
        ge=1,
        le=1000
    )

class ProfileResult(BaseModel):
    """Code profiling result model."""
    success: bool
    stats: Optional[Dict[str, Any]] = None
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float

class DebugRequest(BaseModel):
    """Debug function request model."""
    function: str = Field(..., description="Function to debug (as a string)")
    args: List[Any] = Field(default_factory=list, description="Positional arguments")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Keyword arguments")
    capture_output: bool = Field(True, description="Whether to capture function output")
    show_locals: bool = Field(True, description="Whether to show local variables")

class DebugResult(BaseModel):
    """Debug function result model."""
    success: bool
    result: Optional[Any] = None
    output: Optional[str] = None
    execution_time: float
    error: Optional[str] = None

class TraceRequest(BaseModel):
    """Trace execution request model."""
    code: str = Field(..., description="Code to trace")
    globals_dict: Optional[Dict[str, Any]] = Field(
        None,
        description="Global variables to make available to the code"
    )

class TraceResult(BaseModel):
    """Trace execution result model."""
    success: bool
    trace: Optional[List[Dict[str, Any]]] = None
    output: Optional[str] = None
    error: Optional[str] = None
    execution_time: float

class MemoryUsage(BaseModel):
    """Memory usage information."""
    rss: int  # Resident Set Size
    vms: int  # Virtual Memory Size
    percent: float
    available: int  # Available system memory
    total: int  # Total system memory

class ProcessInfo(BaseModel):
    """Process information."""
    pid: int
    name: str
    status: str
    cpu_percent: float
    memory_percent: float
    create_time: float
    threads: int
    memory_info: Dict[str, int]
    cmdline: List[str]

class SystemInfo(BaseModel):
    """System information."""
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    disk: Dict[str, Any]
    network: Dict[str, Any]
    processes: List[ProcessInfo]

# API Endpoints
@router.post("/profile", response_model=ProfileResult)
async def profile_code_endpoint(
    request: ProfileRequest,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Profile the execution of Python code.
    
    Args:
        request: Profiling request with code and options
        
    Returns:
        Profiling results
    """
    start_time = time.time()
    
    try:
        # Create a local namespace
        local_vars = {}
        
        # Add any provided globals
        if request.globals_dict:
            local_vars.update(request.globals_dict)
        
        # Redirect stdout to capture output
        old_stdout = sys.stdout
        output = io.StringIO()
        sys.stdout = output
        
        # Profile the code
        profiler = cProfile.Profile()
        profiler.enable()
        
        try:
            # Execute the code
            exec(request.code, globals(), local_vars)
            
            # Get the result if there's a variable called 'result'
            result = local_vars.get('result', None)
            
        finally:
            profiler.disable()
            sys.stdout = old_stdout
        
        # Get profiling stats
        s = io.StringIO()
        ps = pstats.Stats(profiler, stream=s).sort_stats(request.sort_by)
        ps.print_stats(request.limit)
        
        # Format the stats
        stats_output = s.getvalue()
        
        # Parse the stats into a structured format
        stats_lines = stats_output.strip().split('\n')
        stats = {
            'ncalls': [],
            'tottime': [],
            'percall': [],
            'cumtime': [],
            'percall_cum': [],
            'filename:lineno(function)': []
        }
        
        # Skip the header lines
        for line in stats_lines[5:]:
            parts = line.split()
            if len(parts) >= 6:
                stats['ncalls'].append(parts[0])
                stats['tottime'].append(parts[1])
                stats['percall'].append(parts[2])
                stats['cumtime'].append(parts[3])
                stats['percall_cum'].append(parts[4])
                stats['filename:lineno(function)'].append(' '.join(parts[5:]))
        
        return ProfileResult(
            success=True,
            stats=stats,
            output=output.getvalue(),
            execution_time=time.time() - start_time
        )
        
    except Exception as e:
        return ProfileResult(
            success=False,
            error=str(e),
            execution_time=time.time() - start_time
        )

@router.post("/debug", response_model=DebugResult)
async def debug_function_endpoint(
    request: DebugRequest,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Debug a Python function.
    
    Args:
        request: Debug request with function code and arguments
        
    Returns:
        Debugging results
    """
    start_time = time.time()
    
    try:
        # Create a local namespace
        local_vars = {}
        
        # Execute the function definition
        exec(request.function, globals(), local_vars)
        
        # Find the function in the local namespace
        func = None
        for name, obj in local_vars.items():
            if inspect.isfunction(obj):
                func = obj
                break
                
        if not func:
            raise ValueError("No function found in the provided code")
        
        # Redirect stdout to capture output
        old_stdout = sys.stdout
        output = io.StringIO()
        sys.stdout = output
        
        try:
            # Call the function with debugging
            result = debug_function(
                func=func,
                args=request.args,
                kwargs=request.kwargs,
                capture_output=request.capture_output,
                show_locals=request.show_locals
            )
            
            return DebugResult(
                success=True,
                result=result,
                output=output.getvalue(),
                execution_time=time.time() - start_time
            )
            
        finally:
            sys.stdout = old_stdout
            
    except Exception as e:
        return DebugResult(
            success=False,
            error=str(e),
            execution_time=time.time() - start_time
        )

@router.post("/trace", response_model=TraceResult)
async def trace_execution_endpoint(
    request: TraceRequest,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Trace the execution of Python code.
    
    Args:
        request: Trace request with code to trace
        
    Returns:
        Execution trace
    """
    start_time = time.time()
    
    try:
        # Create a local namespace
        local_vars = {}
        
        # Add any provided globals
        if request.globals_dict:
            local_vars.update(request.globals_dict)
        
        # Redirect stdout to capture output
        old_stdout = sys.stdout
        output = io.StringIO()
        sys.stdout = output
        
        try:
            # Trace the code execution
            trace = []
            
            def trace_callback(frame, event, arg):
                if event in ['call', 'line', 'return', 'exception']:
                    # Get the code and line number
                    code = frame.f_code
                    filename = code.co_filename
                    lineno = frame.f_lineno
                    
                    # Get the function name
                    func_name = code.co_name
                    
                    # Get the local variables
                    if event == 'call':
                        # Only show args on call
                        args = {}
                        arg_names = code.co_varnames[:code.co_argcount]
                        for name in arg_names:
                            if name in frame.f_locals:
                                try:
                                    args[name] = repr(frame.f_locals[name])
                                except Exception:
                                    args[name] = '<unable to represent>'
                        
                        trace_entry = {
                            'event': event,
                            'filename': filename,
                            'lineno': lineno,
                            'function': func_name,
                            'args': args,
                            'locals': {}
                        }
                    else:
                        trace_entry = {
                            'event': event,
                            'filename': filename,
                            'lineno': lineno,
                            'function': func_name,
                            'args': {},
                            'locals': {}
                        }
                    
                    # Add to trace
                    trace.append(trace_entry)
                
                return trace_callback
            
            # Set up the trace
            sys.settrace(trace_callback)
            
            try:
                # Execute the code
                exec(request.code, globals(), local_vars)
            finally:
                # Reset the trace
                sys.settrace(None)
            
            return TraceResult(
                success=True,
                trace=trace,
                output=output.getvalue(),
                execution_time=time.time() - start_time
            )
            
        finally:
            sys.stdout = old_stdout
            
    except Exception as e:
        return TraceResult(
            success=False,
            error=str(e),
            execution_time=time.time() - start_time
        )

@router.get("/memory", response_model=MemoryUsage)
async def get_memory_usage(
    current_user: Any = Depends(get_current_active_user)
):
    """
    Get memory usage information.
    
    Returns:
        Memory usage information
    """
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    virtual_memory = psutil.virtual_memory()
    
    return MemoryUsage(
        rss=memory_info.rss,
        vms=memory_info.vms,
        percent=process.memory_percent(),
        available=virtual_memory.available,
        total=virtual_memory.total
    )

@router.get("/system", response_model=SystemInfo)
async def get_system_info(
    current_user: Any = Depends(get_current_active_user)
):
    """
    Get system information.
    
    Returns:
        System information
    """
    # CPU info
    cpu_info = {
        'cores': psutil.cpu_count(logical=False),
        'logical_cores': psutil.cpu_count(logical=True),
        'usage_percent': psutil.cpu_percent(interval=1, percpu=True),
        'avg_load': [x / psutil.cpu_count() * 100 for x in psutil.getloadavg()],
        'cpu_times': psutil.cpu_times_percent(interval=1)._asdict()
    }
    
    # Memory info
    virtual_memory = psutil.virtual_memory()
    swap_memory = psutil.swap_memory()
    
    memory_info = {
        'total': virtual_memory.total,
        'available': virtual_memory.available,
        'percent': virtual_memory.percent,
        'used': virtual_memory.used,
        'free': virtual_memory.free,
        'active': getattr(virtual_memory, 'active', None),
        'inactive': getattr(virtual_memory, 'inactive', None),
        'buffers': getattr(virtual_memory, 'buffers', None),
        'cached': getattr(virtual_memory, 'cached', None),
        'shared': getattr(virtual_memory, 'shared', None),
        'swap_total': swap_memory.total,
        'swap_used': swap_memory.used,
        'swap_free': swap_memory.free,
        'swap_percent': swap_memory.percent
    }
    
    # Disk info
    disk_usage = psutil.disk_usage('/')
    disk_io = psutil.disk_io_counters()
    
    disk_info = {
        'total': disk_usage.total,
        'used': disk_usage.used,
        'free': disk_usage.free,
        'percent': disk_usage.percent,
        'read_count': disk_io.read_count if disk_io else None,
        'write_count': disk_io.write_count if disk_io else None,
        'read_bytes': disk_io.read_bytes if disk_io else None,
        'write_bytes': disk_io.write_bytes if disk_io else None,
        'read_time': disk_io.read_time if disk_io else None,
        'write_time': disk_io.write_time if disk_io else None
    }
    
    # Network info
    net_io = psutil.net_io_counters()
    net_connections = psutil.net_connections(kind='inet')
    
    network_info = {
        'bytes_sent': net_io.bytes_sent,
        'bytes_recv': net_io.bytes_recv,
        'packets_sent': net_io.packets_sent,
        'packets_recv': net_io.packets_recv,
        'errin': net_io.errin,
        'errout': net_io.errout,
        'dropin': net_io.dropin,
        'dropout': net_io.dropout,
        'connections': [
            {
                'fd': conn.fd,
                'family': conn.family.name,
                'type': conn.type.name,
                'local_addr': f"{conn.laddr.ip}:{conn.laddr.port}" if conn.laddr else None,
                'remote_addr': f"{conn.raddr.ip}:{conn.raddr.port}" if conn.raddr else None,
                'status': conn.status,
                'pid': conn.pid
            }
            for conn in net_connections
        ]
    }
    
    # Process info
    processes = []
    for proc in psutil.process_iter(['pid', 'name', 'status', 'cpu_percent', 'memory_percent', 'create_time', 'num_threads', 'memory_info', 'cmdline']):
        try:
            pinfo = proc.info
            processes.append(
                ProcessInfo(
                    pid=pinfo['pid'],
                    name=pinfo['name'],
                    status=pinfo['status'],
                    cpu_percent=pinfo['cpu_percent'],
                    memory_percent=pinfo['memory_percent'],
                    create_time=pinfo['create_time'],
                    threads=pinfo['num_threads'],
                    memory_info=pinfo['memory_info']._asdict() if pinfo['memory_info'] else {},
                    cmdline=pinfo['cmdline']
                )
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    
    return SystemInfo(
        cpu=cpu_info,
        memory=memory_info,
        disk=disk_info,
        network=network_info,
        processes=processes
    )

# WebSocket endpoint for real-time monitoring
@router.websocket("/monitor")
async def websocket_monitor(
    websocket: WebSocket,
    token: str,
    interval: float = 1.0
):
    """
    WebSocket endpoint for real-time system monitoring.
    
    Args:
        websocket: WebSocket connection
        token: Authentication token
        interval: Update interval in seconds
    """
    # Authenticate
    try:
        await websocket.accept()
        current_user = await get_current_active_user(token)
    except Exception as e:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return
    
    try:
        while True:
            # Get system info
            system_info = await get_system_info()
            
            # Send update
            await websocket.send_json({
                'type': 'update',
                'timestamp': time.time(),
                'cpu': system_info.cpu,
                'memory': system_info.memory,
                'disk': system_info.disk,
                'network': system_info.network
            })
            
            # Wait for the next update
            await asyncio.sleep(interval)
            
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {str(e)}")
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
