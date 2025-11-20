import duckdb
import boto3
import uuid

# ============================================================
# 1. Connect to or create a local DuckDB database file
# ============================================================
con = duckdb.connect("etl.duckdb")

s3 = boto3.client(
    's3',
    endpoint_url="http://127.0.0.1:9000",
    aws_access_key_id="minio",
    aws_secret_access_key="minio123",
    region_name="us-east-1"
)

con.execute("""
    SET s3_endpoint='127.0.0.1:9000';
    SET s3_use_ssl=false;
    SET s3_url_style='path';
    SET s3_access_key_id='minio';
    SET s3_secret_access_key='minio123';
    SET s3_region='us-east-1';
""")

df = con.execute("""
SELECT * FROM read_parquet('s3://datalake/gold/gold_07dd74f74eb3443cac4ba4cf1d59badb.parquet')
WHERE month >= '2025-01-01'
ORDER BY total_spent DESC
LIMIT 10;
""").fetchdf()

print(df)