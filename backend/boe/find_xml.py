import requests
from datetime import date, timedelta

def find_first_available_boe():
    start_date = date(1960, 1, 1)
    end_date = date(2025, 1, 1)
    delta = timedelta(days=1)

    base_url = "https://www.boe.es/diario_boe/xml.php?id=BOE-S-{}"
    
    current = start_date
    while current <= end_date:
        boe_id = current.strftime("%Y%m%d")
        url = base_url.format(boe_id)
        response = requests.head(url)
        
        if response.status_code == 200:
            print(f"✅ First available BOE found: {boe_id} ({url})")
            return boe_id
        current += delta
    
    print("❌ No valid BOE found between 1960 and 2025.")
    return None

if __name__ == "__main__":
    find_first_available_boe()
