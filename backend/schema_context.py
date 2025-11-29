"""
Star Schema Context for LLM
Provides complete schema information to help LLM generate accurate SQL queries
"""

STAR_SCHEMA_CONTEXT = """
# Data Warehouse Star Schema

## Fact Table

### transaction_fact
The main fact table containing transaction records.

**Columns:**
- transaction_id (VARCHAR, PRIMARY KEY): Unique transaction identifier
- category_id (BIGINT, FOREIGN KEY): Links to dim_category
- date_id (BIGINT, FOREIGN KEY): Links to dim_date
- user_id (VARCHAR, FOREIGN KEY): Links to dim_user
- payment_id (BIGINT, FOREIGN KEY): Links to dim_payment
- transaction_amount (NUMERIC(18,2)): Transaction amount in decimal

## Dimension Tables

### dim_user
User/customer information.

**Columns:**
- user_id (VARCHAR, PRIMARY KEY): Unique user identifier
- name (VARCHAR): User's full name
- address (VARCHAR): Street address
- phone_number (VARCHAR): Contact phone number
- city (VARCHAR): City name
- country (VARCHAR): Country name
- email (VARCHAR): Email address

### dim_category
Transaction category and merchant information.

**Columns:**
- category_id (BIGINT, PRIMARY KEY): Unique category identifier
- category_type (VARCHAR): Type of transaction category (e.g., "Food", "Shopping", "Transport")
- merchant (VARCHAR): Merchant or vendor name

### dim_payment
Payment method and currency information.

**Columns:**
- payment_id (BIGINT, PRIMARY KEY): Unique payment identifier
- payment_type (VARCHAR): Type of payment (e.g., "credit", "debit", "cash")
- payment_currency (VARCHAR): Currency code (e.g., "USD", "EUR")
- payment_method (VARCHAR): Payment method (e.g., "card", "transfer", "wallet")

### dim_date
Date and time dimension for temporal analysis.

**Columns:**
- date_id (BIGINT, PRIMARY KEY): Date identifier in format YYYYMMDDHHMM
- year (INT): Year
- quarter (INT): Quarter (1-4)
- month (INT): Month (1-12)
- weekday (VARCHAR): Day of week name
- day (INT): Day of month (1-31)
- hour (INT): Hour of day (0-23)
- minute (INT): Minute (0-59)

## Relationships

- transaction_fact.category_id → dim_category.category_id
- transaction_fact.date_id → dim_date.date_id
- transaction_fact.user_id → dim_user.user_id
- transaction_fact.payment_id → dim_payment.payment_id

## Example Queries

1. Get total transactions by category:
   SELECT c.category_type, SUM(t.transaction_amount) as total
   FROM transaction_fact t
   JOIN dim_category c ON t.category_id = c.category_id
   GROUP BY c.category_type

2. Get transactions by user:
   SELECT u.name, COUNT(*) as transaction_count, SUM(t.transaction_amount) as total_spent
   FROM transaction_fact t
   JOIN dim_user u ON t.user_id = u.user_id
   GROUP BY u.user_id, u.name

3. Get transactions by date:
   SELECT d.year, d.month, COUNT(*) as transaction_count
   FROM transaction_fact t
   JOIN dim_date d ON t.date_id = d.date_id
   GROUP BY d.year, d.month
   ORDER BY d.year, d.month
"""

def get_schema_context() -> str:
    """Return the star schema context string"""
    return STAR_SCHEMA_CONTEXT

