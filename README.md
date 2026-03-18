# 🔍 Document Intelligence API

![Python](https://img.shields.io/badge/Python-3.11-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.104-009688?style=flat-square&logo=fastapi&logoColor=white)
![Gemini](https://img.shields.io/badge/Gemini-2.0%20Flash-4285F4?style=flat-square&logo=google&logoColor=white)
![React](https://img.shields.io/badge/React-18-61DAFB?style=flat-square&logo=react&logoColor=black)
![GCP](https://img.shields.io/badge/GCP-Cloud%20Run-4285F4?style=flat-square&logo=googlecloud&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?style=flat-square&logo=docker&logoColor=white)
![BigQuery](https://img.shields.io/badge/GCP-BigQuery-4285F4?style=flat-square&logo=googlecloud&logoColor=white)

A **production-realistic financial document processing API** powered by Google Gemini 2.0 Flash — extracting structured data from invoices, bank statements, and KYC documents with per-field confidence scoring and automatic sensitive data masking.

> Built to demonstrate AI/LLM integration, prompt engineering, and financial document intelligence in a real-world banking context — the kind of document automation JPMorgan Chase runs at scale with their COiN platform.

---

## 🎯 What It Does

Upload any financial document and the system autonomously:

1. **Detects** document type (Invoice / Bank Statement / KYC) — auto or manual
2. **Extracts** text and renders page images via PyMuPDF at 200 DPI
3. **Sends** both text + images to Gemini 2.0 Flash with a precision-engineered prompt
4. **Parses** structured JSON response with per-field confidence scores
5. **Masks** sensitive fields (account numbers → last 4 digits, document IDs → XXXX-1234)
6. **Persists** results to SQLite (swappable to BigQuery in prod)
7. **Returns** fully structured ExtractionResult in < 10 seconds

---

## 📄 Supported Document Types

### 🧾 Invoice
| Field | Example |
|---|---|
| Vendor Name | Acme Corp Pvt Ltd |
| Invoice Number | INV-2024-001 |
| Invoice Date | 2024-01-15 |
| Line Items | [ { description, quantity, unit_price, total } ] |
| Subtotal / Tax / Total | ₹45,000 / ₹8,100 / ₹53,100 |
| Currency | ₹ / $ / € |
| Payment Terms | Net 30 |

### 🏦 Bank Statement
| Field | Example |
|---|---|
| Account Holder | Sayeesh Mahale |
| Account Number | 🔒 XXXX-1234 (masked) |
| Bank Name | HDFC Bank |
| Statement Period | Jan 1 – Jan 31, 2024 |
| Opening / Closing Balance | ₹1,20,000 / ₹95,430 |
| Transactions | [ { date, description, credit, debit, balance } ] |

### 🪪 KYC Document
| Field | Example |
|---|---|
| Document Type | Aadhaar / PAN / Passport / Driving License |
| Full Name | Sayeesh Mahale |
| Date of Birth | 2005-03-15 |
| Document Number | 🔒 XXXX-XXXX-1234 (masked) |
| Address | Bengaluru, Karnataka |
| Expiry Date | 2034-03-14 |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  DOCUMENT INTELLIGENCE PIPELINE              │
│                                                             │
│  Upload           Extractor          Gemini 2.0 Flash       │
│  ────────        ──────────         ────────────────        │
│  PDF/PNG/JPG  →  PyMuPDF +       →  Prompt Engineering  →  │
│  via API         Pillow              Structured JSON         │
│  (max 10MB)      200 DPI render      per-field confidence    │
│                                             │               │
│                                             ▼               │
│                                    Confidence Scoring        │
│                                    + Sensitive Masking       │
│                                             │               │
│                                             ▼               │
│                                       SQLite DB             │
│                                      (BigQuery              │
│                                       in prod)              │
└─────────────────────────────────────────────────────────────┘
                                             │
                                             ▼
┌─────────────────────────────────────────────────────────────┐
│                     REACT DASHBOARD                          │
│                                                             │
│  [ Drag & Drop Upload ]    [ Extracted Data + Confidence ]  │
│                                                             │
│  [ Document History — last 10 processed ]                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 🤖 How the AI Works

### Prompt Engineering
Each document type has a precision-engineered prompt that instructs Gemini to:
- Respond **only in valid JSON** — no markdown, no preamble
- Set `null` for fields it cannot find (never hallucinate)
- Include a `confidence` object with per-field scores (0.0–1.0)
- Apply domain-specific rules (e.g. mask account numbers, validate amounts)

### Confidence Scoring
```
overall_confidence = avg(per_field_scores)
                   - 0.1 per missing required field

Required fields:
  Invoice        → total_amount, vendor_name, invoice_date
  Bank Statement → account_holder, closing_balance, bank_name
  KYC            → full_name, document_type, document_number
```

| Score | Meaning | Badge Color |
|---|---|---|
| > 80% | High confidence | 🟢 Green |
| 60–80% | Medium confidence | 🟡 Yellow |
| < 60% | Low confidence | 🔴 Red |

### Retry Logic
Gemini API calls use exponential backoff (3 attempts: 1s → 2s → 4s) on rate limit errors — production-grade resilience.

---

## 🚀 Local Setup

### Prerequisites
- Docker Desktop
- Gemini API key (free — get it at [aistudio.google.com/apikey](https://aistudio.google.com/apikey))

### Step 1 — Clone and configure
```bash
git clone https://github.com/Sayeesh12/Document-llm.git
cd Document-llm
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### Step 2 — Run
```bash
docker-compose up --build
```

| Service | URL |
|---|---|
| React Dashboard | http://localhost:5173 |
| FastAPI Backend | http://localhost:8000 |
| API Docs (Swagger) | http://localhost:8000/docs |

---

## 📡 API Reference

All endpoints require header: `X-API-Key: dev-api-key-12345`

### Process a document
```bash
curl -X POST http://localhost:8000/documents/process \
  -H "X-API-Key: dev-api-key-12345" \
  -F "file=@invoice.pdf" \
  -F "document_type=INVOICE"
```

### Get processing history
```bash
curl http://localhost:8000/documents \
  -H "X-API-Key: dev-api-key-12345"
```

### Get statistics
```bash
curl http://localhost:8000/stats \
  -H "X-API-Key: dev-api-key-12345"
```

| Method | Endpoint | Description |
|---|---|---|
| POST | `/documents/process` | Upload and process a document |
| GET | `/documents` | List processed documents |
| GET | `/documents/{id}` | Get full result by ID |
| GET | `/stats` | Processing statistics |
| GET | `/health` | Service health + Gemini status |
| DELETE | `/documents/{id}` | Delete a document |

---

## ☁️ GCP Deployment

### Prerequisites
```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable cloudbuild.googleapis.com run.googleapis.com containerregistry.googleapis.com
```

### Step 1 — Build and push via Cloud Build
```bash
gcloud builds submit --config cloudbuild.yaml .
```

### Step 2 — Deploy backend
```bash
gcloud run deploy document-intelligence-backend \
  --image gcr.io/YOUR_PROJECT_ID/doc-intelligence-backend:latest \
  --platform managed \
  --region asia-south1 \
  --set-env-vars API_KEY=your-secret-key,GEMINI_API_KEY=your-gemini-key,ENV=production \
  --allow-unauthenticated
```

### Step 3 — Deploy frontend
```bash
gcloud run deploy document-intelligence-frontend \
  --image gcr.io/YOUR_PROJECT_ID/doc-intelligence-frontend:latest \
  --platform managed \
  --region asia-south1 \
  --set-env-vars VITE_API_URL=https://document-intelligence-backend-xxxx.run.app \
  --allow-unauthenticated
```

### Step 4 — Swap SQLite → BigQuery (2 changes)
```python
# 1. In database.py, replace SQLAlchemy session with:
from google.cloud import bigquery
client = bigquery.Client()

# 2. Replace save() method with:
client.insert_rows_json("YOUR_PROJECT.dataset.documents", [result])
```

---

## 🗂️ Project Structure

```
Document-llm/
├── backend/
│   ├── main.py          # FastAPI app, endpoints, lifespan
│   ├── processor.py     # Gemini AI document processing
│   ├── extractor.py     # PDF/image extraction (PyMuPDF + Pillow)
│   ├── database.py      # Repository layer (SQLite → BigQuery)
│   ├── schemas.py       # Pydantic models
│   ├── prompts.py       # Engineered Gemini prompts
│   ├── auth.py          # API key middleware
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── UploadForm.jsx        # Drag and drop upload
│   │   │   ├── ResultCard.jsx        # Extracted data display
│   │   │   ├── ConfidenceBar.jsx     # Confidence score bar
│   │   │   ├── DocumentHistory.jsx   # Past processed docs
│   │   │   └── StatusBadge.jsx       # Processing status
│   │   └── App.jsx
│   └── package.json
├── docker-compose.yml
├── cloudbuild.yaml
├── .env.example
└── README.md
```

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.11, FastAPI, SQLAlchemy |
| AI Model | Google Gemini 2.0 Flash |
| File Processing | PyMuPDF (PDF → images at 200 DPI), Pillow |
| Frontend | React 18, TailwindCSS |
| Database | SQLite local / BigQuery in prod |
| Infra | Docker, docker-compose |
| Cloud | GCP Cloud Run, Container Registry, Cloud Build |
| Auth | API Key middleware |

---

## 👤 Author

**Sayeesh Mahale**
[LinkedIn](http://www.linkedin.com/in/sayeesh-mahale-55788b2b9) • [GitHub](https://github.com/Sayeesh12)
