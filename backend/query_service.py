"""
Query Service for executing SQL queries against DuckDB/MinIO data warehouse
"""
import os
import duckdb
import boto3
from typing import Optional, Dict, Any
import json

# Configuration
DUCKDB_FILE = os.getenv("DUCKDB_FILE", "../scripts/etl.duckdb")
MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT", "http://localhost:9000")
AWS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "minio")
AWS_SECRET = os.getenv("AWS_SECRET_ACCESS_KEY", "minio123")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
BUCKET_NAME = "datalake"
GOLD_PREFIX = "gold"


def get_db_connection() -> duckdb.DuckDBPyConnection:
    """Create and configure DuckDB connection with MinIO access"""
    # Determine DuckDB file path
    script_dir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(os.path.dirname(script_dir), "scripts", "etl.duckdb")
    
    # If running in container or different location
    if not os.path.exists(db_path):
        db_path = DUCKDB_FILE if os.path.exists(DUCKDB_FILE) else ":memory:"
    
    con = duckdb.connect(db_path)
    
    # Configure S3/MinIO access
    minio_host = MINIO_ENDPOINT.replace('http://', '').replace('https://', '')
    con.execute(f"""
        SET s3_endpoint='{minio_host}';
        SET s3_use_ssl=false;
        SET s3_url_style='path';
        SET s3_access_key_id='{AWS_KEY}';
        SET s3_secret_access_key='{AWS_SECRET}';
        SET s3_region='{AWS_REGION}';
    """)
    
    return con


def execute_query(sql_query: str, limit: Optional[int] = None) -> Dict[str, Any]:
    """
    Execute SQL query against the data warehouse.
    
    Args:
        sql_query: SQL query to execute
        limit: Optional limit on result rows (for safety)
    
    Returns:
        dict with 'columns', 'rows', 'row_count', and 'error' keys
    """
    con = None
    try:
        con = get_db_connection()
        
        # Apply limit if specified
        if limit and "LIMIT" not in sql_query.upper():
            # Add LIMIT if not present
            sql_query = f"{sql_query.rstrip(';')} LIMIT {limit}"
        
        # Execute query
        result = con.execute(sql_query)
        
        # Get column names
        columns = [desc[0] for desc in result.description] if result.description else []
        
        # Fetch all rows
        rows = result.fetchall()
        
        # Convert rows to list of dictionaries
        rows_dict = [dict(zip(columns, row)) for row in rows]
        
        # Handle special types (convert to JSON-serializable format)
        for row in rows_dict:
            for key, value in row.items():
                if hasattr(value, 'isoformat'):  # datetime objects
                    row[key] = value.isoformat()
                elif hasattr(value, '__float__'):  # Decimal, etc.
                    try:
                        row[key] = float(value)
                    except (ValueError, TypeError):
                        row[key] = str(value)
        
        return {
            "columns": columns,
            "rows": rows_dict,
            "row_count": len(rows_dict),
            "error": None
        }
    
    except Exception as e:
        return {
            "columns": [],
            "rows": [],
            "row_count": 0,
            "error": str(e)
        }
    
    finally:
        if con:
            con.close()


def get_available_tables() -> list:
    """Get list of available tables in the data warehouse"""
    con = None
    try:
        con = get_db_connection()
        
        # Try to get tables from DuckDB
        try:
            result = con.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'main'
            """).fetchall()
            tables = [row[0] for row in result]
            if tables:
                return tables
        except:
            pass
        
        # Fallback: return expected tables
        return [
            "transaction_fact",
            "dim_user",
            "dim_category",
            "dim_payment",
            "dim_date"
        ]
    
    except Exception as e:
        print(f"Error getting tables: {e}")
        return []
    
    finally:
        if con:
            con.close()

