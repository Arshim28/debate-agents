import json 
import requests
import re
import os
from difflib import SequenceMatcher 

class TrendlyneCompanyTokenExtractor:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.json_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "config", "trendlyne_db.json")
        self.companies_data = self._load_json_data()

    def _load_json_data(self):
        try:
            with open(self.json_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"JSON file not found: {self.json_path}")
            return {}
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON file: {e}")
            return {}

    def _save_json_data(self):
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.companies_data, f, indent=2, ensure_ascii=False)
            print(f"Updated data saved to {self.json_path}")
        except Exception as e:
            print(f"Error saving JSON file: {e}")

    def _extract_token_from_equity_page(self, equity_url, stock_id):
        try:
            print("Extracting token from equity page: ", equity_url)
            response = self.session.get(equity_url)
            if response.status_code != 200:
                return None

            html = response.text
            # Method 1: Look for OHLC API calls in JavaScript
            ohlc_pattern = r'/mapp/v1/stock/web/ohlc/(\d+)/([A-Z0-9+=]+)/'
            ohlc_matches = re.findall(ohlc_pattern, html)

            if ohlc_matches:
                for match_stock_id, token in ohlc_matches:
                    if match_stock_id == str(stock_id):
                        return token

            # Method 2: Look for any token patterns in the page
            token_pattern = r'([A-Z0-9]{20,32}={0,6})'
            token_candidates = re.findall(token_pattern, html)
            for candidate in token_candidates:
                if len(candidate) >= 30 and candidate.endswith('='):
                    if candidate not in html[:1000]:
                        return candidate
        
        except requests.exceptions.RequestException as e:
            print("Request error: ", e)
            return None
        except Exception as e:
            print("Unexpected error: ", e)
            return None
    
    def _test_token(self, stock_id, token, symbol):
        base_url = "https://trendlyne.com"
        referer = f"https://trendlyne.com/equity/{stock_id}/{symbol}/test/"

        headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Accept': '*/*',
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest',
            'Referer': referer,
            'DNT': '1',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'same-origin'
        }

        try:
            fund_url = f"{base_url}/fundamentals/get-fundamental_results-v2/{stock_id}/{token}/"
            response = self.session.get(fund_url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return bool(data.get('body'))
        except Exception as e:
            print("Unexpected error: ", e)
            return False
    
    def get_company_token(self, stock_id, fetch_new=False):
        stock_id_str = str(stock_id)
        
        if not fetch_new:
            # Get cached token from JSON data
            if stock_id_str in self.companies_data:
                return self.companies_data[stock_id_str].get('trendlyne_auth_token')
            else:
                return None
        else:
            # Fetch new token
            if stock_id_str in self.companies_data:
                equity_url = self.companies_data[stock_id_str].get('trendlyne_equity_url')
                if equity_url:
                    token = self._extract_token_from_equity_page(equity_url, stock_id)
                    print(f"Extracted token: {token}")
                    if token:
                        self._update_company_token(stock_id, token)
                        return token
                    else:
                        return None
                else:
                    return None
            else:
                return None
    
    def get_company_equity_url(self, stock_id):
        stock_id_str = str(stock_id)
        if stock_id_str in self.companies_data:
            return self.companies_data[stock_id_str].get('trendlyne_equity_url')
        else:
            return None
    
    def _get_company_name_id_from_db(self):
        result = []
        for stock_id, company_data in self.companies_data.items():
            company_name = company_data.get('company_name')
            if company_name:
                result.append((company_name, int(stock_id)))
        return result

    def _find_best_match(self, company_name_id_list, company_name):
        if not company_name_id_list or not company_name:
            return None
            
        best_match = None
        best_ratio = 0.0
        min_threshold = 0.6  
        normalized_input = company_name.lower().strip()
        
        for db_company_name, company_id in company_name_id_list:
            if not db_company_name:
                continue
                
            normalized_db_name = db_company_name.lower().strip()
            ratio = SequenceMatcher(None, normalized_input, normalized_db_name).ratio()
            
            if normalized_input in normalized_db_name or normalized_db_name in normalized_input:
                ratio = max(ratio, 0.8)  
            
            if ratio > best_ratio and ratio >= min_threshold:
                best_ratio = ratio
                best_match = (db_company_name, company_id)
        
        return best_match
        
    def get_company_id(self, company_name):
        company_name_id_list = self._get_company_name_id_from_db()
        if not company_name_id_list:
            print("No companies found in database")
            return None
        
        best_match = self._find_best_match(company_name_id_list, company_name)
        
        if best_match:
            matched_name, company_id = best_match
            print(f"Found match: '{company_name}' -> '{matched_name}' (ID: {company_id})")
            return best_match
        else:
            print(f"No suitable match found for company: '{company_name}'")
            return None
        
    def _update_company_token(self, stock_id, token):
        if token is None:
            return False
        
        stock_id_str = str(stock_id)
        if stock_id_str in self.companies_data:
            self.companies_data[stock_id_str]['trendlyne_auth_token'] = token
            self._save_json_data()  
            return True
        else:
            print(f"Company ID {stock_id} not found in data")
            return False
    
if __name__ == "__main__":
    # symbol="MOLDTKPAC"
    # token="YOQX2UIPDLN4NJHC6G4WQWB5G4======"
    extractor = TrendlyneCompanyTokenExtractor()
    # print(extractor.get_company_token(1577))
    # print(extractor._test_token(1577, token, symbol))
    # print(extractor.get_company_equity_url(1577))
    
    # Test the new get_company_id function
    # test_companies = ["TCS", "Infosys", "Wipro", "Tata Consultancy Services"]
    # for company in test_companies:
    #     result = extractor.get_company_id(company)
    #     if result:
    #         matched_name, company_id = result
    #         print(f"'{company}' matched to '{matched_name}' with ID: {company_id}")
    #     else:
    #         print(f"No match found for '{company}'")
    
    matched_name, company_id = extractor.get_company_id("wipro")
    print(f"Company ID: {company_id}")
    old_token = extractor.get_company_token(company_id, fetch_new=False)
    print(f"Old token: {old_token}")
    token = extractor.get_company_token(company_id, fetch_new=True)
    print(f"New token: {token}")
    token = extractor.get_company_token(company_id, fetch_new=False)
    print(f"Cached token: {token}")
    
    # # Explicitly save data
    # extractor.save_data()
    # print("Test completed successfully!")