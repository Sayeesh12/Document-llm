"""
Prompts for Gemini AI document processing.
Each prompt is carefully engineered to extract structured data
and provide confidence scores for each field.
"""

from schemas import DocumentType


# ============================================================================
# INVOICE PROMPT
# ============================================================================

INVOICE_PROMPT = """You are an expert financial document analyzer specialized in invoice extraction.

Analyze the provided invoice image and/or text and extract ALL structured data.

IMPORTANT REQUIREMENTS:
1. Respond ONLY with valid JSON - no markdown, no extra text
2. Use EXACTLY these field names (case-sensitive)
3. Set fields to null if you cannot reliably find them
4. Include a "confidence" object with per-field confidence scores (0.0-1.0)
5. Extract ALL line items even if the table is complex or uses non-standard formatting
6. Identify currency from symbols (₹ for INR, $ for USD, € for EUR, etc.)
7. If amounts don't add up correctly (subtotal + tax ≠ total), reduce confidence for those fields
8. For line items, extract description, quantity, unit_price, and total if available

Return JSON in this exact structure:
{
  "invoice_number": "string or null",
  "vendor_name": "string or null",
  "vendor_address": "string or null",
  "invoice_date": "YYYY-MM-DD or null",
  "due_date": "YYYY-MM-DD or null",
  "line_items": [
    {
      "description": "string or null",
      "quantity": "number or null",
      "unit_price": "number or null",
      "total": "number or null"
    }
  ],
  "subtotal": "number or null",
  "tax_amount": "number or null",
  "tax_rate": "number or null (as percentage, e.g., 18 for 18%)",
  "total_amount": "number or null",
  "currency": "string (ISO code like USD, INR, EUR) or null",
  "payment_terms": "string or null",
  "confidence": {
    "invoice_number": 0.0-1.0,
    "vendor_name": 0.0-1.0,
    "vendor_address": 0.0-1.0,
    "invoice_date": 0.0-1.0,
    "due_date": 0.0-1.0,
    "line_items": 0.0-1.0,
    "subtotal": 0.0-1.0,
    "tax_amount": 0.0-1.0,
    "tax_rate": 0.0-1.0,
    "total_amount": 0.0-1.0,
    "currency": 0.0-1.0,
    "payment_terms": 0.0-1.0
  }
}

Analyze the document now."""


# ============================================================================
# BANK STATEMENT PROMPT
# ============================================================================

BANK_STATEMENT_PROMPT = """You are an expert financial document analyzer specialized in bank statement extraction.

Analyze the provided bank statement image and/or text and extract ALL structured data.

IMPORTANT REQUIREMENTS:
1. Respond ONLY with valid JSON - no markdown, no extra text
2. Use EXACTLY these field names (case-sensitive)
3. Set fields to null if you cannot reliably find them
4. Include a "confidence" object with per-field confidence scores (0.0-1.0)
5. MASK account number to show ONLY last 4 digits (format: XXXX-XXXX-1234)
6. Extract up to 20 most recent transactions with date, description, credit, debit, balance
7. If opening_balance + total_credits - total_debits ≠ closing_balance, flag inconsistency by reducing confidence
8. Identify currency from statement (₹ for INR, $ for USD, etc.)

Return JSON in this exact structure:
{
  "account_holder": "string or null",
  "account_number": "XXXX-XXXX-1234 format or null",
  "bank_name": "string or null",
  "statement_period_start": "YYYY-MM-DD or null",
  "statement_period_end": "YYYY-MM-DD or null",
  "opening_balance": "number or null",
  "closing_balance": "number or null",
  "total_credits": "number or null",
  "total_debits": "number or null",
  "transactions": [
    {
      "date": "YYYY-MM-DD or null",
      "description": "string or null",
      "credit": "number or null",
      "debit": "number or null",
      "balance": "number or null"
    }
  ],
  "currency": "string (ISO code like USD, INR, EUR) or null",
  "confidence": {
    "account_holder": 0.0-1.0,
    "account_number": 0.0-1.0,
    "bank_name": 0.0-1.0,
    "statement_period_start": 0.0-1.0,
    "statement_period_end": 0.0-1.0,
    "opening_balance": 0.0-1.0,
    "closing_balance": 0.0-1.0,
    "total_credits": 0.0-1.0,
    "total_debits": 0.0-1.0,
    "transactions": 0.0-1.0,
    "currency": 0.0-1.0
  }
}

Analyze the document now."""


# ============================================================================
# KYC DOCUMENT PROMPT
# ============================================================================

KYC_DOCUMENT_PROMPT = """You are an expert document analyzer specialized in KYC (Know Your Customer) document extraction.

Analyze the provided KYC document image and/or text (Aadhaar, PAN, Passport, Driver's License, etc.)
and extract ALL structured data.

IMPORTANT REQUIREMENTS:
1. Respond ONLY with valid JSON - no markdown, no extra text
2. Use EXACTLY these field names (case-sensitive)
3. Set fields to null if you cannot reliably find them
4. Include a "confidence" object with per-field confidence scores (0.0-1.0)
5. PRIVACY: Mask document_number to show ONLY last 4 digits (format: XXXX-XXXX-1234)
6. DO NOT extract full document numbers - only show masked version
7. Extract document type from the document itself (e.g., "Aadhaar", "PAN", "Passport", "Driver's License")
8. Extract full_name, date_of_birth (YYYY-MM-DD format), address if visible, expiry_date, nationality

Return JSON in this exact structure:
{
  "document_type": "string (e.g., 'Aadhaar', 'PAN', 'Passport', 'Driver's License') or null",
  "full_name": "string or null",
  "date_of_birth": "YYYY-MM-DD or null",
  "document_number": "XXXX-XXXX-1234 format (masked) or null",
  "address": "string or null",
  "expiry_date": "YYYY-MM-DD or null",
  "nationality": "string or null",
  "confidence": {
    "document_type": 0.0-1.0,
    "full_name": 0.0-1.0,
    "date_of_birth": 0.0-1.0,
    "document_number": 0.0-1.0,
    "address": 0.0-1.0,
    "expiry_date": 0.0-1.0,
    "nationality": 0.0-1.0
  }
}

Analyze the document now."""


# ============================================================================
# PROMPT SELECTOR
# ============================================================================

def get_prompt_for_document_type(doc_type: DocumentType) -> str:
    """
    Select the appropriate prompt for a given document type.
    
    Args:
        doc_type: The DocumentType enum value
        
    Returns:
        The corresponding prompt string
    """
    prompts_map = {
        DocumentType.INVOICE: INVOICE_PROMPT,
        DocumentType.BANK_STATEMENT: BANK_STATEMENT_PROMPT,
        DocumentType.KYC_DOCUMENT: KYC_DOCUMENT_PROMPT,
    }
    return prompts_map.get(doc_type, INVOICE_PROMPT)
