# Data Warehouse Query Backend API

FastAPI backend service that converts natural language queries to SQL using OpenAI and executes them against your DuckDB/MinIO data warehouse.

## Features

- 🤖 **LLM Integration**: Converts natural language to SQL using OpenAI GPT models
- 🗄️ **Data Warehouse Access**: Executes queries against DuckDB tables and MinIO parquet files
- 🔒 **Security**: Validates SQL queries to prevent dangerous operations
- 📊 **Star Schema Context**: Provides complete schema information to LLM for accurate queries
- 🚀 **FastAPI**: Modern, fast async API with automatic documentation

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Copy the example environment file and add your OpenAI API key:

```bash
cp .env.example .env
```

Edit `.env` and add your OpenAI API key:

```env
OPENAI_API_KEY=sk-your-actual-api-key-here
```

You can get an API key from: https://platform.openai.com/api-keys

### 3. Run the Server

```bash
python main.py
```

Or with uvicorn directly:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **Alternative Docs**: http://localhost:8000/redoc

## API Endpoints

### 1. Generate SQL from Natural Language

**POST** `/api/generate-sql`

Convert natural language to SQL query.

**Request:**
```json
{
  "query": "Show me the top 10 transactions by amount",
  "model": "gpt-4o-mini"
}
```

**Response:**
```json
{
  "sql_query": "SELECT ...",
  "explanation": "This query returns...",
  "error": null
}
```

### 2. Execute SQL Query

**POST** `/api/execute-query`

Execute SQL query against data warehouse.

**Request:**
```json
{
  "sql_query": "SELECT * FROM transaction_fact LIMIT 10",
  "limit": 1000
}
```

**Response:**
```json
{
  "columns": ["transaction_id", "transaction_amount", ...],
  "rows": [...],
  "row_count": 10,
  "error": null
}
```

### 3. Get Available Tables

**GET** `/api/tables`

Get list of available tables in the data warehouse.

**Response:**
```json
{
  "tables": ["transaction_fact", "dim_user", "dim_category", ...]
}
```

### 4. Health Check

**GET** `/health`

Check if the API is running.

## Project Structure

```
backend/
├── main.py              # FastAPI application and routes
├── llm_service.py       # OpenAI integration for SQL generation
├── query_service.py     # DuckDB/MinIO query execution
├── schema_context.py    # Star schema definitions for LLM context
├── requirements.txt     # Python dependencies
├── .env.example        # Environment variables template
└── README.md           # This file
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY`: Your OpenAI API key (required)
- `DUCKDB_FILE`: Path to DuckDB file (default: `../scripts/etl.duckdb`)
- `MINIO_ENDPOINT`: MinIO endpoint URL (default: `http://localhost:9000`)
- `AWS_ACCESS_KEY_ID`: MinIO access key (default: `minio`)
- `AWS_SECRET_ACCESS_KEY`: MinIO secret key (default: `minio123`)

### LLM Models

You can use different OpenAI models:
- `gpt-4o-mini` (default) - Fast, cost-effective
- `gpt-4o` - More accurate but more expensive
- `gpt-3.5-turbo` - Faster, less accurate

Change the model in the API request or modify the default in `main.py`.

## Security Features

- ✅ Only SELECT queries are allowed
- ✅ Dangerous operations (DROP, DELETE, UPDATE, etc.) are blocked
- ✅ Result limit protection (default: 1000 rows)
- ✅ SQL validation before execution

## Testing

### Test with cURL

1. **Generate SQL:**
```bash
curl -X POST "http://localhost:8000/api/generate-sql" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me the top 10 transactions by amount"}'
```

2. **Execute Query:**
```bash
curl -X POST "http://localhost:8000/api/execute-query" \
  -H "Content-Type: application/json" \
  -d '{"sql_query": "SELECT * FROM transaction_fact LIMIT 10"}'
```

### Test with Swagger UI

Visit http://localhost:8000/docs for interactive API documentation and testing.

## Troubleshooting

### OpenAI API Key Not Set

If you get an error about missing API key:
1. Check that `.env` file exists
2. Verify `OPENAI_API_KEY` is set correctly
3. Restart the server after changing `.env`

### DuckDB File Not Found

If queries fail with file not found errors:
1. Ensure the ETL pipeline has run and created `scripts/etl.duckdb`
2. Check the `DUCKDB_FILE` environment variable path
3. The file path is relative to the backend directory

### MinIO Connection Issues

If MinIO queries fail:
1. Ensure MinIO is running (`docker compose ps`)
2. Check `MINIO_ENDPOINT` in `.env`
3. Verify MinIO credentials are correct

## Next Steps

1. **Test the API**: Use Swagger UI at `/docs` to test endpoints
2. **Connect Frontend**: Update frontend to call these API endpoints
3. **Add Caching**: Consider caching frequent queries
4. **Add Logging**: Add request/response logging
5. **Add Authentication**: Add API key or JWT authentication

## Development

To run in development mode with auto-reload:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Production Deployment

For production, consider:
- Using a production ASGI server (Gunicorn with Uvicorn workers)
- Adding authentication/authorization
- Setting up proper logging
- Using environment-specific configuration
- Adding rate limiting

