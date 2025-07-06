"""
BOE Embedding Processing Service

This service processes downloaded BOE documents, extracts text content,
creates chunks, generates OpenAI embeddings, and stores them in the database.
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from django.db import transaction
from django.utils import timezone
from tqdm import tqdm

from apps.rag_app.models import LegalDocument, DocumentChunk
from apps.rag_app.services.pdf_processing_service import PDFProcessingService
from apps.rag_app.services.embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class BOEEmbeddingService:
    """
    Service for processing legal documents and generating embeddings.

    Handles the complete pipeline from PDF processing to embedding storage:
    1. Scan all subdirectories in documents folder for PDF files
    2. Extract text from PDF files (BOE, laws, and other legal documents)
    3. Split text into chunks
    4. Generate embeddings using OpenAI
    5. Store in database with proper metadata
    """

    def __init__(self, documents_dir: Optional[str] = None):
        """
        Initialize the legal document embedding service.

        Args:
            documents_dir: Root directory containing legal documents. Defaults to backend/documents
        """
        if documents_dir is None:
            from django.conf import settings
            base_dir = getattr(settings, 'BASE_DIR', os.path.dirname(os.path.dirname(__file__)))
            # Go up from backend/ to root project directory, then to documents/
            self.documents_dir = os.path.join(base_dir, '..', 'documents')
        else:
            self.documents_dir = documents_dir

        self.pdf_service = PDFProcessingService()
        self.embedding_service = EmbeddingService()
        
    def get_unprocessed_documents(self) -> List[Dict[str, str]]:
        """
        Get list of PDF files from all subdirectories that haven't been processed yet.

        Returns:
            List of dictionaries with file information: {'filename', 'filepath', 'subdirectory', 'document_type'}
        """
        if not os.path.exists(self.documents_dir):
            logger.warning(f"Documents directory does not exist: {self.documents_dir}")
            return []

        all_files = []

        # Scan all subdirectories for PDF files
        for root, dirs, files in os.walk(self.documents_dir):
            # Get relative path from documents root
            rel_path = os.path.relpath(root, self.documents_dir)
            subdirectory = rel_path if rel_path != '.' else 'root'

            # Find all PDF files in this directory
            pdf_files = [f for f in files if f.endswith('.pdf')]

            for filename in pdf_files:
                full_path = os.path.join(root, filename)

                # Determine document type based on subdirectory
                document_type = self._determine_document_type(subdirectory, filename)

                all_files.append({
                    'filename': filename,
                    'filepath': full_path,
                    'subdirectory': subdirectory,
                    'document_type': document_type,
                    'relative_path': os.path.join(rel_path, filename) if rel_path != '.' else filename
                })

        # Check which ones are already processed by comparing full file paths
        processed_paths = set(
            LegalDocument.objects.values_list('file_path', flat=True)
        )

        unprocessed_files = [
            file_info for file_info in all_files
            if file_info['filepath'] not in processed_paths
        ]

        logger.info(f"Found {len(unprocessed_files)} unprocessed documents out of {len(all_files)} total")
        logger.info(f"Scanning directories: {set(f['subdirectory'] for f in all_files)}")

        return unprocessed_files

    def _determine_document_type(self, subdirectory: str, filename: str) -> str:
        """
        Determine document type based on subdirectory and filename.

        Args:
            subdirectory: Name of the subdirectory
            filename: Name of the file

        Returns:
            Document type string
        """
        subdirectory_lower = subdirectory.lower()
        filename_lower = filename.lower()

        # BOE documents
        if 'boe' in subdirectory_lower or 'boe' in filename_lower:
            return 'BOE_Summary'

        # Laws directory
        elif 'law' in subdirectory_lower or 'ley' in subdirectory_lower:
            if 'iva' in filename_lower or 'vat' in filename_lower:
                return 'VAT_Law'
            elif 'irpf' in filename_lower:
                return 'IRPF_Law'
            elif 'sociedades' in filename_lower or 'corporate' in filename_lower:
                return 'Corporate_Tax_Law'
            elif 'autonomo' in filename_lower or 'self_employed' in filename_lower:
                return 'Self_Employed_Statute'
            elif 'facturacion' in filename_lower or 'invoicing' in filename_lower:
                return 'Invoicing_Regulation'
            elif 'tributaria' in filename_lower or 'tax' in filename_lower:
                return 'General_Tax_Law'
            else:
                return 'Legal_Document'

        # Other subdirectories
        elif 'regulation' in subdirectory_lower or 'reglamento' in subdirectory_lower:
            return 'Regulation'
        elif 'directive' in subdirectory_lower or 'directiva' in subdirectory_lower:
            return 'EU_Directive'
        else:
            return 'Legal_Document'
    
    def process_document(self, file_info: Dict[str, str]) -> Optional[LegalDocument]:
        """
        Process a single legal document and create embeddings.

        Args:
            file_info: Dictionary with file information (filename, filepath, subdirectory, document_type)

        Returns:
            LegalDocument instance if successful, None otherwise
        """
        filename = file_info['filename']
        file_path = file_info['filepath']
        document_type = file_info['document_type']
        subdirectory = file_info['subdirectory']

        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return None

        logger.info(f"Processing {document_type} document: {filename} from {subdirectory}")

        try:
            # Validate PDF file
            validation = self.pdf_service.validate_pdf_file(file_path)
            if not validation['valid']:
                logger.error(f"Invalid PDF file {filename}: {validation['error']}")
                return None

            # Extract text from PDF
            text_content, page_count = self.pdf_service.extract_text_from_pdf(file_path)

            if not text_content.strip():
                logger.warning(f"No text content extracted from {filename}")
                return None

            # Parse metadata based on document type
            metadata = self._parse_document_metadata(filename, document_type, subdirectory)

            # Create document record with enhanced metadata
            with transaction.atomic():
                document = LegalDocument.objects.create(
                    title=metadata['title'],
                    filename=filename,
                    file_path=file_path,
                    document_type=document_type,
                    document_name=metadata['document_name'],
                    publication_date=metadata['publication_date'],
                    boe_number=metadata.get('boe_number', ''),
                    boe_section=metadata.get('boe_section', ''),
                    issuing_authority=metadata['issuing_authority'],
                    legal_status=metadata['legal_status'],
                    effective_date=metadata['effective_date'],
                    total_pages=page_count,
                    total_chunks=0  # Will be updated after chunking
                )
                
                # Process chunks and embeddings
                chunks_created = self._process_document_chunks(document, text_content, metadata)
                
                # Update document with chunk count and processing timestamp
                document.total_chunks = chunks_created
                document.processed_at = timezone.now()
                document.save()
                
                logger.info(f"Successfully processed {filename}: {chunks_created} chunks created")
                return document
                
        except Exception as e:
            logger.error(f"Error processing document {filename}: {e}")
            return None

    def _parse_document_metadata(self, filename: str, document_type: str, subdirectory: str) -> Dict[str, Any]:
        """
        Parse metadata for different types of legal documents.

        Args:
            filename: Name of the file
            document_type: Type of document
            subdirectory: Subdirectory where file is located

        Returns:
            Dictionary with parsed metadata
        """
        if document_type == 'BOE_Summary':
            return self._parse_boe_filename(filename)
        else:
            return self._parse_general_legal_document(filename, document_type, subdirectory)

    def _parse_general_legal_document(self, filename: str, document_type: str, subdirectory: str) -> Dict[str, Any]:
        """
        Parse metadata for general legal documents (laws, regulations, etc.).

        Args:
            filename: Name of the file
            document_type: Type of document
            subdirectory: Subdirectory where file is located

        Returns:
            Dictionary with parsed metadata
        """
        try:
            # Remove .pdf extension
            name_without_ext = filename.replace('.pdf', '')

            # Try to extract date from filename (various formats)
            publication_date = None
            date_patterns = [
                r'(\d{4})-(\d{2})-(\d{2})',  # YYYY-MM-DD
                r'(\d{4})(\d{2})(\d{2})',    # YYYYMMDD
                r'(\d{2})-(\d{2})-(\d{4})',  # DD-MM-YYYY
                r'(\d{2})(\d{2})(\d{4})',    # DDMMYYYY
            ]

            for pattern in date_patterns:
                import re
                match = re.search(pattern, name_without_ext)
                if match:
                    try:
                        if len(match.group(1)) == 4:  # Year first
                            year, month, day = match.groups()
                        else:  # Day first
                            day, month, year = match.groups()
                        publication_date = datetime.strptime(f"{year}-{month}-{day}", '%Y-%m-%d').date()
                        break
                    except ValueError:
                        continue

            # Generate title based on document type and filename
            title = self._generate_document_title(name_without_ext, document_type)
            document_name = self._generate_document_name(name_without_ext, document_type)

            # Determine issuing authority based on document type
            issuing_authority = self._get_issuing_authority(document_type)

            return {
                'title': title,
                'document_name': document_name,
                'publication_date': publication_date,
                'boe_number': '',  # Not applicable for non-BOE documents
                'boe_section': '',  # Not applicable for non-BOE documents
                'issuing_authority': issuing_authority,
                'legal_status': 'active',  # Default to active, can be updated manually
                'effective_date': publication_date,  # Assume same as publication date
                'source': f'Legal Documents - {subdirectory}',
                'date': publication_date.strftime('%Y-%m-%d') if publication_date else None
            }

        except Exception as e:
            logger.warning(f"Error parsing document metadata for {filename}: {e}")
            return {
                'title': f"{document_type.replace('_', ' ')} - {filename}",
                'document_name': f"{document_type.replace('_', ' ')} - {filename}",
                'publication_date': None,
                'boe_number': '',
                'boe_section': '',
                'issuing_authority': 'Unknown',
                'legal_status': 'unknown',
                'effective_date': None,
                'source': f'Legal Documents - {subdirectory}',
                'date': None
            }

    def _generate_document_title(self, name_without_ext: str, document_type: str) -> str:
        """Generate a readable title for the document."""
        type_titles = {
            'VAT_Law': 'Ley del IVA',
            'IRPF_Law': 'Ley del IRPF',
            'Corporate_Tax_Law': 'Ley del Impuesto sobre Sociedades',
            'Self_Employed_Statute': 'Estatuto del Trabajador Autónomo',
            'Invoicing_Regulation': 'Reglamento de Facturación',
            'General_Tax_Law': 'Ley General Tributaria',
            'Regulation': 'Reglamento',
            'EU_Directive': 'Directiva UE',
            'Legal_Document': 'Documento Legal'
        }

        base_title = type_titles.get(document_type, document_type.replace('_', ' '))

        # Try to make the filename more readable
        clean_name = name_without_ext.replace('_', ' ').replace('-', ' ')

        return f"{base_title} - {clean_name}"

    def _generate_document_name(self, name_without_ext: str, document_type: str) -> str:
        """Generate an official document name."""
        return f"{document_type.replace('_', ' ')} - {name_without_ext}"

    def _get_issuing_authority(self, document_type: str) -> str:
        """Get the issuing authority based on document type."""
        authorities = {
            'VAT_Law': 'Ministerio de Hacienda y Función Pública',
            'IRPF_Law': 'Ministerio de Hacienda y Función Pública',
            'Corporate_Tax_Law': 'Ministerio de Hacienda y Función Pública',
            'Self_Employed_Statute': 'Ministerio de Trabajo y Economía Social',
            'Invoicing_Regulation': 'Ministerio de Hacienda y Función Pública',
            'General_Tax_Law': 'Ministerio de Hacienda y Función Pública',
            'BOE_Summary': 'Agencia Estatal Boletín Oficial del Estado',
            'Regulation': 'Gobierno de España',
            'EU_Directive': 'Unión Europea',
            'Legal_Document': 'Gobierno de España'
        }

        return authorities.get(document_type, 'Gobierno de España')

    def _parse_boe_filename(self, filename: str) -> Dict[str, Any]:
        """
        Parse metadata from BOE filename and extract enhanced information.

        Expected format: YYYYMMDD_BOE_NUM_XXX_Sumario.pdf or YYYYMMDD_BOE_Sumario.pdf

        Args:
            filename: BOE PDF filename

        Returns:
            Dictionary with parsed metadata including publication date, BOE number, etc.
        """
        try:
            # Remove .pdf extension
            name_without_ext = filename.replace('.pdf', '')
            parts = name_without_ext.split('_')

            if len(parts) >= 2:
                date_str = parts[0]  # YYYYMMDD

                # Parse date
                try:
                    date_obj = datetime.strptime(date_str, '%Y%m%d')
                    publication_date = date_obj.date()
                    formatted_date = date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    publication_date = None
                    formatted_date = date_str

                # Extract BOE number if present
                boe_number = ""
                if len(parts) >= 4 and parts[1] == 'BOE' and parts[2] == 'NUM':
                    boe_number = f"BOE-{parts[3]}"

                # Create enhanced title
                title = f"BOE Summary {formatted_date}"
                document_name = f"Boletín Oficial del Estado - Sumario {formatted_date}"

                if boe_number:
                    title += f" ({boe_number})"
                    document_name += f" - {boe_number}"

                return {
                    'title': title,
                    'document_name': document_name,
                    'publication_date': publication_date,
                    'boe_number': boe_number,
                    'boe_section': 'Sumario',
                    'issuing_authority': 'Agencia Estatal Boletín Oficial del Estado',
                    'legal_status': 'active',
                    'effective_date': publication_date,  # For summaries, effective date is same as publication
                    'source': 'BOE Official Bulletin',
                    'date': formatted_date
                }
            else:
                # Fallback for unexpected filename format
                return {
                    'title': f"BOE Document - {filename}",
                    'document_name': f"BOE Document - {filename}",
                    'publication_date': None,
                    'boe_number': "",
                    'boe_section': 'Unknown',
                    'issuing_authority': 'Agencia Estatal Boletín Oficial del Estado',
                    'legal_status': 'unknown',
                    'effective_date': None,
                    'source': 'BOE Official Bulletin',
                    'date': None
                }

        except Exception as e:
            logger.warning(f"Error parsing filename {filename}: {e}")
            return {
                'title': f"BOE Document - {filename}",
                'document_name': f"BOE Document - {filename}",
                'publication_date': None,
                'boe_number': "",
                'boe_section': 'Unknown',
                'issuing_authority': 'Agencia Estatal Boletín Oficial del Estado',
                'legal_status': 'unknown',
                'effective_date': None,
                'source': 'BOE Official Bulletin',
                'date': None
            }
    
    def _process_document_chunks(self, document: LegalDocument, text_content: str, metadata: Dict[str, Any]) -> int:
        """
        Process document into chunks and generate embeddings.
        
        Args:
            document: LegalDocument instance
            text_content: Extracted text content
            metadata: Document metadata
            
        Returns:
            Number of chunks created
        """
        # Split text into chunks
        chunk_metadata = {
            'document_id': str(document.id),
            'filename': document.filename,
            'document_type': document.document_type,
            'source': metadata.get('source', 'BOE'),
            'publication_date': metadata.get('publication_date')
        }
        
        chunks = self.pdf_service.split_text_into_chunks(text_content, chunk_metadata)
        
        if not chunks:
            logger.warning(f"No chunks created for document {document.filename}")
            return 0
        
        logger.info(f"Created {len(chunks)} chunks for document {document.filename}")
        
        # Generate embeddings for all chunks
        chunk_texts = [chunk.page_content for chunk in chunks]
        embeddings_map = self.embedding_service.get_embeddings_batch(chunk_texts)
        
        # Create DocumentChunk records
        chunks_created = 0
        for i, chunk in enumerate(chunks):
            try:
                content = chunk.page_content
                content_hash = self.pdf_service.generate_content_hash(content)
                
                # Get embedding for this chunk
                embedding = embeddings_map.get(content, None)
                if embedding is None:
                    logger.warning(f"No embedding generated for chunk {i} of {document.filename}")
                    continue
                
                # Estimate token count
                token_count = self.embedding_service.estimate_tokens(content)
                
                # Create chunk record
                DocumentChunk.objects.create(
                    document=document,
                    chunk_index=i,
                    content=content,
                    content_hash=content_hash,
                    page_numbers=[],  # BOE summaries don't have clear page boundaries
                    start_char=None,
                    end_char=None,
                    embedding_vector=embedding,
                    embedding_model=self.embedding_service.model,
                    token_count=token_count
                )
                
                chunks_created += 1
                
            except Exception as e:
                logger.error(f"Error creating chunk {i} for document {document.filename}: {e}")
                continue
        
        logger.info(f"Successfully created {chunks_created} chunk records with embeddings")
        return chunks_created
    
    def process_all_unprocessed_documents(self) -> Dict[str, Any]:
        """
        Process all unprocessed BOE documents.
        
        Returns:
            Dictionary with processing statistics
        """
        unprocessed_files = self.get_unprocessed_documents()
        
        if not unprocessed_files:
            logger.info("No unprocessed BOE documents found")
            return {
                'total_files': 0,
                'processed': 0,
                'failed': 0,
                'total_chunks': 0
            }
        
        logger.info(f"Processing {len(unprocessed_files)} BOE documents")
        
        processed_count = 0
        failed_count = 0
        total_chunks = 0
        
        # Process files with progress bar
        with tqdm(total=len(unprocessed_files), desc="Processing legal documents") as pbar:
            for file_info in unprocessed_files:
                filename = file_info['filename']
                document_type = file_info['document_type']
                subdirectory = file_info['subdirectory']

                try:
                    document = self.process_document(file_info)
                    if document:
                        processed_count += 1
                        total_chunks += document.total_chunks
                        pbar.set_postfix({
                            'Processed': processed_count,
                            'Failed': failed_count,
                            'Chunks': total_chunks
                        })
                        pbar.set_description(f"Processing {document_type} from {subdirectory}")
                    else:
                        failed_count += 1

                except Exception as e:
                    logger.error(f"Unexpected error processing {filename}: {e}")
                    failed_count += 1

                pbar.update(1)
        
        stats = {
            'total_files': len(unprocessed_files),
            'processed': processed_count,
            'failed': failed_count,
            'total_chunks': total_chunks
        }
        
        logger.info(f"Processing complete - Processed: {processed_count}, "
                   f"Failed: {failed_count}, Total chunks: {total_chunks}")
        
        return stats
    
    def get_processing_stats(self) -> Dict[str, Any]:
        """
        Get statistics about processed BOE documents.
        
        Returns:
            Dictionary with processing statistics
        """
        boe_documents = LegalDocument.objects.filter(document_type='BOE_Summary')
        
        total_documents = boe_documents.count()
        processed_documents = boe_documents.filter(processed_at__isnull=False).count()
        total_chunks = DocumentChunk.objects.filter(document__document_type='BOE_Summary').count()
        
        # Get date range of processed documents
        date_range = None
        if processed_documents > 0:
            dates = []
            for doc in boe_documents.filter(processed_at__isnull=False):
                try:
                    # Extract date from filename
                    date_part = doc.filename[:8]  # YYYYMMDD
                    date_obj = datetime.strptime(date_part, '%Y%m%d')
                    dates.append(date_obj)
                except ValueError:
                    continue
            
            if dates:
                dates.sort()
                date_range = {
                    'start': dates[0].strftime('%Y-%m-%d'),
                    'end': dates[-1].strftime('%Y-%m-%d')
                }
        
        return {
            'total_documents': total_documents,
            'processed_documents': processed_documents,
            'unprocessed_documents': total_documents - processed_documents,
            'total_chunks': total_chunks,
            'date_range': date_range,
            'documents_directory': self.documents_dir
        }

    def process_all_documents(
        self,
        force_reprocess: bool = False,
        max_files: Optional[int] = None,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Process all documents with flexible options for management command.

        Args:
            force_reprocess: If True, reprocess all documents even if already processed
            max_files: Maximum number of files to process (for testing)
            batch_size: Number of files to process in each batch (minimum 3)

        Returns:
            Dictionary with processing statistics
        """
        import time
        start_time = time.time()

        # Enforce minimum batch size of 3 documents for efficiency
        if batch_size < 3 and max_files is None:
            logger.info(f"Adjusting batch_size from {batch_size} to minimum of 3 documents")
            batch_size = 3

        if force_reprocess:
            # Get all documents (processed and unprocessed)
            all_files = self.get_all_documents()
        else:
            # Get only unprocessed documents
            all_files = self.get_unprocessed_documents()

        if not all_files:
            logger.info("No documents found to process")
            return {
                'processed': 0,
                'skipped': 0,
                'errors': 0,
                'total_chunks': 0,
                'total_embeddings': 0,
                'processing_time': 0
            }

        # Limit files if max_files is specified
        if max_files:
            all_files = all_files[:max_files]
            logger.info(f"Limited processing to {max_files} files")

        logger.info(f"Processing {len(all_files)} documents (force_reprocess={force_reprocess})")

        processed_count = 0
        skipped_count = 0
        error_count = 0
        total_chunks = 0
        total_embeddings = 0

        # Process files with progress bar
        with tqdm(total=len(all_files), desc="Processing documents") as pbar:
            for i, file_info in enumerate(all_files):
                filename = file_info['filename']
                document_type = file_info['document_type']
                subdirectory = file_info['subdirectory']

                try:
                    # Check if document already exists and is processed
                    if not force_reprocess:
                        existing_doc = LegalDocument.objects.filter(
                            filename=filename
                        ).first()

                        if existing_doc and existing_doc.processed_at:
                            skipped_count += 1
                            pbar.update(1)
                            pbar.set_postfix({
                                'Processed': processed_count,
                                'Skipped': skipped_count,
                                'Errors': error_count
                            })
                            continue

                    # Process the document
                    document = self.process_document(file_info)
                    if document:
                        processed_count += 1
                        total_chunks += document.total_chunks
                        # Count embeddings (each chunk should have an embedding)
                        chunk_count = document.chunks.filter(embedding_vector__isnull=False).count()
                        total_embeddings += chunk_count

                        pbar.set_postfix({
                            'Processed': processed_count,
                            'Skipped': skipped_count,
                            'Errors': error_count,
                            'Chunks': total_chunks
                        })
                        pbar.set_description(f"Processing {document_type} from {subdirectory}")
                    else:
                        error_count += 1

                except Exception as e:
                    logger.error(f"Error processing {filename}: {e}")
                    error_count += 1

                pbar.update(1)

                # Batch processing pause (optional)
                if batch_size > 0 and (i + 1) % batch_size == 0:
                    logger.info(f"Completed batch {(i + 1) // batch_size}, pausing briefly...")
                    time.sleep(0.5)  # Brief pause between batches

        processing_time = time.time() - start_time

        result = {
            'processed': processed_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total_chunks': total_chunks,
            'total_embeddings': total_embeddings,
            'processing_time': processing_time
        }

        logger.info(f"Processing completed: {result}")
        return result

    def get_all_documents(self) -> List[Dict[str, Any]]:
        """
        Get all documents in the documents directory (processed and unprocessed).

        Returns:
            List of document information dictionaries
        """
        all_files = []

        if not os.path.exists(self.documents_dir):
            logger.warning(f"Documents directory not found: {self.documents_dir}")
            return all_files

        # Scan all subdirectories for PDF files
        for root, dirs, files in os.walk(self.documents_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    file_path = os.path.join(root, file)
                    subdirectory = os.path.relpath(root, self.documents_dir)

                    # Determine document type based on subdirectory and filename
                    document_type = self._determine_document_type(subdirectory, file)

                    all_files.append({
                        'filename': file,
                        'file_path': file_path,
                        'subdirectory': subdirectory,
                        'document_type': document_type,
                        'file_size': os.path.getsize(file_path)
                    })

        # Sort by filename for consistent processing order
        all_files.sort(key=lambda x: x['filename'])

        logger.info(f"Found {len(all_files)} total PDF files in {self.documents_dir}")
        return all_files
