import requests
import os
import json

URL = "https://trendlyne.com/"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36",
    "Accept": "*/*",
    "Accept-Language": "en-GB,en-US;q=0.9,en;q=0.8",
}

class TrendlyneCSRFExtractor:
    def __init__(self):
        self.headers = HEADERS
        self.url = URL
        self.config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "trendlyne_config.json")
        self.config = self._load_config()
    
    def _load_config(self):
        with open(self.config_path, "r") as f:
            return json.load(f)
    
    def extract_csrf_token(self, fetch_new=False):
        if fetch_new:
            print(f"Sending GET request to: {self.url} with custom headers...")
            response = requests.get(self.url, headers=self.headers, timeout=10)
            response.raise_for_status()
            cookies = response.cookies
            csrf_token_value = cookies.get('csrftoken')
            return csrf_token_value
        else:
            return self.config['csrf_token']


if __name__ == "__main__":
    extractor = TrendlyneCSRFExtractor()
    print(extractor.extract_csrf_token(fetch_new=True))