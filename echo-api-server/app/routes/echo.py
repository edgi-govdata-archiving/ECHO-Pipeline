from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from datetime import datetime
from app.auth.github import validate_github_token
from app.services.RateLimiter import RateLimiter
from app.utils.spark import get_spark_session
from app.db.helpers import log_cache_query, get_cached_query
import os
import tempfile
from datetime import timedelta, datetime, timezone
import time
import json

query_cache = {}

DELTA_TABLES_DIR = os.path.join(os.environ.get('DELTA_LAKE_PATH'), "files")
SCHEMA_DIR = os.path.join(os.environ.get('SCHEMA_DIR_PATH'))

router = APIRouter()


@router.get("/{table_name}", dependencies=[
    Depends(validate_github_token),
    Depends(RateLimiter(requests_limit=1, time_window=5))
    ])
async def read_table(request: Request, table_name: str, limit: int = None, sql: str = None, idx_field: str = None, base_table: str = None, echo_type: str = None):
    print(f"Table name: {table_name}")
    print(f"Limit: {limit}")
    print(f"SQL: {sql}")
    
    # only allow SELECT queries
    if not sql or "select" not in sql.lower():
        raise HTTPException(status_code=403, detail="Forbidden: Only SELECT queries are allowed.")

    # Check for cached query
    cached_query = await get_cached_query(sql)
    if cached_query:
        print("Using cached result")
        return FileResponse(
            cached_query.path,
            filename=f"{table_name}_{int(datetime.utcnow().timestamp())}.json",
            media_type="application/json"
        )
    
    # Path to the Delta table
    delta_table_path = os.path.join(DELTA_TABLES_DIR, table_name)

    # Check if the Delta table exists
    if not os.path.exists(delta_table_path):
        return {"error": "Table not found"}

    spark = get_spark_session()
    # Read the Delta table
    if limit:
        df = spark.read.format("delta").load(delta_table_path).limit(limit)
    else:
        df = spark.read.format("delta").load(delta_table_path)
    
    # Cache if it's ECHO_EXPORTER
    if table_name == "ECHO_EXPORTER":
        df = df.cache()
    
    # Run SQL query if provided
    df.createOrReplaceTempView(table_name)
    if sql:
        result_df = spark.sql(sql)
    else:
        result_df = df
    
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as tmp:
        # Write JSON incrementally
        tmp.write("[")
        first = True
        for row in result_df.toJSON().toLocalIterator():
            if not first:
                tmp.write(",")
            tmp.write(row)
            first = False
        tmp.write("]")
        tmp_path = tmp.name
    
    # Cache the file path
    query_cache[sql] = tmp_path
    
    await log_cache_query(table_name, sql, tmp_path, request.client.host)
    print('in db')
    
    return FileResponse(
        tmp_path,
        filename=f"{table_name}_{int(datetime.utcnow().timestamp())}.json",
        media_type="application/json"
    )

@router.get("/schema/{table_name}", dependencies=[
    Depends(validate_github_token),
    Depends(RateLimiter(requests_limit=1, time_window=5))
    ])
async def get_json(table_name:str):
    # Check if the schema file exists
    schema_file_path = os.path.join(SCHEMA_DIR, f"{table_name}_schema.json")
    print(f"Schema file path: {schema_file_path}")
    if not os.path.exists(schema_file_path):
        raise HTTPException(status_code=404, detail="Schema file not found")
    # Read the schema file
    with open(schema_file_path, "r") as f:
        data = json.load(f)
    return JSONResponse(content=data)
