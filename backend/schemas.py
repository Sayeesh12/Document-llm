"""
Pydantic schemas for Document Intelligence API.
Defines all data models for extraction, processing, and storage.
"""

from enum import Enum
from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field


# ============================================================================
# ENUMS
# ============================================================================

class DocumentType(str, Enum):
    """Supported document types for processing."""
    INVOICE = "INVOICE"
    BANK_STATEMENT = "BANK_STATEMENT"
    KYC_DOCUMENT = "KYC_DOCUMENT"


class ProcessingStatus(str, Enum):
    """Processing status of a document."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# ============================================================================
# LINE ITEM AND TRANSACTION MODELS
# ============================================================================

class LineItem(BaseModel):
    """Line item in an invoice."""
    description: Optional[str] = None
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    total: Optional[float] = None


class Transaction(BaseModel):
    """Transaction in a bank statement."""
    date: Optional[str] = None
    description: Optional[str] = None
    credit: Optional[float] = None
    debit: Optional[float] = None
    balance: Optional[float] = None


# ============================================================================
# DOCUMENT-SPECIFIC DATA MODELS
# ============================================================================

class InvoiceData(BaseModel):
    """Extracted data from an invoice."""
    invoice_number: Optional[str] = None
    vendor_name: Optional[str] = None
    vendor_address: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    subtotal: Optional[float] = None
    tax_amount: Optional[float] = None
    tax_rate: Optional[float] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    payment_terms: Optional[str] = None


class BankStatementData(BaseModel):
    """Extracted data from a bank statement."""
    account_holder: Optional[str] = None
    account_number: Optional[str] = None  # Last 4 digits only
    bank_name: Optional[str] = None
    statement_period_start: Optional[str] = None
    statement_period_end: Optional[str] = None
    opening_balance: Optional[float] = None
    closing_balance: Optional[float] = None
    total_credits: Optional[float] = None
    total_debits: Optional[float] = None
    transactions: List[Dict[str, Any]] = Field(default_factory=list)
    currency: Optional[str] = None


class KYCDocumentData(BaseModel):
    """Extracted data from a KYC document."""
    document_type: Optional[str] = None  # Aadhaar/PAN/Passport/DL
    full_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    document_number: Optional[str] = None  # Masked - last 4 digits only
    address: Optional[str] = None
    expiry_date: Optional[str] = None
    nationality: Optional[str] = None


# ============================================================================
# EXTRACTION RESULT MODEL
# ============================================================================

class ExtractionResult(BaseModel):
    """Complete extraction result for a processed document."""
    document_id: str
    filename: str
    document_type: DocumentType
    status: ProcessingStatus
    extracted_data: Dict[str, Any]  # One of: InvoiceData, BankStatementData, KYCDocumentData
    confidence_score: float = Field(ge=0.0, le=1.0)
    confidence_breakdown: Dict[str, float]
    processing_time_ms: int
    page_count: int
    file_size_bytes: int
    created_at: str  # ISO format IST
    error_message: Optional[str] = None

    class Config:
        use_enum_values = False


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    gemini_configured: bool
    total_processed: int


class StatsResponse(BaseModel):
    """Statistics response."""
    total_processed: int
    by_type: Dict[str, int]
    avg_confidence: float
    avg_processing_time_ms: float
    success_rate: float


class ErrorResponse(BaseModel):
    """Error response."""
    detail: str
    error_code: Optional[str] = None
