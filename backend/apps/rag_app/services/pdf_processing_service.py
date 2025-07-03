"""
PDF Processing Service for RAG app.
Service for processing PDF documents and creating embeddings.
"""
import hashlib
import os
from typing import List, Dict, Any, Tuple
import logging

logger = logging.getLogger(__name__)

# Import PDF processing libraries (lightweight version)
try:
    import PyPDF2
    from langchain.text_splitter import RecursiveCharacterTextSplitter
    from langchain_core.documents import Document
    PDF_PROCESSING_AVAILABLE = True
except ImportError:
    PDF_PROCESSING_AVAILABLE = False
    logger.warning("PDF processing libraries not available. Install langchain and PyPDF2.")
    # Define a minimal Document class for fallback
    class Document:
        def __init__(self, page_content: str, metadata: dict = None):
            self.page_content = page_content
            self.metadata = metadata or {}


class PDFProcessingService:
    """
    Service for processing PDF documents and creating embeddings.
    """

    # Text splitting configuration
    CHUNK_SIZE = 1000
    CHUNK_OVERLAP = 200

    @classmethod
    def extract_text_from_pdf(cls, file_path: str) -> Tuple[str, int]:
        """
        Extract text from PDF file using multiple methods for robustness.

        Args:
            file_path: Path to the PDF file

        Returns:
            Tuple of (extracted_text, page_count)

        Raises:
            Exception: If PDF processing fails
        """
        if not PDF_PROCESSING_AVAILABLE:
            raise Exception("PDF processing libraries not installed")

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        try:
            # Use PyPDF2 for text extraction
            return cls._extract_with_pypdf2(file_path)
        except Exception as e:
            logger.error(f"PDF extraction failed for {file_path}: {e}")
            raise Exception(f"Failed to extract text from PDF: {e}")

    @classmethod
    def _extract_with_pypdf2(cls, file_path: str) -> Tuple[str, int]:
        """Extract text using PyPDF2 (primary method)."""
        text_parts = []

        with open(file_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            page_count = len(pdf_reader.pages)

            for page in pdf_reader.pages:
                text = page.extract_text()
                if text.strip():
                    text_parts.append(text)

        return "\n\n".join(text_parts), page_count

    @classmethod
    def split_text_into_chunks(cls, text: str, metadata: Dict[str, Any] = None) -> List[Document]:
        """
        Split text into chunks using LangChain's text splitter.

        Args:
            text: Text to split
            metadata: Optional metadata to attach to each chunk

        Returns:
            List of LangChain Document objects
        """
        if not PDF_PROCESSING_AVAILABLE:
            raise Exception("LangChain text splitter not available")

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=cls.CHUNK_SIZE,
            chunk_overlap=cls.CHUNK_OVERLAP,
            length_function=len,
            separators=["\n\n", "\n", ". ", " ", ""]
        )

        chunks = text_splitter.split_text(text)
        documents = []

        for i, chunk in enumerate(chunks):
            doc_metadata = {
                "chunk_index": i,
                "chunk_size": len(chunk),
                **(metadata or {})
            }
            documents.append(Document(page_content=chunk, metadata=doc_metadata))

        return documents

    @classmethod
    def generate_content_hash(cls, content: str) -> str:
        """Generate SHA-256 hash of content for deduplication."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()

    @classmethod
    def estimate_processing_time(cls, file_path: str) -> float:
        """
        Estimate processing time based on file size.

        Args:
            file_path: Path to the PDF file

        Returns:
            Estimated processing time in seconds
        """
        try:
            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
            # Rough estimate: 2-5 seconds per MB depending on complexity
            return file_size_mb * 3.5
        except Exception:
            return 30.0  # Default estimate

    @classmethod
    def validate_pdf_file(cls, file_path: str) -> Dict[str, Any]:
        """
        Validate PDF file and return basic information.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary with validation results and file info
        """
        try:
            if not os.path.exists(file_path):
                return {
                    "valid": False,
                    "error": "File not found",
                    "file_size_mb": 0,
                    "page_count": 0
                }

            file_size_mb = os.path.getsize(file_path) / (1024 * 1024)

            if not PDF_PROCESSING_AVAILABLE:
                return {
                    "valid": False,
                    "error": "PDF processing libraries not available",
                    "file_size_mb": file_size_mb,
                    "page_count": 0
                }

            # Try to open and read basic info
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                page_count = len(pdf_reader.pages)

                return {
                    "valid": True,
                    "file_size_mb": round(file_size_mb, 2),
                    "page_count": page_count,
                    "estimated_processing_time": cls.estimate_processing_time(file_path)
                }

        except Exception as e:
            return {
                "valid": False,
                "error": str(e),
                "file_size_mb": 0,
                "page_count": 0
            }

    @classmethod
    def get_processing_capabilities(cls) -> Dict[str, Any]:
        """
        Get information about PDF processing capabilities.

        Returns:
            Dictionary with capability information
        """
        return {
            "pdf_processing_available": PDF_PROCESSING_AVAILABLE,
            "chunk_size": cls.CHUNK_SIZE,
            "chunk_overlap": cls.CHUNK_OVERLAP,
            "supported_formats": ["pdf"],
            "text_splitter": "RecursiveCharacterTextSplitter" if PDF_PROCESSING_AVAILABLE else None,
            "pdf_reader": "PyPDF2" if PDF_PROCESSING_AVAILABLE else None
        }
