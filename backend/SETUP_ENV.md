# Setting Up Your .env File

## Quick Setup

1. **Navigate to the backend directory:**
   ```bash
   cd backend
   ```

2. **Create the .env file** (if it doesn't exist):
   ```bash
   cp .env.example .env
   ```

3. **Edit the .env file** and add your OpenAI API key:
   ```bash
   # Open in your editor
   nano .env
   # or
   vim .env
   ```

4. **The .env file should look like this:**
   ```env
   OPENAI_API_KEY=sk-your-actual-openai-api-key-here
   DUCKDB_FILE=../scripts/etl.duckdb
   MINIO_ENDPOINT=http://localhost:9000
   AWS_ACCESS_KEY_ID=minio
   AWS_SECRET_ACCESS_KEY=minio123
   AWS_REGION=us-east-1
   ```

## Important Notes

- **No spaces** around the `=` sign
- **No quotes** around the API key value
- The API key should start with `sk-`
- Make sure there are no extra spaces or newlines

## Verify Setup

After creating/editing your .env file, test if it's working:

```bash
cd backend
source ../.venv/bin/activate  # Activate your virtual environment
python3 -c "from dotenv import load_dotenv; import os; load_dotenv(); print('API Key loaded:', 'Yes' if os.getenv('OPENAI_API_KEY') else 'No')"
```

## Troubleshooting

If the API key still isn't found:

1. **Check file location:** Make sure `.env` is in the `backend/` directory
2. **Check file format:** Should be `KEY=value` format, one per line
3. **Check for hidden characters:** Make sure there are no extra spaces
4. **Restart the server:** After editing .env, restart your Python server

## Alternative: Set Environment Variable Directly

If .env file doesn't work, you can set it as an environment variable:

```bash
export OPENAI_API_KEY=sk-your-actual-key-here
python main.py
```

