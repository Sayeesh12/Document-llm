# Quick Start Guide

Get the Document Intelligence API running in 3 minutes!

## Step 1: Get Gemini API Key (30 seconds)

1. Visit https://makersuite.google.com/app/apikey
2. Sign in with your Google account
3. Click "Create API Key"
4. Copy the key

## Step 2: Configure (30 seconds)

```bash
cd "document api"
cp .env.example .env
```

Edit `.env` and paste your Gemini API key:
```
GEMINI_API_KEY=your-actual-key-here
```

## Step 3: Start with Docker (2 minutes)

```bash
docker-compose up --build
```

Wait for:
```
backend_1   | INFO:     Application startup complete.
frontend_1  | ready in X ms
```

## Step 4: Open and Test

1. Open http://localhost:5173 in your browser
2. Drag and drop a PDF invoice or bank statement
3. Watch the AI extract structured data!

## Without Docker?

**Backend:**
```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY="your-key"
export API_KEY="dev-api-key-12345"
uvicorn main:app --reload
```

**Frontend (new terminal):**
```bash
cd frontend
npm install
npm run dev
```

## API Testing

```bash
# Health check
curl http://localhost:8000/health

# Process document
curl -X POST http://localhost:8000/documents/process \
  -H "X-API-Key: dev-api-key-12345" \
  -F "file=@your-invoice.pdf"
```

## Troubleshooting

**"Gemini API key not configured"**
→ Check `.env` file has `GEMINI_API_KEY=...`

**Port already in use**
→ Change ports in `docker-compose.yml`

**Frontend can't reach backend**
→ Make sure both services are running
→ Check `VITE_API_URL` in `.env`

## Next Steps

- Read README.md for full documentation
- Check `/docs` endpoint for API explorer
- Add sample documents to `sample_docs/` folder
- Deploy to GCP using `cloudbuild.yaml`

Happy processing!
