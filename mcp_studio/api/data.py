"""
Data API Endpoints for MCP Studio

This module provides API endpoints for data processing operations.
"""
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from pydantic import BaseModel, Field, HttpUrl, validator
import pandas as pd
import json
import io

from ..tools.data import (
    convert_data,
    filter_data,
    transform_data
)
from .auth import get_current_active_user

router = APIRouter()

# Enums for data formats
class DataFormat(str, Enum):
    JSON = "json"
    CSV = "csv"
    PARQUET = "parquet"
    EXCEL = "excel"
    DICT = "dict"
    DATAFRAME = "dataframe"

# Pydantic models
class DataConversionRequest(BaseModel):
    """Data conversion request model."""
    data: Union[Dict, List, str, bytes]
    from_format: DataFormat
    to_format: DataFormat
    options: Dict[str, Any] = Field(default_factory=dict)

class DataFilterRequest(BaseModel):
    """Data filter request model."""
    data: Union[Dict, List, str, bytes]
    data_format: DataFormat
    query: str
    options: Dict[str, Any] = Field(default_factory=dict)

class DataTransformRequest(BaseModel):
    """Data transform request model."""
    data: Union[Dict, List, str, bytes]
    data_format: DataFormat
    transformations: List[Dict[str, Any]]
    options: Dict[str, Any] = Field(default_factory=dict)

class DataOperationResponse(BaseModel):
    """Data operation response model."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: Optional[float] = None

# Helper functions
async def parse_input_data(
    data: Union[Dict, List, str, bytes, UploadFile], 
    data_format: DataFormat
) -> Any:
    """Parse input data based on format."""
    try:
        if isinstance(data, UploadFile):
            content = await data.read()
            if isinstance(content, bytes):
                content = content.decode('utf-8')
        else:
            content = data

        if data_format == DataFormat.JSON:
            if isinstance(content, str):
                return json.loads(content)
            return content
        elif data_format == DataFormat.CSV:
            if isinstance(content, str):
                return pd.read_csv(io.StringIO(content))
            return pd.read_csv(io.BytesIO(content))
        elif data_format == DataFormat.EXCEL:
            if isinstance(content, str):
                return pd.read_excel(io.BytesIO(content.encode('utf-8')))
            return pd.read_excel(io.BytesIO(content))
        elif data_format == DataFormat.PARQUET:
            if isinstance(content, str):
                return pd.read_parquet(io.BytesIO(content.encode('utf-8')))
            return pd.read_parquet(io.BytesIO(content))
        return content
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to parse input data: {str(e)}"
        )

def serialize_output(data: Any, output_format: DataFormat) -> Any:
    """Serialize output data based on format."""
    try:
        if output_format == DataFormat.JSON:
            if isinstance(data, (pd.DataFrame, pd.Series)):
                return data.to_dict(orient='records')
            return data
        elif output_format == DataFormat.CSV:
            if isinstance(data, (pd.DataFrame, pd.Series)):
                return data.to_csv(index=False)
            return pd.DataFrame(data).to_csv(index=False)
        elif output_format == DataFormat.EXCEL:
            output = io.BytesIO()
            if isinstance(data, (pd.DataFrame, pd.Series)):
                data.to_excel(output, index=False)
            else:
                pd.DataFrame(data).to_excel(output, index=False)
            return output.getvalue()
        elif output_format == DataFormat.PARQUET:
            output = io.BytesIO()
            if isinstance(data, (pd.DataFrame, pd.Series)):
                data.to_parquet(output, index=False)
            else:
                pd.DataFrame(data).to_parquet(output, index=False)
            return output.getvalue()
        return data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to serialize output data: {str(e)}"
        )

# API Endpoints
@router.post("/convert", response_model=DataOperationResponse)
async def convert_data_endpoint(
    request: DataConversionRequest,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Convert data between different formats.
    
    Args:
        request: Data conversion request
        
    Returns:
        Converted data in the target format
    """
    import time
    start_time = time.time()
    
    try:
        # Parse input data
        parsed_data = await parse_input_data(request.data, request.from_format)
        
        # Perform conversion
        result = convert_data(
            data=parsed_data,
            from_format=request.from_format,
            to_format=request.to_format,
            **request.options
        )
        
        # Serialize output
        serialized_result = serialize_output(result, request.to_format)
        
        return DataOperationResponse(
            success=True,
            result=serialized_result,
            execution_time=time.time() - start_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return DataOperationResponse(
            success=False,
            error=str(e),
            execution_time=time.time() - start_time
        )

@router.post("/filter", response_model=DataOperationResponse)
async def filter_data_endpoint(
    request: DataFilterRequest,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Filter data based on a query.
    
    Args:
        request: Data filter request
        
    Returns:
        Filtered data in the same format as input
    """
    import time
    start_time = time.time()
    
    try:
        # Parse input data
        parsed_data = await parse_input_data(request.data, request.data_format)
        
        # Apply filter
        result = filter_data(
            data=parsed_data,
            query=request.query,
            **request.options
        )
        
        # Serialize output
        serialized_result = serialize_output(result, request.data_format)
        
        return DataOperationResponse(
            success=True,
            result=serialized_result,
            execution_time=time.time() - start_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return DataOperationResponse(
            success=False,
            error=str(e),
            execution_time=time.time() - start_time
        )

@router.post("/transform", response_model=DataOperationResponse)
async def transform_data_endpoint(
    request: DataTransformRequest,
    current_user: Any = Depends(get_current_active_user)
):
    """
    Apply transformations to data.
    
    Args:
        request: Data transform request
        
    Returns:
        Transformed data in the same format as input
    """
    import time
    start_time = time.time()
    
    try:
        # Parse input data
        parsed_data = await parse_input_data(request.data, request.data_format)
        
        # Apply transformations
        result = transform_data(
            data=parsed_data,
            transformations=request.transformations,
            **request.options
        )
        
        # Serialize output
        serialized_result = serialize_output(result, request.data_format)
        
        return DataOperationResponse(
            success=True,
            result=serialized_result,
            execution_time=time.time() - start_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return DataOperationResponse(
            success=False,
            error=str(e),
            execution_time=time.time() - start_time
        )

@router.post("/upload-and-process", response_model=DataOperationResponse)
async def upload_and_process_data(
    file: UploadFile = File(...),
    data_format: DataFormat = Form(...),
    operation: str = Form("convert"),
    target_format: Optional[DataFormat] = Form(None),
    query: Optional[str] = Form(None),
    transformations: Optional[str] = Form(None),
    current_user: Any = Depends(get_current_active_user)
):
    """
    Upload and process data in one step.
    
    Args:
        file: File to upload and process
        data_format: Format of the input file
        operation: Operation to perform (convert, filter, transform)
        target_format: Target format for conversion
        query: Filter query (for filter operation)
        transformations: JSON string of transformations (for transform operation)
        
    Returns:
        Processed data
    """
    import time
    start_time = time.time()
    
    try:
        # Read file content
        content = await file.read()
        
        # Parse input data
        parsed_data = await parse_input_data(content, data_format)
        
        # Perform requested operation
        if operation == "convert":
            if not target_format:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="target_format is required for convert operation"
                )
            result = convert_data(
                data=parsed_data,
                from_format=data_format,
                to_format=target_format
            )
            output_format = target_format
            
        elif operation == "filter":
            if not query:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="query is required for filter operation"
                )
            result = filter_data(data=parsed_data, query=query)
            output_format = data_format
            
        elif operation == "transform":
            if not transformations:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="transformations is required for transform operation"
                )
            try:
                transform_list = json.loads(transformations)
                if not isinstance(transform_list, list):
                    raise ValueError("transformations must be a JSON array")
            except json.JSONDecodeError as e:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid transformations JSON: {str(e)}"
                )
            result = transform_data(data=parsed_data, transformations=transform_list)
            output_format = data_format
            
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported operation: {operation}"
            )
        
        # Serialize output
        serialized_result = serialize_output(result, output_format)
        
        # Determine content type for response
        content_type = "application/octet-stream"
        if output_format == DataFormat.JSON:
            content_type = "application/json"
        elif output_format == DataFormat.CSV:
            content_type = "text/csv"
        elif output_format == DataFormat.EXCEL:
            content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # Return as file download
        from fastapi.responses import Response
        return Response(
            content=serialized_result if isinstance(serialized_result, bytes) else str(serialized_result).encode('utf-8'),
            media_type=content_type,
            headers={
                "Content-Disposition": f"attachment; filename=result.{output_format}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        return DataOperationResponse(
            success=False,
            error=str(e),
            execution_time=time.time() - start_time
        )
