import duckdb
import boto3
import uuid
import os
import sys

# ============================================================
# 1. Connect to DuckDB
# ============================================================
con = duckdb.connect("etl.duckdb")

# ============================================================
# 2. MinIO (S3) client config
# ============================================================
# Use container endpoint if running in Airflow, otherwise use localhost
MINIO_ENDPOINT = "http://localhost:9000"
if os.path.exists('/opt/airflow'):
    MINIO_ENDPOINT = "http://minio:9000"

s3 = boto3.client(
    's3',
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id="minio",
    aws_secret_access_key="minio123",
    region_name="us-east-1"
)

# ============================================================
# 3. DuckDB S3 Settings
# ============================================================
# Extract hostname from endpoint URL
s3_host = MINIO_ENDPOINT.replace('http://', '').replace('https://', '')
con.execute(f"""
    SET s3_endpoint='{s3_host}';
    SET s3_use_ssl=false;
    SET s3_url_style='path';
    SET s3_access_key_id='minio';
    SET s3_secret_access_key='minio123';
    SET s3_region='us-east-1';
""")

bucket_name = "datalake"
bronze_prefix = "bronze"
silver_prefix = "silver"

print("✅ Connected to DuckDB and configured MinIO access")

# ============================================================
# 4. List ALL parquet files from Bronze
# ============================================================
resp = s3.list_objects_v2(
    Bucket=bucket_name,
    Prefix=f"{bronze_prefix}/"
)

if "Contents" not in resp:
    print("⚠️ No objects found inside Bronze folder!")
    sys.exit(0)

parquet_files = [
    f"s3://{bucket_name}/{obj['Key']}"
    for obj in resp["Contents"]
    if obj["Key"].endswith(".parquet")
]

if not parquet_files:
    print("⚠️ No Bronze parquet files found!")
    sys.exit(0)

print(f"📦 Found {len(parquet_files)} Bronze parquet files")

print("🚀 Transforming Bronze → Silver...")

# ============================================================
# 5. Transform each Bronze parquet → cleaned Silver parquet
# ============================================================
for file in parquet_files:

    # Generate unique parquet name
    silver_file = f"s3://{bucket_name}/{silver_prefix}/silver_{uuid.uuid4().hex}.parquet"

    con.execute(f"""
        COPY (
            SELECT 
                user_id,
                name,
                email,
                phone,
                street_address,
                city,
                country,
                transaction_id,
                TRY_CAST(transaction_date AS TIMESTAMP) AS transaction_date,
                TRY_CAST(amount AS DOUBLE) AS amount,
                currency,
                merchant,
                category,
                transaction_type,
                payment_method
            FROM read_parquet('{file}')
            WHERE email LIKE '%@%'
              AND amount IS NOT NULL
              AND TRY_CAST(amount AS DOUBLE) > 0
              AND TRY_CAST(transaction_date AS TIMESTAMP) IS NOT NULL
        )
        TO '{silver_file}'
        (FORMAT PARQUET, OVERWRITE_OR_IGNORE TRUE)
    """)

    print(f"✅ Silver file written: {silver_file}")

# ============================================================
# 6. Preview sample of silver output
# ============================================================
try:
    df_preview = con.execute(f"""
        SELECT * 
        FROM read_parquet('s3://{bucket_name}/{silver_prefix}/*.parquet')
        LIMIT 5
    """).fetchdf()

    print("🧊 Silver data preview:")
    print(df_preview)

except Exception as e:
    print("⚠️ Could not preview Silver data:", e)

# ============================================================
# 7. Close DB
# ============================================================
con.close()
print("🎉 Silver ETL complete, connection closed.")
