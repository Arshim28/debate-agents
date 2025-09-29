import requests
import json 
import os
from dotenv import load_dotenv

class JinaSearchTool:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://s.jina.ai/?q={query}&gl=IN&hl=en"

    def _format_query(self, query):
        return query.replace(" ", "+")

    def search(self, query):
        headers = {
            'Accept': 'application/json',
            'Authorization': f'Bearer {self.api_key}',
            'X-Engine': 'browser',
            'X-Retain-Images': 'none'
        }
        url = self.base_url.format(query=self._format_query(query))
        print(url)

        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            return self._format_results(response.json())
        except requests.exceptions.RequestException as e:
            print(f"Jina API request failed: {e}")
            return []
        except Exception as e:
            print(f"Jina API error: {e}")
            return []
    
    def _format_results(self, results):
        response_json = []
        # Handle case where results is None or doesn't have expected structure
        if not results or "data" not in results or results["data"] is None:
            print("Warning: Jina API returned no data or unexpected format")
            return response_json

        for res in results["data"]:
            response_json.append({
                "title": res.get("title", ""),
                "url": res.get("url", ""),
                "description": res.get("description", ""),
                "content": res.get("content", ""),
                "publishedTime": res.get("publishedTime", ""),
            })
        return response_json
    
if __name__ == "__main__":
    load_dotenv()
    jina_search_tool = JinaSearchTool(api_key=os.getenv("JINA_API_KEY"))
    results = jina_search_tool.search("infosys latest news")
    with open("outputs/jina_search_results.json", "w", encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)