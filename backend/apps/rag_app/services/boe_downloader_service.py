"""
BOE Document Downloader Service

This service downloads BOE (Boletín Oficial del Estado) documents from the Spanish
government's official API and stores them in the documents folder for processing.
"""

import os
import requests
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from tqdm import tqdm
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from django.conf import settings

logger = logging.getLogger(__name__)


class BOEDownloaderService:
    """
    Service for downloading BOE documents from the Spanish official API.
    
    Downloads daily summaries as PDF files and stores them in the documents folder
    with proper naming conventions for further processing.
    """
    
    BASE_URL = "https://boe.es/datosabiertos/api/boe/sumario"
    HEADERS = {"Accept": "application/json"}
    MAX_WORKERS = 5  # Concurrent downloads
    
    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the BOE downloader service.
        
        Args:
            output_dir: Directory to save documents. Defaults to backend/documents/boe_summaries
        """
        if output_dir is None:
            # Use the documents folder in the backend
            base_dir = getattr(settings, 'BASE_DIR', os.path.dirname(os.path.dirname(__file__)))
            self.output_dir = os.path.join(base_dir, '..', '..', 'documents', 'boe_summaries')
        else:
            self.output_dir = output_dir
            
        # Ensure output directory exists
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Thread lock for progress tracking
        self._lock = threading.Lock()
        
    def fetch_daily_summary_info(self, date_str: str) -> Optional[Dict[str, Any]]:
        """
        Fetch daily summary info including metadata for proper naming.
        
        Args:
            date_str: Date in YYYYMMDD format
            
        Returns:
            Dictionary with summary info or None if error
        """
        url = f"{self.BASE_URL}/{date_str}"
        try:
            response = requests.get(url, headers=self.HEADERS, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            diario = data.get("data", {}).get("sumario", {}).get("diario", [])
            if isinstance(diario, dict):
                diario = [diario]
                
            for d in diario:
                pdf_url = d.get("sumario_diario", {}).get("url_pdf", {}).get("texto")
                if pdf_url:
                    # Extract metadata for proper naming
                    nbo = d.get("nbo", "")  # BOE number
                    fecha = d.get("fecha", date_str)  # Date
                    
                    return {
                        "url": pdf_url,
                        "date": date_str,
                        "nbo": nbo,
                        "fecha": fecha
                    }
        except Exception as e:
            logger.error(f"Error fetching summary info for {date_str}: {e}")
            return {"error": f"[ERROR] {date_str}: {e}"}
        return None

    def generate_summary_filename(self, summary_info: Dict[str, Any]) -> str:
        """
        Generate proper filename for daily summary.
        
        Args:
            summary_info: Dictionary with summary metadata
            
        Returns:
            Generated filename
        """
        date = summary_info["date"]
        nbo = summary_info.get("nbo", "")
        
        # Format: YYYYMMDD_BOE_NUM_XXX_Sumario.pdf
        if nbo:
            filename = f"{date}_BOE_NUM_{nbo}_Sumario.pdf"
        else:
            filename = f"{date}_BOE_Sumario.pdf"
        
        return filename

    def download_summary(self, summary_info: Dict[str, Any]) -> str:
        """
        Download a daily summary PDF.
        
        Args:
            summary_info: Dictionary with summary metadata and URL
            
        Returns:
            Status message indicating success, skip, or error
        """
        if "error" in summary_info:
            return summary_info["error"]
        
        if not summary_info:
            return "No summary data available"
        
        filename = self.generate_summary_filename(summary_info)
        output_path = os.path.join(self.output_dir, filename)
        
        if os.path.exists(output_path):
            return f"Skipped (exists): {filename}"
        
        try:
            response = requests.get(summary_info["url"], stream=True, timeout=15)
            response.raise_for_status()
            
            with open(output_path, "wb") as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
                    
            logger.info(f"Downloaded: {filename}")
            return f"Downloaded: {filename}"
        except Exception as e:
            logger.error(f"Error downloading {filename}: {e}")
            return f"ERROR downloading {filename}: {e}"

    def fetch_and_download_summary(self, date_str: str) -> str:
        """
        Combined function to fetch info and download summary.
        
        Args:
            date_str: Date in YYYYMMDD format
            
        Returns:
            Status message
        """
        summary_info = self.fetch_daily_summary_info(date_str)
        return self.download_summary(summary_info)

    def download_date_range(self, start_date: datetime, end_date: Optional[datetime] = None) -> Dict[str, int]:
        """
        Download BOE summaries for a date range.
        
        Args:
            start_date: Start date for downloads
            end_date: End date for downloads. Defaults to today.
            
        Returns:
            Dictionary with download statistics
        """
        if end_date is None:
            end_date = datetime.today()
            
        logger.info(f"Downloading BOE summaries from {start_date.date()} to {end_date.date()}")
        
        # Generate all dates to process
        dates_to_process = []
        current_date = start_date
        while current_date <= end_date:
            dates_to_process.append(current_date.strftime('%Y%m%d'))
            current_date += timedelta(days=1)
        
        logger.info(f"Total dates to process: {len(dates_to_process)}")
        
        # Statistics tracking
        downloaded_count = 0
        skipped_count = 0
        error_count = 0
        
        # Use ThreadPoolExecutor for concurrent downloads
        with ThreadPoolExecutor(max_workers=self.MAX_WORKERS) as executor:
            # Submit all download tasks
            future_to_date = {
                executor.submit(self.fetch_and_download_summary, date_str): date_str 
                for date_str in dates_to_process
            }
            
            # Process completed downloads with progress bar
            with tqdm(total=len(dates_to_process), desc="Processing summaries") as pbar:
                for future in as_completed(future_to_date):
                    result = future.result()
                    
                    with self._lock:
                        if "Downloaded:" in result:
                            downloaded_count += 1
                        elif "Skipped:" in result:
                            skipped_count += 1
                        elif "ERROR" in result:
                            error_count += 1
                            tqdm.write(result)  # Print errors
                    
                    pbar.update(1)
                    pbar.set_postfix({
                        'Downloaded': downloaded_count,
                        'Skipped': skipped_count, 
                        'Errors': error_count
                    })
        
        stats = {
            'downloaded': downloaded_count,
            'skipped': skipped_count,
            'errors': error_count,
            'total': len(dates_to_process)
        }
        
        logger.info(f"Download complete - Downloaded: {downloaded_count}, "
                   f"Skipped: {skipped_count}, Errors: {error_count}")
        
        return stats

    def download_missing_documents(self, start_date: Optional[datetime] = None) -> Dict[str, int]:
        """
        Download missing BOE documents from start_date to current date.
        
        Args:
            start_date: Start date for downloads. Defaults to 2022-01-01.
            
        Returns:
            Dictionary with download statistics
        """
        if start_date is None:
            start_date = datetime(2022, 1, 1)
            
        return self.download_date_range(start_date, datetime.today())

    def get_downloaded_files(self) -> List[str]:
        """
        Get list of already downloaded BOE files.
        
        Returns:
            List of downloaded filenames
        """
        if not os.path.exists(self.output_dir):
            return []
            
        files = [f for f in os.listdir(self.output_dir) 
                if f.endswith('.pdf') and 'BOE' in f]
        return sorted(files)

    def get_download_stats(self) -> Dict[str, Any]:
        """
        Get statistics about downloaded files.
        
        Returns:
            Dictionary with download statistics
        """
        files = self.get_downloaded_files()
        
        if not files:
            return {
                'total_files': 0,
                'total_size_mb': 0,
                'date_range': None,
                'output_directory': self.output_dir
            }
        
        # Calculate total size
        total_size = 0
        for filename in files:
            filepath = os.path.join(self.output_dir, filename)
            if os.path.exists(filepath):
                total_size += os.path.getsize(filepath)
        
        # Extract date range from filenames
        dates = []
        for filename in files:
            if filename.startswith('2'):  # Starts with year
                date_part = filename[:8]  # YYYYMMDD
                try:
                    dates.append(datetime.strptime(date_part, '%Y%m%d'))
                except ValueError:
                    continue
        
        date_range = None
        if dates:
            dates.sort()
            date_range = {
                'start': dates[0].strftime('%Y-%m-%d'),
                'end': dates[-1].strftime('%Y-%m-%d')
            }
        
        return {
            'total_files': len(files),
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'date_range': date_range,
            'output_directory': self.output_dir
        }
