"""
LLM Service for converting natural language to SQL
Uses OpenAI GPT models to generate SQL queries from natural language
"""
import os
from openai import OpenAI
from typing import Optional
from schema_context import get_schema_context
from dotenv import load_dotenv

# Load environment variables - try multiple locations
backend_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(dotenv_path=os.path.join(backend_dir, '.env'))
load_dotenv()  # Also try loading from current directory

# Lazy initialization of OpenAI client
_client = None

def get_openai_client() -> OpenAI:
    """Get or create OpenAI client (lazy initialization)"""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set. Please check your .env file.")
        
        try:
            # Initialize client - the OpenAI library should handle this correctly
            # If proxies parameter error occurs, it's likely a version issue
            _client = OpenAI(api_key=api_key)
        except TypeError as e:
            error_msg = str(e)
            if 'proxies' in error_msg.lower():
                raise ValueError(
                    f"OpenAI client initialization error: {error_msg}\n\n"
                    "This is likely a version compatibility issue. Please try:\n"
                    "1. Upgrade OpenAI library: pip install --upgrade openai\n"
                    "2. Or downgrade: pip install 'openai>=1.0,<1.50'\n"
                    "3. Check for conflicting environment variables"
                )
            raise ValueError(f"Error initializing OpenAI client: {error_msg}")
    
    return _client

def generate_sql_query(natural_language_query: str, model: str = "gpt-4o-mini") -> dict:
    """
    Convert natural language query to SQL using OpenAI.
    
    Args:
        natural_language_query: User's question in natural language
        model: OpenAI model to use (default: gpt-4o-mini for cost efficiency)
    
    Returns:
        dict with 'sql_query' and 'explanation' keys
    """
    schema_context = get_schema_context()
    
    system_prompt = f"""You are a SQL expert assistant. Your task is to convert natural language questions into accurate SQL queries for a data warehouse with a star schema.

{schema_context}

**Important Guidelines:**
1. Always use proper JOINs to connect fact and dimension tables
2. Use descriptive column aliases where helpful
3. Include appropriate WHERE clauses when filtering is mentioned
4. Use aggregate functions (SUM, COUNT, AVG, etc.) when asked for totals, averages, counts
5. Include ORDER BY for "top", "highest", "lowest" type queries
6. Use LIMIT for queries asking for "top N" or "first N"
7. Return ONLY the SQL query, no explanations in the SQL itself
8. Use DuckDB SQL syntax
9. Table names are case-sensitive: transaction_fact, dim_user, dim_category, dim_payment, dim_date
10. Always validate that foreign key relationships are correct

Respond in JSON format with two keys:
- "sql_query": The generated SQL query (as a string)
- "explanation": A brief explanation of what the query does"""
    
    user_prompt = f"""Convert this natural language question to SQL:

"{natural_language_query}"

Generate a SQL query that answers this question using the star schema provided above."""
    
    try:
        client = get_openai_client()
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,  # Lower temperature for more deterministic SQL
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        import json
        result = json.loads(response.choices[0].message.content)
        
        return {
            "sql_query": result.get("sql_query", "").strip(),
            "explanation": result.get("explanation", "")
        }
    
    except Exception as e:
        raise Exception(f"Failed to generate SQL query: {str(e)}")


def validate_sql_query(sql_query: str) -> dict:
    """
    Basic SQL validation - checks for potentially dangerous operations.
    
    Args:
        sql_query: SQL query to validate
    
    Returns:
        dict with 'valid' (bool) and 'error' (str) keys
    """
    sql_upper = sql_query.upper().strip()
    
    # Block dangerous operations
    dangerous_keywords = [
        "DROP", "DELETE", "UPDATE", "INSERT", "ALTER", 
        "CREATE", "TRUNCATE", "GRANT", "REVOKE"
    ]
    
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return {
                "valid": False,
                "error": f"Query contains forbidden operation: {keyword}. Only SELECT queries are allowed."
            }
    
    # Check if it's a SELECT query
    if not sql_upper.startswith("SELECT"):
        return {
            "valid": False,
            "error": "Only SELECT queries are allowed."
        }
    
    return {"valid": True, "error": None}

