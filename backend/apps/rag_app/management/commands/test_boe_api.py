"""
Management command to test BOE API integration
"""

from django.core.management.base import BaseCommand
from apps.rag_app.services.boe_service import BOEAPIService
import json


class Command(BaseCommand):
    help = 'Test BOE API integration and display results'

    def add_arguments(self, parser):
        parser.add_argument(
            '--date',
            type=str,
            help='Date in YYYYMMDD format (default: today)',
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=3,
            help='Number of days to look back for recent updates (default: 3)',
        )
        parser.add_argument(
            '--fetch-content',
            action='store_true',
            help='Fetch full content for found documents',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Testing BOE API Integration...\n')
        )
        
        boe_service = BOEAPIService()
        
        # Test 1: Get daily summary
        self.stdout.write("📅 Testing daily summary...")
        date = options.get('date')
        summary = boe_service.get_daily_summary(date)
        
        if summary:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Successfully fetched BOE summary")
            )
            
            # Count total items
            total_items = 0
            diario_data = summary.get('sumario', {}).get('diario', [])
            if not isinstance(diario_data, list):
                diario_data = [diario_data]
            
            for diario in diario_data:
                sections = diario.get('seccion', [])
                if not isinstance(sections, list):
                    sections = [sections]
                
                for section in sections:
                    departments = section.get('departamento', [])
                    if not isinstance(departments, list):
                        departments = [departments]
                    
                    for dept in departments:
                        epigrafes = dept.get('epigrafe', [])
                        if not isinstance(epigrafes, list):
                            epigrafes = [epigrafes]
                        
                        for epigrafe in epigrafes:
                            items = epigrafe.get('item', [])
                            if isinstance(items, list):
                                total_items += len(items)
                            elif items:
                                total_items += 1
            
            self.stdout.write(f"   📊 Total BOE items found: {total_items}")
        else:
            self.stdout.write(
                self.style.ERROR("❌ Failed to fetch BOE summary")
            )
            return
        
        # Test 2: Search tax-related content
        self.stdout.write("\n🏛️ Testing tax-related content search...")
        tax_items = boe_service.search_tax_related_content(date)
        
        if tax_items:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Found {len(tax_items)} tax-related items")
            )
            
            for i, item in enumerate(tax_items[:5], 1):  # Show first 5
                self.stdout.write(f"   {i}. {item.get('title', 'No title')[:80]}...")
                self.stdout.write(f"      Department: {item.get('department', 'Unknown')}")
                self.stdout.write(f"      ID: {item.get('id', 'No ID')}")
        else:
            self.stdout.write(
                self.style.WARNING("⚠️ No tax-related items found for today")
            )
        
        # Test 3: Get recent updates
        self.stdout.write(f"\n📈 Testing recent updates (last {options['days_back']} days)...")
        recent_items = boe_service.get_recent_tax_updates(options['days_back'])
        
        if recent_items:
            self.stdout.write(
                self.style.SUCCESS(f"✅ Found {len(recent_items)} recent tax updates")
            )
            
            # Group by date
            by_date = {}
            for item in recent_items:
                date_key = item.get('date', 'Unknown')
                if date_key not in by_date:
                    by_date[date_key] = []
                by_date[date_key].append(item)
            
            for date_key, items in sorted(by_date.items(), reverse=True):
                self.stdout.write(f"   📅 {date_key}: {len(items)} items")
        else:
            self.stdout.write(
                self.style.WARNING("⚠️ No recent tax updates found")
            )
        
        # Test 4: Fetch content (if requested and items available)
        if options['fetch_content'] and tax_items:
            self.stdout.write("\n📄 Testing content extraction...")
            
            # Test with first item
            test_item = tax_items[0]
            boe_id = test_item.get('id')
            
            if boe_id:
                self.stdout.write(f"   Fetching content for: {boe_id}")
                content = boe_service.get_document_content(boe_id)
                
                if content:
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Successfully extracted content")
                    )
                    self.stdout.write(f"   📏 Content length: {len(content)} characters")
                    self.stdout.write(f"   📝 Preview: {content[:200]}...")
                else:
                    self.stdout.write(
                        self.style.ERROR("❌ Failed to extract content")
                    )
            else:
                self.stdout.write(
                    self.style.WARNING("⚠️ No BOE ID available for content test")
                )
        
        # Test 5: Format for RAG
        if tax_items:
            self.stdout.write("\n🤖 Testing RAG formatting...")
            formatted_items = boe_service.format_for_rag(
                tax_items[:2], 
                include_content=options['fetch_content']
            )
            
            if formatted_items:
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Successfully formatted {len(formatted_items)} items for RAG")
                )
                
                # Show structure of first item
                if formatted_items:
                    first_item = formatted_items[0]
                    self.stdout.write("   📋 Sample formatted item structure:")
                    for key, value in first_item.items():
                        if key == 'content':
                            self.stdout.write(f"      {key}: {len(str(value))} characters")
                        elif isinstance(value, dict):
                            self.stdout.write(f"      {key}: {len(value)} metadata fields")
                        else:
                            self.stdout.write(f"      {key}: {str(value)[:50]}...")
        
        self.stdout.write(
            self.style.SUCCESS('\n🎉 BOE API testing completed!')
        )
