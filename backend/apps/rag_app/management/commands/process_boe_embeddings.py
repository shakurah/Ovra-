"""
Management command to process legal documents and generate embeddings.

This command processes legal PDF files from all subdirectories (BOE, laws, regulations, etc.),
extracts text content, creates chunks, generates OpenAI embeddings, and stores them in the database.
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from apps.rag_app.services.boe_embedding_service import BOEEmbeddingService
from apps.rag_app.models import LegalDocument, DocumentChunk
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Process legal documents from all subdirectories and generate embeddings using OpenAI'

    def add_arguments(self, parser):
        parser.add_argument(
            '--documents-dir',
            type=str,
            help='Custom root directory containing legal documents (default: documents/)',
        )
        parser.add_argument(
            '--filename',
            type=str,
            help='Process a specific document by filename',
        )
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Show processing statistics without processing new documents',
        )
        parser.add_argument(
            '--reprocess',
            action='store_true',
            help='Reprocess documents that have already been processed',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually processing',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force processing even if documents appear to be processed',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🧠 BOE Embedding Processor\n')
        )
        
        # Initialize the embedding service
        embedding_service = BOEEmbeddingService(documents_dir=options.get('documents_dir'))
        
        # Show current statistics
        self.stdout.write("📊 Current processing statistics:")
        self._show_stats(embedding_service, prefix="   ")
        
        # Show stats only if requested
        if options['stats_only']:
            return
        
        # Handle specific file processing
        if options.get('filename'):
            self._process_specific_file(embedding_service, options['filename'], options)
            return
        
        # Handle reprocessing
        if options['reprocess']:
            self._handle_reprocessing(embedding_service, options)
            return
        
        # Get unprocessed documents
        unprocessed_files = embedding_service.get_unprocessed_documents()
        
        if not unprocessed_files:
            self.stdout.write(
                self.style.SUCCESS("✅ All BOE documents have been processed!")
            )
            return
        
        self.stdout.write(f"\n📋 Found {len(unprocessed_files)} unprocessed documents:")
        for i, filename in enumerate(unprocessed_files[:10], 1):  # Show first 10
            self.stdout.write(f"   {i}. {filename}")
        
        if len(unprocessed_files) > 10:
            self.stdout.write(f"   ... and {len(unprocessed_files) - 10} more")
        
        # Dry run check
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING("\n🔍 DRY RUN: No documents will be processed")
            )
            return
        
        # Confirm before processing
        if not self._confirm_processing(len(unprocessed_files)):
            self.stdout.write(self.style.WARNING("❌ Processing cancelled by user"))
            return
        
        # Start processing
        self.stdout.write("\n🚀 Starting BOE document processing...\n")
        
        try:
            stats = embedding_service.process_all_unprocessed_documents()
            
            # Display results
            self._display_results(stats)
            
            # Show updated statistics
            self.stdout.write("\n📊 Updated processing statistics:")
            self._show_stats(embedding_service, prefix="   ")
            
            if stats['failed'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️ Processing completed with {stats['failed']} failures. "
                        "Check logs for details."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\n✅ All documents processed successfully!")
                )
                
        except Exception as e:
            logger.error(f"Error during BOE embedding processing: {e}")
            raise CommandError(f"Processing failed: {e}")

    def _process_specific_file(self, embedding_service, filename, options):
        """Process a specific legal document file."""
        self.stdout.write(f"\n📄 Processing specific file: {filename}")

        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN: File would be processed")
            )
            return

        try:
            # Find the file in the unprocessed documents list
            unprocessed_files = embedding_service.get_unprocessed_documents()
            file_info = None

            for file_data in unprocessed_files:
                if file_data['filename'] == filename:
                    file_info = file_data
                    break

            if not file_info:
                # Check if file exists but is already processed
                all_files = []
                import os
                for root, dirs, files in os.walk(embedding_service.documents_dir):
                    for file in files:
                        if file == filename and file.endswith('.pdf'):
                            rel_path = os.path.relpath(root, embedding_service.documents_dir)
                            subdirectory = rel_path if rel_path != '.' else 'root'
                            document_type = embedding_service._determine_document_type(subdirectory, filename)

                            file_info = {
                                'filename': filename,
                                'filepath': os.path.join(root, filename),
                                'subdirectory': subdirectory,
                                'document_type': document_type,
                                'relative_path': os.path.join(rel_path, filename) if rel_path != '.' else filename
                            }
                            break

                if not file_info:
                    raise CommandError(f"File not found: {filename}")
                else:
                    self.stdout.write(
                        self.style.WARNING(f"⚠️ File {filename} appears to be already processed")
                    )
                    if not options.get('force'):
                        return

            self.stdout.write(f"📁 Found in: {file_info['subdirectory']}")
            self.stdout.write(f"📋 Document type: {file_info['document_type']}")

            document = embedding_service.process_document(file_info)

            if document:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✅ Successfully processed {filename}: "
                        f"{document.total_chunks} chunks created"
                    )
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"❌ Failed to process {filename}")
                )

        except Exception as e:
            logger.error(f"Error processing specific file {filename}: {e}")
            raise CommandError(f"Failed to process {filename}: {e}")

    def _handle_reprocessing(self, embedding_service, options):
        """Handle reprocessing of already processed documents."""
        self.stdout.write("\n🔄 Reprocessing mode")
        
        # Get all processed BOE documents
        processed_docs = LegalDocument.objects.filter(
            document_type='BOE_Summary',
            processed_at__isnull=False
        )
        
        if not processed_docs.exists():
            self.stdout.write(
                self.style.WARNING("⚠️ No processed BOE documents found to reprocess")
            )
            return
        
        self.stdout.write(f"📋 Found {processed_docs.count()} processed documents")
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING("🔍 DRY RUN: Documents would be reprocessed")
            )
            return
        
        if not self._confirm_reprocessing(processed_docs.count()):
            self.stdout.write(self.style.WARNING("❌ Reprocessing cancelled by user"))
            return
        
        # Delete existing chunks and reprocess
        reprocessed_count = 0
        failed_count = 0
        
        for document in processed_docs:
            try:
                with transaction.atomic():
                    # Delete existing chunks
                    DocumentChunk.objects.filter(document=document).delete()
                    
                    # Reset document processing status
                    document.processed_at = None
                    document.total_chunks = 0
                    document.save()
                    
                    # Reprocess the document
                    result = embedding_service.process_document(document.filename)
                    
                    if result:
                        reprocessed_count += 1
                        self.stdout.write(f"✅ Reprocessed: {document.filename}")
                    else:
                        failed_count += 1
                        self.stdout.write(f"❌ Failed to reprocess: {document.filename}")
                        
            except Exception as e:
                failed_count += 1
                logger.error(f"Error reprocessing {document.filename}: {e}")
                self.stdout.write(f"❌ Error reprocessing {document.filename}: {e}")
        
        self.stdout.write(f"\n📊 Reprocessing complete:")
        self.stdout.write(f"   ✅ Reprocessed: {reprocessed_count}")
        self.stdout.write(f"   ❌ Failed: {failed_count}")

    def _show_stats(self, embedding_service, prefix=""):
        """Display current processing statistics."""
        stats = embedding_service.get_processing_stats()
        
        self.stdout.write(f"{prefix}📁 Total documents: {stats['total_documents']}")
        self.stdout.write(f"{prefix}✅ Processed: {stats['processed_documents']}")
        self.stdout.write(f"{prefix}⏳ Unprocessed: {stats['unprocessed_documents']}")
        self.stdout.write(f"{prefix}🧩 Total chunks: {stats['total_chunks']}")
        
        if stats['date_range']:
            self.stdout.write(
                f"{prefix}📅 Date range: {stats['date_range']['start']} to {stats['date_range']['end']}"
            )
        else:
            self.stdout.write(f"{prefix}📅 Date range: No documents processed yet")
        
        self.stdout.write(f"{prefix}📂 Directory: {stats['documents_directory']}")

    def _confirm_processing(self, file_count):
        """Ask user for confirmation before starting processing."""
        self.stdout.write(f"\n⚠️ About to process {file_count} BOE documents")
        self.stdout.write("This will:")
        self.stdout.write("   • Extract text from PDF files")
        self.stdout.write("   • Split text into chunks")
        self.stdout.write("   • Generate OpenAI embeddings (API costs apply)")
        self.stdout.write("   • Store embeddings in the database")
        self.stdout.write("\nThis may take several minutes and will consume OpenAI API credits.")
        
        response = input("\nDo you want to continue? [y/N]: ")
        return response.lower() in ['y', 'yes']

    def _confirm_reprocessing(self, doc_count):
        """Ask user for confirmation before reprocessing."""
        self.stdout.write(f"\n⚠️ About to reprocess {doc_count} documents")
        self.stdout.write("This will:")
        self.stdout.write("   • Delete existing chunks and embeddings")
        self.stdout.write("   • Regenerate all embeddings (API costs apply)")
        self.stdout.write("   • May take significant time")
        
        response = input("\nAre you sure you want to reprocess? [y/N]: ")
        return response.lower() in ['y', 'yes']

    def _display_results(self, stats):
        """Display processing results in a formatted way."""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("📋 PROCESSING RESULTS"))
        self.stdout.write("="*50)
        
        self.stdout.write(f"📄 Total files: {stats['total_files']}")
        self.stdout.write(f"✅ Processed: {stats['processed']} files")
        self.stdout.write(f"❌ Failed: {stats['failed']} files")
        self.stdout.write(f"🧩 Total chunks created: {stats['total_chunks']}")
        
        # Calculate success rate
        if stats['total_files'] > 0:
            success_rate = (stats['processed'] / stats['total_files']) * 100
            self.stdout.write(f"📊 Success rate: {success_rate:.1f}%")
        
        self.stdout.write("="*50)
