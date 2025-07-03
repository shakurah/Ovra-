"""
Management command to process documents and generate embeddings for the knowledge bank.
This command scans the documents folder, processes PDFs, generates embeddings, and stores them in the database.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime
from apps.rag_app.services.boe_embedding_service import BOEEmbeddingService
from apps.rag_app.models import LegalDocument, DocumentChunk
import logging
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process documents and generate embeddings for the knowledge bank'

    def add_arguments(self, parser):
        parser.add_argument(
            '--documents-dir',
            type=str,
            help='Custom documents directory to process (default: backend/documents)',
        )
        parser.add_argument(
            '--force-reprocess',
            action='store_true',
            help='Force reprocessing of all documents (even if already processed)',
        )
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Show embedding statistics without processing new documents',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing',
        )
        parser.add_argument(
            '--max-files',
            type=int,
            help='Maximum number of files to process (for testing)',
        )
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=1000,
            help='Chunk size for text splitting (default: 1000)',
        )
        parser.add_argument(
            '--chunk-overlap',
            type=int,
            default=200,
            help='Chunk overlap for text splitting (default: 200)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of files to process in each batch (default: 10, minimum: 3)',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧠 Document Embedding Processor\n')
        )
        
        # Initialize the embedding service
        embedding_service = BOEEmbeddingService(
            documents_dir=options.get('documents_dir')
        )
        
        # Show current statistics if requested
        if options['stats_only']:
            self._show_stats()
            return
        
        # Show current stats before processing
        self.stdout.write("📊 Current embedding statistics:")
        self._show_stats(prefix="   ")
        
        # Handle dry run
        if options.get('dry_run'):
            self._show_dry_run(embedding_service, options)
            return
        
        # Confirm before proceeding with large operations
        if not self._confirm_processing(embedding_service, options):
            self.stdout.write(self.style.WARNING("❌ Processing cancelled by user"))
            return
        
        # Start processing
        self.stdout.write("\n🚀 Starting document processing and embedding generation...\n")
        
        try:
            # Ensure minimum batch size of 3 documents
            batch_size = max(3, options.get('batch_size', 10))
            max_files = options.get('max_files')

            # If max_files is specified and less than 3, warn user
            if max_files and max_files < 3:
                self.stdout.write(
                    self.style.WARNING(
                        f'⚠️  Warning: max_files ({max_files}) is less than minimum batch size (3). '
                        f'Processing will continue with {max_files} files.'
                    )
                )

            # Process documents and generate embeddings
            stats = embedding_service.process_all_documents(
                force_reprocess=options.get('force_reprocess', False),
                max_files=max_files,
                batch_size=batch_size
            )
            
            # Display results
            self._display_results(stats)
            
            # Show updated statistics
            self.stdout.write("\n📊 Updated embedding statistics:")
            self._show_stats(prefix="   ")
            
            if stats.get('errors', 0) > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️ Processing completed with {stats['errors']} errors. "
                        "Check logs for details."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\n✅ Processing completed successfully!")
                )
                
        except Exception as e:
            logger.error(f"Error during embedding processing: {e}")
            raise CommandError(f"Processing failed: {e}")

    def _show_stats(self, prefix=""):
        """Show current embedding statistics."""
        total_documents = LegalDocument.objects.count()
        total_chunks = DocumentChunk.objects.count()
        processed_documents = LegalDocument.objects.filter(
            chunks__isnull=False
        ).distinct().count()
        
        self.stdout.write(f"{prefix}📄 Total documents in database: {total_documents}")
        self.stdout.write(f"{prefix}🧩 Total chunks in database: {total_chunks}")
        self.stdout.write(f"{prefix}✅ Processed documents: {processed_documents}")
        self.stdout.write(f"{prefix}⏳ Unprocessed documents: {total_documents - processed_documents}")
        
        if total_chunks > 0:
            avg_chunks_per_doc = total_chunks / max(processed_documents, 1)
            self.stdout.write(f"{prefix}📊 Average chunks per document: {avg_chunks_per_doc:.1f}")
        
        # Show recent documents
        recent_docs = LegalDocument.objects.order_by('-created_at')[:5]
        if recent_docs:
            self.stdout.write(f"{prefix}📋 Recent documents:")
            for doc in recent_docs:
                chunk_count = doc.chunks.count()
                self.stdout.write(f"{prefix}  - {doc.filename} ({chunk_count} chunks)")

    def _show_dry_run(self, embedding_service, options):
        """Show what would be processed in a dry run."""
        self.stdout.write(
            self.style.WARNING("🔍 DRY RUN: Scanning for documents to process...")
        )
        
        # Get list of files that would be processed
        documents_dir = embedding_service.documents_dir
        if not os.path.exists(documents_dir):
            self.stdout.write(
                self.style.ERROR(f"❌ Documents directory not found: {documents_dir}")
            )
            return
        
        # Count files by type
        pdf_files = []
        for root, dirs, files in os.walk(documents_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(os.path.join(root, file))
        
        self.stdout.write(f"📁 Documents directory: {documents_dir}")
        self.stdout.write(f"📄 PDF files found: {len(pdf_files)}")
        
        if options.get('max_files'):
            max_files = options['max_files']
            self.stdout.write(f"🔢 Limited to: {max_files} files")
            pdf_files = pdf_files[:max_files]
        
        # Show sample files
        if pdf_files:
            self.stdout.write("📋 Sample files to process:")
            for file in pdf_files[:10]:  # Show first 10
                rel_path = os.path.relpath(file, documents_dir)
                self.stdout.write(f"   - {rel_path}")
            
            if len(pdf_files) > 10:
                self.stdout.write(f"   ... and {len(pdf_files) - 10} more files")
        
        self.stdout.write("\n💡 Remove --dry-run to start actual processing")

    def _confirm_processing(self, embedding_service, options):
        """Confirm processing with user for large operations."""
        # Count files to process
        documents_dir = embedding_service.documents_dir
        pdf_files = []
        for root, dirs, files in os.walk(documents_dir):
            for file in files:
                if file.lower().endswith('.pdf'):
                    pdf_files.append(file)
        
        total_files = len(pdf_files)
        if options.get('max_files'):
            total_files = min(total_files, options['max_files'])
        
        # Auto-confirm for small operations
        if total_files <= 10:
            return True
        
        # Ask for confirmation for large operations
        self.stdout.write(
            self.style.WARNING(
                f"⚠️ About to process {total_files} PDF files. This may take significant time."
            )
        )
        
        response = input("Continue? [y/N]: ").lower().strip()
        return response in ['y', 'yes']

    def _display_results(self, stats):
        """Display processing results."""
        self.stdout.write("\n📈 Processing Results:")
        self.stdout.write(f"✅ Successfully processed: {stats.get('processed', 0)}")
        self.stdout.write(f"⏭️ Skipped (already processed): {stats.get('skipped', 0)}")
        self.stdout.write(f"❌ Failed: {stats.get('errors', 0)}")
        self.stdout.write(f"🧩 Total chunks created: {stats.get('total_chunks', 0)}")
        self.stdout.write(f"🔗 Total embeddings generated: {stats.get('total_embeddings', 0)}")
        
        if stats.get('processing_time'):
            self.stdout.write(f"⏱️ Total processing time: {stats['processing_time']:.2f} seconds")
            
        if stats.get('processed', 0) > 0 and stats.get('processing_time'):
            avg_time = stats['processing_time'] / stats['processed']
            self.stdout.write(f"📊 Average time per document: {avg_time:.2f} seconds")
