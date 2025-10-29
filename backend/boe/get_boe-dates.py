import requests
import datetime
import time

# Base URL for the BOE sumaries API
BASE_SUMARIO_URL = "https://www.boe.es/datosabiertos/api/boe/sumario/{date}"

def fetch_sumario_for_date(date: datetime.date, retry: int = 3, sleep: float = 1.0):
    """Fetch the sumario (summary) for a single date. Returns JSON or None if not found."""
    url = BASE_SUMARIO_URL.format(date=date.strftime("%Y%m%d"))
    for attempt in range(retry):
        try:
            resp = requests.get(url, timeout=10, headers={"Accept": "application/json"})
            if resp.status_code == 200:
                return resp.json()
            elif resp.status_code == 404:
                # No summary for that date
                return None
            else:
                print(f"Warning: received status {resp.status_code} for {url}")
        except Exception as e:
            print(f"Error fetching {url}: {e}")
        time.sleep(sleep)
    return None

def find_available_dates(start_year=1960, end_year=None):
    """Loop over dates from start_year up to today (or end_year) and find which have summaries."""
    if end_year is None:
        end_year = datetime.date.today().year
    
    results = []
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    d = datetime.date(year, month, day)
                except ValueError:
                    continue
                summary = fetch_sumario_for_date(d)
                if summary:
                    print(f"✅ Summary found for {d}")
                    results.append(d)
                else:
                    print(f"— No summary for {d}")
                # optionally sleep lightly to avoid heavy load
                time.sleep(0.1)
    return results

if __name__ == "__main__":
    available_dates = find_available_dates(start_year=1960, end_year=1961)  # test for one year
    print(f"Found {len(available_dates)} dates in 1960 with summaries: {available_dates}")
