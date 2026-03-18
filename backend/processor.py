"""
Gemini AI processor for document extraction and analysis.
Handles API calls to Gemini 2.0 Flash and JSON response parsing.
"""

import json
import logging
import time
import os
import re
from typing import Optional, Dict, Any
from datetime import datetime, timezone
import asyncio

try:
    import google.generativeai as genai
except ImportError:
    genai = None

from schemas import DocumentType, ProcessingStatus, ExtractionResult
from prompts import get_prompt_for_document_type
from extractor import FileExtractor


logger = logging.getLogger(__name__)


class GeminiProcessor:
    """Processes documents using Gemini 2.0 Flash API."""
    
    MAX_RETRIES = 3
    RETRY_DELAY_BASE = 1  # Starting delay in seconds
    
    def __init__(self):
        """Initialize Gemini processor and load API key."""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = "gemini-2.0-flash"
        
        if not self.api_key:
            logger.warning("GEMINI_API_KEY not set in environment. Document processing will fail.")
            self.model = None
        else:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(self.model_name)
                logger.info(f"Gemini model '{self.model_name}' initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini: {e}")
                self.model = None
    
    async def process_document(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: str,
        document_type: Optional[DocumentType] = None,
    ) -> ExtractionResult:
        """
        Process a document and extract structured data using Gemini.
        
        Args:
            file_bytes: Document file content
            filename: Original filename
            content_type: MIME type
            document_type: Optional override for document type
            
        Returns:
            ExtractionResult with extracted data and confidence scores
        """
        start_time = time.time()
        document_id = self._generate_document_id()
        
        try:
            if not self.model:
                raise RuntimeError("Gemini API not configured. Set GEMINI_API_KEY environment variable.")
            
            # Extract file (PDF or image)
            logger.info(f"Extracting content from {filename}")
            if content_type == "application/pdf":
                extracted = FileExtractor.extract_from_pdf(file_bytes)
                file_text = extracted["text"]
                images = extracted["images"]
                page_count = extracted["page_count"]
            else:
                extracted = FileExtractor.extract_from_image(file_bytes, content_type)
                file_text = ""
                images = [extracted["image"]]
                page_count = 1
            
            # Auto-detect document type if not provided
            if not document_type:
                document_type = FileExtractor.detect_document_type(file_text, filename)
                logger.info(f"Auto-detected document type: {document_type}")
            
            # Get appropriate prompt
            prompt = get_prompt_for_document_type(document_type)
            
            # Build message with text and images
            message_content = [prompt]
            
            if file_text.strip():
                message_content.append(f"\n\nExtracted text from document:\n{file_text}")
            
            # Add page images for Gemini vision
            for idx, img_b64 in enumerate(images):
                image_part = {
                    "inline_data": {
                        "mime_type": "image/png" if "png" in content_type.lower() else "image/jpeg",
                        "data": img_b64,
                    }
                }
                message_content.append(image_part)
            
            # Call Gemini API with retry logic
            logger.info(f"Sending document to Gemini for processing")
            response_text = await self._call_gemini_with_retry(message_content)
            
            # Parse JSON response (handle markdown fences)
            logger.info("Parsing Gemini response")
            extracted_data, confidence_breakdown = self._parse_gemini_response(
                response_text, document_type
            )
            
            # Calculate confidence score
            confidence_score = self.calculate_confidence(
                extracted_data, confidence_breakdown, document_type
            )
            
            # Calculate processing time
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            # Get current timestamp in IST
            now_ist = datetime.now(timezone.utc).astimezone()
            
            logger.info(f"Document {document_id} processed successfully")
            
            return ExtractionResult(
                document_id=document_id,
                filename=filename,
                document_type=document_type,
                status=ProcessingStatus.COMPLETED,
                extracted_data=extracted_data,
                confidence_score=confidence_score,
                confidence_breakdown=confidence_breakdown,
                processing_time_ms=processing_time_ms,
                page_count=page_count,
                file_size_bytes=len(file_bytes),
                created_at=now_ist.isoformat(),
                error_message=None,
            )
        
        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            processing_time_ms = int((time.time() - start_time) * 1000)
            now_ist = datetime.now(timezone.utc).astimezone()
            
            return ExtractionResult(
                document_id=document_id,
                filename=filename,
                document_type=document_type or DocumentType.INVOICE,
                status=ProcessingStatus.FAILED,
                extracted_data={},
                confidence_score=0.0,
                confidence_breakdown={},
                processing_time_ms=processing_time_ms,
                page_count=0,
                file_size_bytes=len(file_bytes),
                created_at=now_ist.isoformat(),
                error_message=str(e),
            )
    
    async def _call_gemini_with_retry(
        self, message_content: list, retry_count: int = 0
    ) -> str:
        """
        Call Gemini API with exponential backoff retry logic.
        
        Args:
            message_content: Message parts to send to Gemini
            retry_count: Current retry attempt number
            
        Returns:
            Response text from Gemini
        """
        try:
            # Run Gemini call in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, lambda: self.model.generate_content(message_content)
            )
            return response.text
        
        except Exception as e:
            error_str = str(e).lower()
            
            # Check for rate limiting
            if "rate_limit" in error_str or "429" in error_str:
                if retry_count < self.MAX_RETRIES:
                    delay = self.RETRY_DELAY_BASE * (2 ** retry_count)
                    logger.warning(f"Rate limited. Retrying in {delay}s (attempt {retry_count + 1}/{self.MAX_RETRIES})")
                    await asyncio.sleep(delay)
                    return await self._call_gemini_with_retry(message_content, retry_count + 1)
            
            logger.error(f"Gemini API error: {e}")
            raise
    
    def _parse_gemini_response(
        self, response_text: str, document_type: DocumentType
    ) -> tuple[Dict[str, Any], Dict[str, float]]:
        """
        Parse JSON response from Gemini, handling markdown fences.
        
        Args:
            response_text: Raw response from Gemini
            document_type: Type of document for validation
            
        Returns:
            Tuple of (extracted_data, confidence_breakdown)
        """
        try:
            # Remove markdown fences if present
            cleaned = response_text.strip()
            if cleaned.startswith("```json"):
                cleaned = cleaned[7:]  # Remove ```json
            elif cleaned.startswith("```"):
                cleaned = cleaned[3:]  # Remove ```
            
            if cleaned.endswith("```"):
                cleaned = cleaned[:-3]  # Remove trailing ```
            
            cleaned = cleaned.strip()
            
            # Parse JSON
            data = json.loads(cleaned)
            
            # Extract confidence breakdown
            confidence = data.pop("confidence", {})
            
            return data, confidence
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}\nResponse: {response_text}")
            return {}, {}
    
    def calculate_confidence(
        self,
        extracted_data: Dict[str, Any],
        confidence_breakdown: Dict[str, float],
        document_type: DocumentType,
    ) -> float:
        """
        Calculate overall confidence score with penalties.
        
        Args:
            extracted_data: Extracted fields
            confidence_breakdown: Per-field confidence scores
            document_type: Type of document
            
        Returns:
            Overall confidence score (0.0-1.0)
        """
        # Required fields by document type
        required_fields = {
            DocumentType.INVOICE: ["total_amount", "vendor_name", "invoice_date"],
            DocumentType.BANK_STATEMENT: ["account_holder", "closing_balance", "bank_name"],
            DocumentType.KYC_DOCUMENT: ["full_name", "document_type", "document_number"],
        }
        
        required = required_fields.get(document_type, [])
        
        # Start with average of per-field confidence scores
        if confidence_breakdown:
            scores = list(confidence_breakdown.values())
            avg_confidence = sum(scores) / len(scores) if scores else 0.5
        else:
            avg_confidence = 0.5
        
        # Apply penalties for missing required fields
        penalty = 0.0
        for field in required:
            if extracted_data.get(field) is None:
                penalty += 0.1
                logger.info(f"Missing required field '{field}' - applying confidence penalty")
        
        # Clip to [0.0, 1.0]
        final_score = max(0.0, min(1.0, avg_confidence - penalty))
        
        return final_score
    
    @staticmethod
    def _generate_document_id() -> str:
        """Generate a unique document ID."""
        import uuid
        return str(uuid.uuid4())
