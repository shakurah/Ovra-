"""
BOE API Service for Spanish Official State Bulletin Integration

This service handles requests to the Spanish government's official legal bulletin API
to retrieve real-time legal content and integrate it with the RAG system.
"""

import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup
import re
from django.conf import settings

logger = logging.getLogger(__name__)


class BOEAPIService:
    """
    Service for interacting with the Spanish BOE (Boletín Oficial del Estado) API.
    
    Provides methods to:
    - Fetch daily BOE summaries
    - Search for specific legal content
    - Extract and clean legal text
    - Format content for RAG integration
    """
    
    BASE_URL = "https://www.boe.es"
    API_BASE = f"{BASE_URL}/datosabiertos/api"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Ovra-AI-Legal-Assistant/1.0',
            'Accept': 'application/json',
            'Accept-Language': 'es-ES,es;q=0.9'
        })
    
    def get_daily_summary(self, date: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get BOE summary for a specific date.
        
        Args:
            date: Date in YYYYMMDD format. If None, uses today.
            
        Returns:
            Dictionary with BOE summary data or None if error
        """
        if not date:
            date = datetime.now().strftime("%Y%m%d")
        
        url = f"{self.API_BASE}/boe/sumario/{date}"
        
        try:
            logger.info(f"Fetching BOE summary for date: {date}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get('status', {}).get('code') == '200':
                return data.get('data', {})
            else:
                logger.warning(f"BOE API returned error: {data.get('status', {})}")
                return None
                
        except requests.RequestException as e:
            logger.error(f"Error fetching BOE summary: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in get_daily_summary: {e}")
            return None
    
    def search_tax_related_content(self, date: Optional[str] = None, 
                                 keywords: List[str] = None) -> List[Dict[str, Any]]:
        """
        Search for tax-related content in BOE for a specific date.
        
        Args:
            date: Date in YYYYMMDD format
            keywords: List of keywords to filter content
            
        Returns:
            List of relevant BOE items
        """
        if keywords is None:
            keywords = [
                'iva', 'irpf', 'impuesto', 'tributario', 'fiscal', 'hacienda',
                'autónomo', 'facturación', 'sociedades', 'cultural', 'artístico'
            ]
        
        summary = self.get_daily_summary(date)
        if not summary:
            return []
        
        relevant_items = []
        
        try:
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
                            if not isinstance(items, list):
                                items = [items] if items else []
                            
                            for item in items:
                                if self._is_tax_related(item, keywords):
                                    relevant_items.append({
                                        'id': item.get('identificador'),
                                        'title': item.get('titulo', ''),
                                        'department': dept.get('nombre', ''),
                                        'section': section.get('nombre', ''),
                                        'epigrafe': epigrafe.get('nombre', ''),
                                        'url_html': item.get('url_html', ''),
                                        'url_xml': item.get('url_xml', ''),
                                        'url_pdf': item.get('url_pdf', {}),
                                        'date': date
                                    })
        
        except Exception as e:
            logger.error(f"Error processing BOE summary: {e}")
        
        logger.info(f"Found {len(relevant_items)} tax-related BOE items")
        return relevant_items
    
    def _is_tax_related(self, item: Dict[str, Any], keywords: List[str]) -> bool:
        """Check if a BOE item is related to tax/fiscal matters."""
        title = item.get('titulo', '').lower()
        
        # Check for tax-related keywords
        for keyword in keywords:
            if keyword.lower() in title:
                return True
        
        return False
    
    def get_document_content(self, boe_id: str) -> Optional[str]:
        """
        Fetch the full text content of a BOE document.
        
        Args:
            boe_id: BOE document identifier (e.g., 'BOE-A-2025-13411')
            
        Returns:
            Cleaned text content or None if error
        """
        url = f"{self.BASE_URL}/diario_boe/txt.php?id={boe_id}"
        
        try:
            logger.info(f"Fetching BOE document content: {boe_id}")
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse HTML and extract text content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Find the main content area
            content_div = soup.find('div', {'id': 'contenido'}) or soup.find('div', class_='texto')
            
            if content_div:
                text = content_div.get_text()
            else:
                # Fallback to body text
                text = soup.get_text()
            
            # Clean and normalize text
            cleaned_text = self._clean_text(text)
            
            logger.info(f"Successfully extracted {len(cleaned_text)} characters from {boe_id}")
            return cleaned_text
            
        except requests.RequestException as e:
            logger.error(f"Error fetching BOE document {boe_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error extracting content from {boe_id}: {e}")
            return None
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        if not text:
            return ""
        
        # Remove excessive whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common HTML artifacts
        text = re.sub(r'&nbsp;', ' ', text)
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        
        # Remove navigation and footer text
        text = re.sub(r'Ir a contenido.*?BOE', '', text, flags=re.DOTALL)
        text = re.sub(r'Contactar.*?$', '', text, flags=re.DOTALL)
        
        # Clean up line breaks and spacing
        text = text.strip()
        
        return text
    
    def get_recent_tax_updates(self, days_back: int = 7) -> List[Dict[str, Any]]:
        """
        Get tax-related updates from the last N days.
        
        Args:
            days_back: Number of days to look back
            
        Returns:
            List of recent tax-related BOE items
        """
        all_items = []
        
        for i in range(days_back):
            date = (datetime.now() - timedelta(days=i)).strftime("%Y%m%d")
            items = self.search_tax_related_content(date)
            all_items.extend(items)
        
        # Sort by date (most recent first)
        all_items.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        logger.info(f"Found {len(all_items)} tax updates in last {days_back} days")
        return all_items
    
    def format_for_rag(self, boe_items: List[Dict[str, Any]], 
                      include_content: bool = True) -> List[Dict[str, Any]]:
        """
        Format BOE items for RAG system integration.
        
        Args:
            boe_items: List of BOE items
            include_content: Whether to fetch full content
            
        Returns:
            List of formatted items for RAG
        """
        formatted_items = []
        
        for item in boe_items:
            formatted_item = {
                'source': 'BOE',
                'document_id': item.get('id'),
                'title': item.get('title'),
                'department': item.get('department'),
                'section': item.get('section'),
                'date': item.get('date'),
                'url': item.get('url_html'),
                'metadata': {
                    'source_type': 'official_bulletin',
                    'authority': 'Spanish Government',
                    'publication_date': item.get('date'),
                    'department': item.get('department'),
                    'section': item.get('section')
                }
            }
            
            if include_content and item.get('id'):
                content = self.get_document_content(item['id'])
                if content:
                    formatted_item['content'] = content
                    formatted_item['content_length'] = len(content)
            
            formatted_items.append(formatted_item)
        
        return formatted_items
