import { useState } from 'react'
import './App.css'

// API base URL - change if backend is on different host/port
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

function App() {
  const [query, setQuery] = useState('')
  const [sqlQuery, setSqlQuery] = useState('')
  const [explanation, setExplanation] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleQueryChange = (e) => {
    setQuery(e.target.value)
    setError(null)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)
    setSqlQuery('')
    setExplanation('')
    setResults(null)

    try {
      const response = await fetch(`${API_BASE_URL}/api/generate-sql`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: query,
          model: 'gpt-4o-mini'
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setSqlQuery(data.sql_query || '')
      setExplanation(data.explanation || '')
      
      if (data.error) {
        setError(data.error)
      }
      
    } catch (err) {
      setError(err.message || 'An error occurred while generating SQL')
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  const executeSQL = async () => {
    if (!sqlQuery.trim()) return

    setLoading(true)
    setError(null)
    setResults(null)

    try {
      // Extract just the SQL query (remove comments if any)
      const cleanSql = sqlQuery.split('\n')
        .filter(line => !line.trim().startsWith('--'))
        .join('\n')
        .trim()

      const response = await fetch(`${API_BASE_URL}/api/execute-query`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          sql_query: cleanSql,
          limit: 1000
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || `HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      
      if (data.error) {
        setError(data.error)
        setResults(null)
      } else {
        setResults(data)
        setError(null)
      }
      
    } catch (err) {
      setError(err.message || 'Failed to execute query')
      setResults(null)
      console.error('Error:', err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="app">
      <div className="background-gradient"></div>
      <div className="container">
        <header className="header">
          <div className="header-icon">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
              <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
              <line x1="12" y1="22.08" x2="12" y2="12"></line>
            </svg>
          </div>
          <h1>Data Warehouse Query</h1>
          <p className="subtitle">Ask questions in natural language and get instant SQL insights</p>
        </header>

        <form onSubmit={handleSubmit} className="query-form">
          <div className="input-group">
            <label htmlFor="natural-query">
              <span className="label-icon">💬</span>
              Ask your question
            </label>
            <div className="textarea-wrapper">
              <textarea
                id="natural-query"
                value={query}
                onChange={handleQueryChange}
                placeholder="e.g., 'Show me the top 10 transactions by amount' or 'What are the total sales by category?'"
                rows={4}
                disabled={loading}
                className={loading ? 'loading' : ''}
              />
              {loading && (
                <div className="loading-indicator">
                  <div className="spinner"></div>
                </div>
              )}
            </div>
          </div>
          
          <button 
            type="submit" 
            disabled={loading || !query.trim()}
            className="btn btn-primary"
          >
            {loading ? (
              <>
                <span className="btn-spinner"></span>
                Generating SQL...
              </>
            ) : (
              <>
                <span className="btn-icon">✨</span>
                Generate SQL Query
              </>
            )}
          </button>
        </form>

        {error && (
          <div className="error-message animate-slide-in">
            <div className="error-icon">⚠️</div>
            <div className="error-content">
              <strong>Error</strong>
              <p>{error}</p>
            </div>
          </div>
        )}

        {sqlQuery && (
          <div className="sql-section animate-fade-in">
            <div className="sql-header">
              <div className="section-title">
                <span className="section-icon">📝</span>
                <h2>Generated SQL Query</h2>
              </div>
              <button 
                onClick={executeSQL}
                disabled={loading}
                className="btn btn-secondary"
              >
                {loading ? (
                  <>
                    <span className="btn-spinner"></span>
                    Executing...
                  </>
                ) : (
                  <>
                    <span className="btn-icon">▶️</span>
                    Execute Query
                  </>
                )}
              </button>
            </div>
            {explanation && (
              <div className="explanation">
                <span className="explanation-icon">💡</span>
                <div className="explanation-content">
                  <strong>Explanation:</strong> {explanation}
                </div>
              </div>
            )}
            <div className="sql-code-wrapper">
              <pre className="sql-query"><code>{sqlQuery}</code></pre>
            </div>
          </div>
        )}

        {results && results.rows && results.rows.length > 0 && (
          <div className="results-section animate-fade-in">
            <div className="section-title">
              <span className="section-icon">📊</span>
              <h2>Query Results</h2>
              <span className="results-count">{results.row_count} rows</span>
            </div>
            <div className="results-table-wrapper">
              <div className="results-table">
                <table>
                  <thead>
                    <tr>
                      {results.columns.map((col) => (
                        <th key={col}>{col}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {results.rows.map((row, idx) => (
                      <tr key={idx}>
                        {results.columns.map((col) => (
                          <td key={col}>{row[col] ?? <span className="null-value">NULL</span>}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default App
