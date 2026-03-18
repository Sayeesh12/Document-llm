"""
File extraction module for PDFs and images.
Handles PDF-to-image conversion, text extraction, and image processing.
"""

import io
import re
import logging
import base64
from typing import Optional, List, Dict, Any
from PIL import Image
from schemas import DocumentType

try:
    import fitz  # PyMuPDF
except ImportError:
    fitz = None


logger = logging.getLogger(__name__)


class FileExtractor:
    """Extracts text and images from PDF and image files."""
    
    MAX_IMAGE_SIZE_MB = 4
    DPI = 200  # Resolution for PDF rendering
    
    @staticmethod
    def extract_from_pdf(file_bytes: bytes) -> Dict[str, Any]:
        """
        Extract text and images from a PDF file.
        
        Args:
            file_bytes: PDF file content as bytes
            
        Returns:
            Dictionary with keys:
            - text: concatenated text from all pages
            - images: list of base64 encoded page images
            - page_count: number of pages
            - metadata: PDF metadata dictionary
        """
        if not fitz:
            raise RuntimeError("PyMuPDF (fitz) not installed. Required for PDF processing.")
        
        try:
            pdf_doc = fitz.open(stream=file_bytes, filetype="pdf")
            page_count = len(pdf_doc)
            text_parts = []
            images = []
            metadata = {}
            
            # Extract metadata
            try:
                metadata = pdf_doc.metadata or {}
            except Exception as e:
                logger.warning(f"Failed to extract PDF metadata: {e}")
            
            # Process each page
            for page_num in range(page_count):
                page = pdf_doc[page_num]
                
                # Extract text
                try:
                    text = page.get_text()
                    if text.strip():
                        text_parts.append(f"--- Page {page_num + 1} ---\n{text}")
                except Exception as e:
                    logger.warning(f"Failed to extract text from page {page_num + 1}: {e}")
                
                # Render page as image
                try:
                    pix = page.get_pixmap(
                        matrix=fitz.Matrix(FileExtractor.DPI / 72, FileExtractor.DPI / 72),
                        alpha=False
                    )
                    img_bytes = pix.tobytes("ppm")
                    img_b64 = base64.b64encode(img_bytes).decode("utf-8")
                    images.append(img_b64)
                except Exception as e:
                    logger.warning(f"Failed to render page {page_num + 1} as image: {e}")
            
            pdf_doc.close()
            
            return {
                "text": "\n".join(text_parts),
                "images": images,
                "page_count": page_count,
                "metadata": metadata,
            }
        
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            raise
    
    @staticmethod
    def extract_from_image(file_bytes: bytes, content_type: str) -> Dict[str, Any]:
        """
        Extract image data and encode to base64.
        
        Args:
            file_bytes: Image file content as bytes
            content_type: MIME type (e.g., "image/png", "image/jpeg")
            
        Returns:
            Dictionary with keys:
            - image: base64 encoded image
            - format: image format (PNG, JPEG, etc.)
            - dimensions: (width, height)
            - file_size_bytes: original file size
        """
        try:
            # Open image using PIL
            img = Image.open(io.BytesIO(file_bytes))
            
            # Validate image
            if img.mode not in ("RGB", "RGBA", "L", "P"):
                img = img.convert("RGB")
            
            # Resize if too large (> 4MB)
            file_size_mb = len(file_bytes) / (1024 * 1024)
            
            if file_size_mb > FileExtractor.MAX_IMAGE_SIZE_MB:
                # Calculate max dimensions (rough estimate)
                max_dim = int((FileExtractor.MAX_IMAGE_SIZE_MB / file_size_mb) ** 0.5 * min(img.size))
                img.thumbnail((max_dim, max_dim), Image.Resampling.LANCZOS)
                logger.info(f"Resized image from {file_bytes.__sizeof__()} to fit {FileExtractor.MAX_IMAGE_SIZE_MB}MB limit")
            
            # Encode to base64
            img_buffer = io.BytesIO()
            fmt = img.format or "PNG"
            img.save(img_buffer, format=fmt)
            img_b64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")
            
            return {
                "image": img_b64,
                "format": fmt,
                "dimensions": img.size,
                "file_size_bytes": len(file_bytes),
            }
        
        except Exception as e:
            logger.error(f"Image extraction failed: {e}")
            raise
    
    @staticmethod
    def detect_document_type(text: str, filename: str) -> DocumentType:
        """
        Auto-detect document type from filename and text content.
        
        Args:
            text: Extracted text from document
            filename: Original filename
            
        Returns:
            Detected DocumentType
        """
        text_lower = text.lower()
        filename_lower = filename.lower()
        
        # Check filename first
        invoice_keywords = ["invoice", "bill", "billing", "receipt"]
        bank_keywords = ["statement", "account", "bank"]
        kyc_keywords = ["aadhaar", "pan", "passport", "driving", "license", "kyc", "aadhar"]
        
        if any(kw in filename_lower for kw in invoice_keywords):
            return DocumentType.INVOICE
        
        if any(kw in filename_lower for kw in bank_keywords):
            return DocumentType.BANK_STATEMENT
        
        if any(kw in filename_lower for kw in kyc_keywords):
            return DocumentType.KYC_DOCUMENT
        
        # Check text content
        if any(kw in text_lower for kw in ["invoice", "bill no", "billed to", "invoice date", "bill date"]):
            return DocumentType.INVOICE
        
        if any(kw in text_lower for kw in ["account number", "account bank", "balance", "statement of", "transactions"]):
            return DocumentType.BANK_STATEMENT
        
        if any(kw in text_lower for kw in ["aadhaar", "pan", "passport", "aadhar", "date of birth", "driving license"]):
            return DocumentType.KYC_DOCUMENT
        
        # Default to invoice
        logger.info(f"Document type not detected from '{filename}', defaulting to INVOICE")
        return DocumentType.INVOICE
    
    @staticmethod
    def validate_file(file_bytes: bytes, content_type: str, max_size_mb: int = 10) -> tuple[bool, Optional[str]]:
        """
        Validate file format and size.
        
        Args:
            file_bytes: File content
            content_type: MIME type
            max_size_mb: Maximum allowed file size in MB
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check size
        file_size_mb = len(file_bytes) / (1024 * 1024)
        if file_size_mb > max_size_mb:
            return False, f"File size {file_size_mb:.1f}MB exceeds limit of {max_size_mb}MB"
        
        # Check format
        valid_formats = ["application/pdf", "image/png", "image/jpeg", "image/jpg"]
        if content_type not in valid_formats:
            return False, f"Unsupported file format: {content_type}. Supported: PDF, PNG, JPG, JPEG"
        
        return True, None
