#!/usr/bin/env python3
"""
Query script for Data Warehouse
Works both locally and in containers
Queries from DuckDB tables or MinIO parquet files
"""
import duckdb
import boto3
import os
import sys

# Configuration
BUCKET_NAME = "datalake"
GOLD_PREFIX = "gold"
MINIO_ENDPOINT_LOCAL = "http://localhost:9000"
MINIO_ENDPOINT_CONTAINER = "http://minio:9000"
AWS_KEY = "minio"
AWS_SECRET = "minio123"
AWS_REGION = "us-east-1"

def get_minio_endpoint():
    """Detect if running in container or locally"""
    if os.path.exists('/opt/airflow'):
        return MINIO_ENDPOINT_CONTAINER
    return MINIO_ENDPOINT_LOCAL

def setup_duckdb_s3(con, minio_endpoint):
    """Configure DuckDB to access MinIO/S3"""
    s3_host = minio_endpoint.replace('http://', '').replace('https://', '')
    con.execute(f"""
        SET s3_endpoint='{s3_host}';
        SET s3_use_ssl=false;
        SET s3_url_style='path';
        SET s3_access_key_id='{AWS_KEY}';
        SET s3_secret_access_key='{AWS_SECRET}';
        SET s3_region='{AWS_REGION}';
    """)

def query_from_duckdb_table(con, table_name):
    """Try to query from DuckDB table"""
    try:
        # Check if table exists
        result = con.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name}'").fetchone()
        if result[0] > 0:
            query = f"SELECT COUNT(*) AS total_rows FROM {table_name};"
            result = con.execute(query).fetchone()
            return result[0]
    except Exception as e:
        print(f"⚠️ Could not query from DuckDB table: {e}")
    return None

def query_from_minio_parquet(con, table_name):
    """Query from MinIO parquet file"""
    try:
        parquet_path = f"s3://{BUCKET_NAME}/{GOLD_PREFIX}/{table_name}.parquet"
        query = f"SELECT COUNT(*) AS total_rows FROM read_parquet('{parquet_path}');"
        result = con.execute(query).fetchone()
        return result[0]
    except Exception as e:
        print(f"⚠️ Could not query from MinIO parquet: {e}")
    return None

def get_table_data(con, table_name, limit=10):
    """Get sample data from table"""
    try:
        # Try DuckDB table first
        try:
            result = con.execute(f"SELECT COUNT(*) FROM information_schema.tables WHERE table_name = '{table_name}'").fetchone()
            if result[0] > 0:
                query = f"SELECT * FROM {table_name} LIMIT {limit};"
                return con.execute(query).fetchdf()
        except:
            pass
        
        # Fallback to MinIO parquet
        parquet_path = f"s3://{BUCKET_NAME}/{GOLD_PREFIX}/{table_name}.parquet"
        query = f"SELECT * FROM read_parquet('{parquet_path}') LIMIT {limit};"
        return con.execute(query).fetchdf()
    except Exception as e:
        print(f"⚠️ Could not get table data: {e}")
        return None

def main():
    # Determine if running locally or in container
    minio_endpoint = get_minio_endpoint()
    is_local = minio_endpoint == MINIO_ENDPOINT_LOCAL
    
    # Path to DuckDB file
    script_dir = os.path.dirname(os.path.realpath(__file__))
    db_path = os.path.join(script_dir, "etl.duckdb")
    
    # If running locally and file doesn't exist in scripts, check root
    if not os.path.exists(db_path) and is_local:
        root_db = os.path.join(os.path.dirname(script_dir), "etl.duckdb")
        if os.path.exists(root_db):
            db_path = root_db
    
    print(f"📊 Data Warehouse Query Tool")
    print(f"📍 Running: {'Local' if is_local else 'Container'}")
    print(f"🔗 MinIO: {minio_endpoint}")
    print(f"💾 DuckDB: {db_path if os.path.exists(db_path) else 'N/A (will use MinIO only)'}")
    print("-" * 60)
    
    try:
        # Connect to DuckDB
        con = duckdb.connect(db_path if os.path.exists(db_path) else ":memory:")
        
        # Configure S3/MinIO access
        setup_duckdb_s3(con, minio_endpoint)
        print("✅ Connected to DuckDB and configured MinIO access\n")
        
        # Query transaction_fact table
        table_name = "transaction_fact"
        print(f"🔍 Querying {table_name}...")
        
        # Try DuckDB table first
        count = query_from_duckdb_table(con, table_name)
        if count is not None:
            print(f"✅ Found {count} rows in DuckDB table: {table_name}")
        else:
            # Fallback to MinIO parquet
            print(f"📦 DuckDB table not found, trying MinIO parquet...")
            count = query_from_minio_parquet(con, table_name)
            if count is not None:
                print(f"✅ Found {count} rows in MinIO parquet: {table_name}.parquet")
            else:
                print(f"❌ Could not find {table_name} in DuckDB or MinIO")
                return
        
        # Get sample data
        print(f"\n📋 Sample data from {table_name} (first 5 rows):")
        print("-" * 60)
        df = get_table_data(con, table_name, limit=5)
        if df is not None and not df.empty:
            print(df.to_string())
        else:
            print("No data available")
        
        # Additional queries
        print(f"\n📈 Additional Statistics:")
        print("-" * 60)
        
        # Try to get more stats if available
        try:
            if count and count > 0:
                # Get sample of other tables
                other_tables = ["dim_user", "dim_category", "dim_payment", "dim_date"]
                for other_table in other_tables:
                    other_count = query_from_duckdb_table(con, other_table)
                    if other_count is None:
                        other_count = query_from_minio_parquet(con, other_table)
                    if other_count is not None:
                        print(f"  {other_table}: {other_count} rows")
        except Exception as e:
            print(f"  (Could not get additional stats: {e})")
        
        con.close()
        print("\n✅ Query complete")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()