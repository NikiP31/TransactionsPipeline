# Data Warehouse Query Frontend

A React-based frontend application that allows users to query the data warehouse using natural language. The application converts natural language queries to SQL using an LLM (like ChatGPT) and executes them against the data warehouse.

## Features

- 🗣️ Natural language query interface
- 🤖 LLM-powered SQL query generation
- 📊 Query results visualization
- 🔍 Data warehouse integration

## Getting Started

### Prerequisites

- Node.js (v18 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx          # Main application component
│   ├── App.css          # Application styles
│   ├── main.jsx         # Application entry point
│   └── index.css        # Global styles
├── public/              # Static assets
├── package.json         # Dependencies and scripts
└── vite.config.js       # Vite configuration
```

## Next Steps

### 1. Set up Backend API

Create a Flask/FastAPI backend to handle:
- LLM integration (OpenAI API, Anthropic, etc.)
- SQL query execution against DuckDB/MinIO
- Star schema context for the LLM

**Suggested structure:**
```
backend/
├── app.py              # Main Flask/FastAPI application
├── llm_service.py      # LLM integration for SQL generation
├── query_service.py    # Execute SQL queries against DuckDB
└── schema_context.py   # Star schema definitions for LLM context
```

### 2. Integrate LLM API

Update `App.jsx` to call your backend API:

```javascript
const handleSubmit = async (e) => {
  e.preventDefault()
  setLoading(true)
  
  try {
    const response = await fetch('http://localhost:8000/api/generate-sql', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        query: query,
        schema_context: starSchemaContext 
      })
    })
    
    const data = await response.json()
    setSqlQuery(data.sql_query)
  } catch (err) {
    setError(err.message)
  } finally {
    setLoading(false)
  }
}
```

### 3. Add Star Schema Context

Create a file with your star schema definition to provide context to the LLM:

```javascript
// src/schema.js
export const starSchema = {
  fact_tables: {
    transaction_fact: {
      description: "Main fact table containing transaction records",
      columns: {
        transaction_id: "Unique transaction identifier",
        category_id: "Foreign key to dim_category",
        date_id: "Foreign key to dim_date",
        user_id: "Foreign key to dim_user",
        payment_id: "Foreign key to dim_payment",
        transaction_amount: "Transaction amount in decimal"
      }
    }
  },
  dimension_tables: {
    dim_user: { /* ... */ },
    dim_category: { /* ... */ },
    dim_date: { /* ... */ },
    dim_payment: { /* ... */ }
  }
}
```

### 4. Execute SQL Queries

Add functionality to execute SQL queries:

```javascript
const executeSQL = async () => {
  setLoading(true)
  
  try {
    const response = await fetch('http://localhost:8000/api/execute-query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ sql_query: sqlQuery })
    })
    
    const data = await response.json()
    setResults(data.results)
  } catch (err) {
    setError(err.message)
  } finally {
    setLoading(false)
  }
}
```

### 5. Improve UI

- Add a data table component for results display
- Add query history
- Add export functionality (CSV, JSON)
- Add query validation and error handling

## Available Scripts

- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run preview` - Preview production build
- `npm run lint` - Run ESLint

## Environment Variables

Create a `.env` file for configuration:

```env
VITE_API_URL=http://localhost:8000
VITE_LLM_PROVIDER=openai
```

## Technologies Used

- React 19
- Vite
- Modern CSS

## Future Enhancements

- [ ] Query history and favorites
- [ ] Query result export (CSV, Excel)
- [ ] Data visualization charts
- [ ] Query validation and suggestions
- [ ] Authentication and user management
- [ ] Query performance metrics
