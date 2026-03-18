"""
FastAPI application for Document Intelligence API.
Exposes endpoints for document processing, retrieval, and statistics.
"""

import os
import logging
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from schemas import (
    DocumentType,
    ExtractionResult,
    HealthResponse,
    StatsResponse,
    ErrorResponse,
)
from processor import GeminiProcessor
from database import DocumentRepository
from extractor import FileExtractor
from auth_middleware import APIKeyMiddleware


# ============================================================================
# LOGGING SETUP
# ============================================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# GLOBAL STATE
# ============================================================================

processor: GeminiProcessor = None
db: DocumentRepository = None


# ============================================================================
# LIFESPAN CONTEXT
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan management.
    Initializes resources on startup, cleans up on shutdown.
    """
    global processor, db
    
    # Startup
    logger.info("=== Document Intelligence API Starting ===")
    
    # Initialize Gemini processor
    processor = GeminiProcessor()
    logger.info(f"Gemini configured: {processor.model is not None}")
    
    # Initialize database
    db = DocumentRepository()
    logger.info("Database initialized")
    
    yield
    
    # Shutdown
    logger.info("=== Document Intelligence API Shutting Down ===")


# ============================================================================
# APPLICATION FACTORY
# ============================================================================

app = FastAPI(
    title="Document Intelligence API",
    description="Extract structured data from financial documents using Gemini AI",
    version="1.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add API key middleware
app.add_middleware(APIKeyMiddleware)


# ============================================================================
# ENDPOINTS - HEALTH & STATUS
# ============================================================================

@app.get(
    "/health",
    response_model=HealthResponse,
    tags=["Status"],
    summary="Health check endpoint",
)
async def health_check() -> HealthResponse:
    """
    Check API health and configuration status.
    Does not require API key authentication.
    """
    stats = db.get_stats() if db else {}
    return HealthResponse(
        status="healthy" if (processor and processor.model) else "configured",
        gemini_configured=processor.model is not None if processor else False,
        total_processed=stats.get("total_processed", 0),
    )


@app.get(
    "/stats",
    response_model=StatsResponse,
    tags=["Statistics"],
    summary="Get processing statistics",
)
async def get_stats() -> StatsResponse:
    """
    Get aggregate statistics about processed documents.
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    stats = db.get_stats()
    return StatsResponse(**stats)


# ============================================================================
# ENDPOINTS - DOCUMENT PROCESSING
# ============================================================================

@app.post(
    "/documents/process",
    response_model=ExtractionResult,
    tags=["Documents"],
    summary="Process a financial document",
)
async def process_document(
    file: UploadFile = File(..., description="PDF, PNG, or JPG file"),
    document_type: Optional[str] = Form(None, description="Optional: INVOICE, BANK_STATEMENT, or KYC_DOCUMENT"),
) -> ExtractionResult:
    """
    Upload and process a financial document.
    
    Supported formats:
    - PDF (.pdf)
    - PNG (.png)
    - JPEG (.jpg, .jpeg)
    
    Max file size: 10MB
    
    Query parameters:
    - document_type: Optional type override. If not provided, auto-detected.
    """
    if not processor or not processor.model:
        raise HTTPException(
            status_code=503,
            detail="Gemini API not configured. Set GEMINI_API_KEY environment variable.",
        )
    
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    # Validate content type
    valid_types = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
    if file.content_type not in valid_types:
        raise HTTPException(
            status_code=422,
            detail=f"Unsupported file type: {file.content_type}. Supported: PDF, PNG, JPG, JPEG",
        )
    
    try:
        # Read file
        file_bytes = await file.read()
        
        # Validate file size and format
        is_valid, error_msg = FileExtractor.validate_file(file_bytes, file.content_type)
        if not is_valid:
            raise HTTPException(status_code=422, detail=error_msg)
        
        # Parse optional document type
        doc_type = None
        if document_type:
            try:
                doc_type = DocumentType[document_type.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=422,
                    detail=f"Invalid document_type: {document_type}. Must be INVOICE, BANK_STATEMENT, or KYC_DOCUMENT",
                )
        
        # Process document
        logger.info(f"Processing document: {file.filename}")
        result = await processor.process_document(
            file_bytes=file_bytes,
            filename=file.filename,
            content_type=file.content_type,
            document_type=doc_type,
        )
        
        # Save to database
        db.save(result)
        
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing document: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error processing document: {str(e)}",
        )


# ============================================================================
# ENDPOINTS - DOCUMENT RETRIEVAL
# ============================================================================

@app.get(
    "/documents",
    tags=["Documents"],
    summary="List processed documents",
)
async def list_documents(
    limit: int = 20,
    document_type: Optional[str] = None,
) -> dict:
    """
    Retrieve list of previously processed documents.
    
    Query parameters:
    - limit: Maximum number of documents to return (default: 20)
    - document_type: Optional filter by document type
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        docs = db.get_all(limit=limit, document_type=document_type)
        return {
            "total": len(docs),
            "documents": docs,
        }
    except Exception as e:
        logger.error(f"Error retrieving documents: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving documents")


@app.get(
    "/documents/{document_id}",
    tags=["Documents"],
    summary="Get document details",
)
async def get_document(document_id: str) -> dict:
    """
    Retrieve detailed extraction result for a specific document.
    
    Path parameters:
    - document_id: UUID of the document
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        doc = db.get_by_id(document_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Error retrieving document")


@app.delete(
    "/documents/{document_id}",
    tags=["Documents"],
    summary="Delete a document",
)
async def delete_document(document_id: str) -> dict:
    """
    Delete a document from the processing history.
    
    Path parameters:
    - document_id: UUID of the document to delete
    """
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")
    
    try:
        deleted = db.delete(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        return {"message": f"Document {document_id} deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting document {document_id}: {e}")
        raise HTTPException(status_code=500, detail="Error deleting document")


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTPException with structured response."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "status_code": exc.status_code,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions."""
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error",
            "status_code": 500,
        },
    )


# ============================================================================
# ROOT ENDPOINT
# ============================================================================

@app.get("/", tags=["Root"])
async def root():
    """API information endpoint."""
    return {
        "name": "Document Intelligence API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
