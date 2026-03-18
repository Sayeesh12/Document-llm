# Document Intelligence API

A production-realistic financial document processing system that extracts structured data from invoices, bank statements, and KYC documents using Google Gemini AI.

## Overview

This system leverages Google's Gemini 1.5 Flash AI model to intelligently extract and structure data from financial documents. It provides a REST API for document processing and a minimal React frontend for testing.

## Supported Document Types

### 📄 Invoices
Extracted fields:
- Invoice number, vendor name, vendor address
- Invoice date, due date, payment terms
- Line items (description, quantity, unit price, total)
- Subtotal, tax amount, tax rate, total amount, currency

### 🏦 Bank Statements  
Extracted fields:
- Account holder, bank name, account number (masked)
- Statement period (start/end dates)
- Opening/closing balance, total credits/debits
- Recent transactions (up to 20)
- Currency

### 🆔 KYC Documents
Extracted fields:
- Document type (Aadhaar, PAN, Passport, Driving License)
- Full name, date of birth, nationality
- Document number (masked for privacy)
- Address, expiry date

**Privacy Note:** Sensitive fields like account numbers and document numbers are automatically masked to show only the last 4 digits.

## Architecture

```
┌─────────────────┐
│  React Frontend │  (Port 5173)
│  TailwindCSS    │
└────────┬────────┘
         │ HTTP + X-API-Key
         ▼
┌─────────────────┐
│  FastAPI Backend│  (Port 8000)
│  + Auth Layer   │
└────────┬────────┘
         │
         ├──────────────┬──────────────┬
         ▼              ▼              ▼
┌────────────┐  ┌──────────────┐  ┌─────────┐
│  Gemini AI │  │  PyMuPDF     │  │ SQLite  │
│  1.5 Flash │  │  + Pillow    │  │  DB     │
└────────────┘  └──────────────┘  └─────────┘
```

## Tech Stack

**Backend:**
- Python 3.11 + FastAPI
- Google Gemini 1.5 Flash API (free tier)
- PyMuPDF (fitz) for PDF processing
- Pillow for image processing
- SQLAlchemy + SQLite
- Pydantic for validation

**Frontend:**
- React 18
- TailwindCSS
- Vite

**Infrastructure:**
- Docker + docker-compose  
- GCP Cloud Build ready
- Cloud Run deployment support

## Getting Started

### Prerequisites

1. **Get a free Gemini API key:**
   - Visit: https://makersuite.google.com/app/apikey
   - Sign in with Google account
   - Create API key (free tier: 60 requests/minute)

2. **Install Docker** (recommended) or:
   - Python 3.11+
   - Node.js 20+

### Local Setup with Docker

1. **Clone and configure:**
   ```bash
   cd "document-intelligence-api"
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

2. **Start services:**
   ```bash
   docker-compose up --build
   ```

3. **Access the application:**
   - Frontend: http://localhost:5173
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Local Setup without Docker

**Backend:**
```bash
cd backend
pip install -r requirements.txt
export GEMINI_API_KEY="your-key-here"
export API_KEY="dev-api-key-12345"
uvicorn main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## API Reference

### Authentication

All endpoints require the `X-API-Key` header:
```bash
curl -H "X-API-Key: dev-api-key-12345" http://localhost:8000/health
```

### Endpoints

#### POST /documents/process
Upload and process a document.

**Request:**
- Content-Type: `multipart/form-data`
- Fields:
  - `file`: PDF, PNG, JPG, JPEG (max 10MB)
  - `document_type` (optional): `INVOICE`, `BANK_STATEMENT`, `KYC_DOCUMENT`

**Example:**
```bash
curl -X POST http://localhost:8000/documents/process   -H "X-API-Key: dev-api-key-12345"   -F "file=@invoice.pdf"   -F "document_type=INVOICE"
```

**Response:**
```json
{
  "document_id": "uuid",
  "filename": "invoice.pdf",
  "document_type": "INVOICE",
  "status": "COMPLETED",
  "extracted_data": {
    "invoice_number": "INV-2024-001",
    "vendor_name": "Acme Corp",
    "total_amount": 1500.00
  },
  "confidence_score": 0.92,
  "processing_time_ms": 2340,
  "page_count": 2
}
```

#### GET /documents
Retrieve processed documents.

**Query Parameters:**
- `limit` (default: 20): Number of documents
- `document_type` (optional): Filter by type

#### GET /documents/{document_id}
Get a specific document by ID.

#### GET /stats
Get processing statistics.

#### DELETE /documents/{document_id}
Delete a document from history.

#### GET /health
Health check endpoint (no auth required).

## Confidence Scoring

**Per-field confidence (0.0-1.0):** Gemini's certainty for each field  
**Overall confidence:** Weighted average with penalties

**Penalties:**
- Missing required field: -0.1 per field

**Required fields by type:**
- Invoice: `total_amount`, `vendor_name`, `invoice_date`
- Bank Statement: `account_holder`, `closing_balance`, `bank_name`
- KYC: `full_name`, `document_type`, `document_number`

**Interpretation:**
- 🟢 >80%: High confidence
- 🟡 60-80%: Medium - review recommended
- 🔴 <60%: Low - manual verification needed

## GCP Deployment

### Using Cloud Build

```bash
gcloud builds submit --config=cloudbuild.yaml
```

### Manual Cloud Run Deployment

```bash
docker build -t gcr.io/YOUR_PROJECT/doc-api ./backend
docker push gcr.io/YOUR_PROJECT/doc-api

gcloud run deploy document-api   --image gcr.io/YOUR_PROJECT/doc-api   --platform managed   --region us-central1   --set-env-vars "GEMINI_API_KEY=your-key"
```

## BigQuery Integration

To swap SQLite for BigQuery:

1. Install: `pip install sqlalchemy-bigquery`
2. Update `database.py`:
   ```python
   database_url = "bigquery://project/dataset"
   ```
3. Set credentials:
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="service-account.json"
   ```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `API_KEY` | Backend auth key | `dev-api-key-12345` |
| `ENV` | Environment | `development` |
| `VITE_API_URL` | Frontend API URL | `http://localhost:8000` |

## Error Handling

Common errors:
- **401**: Missing/invalid API key
- **422**: Invalid file format or size
- **503**: Gemini API unavailable

## Security

- 🔒 Automatic sensitive data masking
- 🔑 API key authentication required
- 📝 No sensitive data in logs

## Troubleshooting

**"Gemini API key not configured"**
- Set `GEMINI_API_KEY` in `.env`

**"Rate limit exceeded"**
- Free tier: 60/min, 1500/day
- Wait or upgrade

**Frontend can't connect**
- Check `VITE_API_URL` matches backend port

## License

MIT License

---

**Built with** Google Gemini AI • FastAPI • React • TailwindCSS
