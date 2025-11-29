"""
Data Processing and Transformation Tools for MCP Studio

Core data processing and transformation utilities.
"""
import json
import logging
from enum import Enum
from typing import Any, Dict, List, Optional, Union, Callable

from pydantic import BaseModel, Field

from mcp_studio.tools import tool, structured_log, validate_input

logger = logging.getLogger("mcp.tools.data")

class DataFormat(str, Enum):
    """Supported data formats for conversion."""
    JSON = "json"
    CSV = "csv"
    PANDAS = "pandas"
    DICT = "dict"

class DataTransformationInput(BaseModel):
    """Input model for data transformation tools."""
    data: Any = Field(..., description="Input data to transform")
    input_format: Optional[DataFormat] = Field(None, description="Format of the input data")
    output_format: DataFormat = Field(DataFormat.JSON, description="Desired output format")

@tool(
    name="convert_data",
    description="Convert data between different formats",
    tags=["data", "conversion"]
)
@structured_log()
async def convert_data(
    data: Any,
    input_format: Optional[DataFormat] = None,
    output_format: DataFormat = DataFormat.JSON,
) -> Any:
    """Convert data between JSON, CSV, Pandas, and Python dict formats."""
    # Input conversion to Python dict
    if input_format == DataFormat.JSON and isinstance(data, str):
        data = json.loads(data)
    
    # Output conversion
    if output_format == DataFormat.JSON:
        return json.dumps(data, indent=2)
    return data

@tool(
    name="filter_data",
    description="Filter data based on conditions",
    tags=["data", "filtering"]
)
@structured_log()
async def filter_data(
    data: Union[List[Dict], str],
    condition: Union[str, Callable],
    input_format: Optional[DataFormat] = None,
) -> List[Dict]:
    """Filter data using a condition (string or callable)."""
    if isinstance(data, str):
        data = json.loads(data)
    
    if callable(condition):
        return [item for item in data if condition(item)]
    
    # Simple string condition evaluation
    return [item for item in data if eval(condition, {}, item)]

@tool(
    name="transform_data",
    description="Apply transformations to data",
    tags=["data", "transformation"]
)
@structured_log()
async def transform_data(
    data: Union[List[Dict], str],
    transformations: Dict[str, str],
    input_format: Optional[DataFormat] = None,
) -> List[Dict]:
    """Apply transformations to data fields."""
    if isinstance(data, str):
        data = json.loads(data)
    
    result = []
    for item in data:
        new_item = item.copy()
        for field, expr in transformations.items():
            new_item[field] = eval(expr, {}, {"item": item})
        result.append(new_item)
    
    return result
