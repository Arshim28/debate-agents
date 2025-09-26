from google import genai
from google.genai import types
from pydantic import BaseModel
import json

class CompanyOverviewSchema(BaseModel):
    company_description: str
    domain: str
    closest_nifty_sectoral_index: str

class CompanyOverview:
    def __init__(self, gemini_api_key):
        self.gemini_api_key = gemini_api_key
        self.gemini_client = genai.Client(api_key=gemini_api_key)
        self.permisible_indexes = ["Nifty Auto", "Nifty Bank", "Nifty Energy", "Nifty Financial Services", "Nifty FMCG", "Nifty IT", "Nifty Media", "Nifty Metal", "Nifty MNC", "Nifty Pharma", "Nifty PSU Bank", "Nifty Realty", "Nifty India Consumption", "Nifty Commodities", "Nifty Dividend Opportunities 50", "Nifty Infrastructure", "Nifty PSE", "Nifty Services Sector", "Nifty India Infrastructure & Logistics", "Nifty Private Bank", "NIFTY SME EMERGE", "Nifty Oil & Gas", "Nifty Financial Services 25/50", "Nifty Healthcare Index", "Nifty Mobility", "Nifty India Defence", "Nifty Financial Services Ex-Bank", "Nifty Housing", "Nifty Transportation & Logistics", "Nifty MidSmall Financial Services", "Nifty MidSmall Healthcare", "Nifty MidSmall IT & Telecom", "Nifty MidSmall India Consumption", "Nifty REITs & InvITs", "Nifty Core Housing", "Nifty Rural", "Nifty Capital Markets", "Nifty India New Age Consumption", "Nifty India Railways PSU", "Nifty Consumer Durables", "Nifty Non-Cyclical Consumer", "Nifty EV & New Age Automotive", "Nifty India Tourism", "Nifty India Internet", "Nifty Chemicals"]
    
    def _get_company_domain(self, company_name):
        input_prompt = f"""
        Use Google Search to find reliable information about {company_name}. Based on the results, provide:
        A short 2–3 sentence description of {company_name} and the domain in which it operates (example: automobile manufacturing, pharmaceuticals, banking, consumer goods, etc.).
        From the following list of sectoral indices, identify the single most relevant index that best corresponds to {company_name}’s operations: {self.permisible_indexes}

        Answer in this format:
        {{
            "company_description": "short description",
            "domain": "domain in simple terms",
            "closest_nifty_sectoral_index": "index name"
        }}

        The returned json should be valid json and should only contain the json object and nothing else.
        """
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=input_prompt,
            config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )
        )
        return self._response_loader(response, type="json")

    def _get_buisness_model(self, company_name):
        input_prompt = f"""
        Use Google Search to gather reliable information about {company_name}. Based on the results, provide a short text response that clearly answers the following three points:
            -Core business activities and main products or services offered
            - Primary customer segments and markets served (domestic or global)
            -Key revenue streams (how the company makes money)
        Answer in plain text with separate sections for each point.
        Return just the text response and nothing else.
        """
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=input_prompt,
            config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )
        )
        return response.text
    
    def _response_loader(self, response, type="json"):
        if type == "json":
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse JSON from response: {response.text}")
        elif type == "list":
            try:
                return json.loads(response.text)
            except json.JSONDecodeError:
                import re
                json_match = re.search(r'\[.*\]', response.text, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
                else:
                    raise ValueError(f"Could not parse JSON list from response: {response.text}")
        else:
            raise ValueError(f"Invalid type: {type}")
            
    def _get_listed_peers(self, company_name):
        input_prompt = f"""
        Use Google Search to identify up to 5 companies listed on Indian stock exchanges (NSE or BSE) that are competitors or peers of {company_name}. Focus only on companies that operate in the same domain or industry as {company_name}.

        Return the output strictly as a list of strings with company names only. If fewer than 5 relevant Indian listed competitors exist, return only those that are available.

        Example output:
        ["Company A", "Company B", "Company C"]

        The output must be a valid list and nothing else.
        """
        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=input_prompt,
            config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )
        )
        return self._response_loader(response, type="list")
        
    def _get_subsidaries(self, company_name):
        input_prompt = f"""
        Use Google Search to gather reliable information about {company_name} and its subsidiaries 
        (including associate companies, joint ventures, or acquired entities if relevant). 
        Collect details such as company name, dba/brand name (if any), business focus.

        Return the final answer strictly in the following JSON format:

        {{
            "parent_company": {{
                "name": "[Full legal name of parent company]",
                "dba": "[Commonly known as / trade name if any, else omit]",
                "focus": "[Brief 1–2 line description of the parent company’s primary focus]"
            }},
            "subsidiaries": [
                {{
                    "name": "[Subsidiary legal name]",
                    "dba": "[Commonly known as / trade name if any, else omit]",
                    "focus": "[Brief 1–2 line description of business focus]"
                }}
            ]
        }}

        If no subsidiaries are found, return an empty json object: {{}}

        The response must be a valid json and nothing else.
        If the company name is not found, return an empty json object: {{}}
        """

        grounding_tool = types.Tool(
            google_search=types.GoogleSearch()
        )
        response = self.gemini_client.models.generate_content(
            model="gemini-2.5-flash",
            contents=input_prompt,
            config = types.GenerateContentConfig(
                tools=[grounding_tool]
            )
        )
        return self._response_loader(response, type="json")

    def get_overview(self, company_name):
        company_domain = self._get_company_domain(company_name)
        buisness_model = self._get_buisness_model(company_name)
        listed_peers = self._get_listed_peers(company_name)
        subsidiaries = self._get_subsidaries(company_name)
        return {
            "company_domain": company_domain,
            "buisness_model": buisness_model,
            "listed_peers": listed_peers,
            "subsidiaries": subsidiaries
        }

if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    company_overview = CompanyOverview(gemini_api_key=os.getenv("GEMINI_API_KEY"))
    print(company_overview.get_overview("ZETWERK MANUFACTURING BUSINESSES PRIVATE LIMITED"))


    
    
    
    