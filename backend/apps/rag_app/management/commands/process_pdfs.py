"""
Django management command to process PDF documents and generate embeddings.
"""
import os
import glob
from pathlib import Path
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from apps.rag_app.services import DocumentProcessingService


class Command(BaseCommand):
    help = 'Process PDF documents in the media folder and generate embeddings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--media-folder',
            type=str,
            default='media',
            help='Path to media folder containing PDFs (default: media)'
        )
        parser.add_argument(
            '--file-pattern',
            type=str,
            default='*.pdf',
            help='File pattern to match (default: *.pdf)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reprocessing of already processed documents'
        )
        parser.add_argument(
            '--specific-file',
            type=str,
            help='Process only a specific PDF file'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting PDF processing...')
        )
        
        # Initialize processing service
        processor = DocumentProcessingService()
        
        # Determine media folder path
        media_folder = options['media_folder']
        if not os.path.isabs(media_folder):
            media_folder = os.path.join(settings.BASE_DIR, media_folder)
        
        if not os.path.exists(media_folder):
            raise CommandError(f'Media folder does not exist: {media_folder}')
        
        # Find PDF files
        if options['specific_file']:
            pdf_files = [os.path.join(media_folder, options['specific_file'])]
            if not os.path.exists(pdf_files[0]):
                raise CommandError(f'Specific file not found: {pdf_files[0]}')
        else:
            pattern = os.path.join(media_folder, options['file_pattern'])
            pdf_files = glob.glob(pattern)
        
        if not pdf_files:
            self.stdout.write(
                self.style.WARNING(f'No PDF files found in {media_folder}')
            )
            return
        
        self.stdout.write(f'Found {len(pdf_files)} PDF files to process')
        
        # Process each PDF
        total_processed = 0
        total_failed = 0
        
        for pdf_path in pdf_files:
            filename = os.path.basename(pdf_path)
            self.stdout.write(f'\nProcessing: {filename}')
            
            try:
                # Determine document title and type from filename
                document_title, document_type = self._parse_filename(filename)
                
                # Process the document
                result = processor.process_pdf_document(
                    file_path=pdf_path,
                    document_title=document_title,
                    document_type=document_type
                )
                
                if result['success']:
                    total_processed += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'✓ Successfully processed: {document_title}\n'
                            f'  - Pages: {result["total_pages"]}\n'
                            f'  - Chunks: {result["total_chunks"]}\n'
                            f'  - Time: {result["processing_time_seconds"]}s\n'
                            f'  - Database: {"✓" if result.get("database_storage_success", False) else "✗"}'
                        )
                    )
                else:
                    total_failed += 1
                    self.stdout.write(
                        self.style.ERROR(
                            f'✗ Failed to process: {filename}\n'
                            f'  Error: {result["error"]}'
                        )
                    )
                    
            except Exception as e:
                total_failed += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ Exception processing {filename}: {str(e)}')
                )
        
        # Summary
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Processing Complete ===\n'
                f'Total files: {len(pdf_files)}\n'
                f'Successfully processed: {total_processed}\n'
                f'Failed: {total_failed}'
            )
        )
        
        # Show processing status
        status = processor.get_processing_status()
        self.stdout.write(
            f'\n=== System Status ===\n'
            f'Total documents in DB: {status.get("total_documents", 0)}\n'
            f'Processed documents: {status.get("processed_documents", 0)}\n'
            f'Total chunks: {status.get("total_chunks", 0)}\n'
            f'Vector DB chunks: {status.get("vector_database", {}).get("total_chunks", 0)}'
        )

    def _parse_filename(self, filename: str) -> tuple:
        """
        Parse filename to extract document title and type.
        
        Args:
            filename: PDF filename
            
        Returns:
            Tuple of (title, document_type)
        """
        # Remove .pdf extension
        name = filename.replace('.pdf', '')
        
        # Map of filename patterns to document types
        type_mapping = {
            'iva': 'VAT Law',
            'irpf': 'Personal Income Tax Law',
            'sociedades': 'Corporate Income Tax Law',
            'tributaria': 'General Tax Law',
            'facturación': 'Invoicing Regulation',
            'facturacion': 'Invoicing Regulation',
            'contable': 'Accounting Plan',
            'autónomo': 'Self-Employed Workers Statute',
            'autonomo': 'Self-Employed Workers Statute'
        }
        
        # Try to identify document type from filename
        name_lower = name.lower()
        document_type = 'Legal Document'  # Default
        
        for keyword, doc_type in type_mapping.items():
            if keyword in name_lower:
                document_type = doc_type
                break
        
        # Clean up title
        title = name.replace('_', ' ').replace('-', ' ').title()
        
        return title, document_type
