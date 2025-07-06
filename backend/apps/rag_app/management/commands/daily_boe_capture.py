"""
Daily BOE Capture Management Command

This command automatically captures daily BOE updates, downloads relevant documents,
processes them for embedding generation, and stores them in the database to maintain
the most current legal context for the RAG system.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from django.db import transaction
import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from apps.rag_app.services.boe_service import BOEAPIService
from apps.rag_app.services.boe_downloader_service import BOEDownloaderService
from apps.rag_app.services.boe_embedding_service import BOEEmbeddingService
from apps.rag_app.models import LegalDocument, DocumentChunk
from apps.common.responses import APIResponse

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Daily BOE capture - automatically fetch, process and store BOE updates'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Specific date to capture in YYYY-MM-DD format (default: today)',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1,
            help='Number of days back to capture (default: 1)',
        )
        parser.add_argument(
            '--skip-download',
            action='store_true',
            help='Skip PDF download, only process existing documents',
        )
        parser.add_argument(
            '--skip-embedding',
            action='store_true',
            help='Skip embedding generation, only download and store metadata',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be captured without actually processing',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force processing even if documents already exist',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Custom output directory for daily captures',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('😊 Daily BOE Capture System\n')
        )
        
        # Initialize services
        self.boe_api = BOEAPIService()
        self.downloader = BOEDownloaderService(output_dir=options.get('output_dir'))
        self.embedding_service = BOEEmbeddingService()
        
        # Parse date arguments
        capture_dates = self._parse_dates(options)
        
        # Show summary
        self._show_capture_summary(capture_dates, options)
        
        if options['dry_run']:
            self.stdout.write(
                self.style.WARNING('\n🔍 DRY RUN: No actual processing will occur')
            )
            return
        
        # Start capture process
        self.stdout.write('\n🚀 Starting daily BOE capture...\n')
        
        try:
            total_stats = {
                'dates_processed': 0,
                'documents_found': 0,
                'documents_downloaded': 0,
                'documents_processed': 0,
                'embeddings_created': 0,
                'errors': 0
            }
            
            for capture_date in capture_dates:
                self.stdout.write(f'📅 Processing date: {capture_date}')
                
                try:
                    date_stats = self._process_single_date(capture_date, options)
                    
                    # Accumulate stats
                    total_stats['dates_processed'] += 1
                    total_stats['documents_found'] += date_stats['documents_found']
                    total_stats['documents_downloaded'] += date_stats['documents_downloaded']
                    total_stats['documents_processed'] += date_stats['documents_processed']
                    total_stats['embeddings_created'] += date_stats['embeddings_created']
                    total_stats['errors'] += date_stats['errors']
                    
                    self.stdout.write(
                        f'   ✅ Date complete: {date_stats["documents_found"]} found, '
                        f'{date_stats["documents_downloaded"]} downloaded, '
                        f'{date_stats["documents_processed"]} processed'
                    )
                    
                except Exception as e:
                    total_stats['errors'] += 1
                    logger.error(f'Error processing date {capture_date}: {e}')
                    self.stdout.write(
                        self.style.ERROR(f'   ❌ Error processing {capture_date}: {e}')
                    )
            
            # Display final results
            self._display_final_results(total_stats)
            
        except Exception as e:
            logger.error(f'Critical error in daily BOE capture: {e}')
            raise CommandError(f'Daily capture failed: {e}')

    def _parse_dates(self, options) -> List[str]:
        """Parse and validate date arguments."""
        dates = []
        
        if options.get('date'):
            # Specific date provided
            try:
                date_obj = datetime.strptime(options['date'], '%Y-%m-%d')
                dates.append(date_obj.strftime('%Y%m%d'))
            except ValueError:
                raise CommandError(f'Invalid date format: {options["date"]}. Use YYYY-MM-DD')
        else:
            # Use days_back
            days_back = options.get('days_back', 1)
            for i in range(days_back):
                date_obj = datetime.now() - timedelta(days=i)
                dates.append(date_obj.strftime('%Y%m%d'))
        
        return dates

    def _show_capture_summary(self, dates: List[str], options: Dict[str, Any]):
        """Display capture summary before processing."""
        self.stdout.write(f'📋 Capture Summary:')
        self.stdout.write(f'   📅 Dates to process: {len(dates)}')
        
        if len(dates) <= 5:
            for date in dates:
                formatted_date = datetime.strptime(date, '%Y%m%d').strftime('%Y-%m-%d')
                self.stdout.write(f'      • {formatted_date}')
        else:
            self.stdout.write(f'      • {dates[0][:4]}-{dates[0][4:6]}-{dates[0][6:]} to {dates[-1][:4]}-{dates[-1][4:6]}-{dates[-1][6:]}')
        
        self.stdout.write(f'   📥 Download: {"Disabled" if options["skip_download"] else "Enabled"}')
        self.stdout.write(f'   🧠 Embeddings: {"Disabled" if options["skip_embedding"] else "Enabled"}')
        self.stdout.write(f'   📁 Output directory: {self.downloader.output_dir}')

    def _process_single_date(self, date: str, options: Dict[str, Any]) -> Dict[str, int]:
        """Process BOE updates for a single date - complete workflow."""
        stats = {
            'documents_found': 0,
            'documents_downloaded': 0,
            'documents_processed': 0,
            'embeddings_created': 0,
            'errors': 0
        }
        
        # Step 1: Download BOE daily summaries (PDFs)
        if not options['skip_download']:
            try:
                date_obj = datetime.strptime(date, '%Y%m%d')
                self.stdout.write(f'   📥 Downloading BOE summaries for {date}...')
                
                # Download daily summaries using the BOE downloader
                download_stats = self.downloader.download_date_range(date_obj, date_obj)
                stats['documents_downloaded'] = download_stats.get('downloaded', 0)
                
                self.stdout.write(f'   📥 Downloaded {stats["documents_downloaded"]} documents')
                
            except Exception as e:
                logger.error(f'Error downloading PDFs for {date}: {e}')
                stats['errors'] += 1
        
        # Step 2: Fetch BOE API data for metadata
        try:
            tax_items = self.boe_api.search_tax_related_content(date)
            stats['documents_found'] = len(tax_items)
            
            if tax_items:
                self.stdout.write(f'   📊 Found {len(tax_items)} tax-related BOE items')
                
                # Store metadata for API items
                for item in tax_items:
                    try:
                        self._store_boe_item_metadata(item, date)
                    except Exception as e:
                        logger.error(f'Error storing metadata for {item.get("id", "unknown")}: {e}')
                        stats['errors'] += 1
            else:
                self.stdout.write(f'   ℹ️  No tax-related BOE items found for {date}')
                
        except Exception as e:
            logger.error(f'Error fetching BOE API data for {date}: {e}')
            stats['errors'] += 1
        
        # Step 3: Process downloaded PDFs and generate embeddings
        if not options['skip_embedding']:
            try:
                self.stdout.write(f'   🧠 Processing embeddings for downloaded documents...')
                
                # Process any new unprocessed documents
                embedding_stats = self.embedding_service.process_all_unprocessed_documents()
                stats['documents_processed'] = embedding_stats.get('processed', 0)
                stats['embeddings_created'] = embedding_stats.get('total_chunks', 0)
                
                self.stdout.write(f'   🧠 Processed {stats["documents_processed"]} documents, created {stats["embeddings_created"]} embeddings')
                
            except Exception as e:
                logger.error(f'Error processing embeddings for {date}: {e}')
                stats['errors'] += 1
        
        return stats

    def _store_boe_item_metadata(self, item: Dict[str, Any], date: str):
        """Store BOE item metadata in database."""
        try:
            # Parse date
            date_obj = datetime.strptime(date, '%Y%m%d').date()
            
            # Create or update document record
            document, created = LegalDocument.objects.get_or_create(
                boe_id=item.get('id'),
                defaults={
                    'title': item.get('title', '')[:255],  # Truncate if too long
                    'filename': f"{item.get('id', 'unknown')}.txt",
                    'document_type': 'BOE_Daily_Update',
                    'publication_date': date_obj,
                    'department': item.get('department', '')[:100],
                    'section': item.get('section', '')[:100],
                    'legal_status': 'published',
                    'metadata': {
                        'source': 'BOE_API',
                        'capture_date': date,
                        'url_html': item.get('url_html', ''),
                        'url_xml': item.get('url_xml', ''),
                        'epigrafe': item.get('epigrafe', ''),
                    }
                }
            )
            
            if created:
                logger.info(f'Created new BOE document record: {item.get("id")}')
            else:
                logger.info(f'BOE document already exists: {item.get("id")}')
                
        except Exception as e:
            logger.error(f'Error storing BOE item metadata: {e}')
            raise

    def _display_final_results(self, stats: Dict[str, int]):
        """Display final capture results."""
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('📊 DAILY BOE CAPTURE RESULTS'))
        self.stdout.write('=' * 60)
        
        self.stdout.write(f'📅 Dates processed: {stats["dates_processed"]}')
        self.stdout.write(f'📄 Documents found: {stats["documents_found"]}')
        self.stdout.write(f'📥 Documents downloaded: {stats["documents_downloaded"]}')
        self.stdout.write(f'⚙️  Documents processed: {stats["documents_processed"]}')
        self.stdout.write(f'🧠 Embeddings created: {stats["embeddings_created"]}')
        self.stdout.write(f'❌ Errors: {stats["errors"]}')
        
        # Calculate success rate
        total_operations = stats['dates_processed']
        if total_operations > 0:
            success_rate = ((total_operations - stats['errors']) / total_operations) * 100
            self.stdout.write(f'✅ Success rate: {success_rate:.1f}%')
        
        self.stdout.write('=' * 60)
        
        if stats['errors'] > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  Capture completed with {stats["errors"]} errors. '
                    'Check logs for details.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('\n🎉 Daily BOE capture completed successfully!')
            )

    def get_capture_status(self) -> Dict[str, Any]:
        """Get current capture status for API responses."""
        # Get recent capture statistics
        recent_documents = LegalDocument.objects.filter(
            document_type='BOE_Daily_Update',
            created_at__gte=timezone.now() - timedelta(days=7)
        )
        
        return {
            'last_capture_date': timezone.now().strftime('%Y-%m-%d'),
            'recent_documents_count': recent_documents.count(),
            'total_boe_documents': LegalDocument.objects.filter(
                document_type__in=['BOE_Daily_Update', 'BOE_Summary']
            ).count(),
            'status': 'active'
        }