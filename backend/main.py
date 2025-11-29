"""
FastAPI Backend for Data Warehouse Query Interface
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import os
from dotenv import load_dotenv

# Load environment variables FIRST, before importing modules that need them
backend_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(backend_dir, '.env'))
load_dotenv()  # Also try loading from current directory

from llm_service import generate_sql_query, validate_sql_query
from query_service import execute_query, get_available_tables

# Initialize FastAPI app
app = FastAPI(
    title="Data Warehouse Query API",
    description="API for converting natural language to SQL and executing queries",
    version="1.0.0"
)

# Configure CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],  # Vite default ports
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response Models
class NaturalLanguageQuery(BaseModel):
    query: str
    model: Optional[str] = "gpt-4o-mini"


class SQLQueryRequest(BaseModel):
    sql_query: str
    limit: Optional[int] = 1000  # Safety limit


class SQLQueryResponse(BaseModel):
    columns: list
    rows: list
    row_count: int
    error: Optional[str] = None


class SQLGenerationResponse(BaseModel):
    sql_query: str
    explanation: str
    error: Optional[str] = None


# API Routes
@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Data Warehouse Query API",
        "version": "1.0.0",
        "endpoints": {
            "generate_sql": "/api/generate-sql",
            "execute_query": "/api/execute-query",
            "tables": "/api/tables",
            "health": "/health"
        }
    }


@app.get("/health")
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@app.get("/api/tables")
def get_tables():
    """Get list of available tables in the data warehouse"""
    try:
        tables = get_available_tables()
        return {"tables": tables}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get tables: {str(e)}")


@app.post("/api/generate-sql", response_model=SQLGenerationResponse)
def generate_sql(request: NaturalLanguageQuery):
    """
    Convert natural language query to SQL using LLM.
    
    Example:
        {
            "query": "Show me the top 10 transactions by amount",
            "model": "gpt-4o-mini"
        }
    """
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty")
    
    # Check if OpenAI API key is set
    if not os.getenv("OPENAI_API_KEY"):
        raise HTTPException(
            status_code=500,
            detail="OPENAI_API_KEY environment variable not set"
        )
    
    try:
        result = generate_sql_query(request.query, request.model)
        
        # Validate the generated SQL
        validation = validate_sql_query(result["sql_query"])
        if not validation["valid"]:
            return SQLGenerationResponse(
                sql_query=result["sql_query"],
                explanation=result["explanation"],
                error=validation["error"]
            )
        
        return SQLGenerationResponse(
            sql_query=result["sql_query"],
            explanation=result["explanation"],
            error=None
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate SQL: {str(e)}")


@app.post("/api/execute-query", response_model=SQLQueryResponse)
def execute_sql(request: SQLQueryRequest):
    """
    Execute SQL query against the data warehouse.
    
    Example:
        {
            "sql_query": "SELECT * FROM transaction_fact LIMIT 10",
            "limit": 1000
        }
    """
    if not request.sql_query.strip():
        raise HTTPException(status_code=400, detail="SQL query cannot be empty")
    
    # Validate SQL query
    validation = validate_sql_query(request.sql_query)
    if not validation["valid"]:
        raise HTTPException(status_code=400, detail=validation["error"])
    
    try:
        result = execute_query(request.sql_query, request.limit)
        
        if result["error"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return SQLQueryResponse(
            columns=result["columns"],
            rows=result["rows"],
            row_count=result["row_count"],
            error=None
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute query: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("API_PORT", "8000"))  # Use 8000 instead of 5000 to avoid conflicts
    uvicorn.run(app, host="0.0.0.0", port=port)

