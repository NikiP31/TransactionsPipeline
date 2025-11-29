# Complete Setup Guide - Data Warehouse Query System

This guide will help you set up the entire system: ETL pipeline, backend API, and frontend interface.

## System Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   Frontend  │────▶│  Backend API │────▶│  Data       │
│   (React)   │     │  (FastAPI)   │     │  Warehouse  │
└─────────────┘     └──────────────┘     └─────────────┘
                            │                    │
                            ▼                    ▼
                     ┌──────────────┐     ┌─────────────┐
                     │ OpenAI LLM   │     │  DuckDB +   │
                     │  (ChatGPT)   │     │   MinIO     │
                     └──────────────┘     └─────────────┘
```

## Prerequisites

- Docker and Docker Compose
- Node.js (v18+)
- Python 3.8+
- OpenAI API key (get from https://platform.openai.com/api-keys)

## Step-by-Step Setup

### Step 1: Start Infrastructure (Kafka, MinIO, Airflow)

```bash
# Start all services
docker compose up -d

# Wait for services to start (1-2 minutes)
docker compose ps

# Verify services are running
# - Kafka: localhost:9092
# - MinIO: localhost:9000 (console: localhost:9001)
# - Airflow: localhost:8080
```

### Step 2: Run ETL Pipeline

**Option A: Via Airflow (Recommended)**
1. Open http://localhost:8080
2. Login: `admin` / `admin`
3. Find `etl_pipeline` DAG
4. Click play button (▶️) to trigger

**Option B: Manually** (for testing)
```bash
# 1. Create Kafka topic
docker exec -it kafka-diplomska-kafka-1 kafka-topics.sh \
  --create --topic raw-data --bootstrap-server localhost:9092 \
  --partitions 1 --replication-factor 1

# 2. Produce data
python3 newProducer.py

# 3. Run ETL scripts
cd scripts
python3 bronze_write.py
python3 bronze_to_silver.py
python3 silver_to_gold.py
```

### Step 3: Setup Backend API

```bash
cd backend

# 1. Create virtual environment (optional but recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key:
# OPENAI_API_KEY=sk-your-actual-key-here

# 4. Start the API server
python main.py
# Or: uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

### Step 4: Setup Frontend

```bash
cd frontend

# 1. Install dependencies
npm install

# 2. Configure API URL (optional)
# Create .env file:
# VITE_API_URL=http://localhost:8000

# 3. Start development server
npm run dev
```

The frontend will be available at: http://localhost:5173

## Testing the System

### 1. Test Backend API

**Using Swagger UI:**
- Open http://localhost:8000/docs
- Try the `/api/generate-sql` endpoint with:
  ```json
  {
    "query": "Show me the top 10 transactions by amount"
  }
  ```

**Using cURL:**
```bash
# Generate SQL
curl -X POST "http://localhost:8000/api/generate-sql" \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me the top 10 transactions by amount"}'

# Execute Query
curl -X POST "http://localhost:8000/api/execute-query" \
  -H "Content-Type: application/json" \
  -d '{"sql_query": "SELECT * FROM transaction_fact LIMIT 10"}'
```

### 2. Test Frontend

1. Open http://localhost:5173
2. Type a natural language query: "Show me the top 10 transactions by amount"
3. Click "Generate SQL Query"
4. Review the generated SQL
5. Click "Execute Query" to see results

## Example Queries

Try these natural language queries:

- "Show me the top 10 transactions by amount"
- "What are the total transactions by category?"
- "How many transactions happened in each month?"
- "Show me all users who made transactions"
- "What is the average transaction amount by payment method?"

## Troubleshooting

### Backend can't connect to DuckDB

- Ensure ETL pipeline has run and created `scripts/etl.duckdb`
- Check `DUCKDB_FILE` path in `.env`
- Verify the file exists: `ls -la scripts/etl.duckdb`

### Frontend can't connect to Backend

- Ensure backend is running on port 8000
- Check browser console for CORS errors
- Verify `VITE_API_URL` in frontend `.env` matches backend URL

### OpenAI API errors

- Verify `OPENAI_API_KEY` is set in backend `.env`
- Check API key is valid at https://platform.openai.com/api-keys
- Ensure you have API credits

### MinIO connection issues

- Check MinIO is running: `docker compose ps minio`
- Verify credentials in backend `.env` match docker-compose.yaml
- Check MinIO console: http://localhost:9001 (minio/minio123)

## File Structure

```
kafka-diplomska/
├── backend/              # FastAPI backend
│   ├── main.py          # API routes
│   ├── llm_service.py   # OpenAI integration
│   ├── query_service.py # DuckDB/MinIO queries
│   └── schema_context.py # Star schema for LLM
├── frontend/            # React frontend
│   └── src/
│       └── App.jsx      # Main UI component
├── scripts/             # ETL scripts
│   ├── bronze_write.py
│   ├── bronze_to_silver.py
│   └── silver_to_gold.py
├── dags/                # Airflow DAGs
│   └── etl_pipeline.py
└── docker-compose.yaml  # Infrastructure
```

## Next Steps

1. ✅ Test the complete workflow end-to-end
2. 🎨 Customize the frontend UI
3. 🔐 Add authentication if needed
4. 📊 Add data visualization charts
5. 🚀 Deploy to production

## Support

- Backend API docs: http://localhost:8000/docs
- Airflow UI: http://localhost:8080
- MinIO Console: http://localhost:9001

