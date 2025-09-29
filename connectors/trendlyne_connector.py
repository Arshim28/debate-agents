import sys
import os
import json
import requests

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.trendlyne_company_token_extractor import TrendlyneCompanyTokenExtractor

class TrendlyneConnector:
    def __init__(self):
        self.company_token_extractor = TrendlyneCompanyTokenExtractor()
        self.base_url = "https://trendlyne.com/fundamentals/get-fundamental_results-v2/"

    def get_company_fundamentals(self, stock_id=None, company_name=None):
        if not stock_id and not company_name:
            raise ValueError("Either stock_id or company_name must be provided")
        
        if company_name and not stock_id:
            company_match = self.company_token_extractor.get_company_id(company_name)
            if not company_match:
                return None
            matched_name, stock_id = company_match
        
        # Try cached token first
        company_token = self.company_token_extractor.get_company_token(stock_id, fetch_new=False)
        if not company_token:
            company_token = self.company_token_extractor.get_company_token(stock_id, fetch_new=True)
            if not company_token:
                return None
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://trendlyne.com/',
            'Origin': 'https://trendlyne.com'
        }
        
        # Try request with cached token
        url = f"{self.base_url}{stock_id}/{company_token}/"
        response = requests.get(url, headers=headers, timeout=30)
        
        # If cached token fails (403/401), try with fresh token
        if response.status_code in [401, 403, 404]:
            company_token = self.company_token_extractor.get_company_token(stock_id, fetch_new=True)
            if company_token:
                url = f"{self.base_url}{stock_id}/{company_token}/"
                response = requests.get(url, headers=headers, timeout=30)
        
        return response.json() if response.status_code == 200 else None

if __name__ == "__main__": 
    connector = TrendlyneConnector()
    
    result = connector.get_company_fundamentals(stock_id=1577)
    print("Stock ID test:", "✓" if result else "✗")
    
    result = connector.get_company_fundamentals(company_name="TCS")
    with open("debug.json", "w") as f:
        json.dump(result, f, indent=4)
    print("Company name test:", "✓" if result else "✗")
