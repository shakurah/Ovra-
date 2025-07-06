"""
Management command to set up daily BOE capture schedule.
"""
from django.core.management.base import BaseCommand
from apps.rag_app.tasks import setup_daily_boe_schedule, get_schedule_status, remove_daily_boe_schedule


class Command(BaseCommand):
    help = 'Set up daily BOE capture schedule using Django Q'

    def add_arguments(self, parser):
        parser.add_argument(
            '--status',
            action='store_true',
            help='Show current schedule status',
        )
        parser.add_argument(
            '--remove',
            action='store_true',
            help='Remove existing schedule',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recreate schedule even if it exists',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('😊 Daily BOE Capture Schedule Manager\n')
        )
        
        # Show status if requested
        if options['status']:
            self._show_status()
            return
        
        # Remove schedule if requested
        if options['remove']:
            self._remove_schedule()
            return
        
        # Set up schedule
        self._setup_schedule(options.get('force', False))
    
    def _show_status(self):
        """Show current schedule status."""
        self.stdout.write('📊 Current Schedule Status:')
        
        status = get_schedule_status()
        
        if status['status'] == 'not_scheduled':
            self.stdout.write('   ❌ No daily BOE capture schedule found')
        elif status['status'] == 'error':
            self.stdout.write(f'   ❌ Error: {status["message"]}')
        else:
            self.stdout.write(f'   ✅ Status: {status["status"]}')
            self.stdout.write(f'   📅 Next run: {status["next_run"]}')
            self.stdout.write(f'   🔄 Last run: {status["last_run"] or "Never"}')
            self.stdout.write(f'   📋 Task: {status["task"]}')
            self.stdout.write(f'   🔁 Repeats: {status["repeats"]}')
    
    def _remove_schedule(self):
        """Remove existing schedule."""
        self.stdout.write('🗑️  Removing daily BOE capture schedule...')
        
        result = remove_daily_boe_schedule()
        
        if result['status'] == 'success':
            self.stdout.write(
                self.style.SUCCESS(f'✅ {result["message"]}')
            )
        elif result['status'] == 'not_found':
            self.stdout.write(
                self.style.WARNING(f'⚠️  {result["message"]}')
            )
        else:
            self.stdout.write(
                self.style.ERROR(f'❌ {result["message"]}')
            )
    
    def _setup_schedule(self, force=False):
        """Set up the daily schedule."""
        self.stdout.write('⚙️  Setting up daily BOE capture schedule...')
        
        # Check if schedule already exists
        status = get_schedule_status()
        
        if status['status'] != 'not_scheduled' and not force:
            self.stdout.write(
                self.style.WARNING(
                    '⚠️  Schedule already exists. Use --force to recreate or --remove to delete.'
                )
            )
            self._show_status()
            return
        
        # Remove existing schedule if force is used
        if force and status['status'] != 'not_scheduled':
            self.stdout.write('🔄 Force mode: removing existing schedule...')
            remove_daily_boe_schedule()
        
        # Create new schedule
        try:
            scheduled_task = setup_daily_boe_schedule()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'✅ Daily BOE capture schedule created successfully!'
                )
            )
            
            # Show the new schedule status
            self.stdout.write('\n📋 Schedule Details:')
            self._show_status()
            
            self.stdout.write(
                self.style.SUCCESS(
                    '\n🎉 Daily BOE capture will run automatically at 11:30 PM every day!'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to create schedule: {e}')
            )