"""
Management command to download BOE documents from the Spanish official API.

This command downloads BOE daily summaries as PDF files and stores them
in the documents folder for further processing and embedding generation.
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import datetime, timedelta
from apps.rag_app.services.boe_downloader_service import BOEDownloaderService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Download BOE documents from the Spanish official API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date in YYYY-MM-DD format (default: 2022-01-01)',
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date in YYYY-MM-DD format (default: today)',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            help='Download documents from N days back to today (alternative to date range)',
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            help='Custom output directory for downloaded files',
        )
        parser.add_argument(
            '--max-workers',
            type=int,
            default=5,
            help='Maximum number of concurrent downloads (default: 5)',
        )
        parser.add_argument(
            '--stats-only',
            action='store_true',
            help='Show download statistics without downloading new files',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force re-download of existing files',
        )
        parser.add_argument(
            '--years-back',
            type=int,
            help='Number of years back from today to download (e.g., 3 for last 3 years)',
        )
        parser.add_argument(
            '--full-historical',
            action='store_true',
            help='Download all documents from the last 3 years (same as --years-back 3)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=30,
            help='Number of days to process in each batch for large downloads (default: 30)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be downloaded without actually downloading',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔽 BOE Document Downloader\n')
        )
        
        # Initialize the downloader service
        downloader = BOEDownloaderService(output_dir=options.get('output_dir'))
        
        # Show current statistics if requested
        if options['stats_only']:
            self._show_stats(downloader)
            return
        
        # Parse date arguments
        start_date, end_date = self._parse_dates(options)

        total_days = (end_date - start_date).days + 1
        self.stdout.write(f"📅 Download period: {start_date.date()} to {end_date.date()}")
        self.stdout.write(f"📊 Total days: {total_days}")
        self.stdout.write(f"📁 Output directory: {downloader.output_dir}")
        self.stdout.write(f"🔧 Max workers: {downloader.MAX_WORKERS}\n")

        # Show current stats before download
        self.stdout.write("📊 Current download statistics:")
        self._show_stats(downloader, prefix="   ")

        # Handle dry run
        if options.get('dry_run'):
            self.stdout.write(
                self.style.WARNING(f"\n🔍 DRY RUN: Would download BOE documents for {total_days} days")
            )
            return

        # Confirm before proceeding
        if not self._confirm_download(start_date, end_date, total_days):
            self.stdout.write(self.style.WARNING("❌ Download cancelled by user"))
            return

        # Start download process
        self.stdout.write("\n🚀 Starting BOE document download...\n")

        try:
            # Handle batch processing for large downloads
            batch_size = options.get('batch_size', 30)
            if total_days > batch_size and total_days > 30:
                stats = self._download_in_batches(downloader, start_date, end_date, batch_size)
            else:
                stats = downloader.download_date_range(start_date, end_date)

            # Display results
            self._display_results(stats)

            # Show updated statistics
            self.stdout.write("\n📊 Updated download statistics:")
            self._show_stats(downloader, prefix="   ")

            if stats['errors'] > 0:
                self.stdout.write(
                    self.style.WARNING(
                        f"\n⚠️ Download completed with {stats['errors']} errors. "
                        "Check logs for details."
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS("\n✅ Download completed successfully!")
                )
                
        except Exception as e:
            logger.error(f"Error during BOE download: {e}")
            raise CommandError(f"Download failed: {e}")

    def _parse_dates(self, options):
        """Parse and validate date arguments with support for historical downloads."""
        end_date = datetime.today()

        # Handle full historical download (3 years)
        if options.get('full_historical'):
            years_back = 3
            start_date = end_date - timedelta(days=years_back * 365)
            self.stdout.write(f"📅 Using full historical: {years_back} years back")

        # Handle years_back option
        elif options.get('years_back'):
            years_back = options['years_back']
            start_date = end_date - timedelta(days=years_back * 365)
            self.stdout.write(f"📅 Using years_back: {years_back} years")

        # Handle days_back option
        elif options.get('days_back'):
            days_back = options['days_back']
            start_date = end_date - timedelta(days=days_back)
            self.stdout.write(f"📅 Using days_back: {days_back} days")

        else:
            # Use date range options
            start_date_str = options.get('start_date', '2022-01-01')
            end_date_str = options.get('end_date')

            try:
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            except ValueError:
                raise CommandError(f"Invalid start date format: {start_date_str}. Use YYYY-MM-DD")

            if end_date_str:
                try:
                    end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
                except ValueError:
                    raise CommandError(f"Invalid end date format: {end_date_str}. Use YYYY-MM-DD")

        # Validate date range
        if start_date > end_date:
            raise CommandError("Start date cannot be after end date")

        if end_date > datetime.today():
            end_date = datetime.today()
            self.stdout.write(
                self.style.WARNING("⚠️ End date adjusted to today (cannot download future documents)")
            )

        # Calculate total days for large downloads
        total_days = (end_date - start_date).days + 1
        if total_days > 365:
            self.stdout.write(
                self.style.WARNING(
                    f"⚠️ Large download detected: {total_days} days ({total_days/365:.1f} years)"
                )
            )
            if options.get('batch_size'):
                self.stdout.write(f"📦 Will process in batches of {options['batch_size']} days")

        return start_date, end_date

    def _download_in_batches(self, downloader, start_date, end_date, batch_size):
        """Download documents in batches to handle large date ranges."""
        current_date = start_date
        total_stats = {'downloaded': 0, 'skipped': 0, 'errors': 0}

        batch_num = 1
        total_days = (end_date - start_date).days + 1
        total_batches = (total_days + batch_size - 1) // batch_size

        self.stdout.write(f"📦 Processing {total_days} days in {total_batches} batches of {batch_size} days each\n")

        while current_date <= end_date:
            batch_end = min(current_date + timedelta(days=batch_size - 1), end_date)

            self.stdout.write(
                f"📦 Batch {batch_num}/{total_batches}: {current_date.date()} to {batch_end.date()}"
            )

            try:
                batch_stats = downloader.download_date_range(current_date, batch_end)

                # Accumulate stats
                total_stats['downloaded'] += batch_stats['downloaded']
                total_stats['skipped'] += batch_stats['skipped']
                total_stats['errors'] += batch_stats['errors']

                self.stdout.write(
                    f"   ✅ Batch {batch_num} complete: "
                    f"Downloaded {batch_stats['downloaded']}, "
                    f"Skipped {batch_stats['skipped']}, "
                    f"Errors {batch_stats['errors']}"
                )

            except Exception as e:
                self.stdout.write(f"   ❌ Batch {batch_num} failed: {e}")
                total_stats['errors'] += 1

            current_date = batch_end + timedelta(days=1)
            batch_num += 1

            # Small delay between batches to be respectful to the API
            if current_date <= end_date:
                import time
                time.sleep(1)

        return total_stats

    def _show_stats(self, downloader, prefix=""):
        """Display current download statistics."""
        stats = downloader.get_download_stats()
        
        self.stdout.write(f"{prefix}📁 Total files: {stats['total_files']}")
        self.stdout.write(f"{prefix}💾 Total size: {stats['total_size_mb']} MB")
        
        if stats['date_range']:
            self.stdout.write(
                f"{prefix}📅 Date range: {stats['date_range']['start']} to {stats['date_range']['end']}"
            )
        else:
            self.stdout.write(f"{prefix}📅 Date range: No files downloaded yet")
        
        self.stdout.write(f"{prefix}📂 Directory: {stats['output_directory']}")

    def _confirm_download(self, start_date, end_date, total_days):
        """Ask user for confirmation before starting download."""
        self.stdout.write(f"\n⚠️ About to download BOE documents for {total_days} days")

        if total_days > 365:
            years = total_days / 365
            self.stdout.write(f"📅 This covers approximately {years:.1f} years of documents")
            self.stdout.write("⏰ Large downloads may take significant time (hours)")
        elif total_days > 30:
            self.stdout.write("⏰ This may take several minutes depending on the date range")
        else:
            self.stdout.write("⏰ This should complete in a few minutes")
        
        response = input("\nDo you want to continue? [y/N]: ")
        return response.lower() in ['y', 'yes']

    def _display_results(self, stats):
        """Display download results in a formatted way."""
        self.stdout.write("\n" + "="*50)
        self.stdout.write(self.style.SUCCESS("📋 DOWNLOAD RESULTS"))
        self.stdout.write("="*50)
        
        self.stdout.write(f"📥 Downloaded: {stats['downloaded']} files")
        self.stdout.write(f"⏭️  Skipped: {stats['skipped']} files (already exist)")
        self.stdout.write(f"❌ Errors: {stats['errors']} files")
        self.stdout.write(f"📊 Total processed: {stats['total']} dates")
        
        # Calculate success rate
        if stats['total'] > 0:
            success_rate = ((stats['downloaded'] + stats['skipped']) / stats['total']) * 100
            self.stdout.write(f"✅ Success rate: {success_rate:.1f}%")
        
        self.stdout.write("="*50)

    def _format_file_size(self, size_bytes):
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
