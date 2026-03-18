"""
Database layer for document storage using SQLAlchemy.
Provides repository pattern for CRUD operations.
Note: BigQuery can be swapped in by modifying the engine connection string.
"""

import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from schemas import ExtractionResult, DocumentType, ProcessingStatus


logger = logging.getLogger(__name__)

Base = declarative_base()


class DocumentRecord(Base):
    """SQLAlchemy model for storing extraction results."""
    
    __tablename__ = "documents"
    
    document_id = Column(String, primary_key=True, index=True)
    filename = Column(String, index=True)
    document_type = Column(String, index=True)
    status = Column(String)
    extracted_data = Column(Text)  # JSON string
    confidence_score = Column(Float)
    confidence_breakdown = Column(Text)  # JSON string
    processing_time_ms = Column(Integer)
    page_count = Column(Integer)
    file_size_bytes = Column(Integer)
    created_at = Column(DateTime, index=True)
    error_message = Column(Text, nullable=True)


class DocumentRepository:
    """Repository for document persistence operations."""
    
    def __init__(self, database_url: str = "sqlite:///./documents.db"):
        """
        Initialize repository with database connection.
        
        Args:
            database_url: SQLAlchemy connection string
                         Default: SQLite at project root
                         For BigQuery: "bigquery://project-id/dataset"
        """
        self.engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {}
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Create tables
        Base.metadata.create_all(bind=self.engine)
        logger.info(f"Database initialized with: {database_url}")
    
    def save(self, result: ExtractionResult) -> None:
        """
        Save extraction result to database.
        
        Args:
            result: ExtractionResult object to persist
        """
        session = self.SessionLocal()
        try:
            record = DocumentRecord(
                document_id=result.document_id,
                filename=result.filename,
                document_type=result.document_type.value,
                status=result.status.value,
                extracted_data=json.dumps(result.extracted_data),
                confidence_score=result.confidence_score,
                confidence_breakdown=json.dumps(result.confidence_breakdown),
                processing_time_ms=result.processing_time_ms,
                page_count=result.page_count,
                file_size_bytes=result.file_size_bytes,
                created_at=datetime.fromisoformat(result.created_at),
                error_message=result.error_message,
            )
            session.add(record)
            session.commit()
            logger.info(f"Saved document {result.document_id} to database")
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save document {result.document_id}: {e}")
            raise
        finally:
            session.close()
    
    def get_by_id(self, document_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve document by ID.
        
        Args:
            document_id: Document UUID
            
        Returns:
            Document data as dictionary or None if not found
        """
        session = self.SessionLocal()
        try:
            record = session.query(DocumentRecord).filter(
                DocumentRecord.document_id == document_id
            ).first()
            
            if not record:
                return None
            
            return self._record_to_dict(record)
        finally:
            session.close()
    
    def get_all(
        self,
        limit: int = 20,
        document_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve all documents with optional filtering.
        
        Args:
            limit: Maximum number of documents to return
            document_type: Optional filter by document type
            
        Returns:
            List of document dictionaries ordered by creation date (newest first)
        """
        session = self.SessionLocal()
        try:
            query = session.query(DocumentRecord)
            
            if document_type:
                query = query.filter(DocumentRecord.document_type == document_type)
            
            records = query.order_by(DocumentRecord.created_at.desc()).limit(limit).all()
            
            return [self._record_to_dict(record) for record in records]
        finally:
            session.close()
    
    def delete(self, document_id: str) -> bool:
        """
        Delete a document by ID.
        
        Args:
            document_id: Document UUID to delete
            
        Returns:
            True if document was deleted, False if not found
        """
        session = self.SessionLocal()
        try:
            record = session.query(DocumentRecord).filter(
                DocumentRecord.document_id == document_id
            ).first()
            
            if not record:
                return False
            
            session.delete(record)
            session.commit()
            logger.info(f"Deleted document {document_id}")
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"Failed to delete document {document_id}: {e}")
            raise
        finally:
            session.close()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with statistics:
            - total_processed: Total number of documents
            - by_type: Count per document type
            - avg_confidence: Average confidence score
            - avg_processing_time_ms: Average processing time
            - success_rate: Percentage of completed documents
        """
        session = self.SessionLocal()
        try:
            all_records = session.query(DocumentRecord).all()
            
            if not all_records:
                return {
                    "total_processed": 0,
                    "by_type": {},
                    "avg_confidence": 0.0,
                    "avg_processing_time_ms": 0.0,
                    "success_rate": 0.0,
                }
            
            # Count by type
            by_type = {}
            for doc_type in [dt.value for dt in DocumentType]:
                count = sum(1 for r in all_records if r.document_type == doc_type)
                by_type[doc_type] = count
            
            # Calculate averages
            confidence_scores = [r.confidence_score for r in all_records if r.confidence_score]
            processing_times = [r.processing_time_ms for r in all_records]
            
            completed = sum(1 for r in all_records if r.status == ProcessingStatus.COMPLETED.value)
            success_rate = (completed / len(all_records) * 100) if all_records else 0.0
            
            return {
                "total_processed": len(all_records),
                "by_type": by_type,
                "avg_confidence": sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0.0,
                "avg_processing_time_ms": sum(processing_times) / len(processing_times) if processing_times else 0.0,
                "success_rate": success_rate,
            }
        finally:
            session.close()
    
    @staticmethod
    def _record_to_dict(record: DocumentRecord) -> Dict[str, Any]:
        """
        Convert database record to dictionary.
        
        Args:
            record: DocumentRecord instance
            
        Returns:
            Dictionary representation of record
        """
        return {
            "document_id": record.document_id,
            "filename": record.filename,
            "document_type": record.document_type,
            "status": record.status,
            "extracted_data": json.loads(record.extracted_data),
            "confidence_score": record.confidence_score,
            "confidence_breakdown": json.loads(record.confidence_breakdown),
            "processing_time_ms": record.processing_time_ms,
            "page_count": record.page_count,
            "file_size_bytes": record.file_size_bytes,
            "created_at": record.created_at.isoformat(),
            "error_message": record.error_message,
        }
