"""
Daily BOE Capture Management Command

Consolidated command that handles the complete BOE automation workflow:
1. Downloads BOE daily summaries (PDFs) to local folder
2. Processes all unprocessed documents (PDF reading, text extraction)
3. Generates embeddings and stores in PostgreSQL database
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from apps.rag_app.services.boe_downloader_service import BOEDownloaderService
from apps.rag_app.services.boe_embedding_service import BOEEmbeddingService
from apps.rag_app.models import LegalDocument, DocumentChunk

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Complete daily BOE automation: download, process, and store embeddings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to process in YYYY-MM-DD format (default: yesterday)',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1,
            help='Number of days back to process (default: 1)',
        )
        parser.add_argument(
            '--skip-download',
            action='store_true',
            help='Skip PDF download, only process existing documents',
        )
        parser.add_argument(
            '--skip-embedding',
            action='store_true',
            help='Skip embedding generation, only download documents',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be processed without actually doing it',
        )
        parser.add_argument(
            '--force-reprocess',
            action='store_true',
            help='Force reprocessing of already processed documents',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('😊 Daily BOE Automation System\n')
        )
        
        # Initialize services
        self.downloader = BOEDownloaderService()
        self.embedding_service = BOEEmbeddingService()
        
        # Parse date arguments
        process_dates = self._parse_dates(options)
        
        # Show summary
        self._show_process_summary(process_dates, options)
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n🔍 DRY RUN: No actual processing will occur')
            )
            return
        
        # Start automation process
        self.stdout.write('\n🚀 Starting daily BOE automation...\n')
        
        try:
            total_stats = {
                'dates_processed': 0,
                'documents_downloaded': 0,
                'documents_processed': 0,
                'embeddings_created': 0,
                'errors': 0
            }
            
            # Step 1: Download documents (if not skipped)
            if not options['skip_download']:
                for process_date in process_dates:
                    download_stats = self._download_date_documents(process_date)
                    total_stats['documents_downloaded'] += download_stats['downloaded']
                    total_stats['errors'] += download_stats['errors']
            
            # Step 2: Process all unprocessed documents (if not skipped)
            if not options['skip_embedding']:
                processing_stats = self._process_unprocessed_documents(
                    force_reprocess=options.get('force_reprocess', False)
                )
                total_stats['documents_processed'] = processing_stats['processed']
                total_stats['embeddings_created'] = processing_stats['total_chunks']
                total_stats['errors'] += processing_stats['failed']
            
            total_stats['dates_processed'] = len(process_dates)
            
            # Display final results
            self._display_final_results(total_stats)
            
        except Exception as e:
            logger.error(f'Critical error in daily BOE automation: {e}')
            raise CommandError(f'Automation failed: {e}')

    def _parse_dates(self, options) -> List[datetime]:
        """Parse and validate date arguments."""
        dates = []
        
        if options.get('date'):
            # Specific date provided
            try:
                date_obj = datetime.strptime(options['date'], '%Y-%m-%d')
                dates.append(date_obj)
            except ValueError:
                raise CommandError(f'Invalid date format: {options["date"]}. Use YYYY-MM-DD')
        else:
            # Use days_back (default: yesterday)
            days_back = options.get('days_back', 1)
            for i in range(days_back):
                date_obj = datetime.now() - timedelta(days=i+1)  # Start from yesterday
                dates.append(date_obj)
        
        return dates

    def _show_process_summary(self, dates: List[datetime], options: Dict[str, Any]):
        """Display processing summary before starting."""
        self.stdout.write(f'📋 Process Summary:')
        self.stdout.write(f'   📅 Dates to process: {len(dates)}')
        
        if len(dates) <= 5:
            for date in dates:
                self.stdout.write(f'      • {date.strftime("%Y-%m-%d")}')
        else:
            self.stdout.write(f'      • {dates[0].strftime("%Y-%m-%d")} to {dates[-1].strftime("%Y-%m-%d")}')
        
        self.stdout.write(f'   📥 Download: {"Disabled" if options["skip_download"] else "Enabled"}')
        self.stdout.write(f'   🧠 Embeddings: {"Disabled" if options["skip_embedding"] else "Enabled"}')
        self.stdout.write(f'   📁 Output directory: {self.downloader.output_dir}')

    def _download_date_documents(self, date: datetime) -> Dict[str, int]:
        """Download BOE documents for a specific date."""
        stats = {'downloaded': 0, 'errors': 0}
        
        try:
            self.stdout.write(f'📥 Downloading BOE documents for {date.strftime("%Y-%m-%d")}...')
            
            # Download using the BOE downloader service
            download_result = self.downloader.download_date_range(date, date)
            stats['downloaded'] = download_result.get('downloaded', 0)
            
            self.stdout.write(f'   ✅ Downloaded {stats["downloaded"]} documents')
            
        except Exception as e:
            logger.error(f'Error downloading documents for {date}: {e}')
            stats['errors'] += 1
            self.stdout.write(f'   ❌ Download failed: {e}')
        
        return stats

    def _process_unprocessed_documents(self, force_reprocess: bool = False) -> Dict[str, int]:
        """Process all unprocessed documents and generate embeddings."""
        self.stdout.write('🧠 Processing unprocessed documents...')
        
        try:
            # Get processing statistics
            processing_result = self.embedding_service.process_all_unprocessed_documents()
            
            processed = processing_result.get('processed', 0)
            failed = processing_result.get('failed', 0)
            total_chunks = processing_result.get('total_chunks', 0)
            
            self.stdout.write(f'   ✅ Processed {processed} documents')
            self.stdout.write(f'   🧩 Created {total_chunks} embedding chunks')
            
            if failed > 0:
                self.stdout.write(f'   ❌ Failed to process {failed} documents')
            
            return {
                'processed': processed,
                'failed': failed,
                'total_chunks': total_chunks
            }
            
        except Exception as e:
            logger.error(f'Error processing documents: {e}')
            self.stdout.write(f'   ❌ Processing failed: {e}')
            return {'processed': 0, 'failed': 1, 'total_chunks': 0}

    def _display_final_results(self, stats: Dict[str, int]):
        """Display final automation results."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('📊 DAILY BOE AUTOMATION RESULTS'))
        self.stdout.write('=' * 60)
        
        self.stdout.write(f'📅 Dates processed: {stats["dates_processed"]}')
        self.stdout.write(f'📥 Documents downloaded: {stats["documents_downloaded"]}')
        self.stdout.write(f'⚙️  Documents processed: {stats["documents_processed"]}')
        self.stdout.write(f'🧠 Embedding chunks created: {stats["embeddings_created"]}')
        self.stdout.write(f'❌ Errors: {stats["errors"]}')
        
        # Calculate success rate
        total_operations = stats['dates_processed'] + stats['documents_processed']
        if total_operations > 0:
            success_rate = ((total_operations - stats['errors']) / total_operations) * 100
            self.stdout.write(f'✅ Success rate: {success_rate:.1f}%')
        
        # Show current database stats
        self._show_database_stats()
        
        self.stdout.write('=' * 60)
        
        if stats['errors'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Automation completed with {stats["errors"]} errors. '
                    'Check logs for details.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Daily BOE automation completed successfully!')
            )

    def _show_database_stats(self):
        """Show current database statistics."""
        try:
            total_docs = LegalDocument.objects.count()
            processed_docs = LegalDocument.objects.filter(processed_at__isnull=False).count()
            total_chunks = DocumentChunk.objects.count()
            boe_docs = LegalDocument.objects.filter(
                document_type__in=['BOE_Summary', 'BOE_Daily_Update']
            ).count()
            
            self.stdout.write(f'📊 Database Statistics:')
            self.stdout.write(f'   📄 Total documents: {total_docs}')
            self.stdout.write(f'   📑 BOE documents: {boe_docs}')
            self.stdout.write(f'   ✅ Processed documents: {processed_docs}')
            self.stdout.write(f'   🧩 Total embedding chunks: {total_chunks}')
            
        except Exception as e:
            logger.warning(f'Could not retrieve database stats: {e}')

    def get_automation_status(self) -> Dict[str, Any]:
        """Get current automation status for API responses."""
        try:
            recent_documents = LegalDocument.objects.filter(
                document_type__in=['BOE_Summary', 'BOE_Daily_Update'],
                created_at__gte=timezone.now() - timedelta(days=7)
            )
            
            return {
                'last_run_date': timezone.now().strftime('%Y-%m-%d'),
                'recent_documents_count': recent_documents.count(),
                'total_boe_documents': LegalDocument.objects.filter(
                    document_type__in=['BOE_Summary', 'BOE_Daily_Update']
                ).count(),
                'total_chunks': DocumentChunk.objects.count(),
                'status': 'active'
            }
        except Exception as e:
            logger.error(f'Error getting automation status: {e}')
            return {'status': 'error', 'message': str(e)}