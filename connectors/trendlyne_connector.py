import sys
import os
import json
import requests
import copy

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.trendlyne_company_token_extractor import TrendlyneCompanyTokenExtractor

class TrendlyneConnector:
    def __init__(self):
        self.company_token_extractor = TrendlyneCompanyTokenExtractor()
        self.base_url = "https://trendlyne.com/fundamentals/get-fundamental_results-v2/"

    def _get_company_fundamentals(self, stock_id=None, company_name=None):
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

    def _get_quarterly_financials(self, fundamentals_data, type="standalone"):
        #type = consolidated, standalone
        if type == "consolidated":
            data = fundamentals_data.get("body", {}).get("quarterlyDataDump", {}).get("consolidated", {})
            data_dict = {}
            for k, v in data.items():
                # Create a deep copy to avoid modifying original data
                v_copy = copy.deepcopy(v)
                v_copy.pop("earnings_transcripts", None)
                v_copy.pop("results_pdf", None)
                v_copy.pop("ai_summary", None)
                v_copy.pop("result_notes", None)
                data_dict[k] = v_copy
            return data_dict
        elif type == "standalone":
            data = fundamentals_data.get("body", {}).get("quarterlyDataDump", {}).get("standalone", {})
            data_dict = {}
            for k, v in data.items():
                # Create a deep copy to avoid modifying original data
                v_copy = copy.deepcopy(v)
                v_copy.pop("earnings_transcripts", None)
                v_copy.pop("results_pdf", None)
                v_copy.pop("ai_summary", None)
                v_copy.pop("result_notes", None)
                data_dict[k] = v_copy
            return data_dict
        else:
            raise ValueError("Invalid type")
    
    def _get_annual_financials(self, fundamentals_data, type="standalone"):
        #type = consolidated, standalone
        if type == "consolidated":
            data = fundamentals_data.get("body", {}).get("annualDataDump", {}).get("consolidated", {})
            data_dict = {}
            for k, v in data.items():
                # Create a deep copy to avoid modifying original data
                v_copy = copy.deepcopy(v)
                v_copy.pop("result_notes", None)
                v_copy.pop("Annual_Reports", None)
                data_dict[k] = v_copy
            return data_dict
        elif type == "standalone":
            data = fundamentals_data.get("body", {}).get("annualDataDump", {}).get("standalone", {})
            data_dict = {}
            for k, v in data.items():
                # Create a deep copy to avoid modifying original data
                v_copy = copy.deepcopy(v)
                v_copy.pop("result_notes", None)
                v_copy.pop("Annual_Reports", None)
                data_dict[k] = v_copy
            return data_dict
        else:
            raise ValueError("Invalid type")
    
    def _get_earnings_transcripts(self, fundamentals_data):
        quarterly_data = fundamentals_data.get("body", {}).get("quarterlyDataDump", {}).get("standalone", {})
        transcript_dict = {}
        for k, v in quarterly_data.items():
            earnings_transcripts = v.get("earnings_transcripts", {})
            values = earnings_transcripts.get("values", [])
            url = values[0].get("url", None) if values else None
            transcript_dict[k] = url
        return transcript_dict
    
    def _get_annual_reports(self, fundamentals_data):
        annual_data = fundamentals_data.get("body", {}).get("annualDataDump", {}).get("standalone", {})
        report_dict = {}
        for k, v in annual_data.items():
            annual_reports = v.get("Annual_Reports", {})
            document_url = annual_reports.get("document_url", None)
            report_dict[k] = document_url
        return report_dict
    
    def _get_peer_companies(self, fundamentals_data):
        peer_data = fundamentals_data.get("body", {}).get("pr", {}).get("table_data", [])
        peer_dict = {}
        for company in peer_data:
            # Create a deep copy to avoid modifying original data
            company_data = copy.deepcopy(company)
            stock_info = company.get("Stock", {})
            company_data["leader_flag"] = stock_info.get("leader_flag", None)
            company_data.pop("Stock", None)
            company_data.pop("Stock Compare", None)
            order_by = stock_info.get("order_by", f"company_{len(peer_dict)}")
            peer_dict[order_by] = company_data
        return peer_dict
    
    def get_info(self, stock_id=None, company_name=None, args=[]):
        """
        Get the info about company fundamentals and peers from trendlyne.
        supported strings in args:
        - peer_companies: get the peer companies of the company
        - quarterly_financials_consolidated: get the quarterly financials of the company in consolidated format. Consolidated means the financials of the company and its subsidiaries.
        - quarterly_financials_standalone: get the quarterly financials of the company in standalone format. Standalone means the financials of the company only.
        - annual_financials_consolidated: get the annual financials of the company in consolidated format. Consolidated means the financials of the company and its subsidiaries.
        - annual_financials_standalone: get the annual financials of the company in standalone format. Standalone means the financials of the company only.
        - earnings_transcripts: get link to the earnings transcripts of the company.
        - annual_reports: get link to the annual reports of the company.
        Args:
            stock_id: int
            company_name: str
            args: list of strings
        Returns:
            dict
        """
        fundamentals_data = self._get_company_fundamentals(stock_id, company_name)
        if "peer_companies" in args:
            peer_companies = self._get_peer_companies(fundamentals_data)
        if "quarterly_financials_consolidated" in args:
            quarterly_financials_consolidated = self._get_quarterly_financials(fundamentals_data, type="consolidated")
        if "annual_financials_consolidated" in args:
            annual_financials_consolidated = self._get_annual_financials(fundamentals_data, type="consolidated")
        if "quarterly_financials_standalone" in args:
            quarterly_financials_standalone = self._get_quarterly_financials(fundamentals_data, type="standalone")
        if "annual_financials_standalone" in args:
            annual_financials_standalone = self._get_annual_financials(fundamentals_data, type="standalone")
        if "earnings_transcripts" in args:
            earnings_transcripts = self._get_earnings_transcripts(fundamentals_data)
        if "annual_reports" in args:
            annual_reports = self._get_annual_reports(fundamentals_data)
        return {
            "peer_companies": peer_companies if "peer_companies" in args else None,
            "quarterly_financials_consolidated": quarterly_financials_consolidated if "quarterly_financials_consolidated" in args else None,
            "quarterly_financials_standalone": quarterly_financials_standalone if "quarterly_financials_standalone" in args else None,
            "annual_financials_consolidated": annual_financials_consolidated if "annual_financials_consolidated" in args else None,
            "annual_financials_standalone": annual_financials_standalone if "annual_financials_standalone" in args else None,
            "earnings_transcripts": earnings_transcripts if "earnings_transcripts" in args else None,
            "annual_reports": annual_reports if "annual_reports" in args else None
        }

if __name__ == "__main__": 
    connector = TrendlyneConnector()
    
    # result = connector.get_company_fundamentals(stock_id=1577)
    # print("Stock ID test:", "✓" if result else "✗")
    
    # result = connector.get_company_fundamentals(company_name="TCS")
    # with open("debug.json", "w") as f:
    #     json.dump(result, f, indent=4)
    # print("Company name test:", "✓" if result else "✗")
    # with open("debug.json", "r") as f:
    #     info_dict = json.load(f)
    
    # # peer companies
    # with open("peer_companies.json", "w") as f:
    #     json.dump(connector._get_peer_companies(info_dict), f, indent=4)
    
    # #quarterly financials consolidated 
    # with open("quarterly_financials_consolidated.json", "w") as f:
    #     json.dump(connector._get_quarterly_financials(info_dict, type="consolidated"), f, indent=4)
    
    # #quarterly financials standalone
    # with open("quarterly_financials_standalone.json", "w") as f:
    #     json.dump(connector._get_quarterly_financials(info_dict, type="standalone"), f, indent=4)
    
    # #annual financials consolidated
    # with open("annual_financials_consolidated.json", "w") as f:
    #     json.dump(connector._get_annual_financials(info_dict, type="consolidated"), f, indent=4)
    
    # #annual financials standalone
    # with open("annual_financials_standalone.json", "w") as f:
    #     json.dump(connector._get_annual_financials(info_dict, type="standalone"), f, indent=4)
    
    # #earnings transcripts
    # with open("earnings_transcripts.json", "w") as f:
    #     json.dump(connector._get_earnings_transcripts(info_dict), f, indent=4)
    
    # #annual reports
    # with open("annual_reports.json", "w") as f:
    #     json.dump(connector._get_annual_reports(info_dict), f, indent=4)

    with open("final.json", "w") as f:
        json.dump(connector.get_info(stock_id=1577, args=["peer_companies", "quarterly_financials_consolidated", "quarterly_financials_standalone", "annual_financials_consolidated", "annual_financials_standalone", "earnings_transcripts", "annual_reports"]), f, indent=4)
    
