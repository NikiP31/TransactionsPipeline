#!/usr/bin/env python3
import duckdb
import boto3
import uuid
import hashlib
import os
import sys
from datetime import datetime

# -------------------------
# Config
# -------------------------
DUCKDB_FILE = "etl.duckdb"
MINIO_ENDPOINT = "http://minio:9000"   # <- use container network hostname
AWS_KEY = "minio"
AWS_SECRET = "minio123"
AWS_REGION = "us-east-1"

bucket_name = "datalake"
silver_prefix = "silver"
gold_prefix = "gold"

# -------------------------
# Helpers
# -------------------------
def hash_key(value: str) -> int:
    return int(hashlib.md5(value.encode()).hexdigest()[:12], 16)

def read_create_sql(path):
    with open(path, "r", encoding="utf-8") as fh:
        return fh.read()

# -------------------------
# DuckDB + MinIO Setup
# -------------------------
con = duckdb.connect(DUCKDB_FILE)

s3 = boto3.client(
    "s3",
    endpoint_url=MINIO_ENDPOINT,
    aws_access_key_id=AWS_KEY,
    aws_secret_access_key=AWS_SECRET,
    region_name=AWS_REGION
)

# Configure DuckDB to use S3/MinIO
con.execute(f"""
    SET s3_endpoint='{MINIO_ENDPOINT.replace('http://','')}';
    SET s3_use_ssl=false;
    SET s3_url_style='path';
    SET s3_access_key_id='{AWS_KEY}';
    SET s3_secret_access_key='{AWS_SECRET}';
    SET s3_region='{AWS_REGION}';
""")

print("✅ DuckDB connected and MinIO configured.")

# -------------------------
# Create DW tables (if provided)
# -------------------------
# try to load create_dw_tables.sql located next to this script
script_dir = os.path.dirname(os.path.realpath(__file__))
create_sql_path = os.path.join(script_dir, "create_dw_tables.sql")

if os.path.exists(create_sql_path):
    try:
        ddl = read_create_sql(create_sql_path)
        con.execute(ddl)
        print(f"✅ Executed DDL from {create_sql_path}")
    except Exception as e:
        print("⚠️ Failed to execute create_dw_tables.sql:", e)
        # continue — tables might already exist or DDL might be incompatible
else:
    print(f"⚠️ create_dw_tables.sql not found at {create_sql_path}. Ensure DW tables exist.")

# -------------------------
# List Silver parquet files
# -------------------------
try:
    resp = s3.list_objects_v2(Bucket=bucket_name, Prefix=f"{silver_prefix}/")
except Exception as e:
    print("❌ Error listing objects from MinIO:", e)
    sys.exit(1)

if "Contents" not in resp:
    print("⚠️ No objects under silver/ prefix (Contents missing). Exiting gracefully.")
    sys.exit(0)

silver_files = [
    f"s3://{bucket_name}/{obj['Key']}"
    for obj in resp["Contents"]
    if obj["Key"].endswith(".parquet")
]

if not silver_files:
    print("⚠️ No Silver parquet files found. Exiting.")
    sys.exit(0)

print(f"📦 Found {len(silver_files)} silver parquet files")

# -------------------------
# Process each Silver file
# -------------------------
required_cols_user = {"user_id", "name", "street_address", "phone", "city", "country", "email"}
required_cols_fact = {"transaction_id", "category", "merchant", "transaction_date", "amount", "transaction_type", "currency", "payment_method", "user_id"}

for file in silver_files:
    print(f"\n➡️ Processing silver file: {file}")
    try:
        df = con.execute(f"SELECT * FROM read_parquet('{file}')").fetchdf()
    except Exception as e:
        print(f"⚠️ Failed to read parquet {file}: {e}. Skipping.")
        continue

    if df.empty:
        print("⚠️ Silver file empty, skipping.")
        continue

    cols = set(df.columns)
    missing_for_user = required_cols_user - cols
    missing_for_fact = required_cols_fact - cols

    if missing_for_user and missing_for_fact:
        print(f"⚠️ Missing many expected columns for this file. Missing (user cols): {missing_for_user}, (fact cols): {missing_for_fact}. Skipping.")
        continue

    # ---------- DIM USER ----------
    try:
        if required_cols_user.intersection(cols):
            take = list(required_cols_user.intersection(cols))
            df_user = df[take].drop_duplicates().copy()
            # rename if column names differ in order; we attempt to unify
            rename_map = {}
            # map street_address -> address, phone -> phone_number
            if "street_address" in df_user.columns:
                rename_map["street_address"] = "address"
            if "phone" in df_user.columns:
                rename_map["phone"] = "phone_number"
            if rename_map:
                df_user = df_user.rename(columns=rename_map)

            con.register("tmp_users", df_user)
            con.execute("""
                INSERT OR IGNORE INTO dim_user
                (user_id, name, address, phone_number, city, country, email)
                SELECT user_id, name, address, phone_number, city, country, email
                FROM tmp_users;
            """)
            print(f"✔ DIM USER upserted ({len(df_user)} rows)")
        else:
            print("⚠️ No user-like columns in this file; skipping dim_user step.")
    except Exception as e:
        print("⚠️ Error inserting dim_user:", e)

    # ---------- DIM CATEGORY ----------
    try:
        if {"category", "merchant"}.issubset(cols):
            df_cat = df[["category", "merchant"]].drop_duplicates().copy()
            df_cat["category_id"] = df_cat.apply(lambda r: hash_key(str(r["category"]) + str(r["merchant"])), axis=1)
            con.register("tmp_cat", df_cat)
            con.execute("""
                INSERT OR IGNORE INTO dim_category
                (category_id, category_type, merchant)
                SELECT category_id, category, merchant FROM tmp_cat;
            """)
            print(f"✔ DIM CATEGORY upserted ({len(df_cat)} rows)")
        else:
            print("⚠️ Missing category/merchant columns; skipping dim_category step.")
    except Exception as e:
        print("⚠️ Error inserting dim_category:", e)

    # ---------- DIM PAYMENT ----------
    try:
        if {"transaction_type", "currency", "payment_method"}.issubset(cols):
            df_pay = df[["transaction_type", "currency", "payment_method"]].drop_duplicates().copy()
            df_pay["payment_id"] = df_pay.apply(lambda r: hash_key(str(r["transaction_type"]) + str(r["currency"]) + str(r["payment_method"])), axis=1)
            con.register("tmp_pay", df_pay)
            con.execute("""
                INSERT OR IGNORE INTO dim_payment
                (payment_id, payment_type, payment_currency, payment_method)
                SELECT payment_id, transaction_type, currency, payment_method
                FROM tmp_pay;
            """)
            print(f"✔ DIM PAYMENT upserted ({len(df_pay)} rows)")
        else:
            print("⚠️ Missing payment-related columns; skipping dim_payment step.")
    except Exception as e:
        print("⚠️ Error inserting dim_payment:", e)

    # ---------- DIM DATE ----------
    try:
        if "transaction_date" in cols:
            # ensure transaction_date is datetime-like
            df["transaction_date"] = df["transaction_date"].astype("datetime64[ns]")
            df_date = df[["transaction_date"]].drop_duplicates().copy()
            df_date["date_id"] = df_date["transaction_date"].apply(lambda d: int(d.strftime("%Y%m%d%H%M")))
            df_date["year"] = df_date["transaction_date"].dt.year
            df_date["quarter"] = df_date["transaction_date"].dt.quarter
            df_date["month"] = df_date["transaction_date"].dt.month
            df_date["weekday"] = df_date["transaction_date"].dt.day_name()
            df_date["day"] = df_date["transaction_date"].dt.day
            df_date["hour"] = df_date["transaction_date"].dt.hour
            df_date["minute"] = df_date["transaction_date"].dt.minute

            con.register("tmp_dates", df_date)
            con.execute("""
                INSERT OR IGNORE INTO dim_date
                (date_id, year, quarter, month, weekday, day, hour, minute)
                SELECT date_id, year, quarter, month, weekday, day, hour, minute
                FROM tmp_dates;
            """)
            print(f"✔ DIM DATE upserted ({len(df_date)} rows)")
        else:
            print("⚠️ transaction_date missing; skipping dim_date step.")
    except Exception as e:
        print("⚠️ Error inserting dim_date:", e)

    # ---------- FACT TABLE ----------
    try:
        # verify minimal columns for fact
        if required_cols_fact.intersection(cols):
            # create computed ids where possible
            # guard conversion of transaction_date
            if "transaction_date" in df.columns:
                df["transaction_date"] = df["transaction_date"].astype("datetime64[ns]")
                df["date_id"] = df["transaction_date"].apply(lambda d: int(d.strftime("%Y%m%d%H%M")))
            else:
                df["date_id"] = None

            # create category_id and payment_id if source cols present
            if {"category", "merchant"}.issubset(df.columns):
                df["category_id"] = df.apply(lambda r: hash_key(str(r["category"]) + str(r["merchant"])), axis=1)
            else:
                df["category_id"] = None

            if {"transaction_type", "currency", "payment_method"}.issubset(df.columns):
                df["payment_id"] = df.apply(lambda r: hash_key(str(r.get("transaction_type","")) + str(r.get("currency","")) + str(r.get("payment_method",""))), axis=1)
            else:
                df["payment_id"] = None

            # select minimal fact columns that exist
            fact_cols = ["transaction_id", "category_id", "date_id", "user_id", "payment_id", "amount"]
            present_fact_cols = [c for c in fact_cols if c in df.columns or c in ["category_id","date_id","payment_id"]]
            df_fact = df[["transaction_id","category_id","date_id","user_id","payment_id","amount"]].copy()

            df_fact.columns = [
                "transaction_id", "category_id", "date_id",
                "user_id", "payment_id", "transaction_amount"
            ]

            con.register("tmp_fact", df_fact)
            con.execute("""
                INSERT OR IGNORE INTO transaction_fact
                (transaction_id, category_id, date_id, user_id, payment_id, transaction_amount)
                SELECT transaction_id, category_id, date_id, user_id, payment_id, transaction_amount
                FROM tmp_fact;
            """)
            print(f"✔ FACT rows inserted ({len(df_fact)} rows)")
        else:
            print("⚠️ Not enough columns to populate fact table; skipping.")
    except Exception as e:
        print("⚠️ Error inserting facts:", e)

# -------------------------
# Export DW tables to Gold parquet
# -------------------------
tables = {
    "dim_user":         f"{gold_prefix}/dim_user.parquet",
    "dim_category":     f"{gold_prefix}/dim_category.parquet",
    "dim_payment":      f"{gold_prefix}/dim_payment.parquet",
    "dim_date":         f"{gold_prefix}/dim_date.parquet",
    "transaction_fact": f"{gold_prefix}/transaction_fact.parquet",
}

for table, path in tables.items():
    try:
        target = f"s3://{bucket_name}/{path}"
        con.execute(f"""
            COPY (SELECT * FROM {table})
            TO '{target}'
            (FORMAT PARQUET, OVERWRITE_OR_IGNORE TRUE);
        """)
        print(f"✔ Wrote {table} → {target}")
    except Exception as e:
        print(f"⚠️ Failed to write {table} to gold: {e}")

print("\n🎉 Data Warehouse Gold ETL Complete")
con.close()
