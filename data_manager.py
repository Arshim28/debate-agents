from openai import OpenAI
from connectors.indices_tracker import NiftyIndicesTracker
from connectors.youtube_connector import YouTubeConnector
from connectors.jina_web_connector import JinaSearchTool
from connectors.local_docs_connector import DataRetriever
import os
import json
from dotenv import load_dotenv

class DataManager:
    def __init__(self, open_router_api_key, youtube_api_key, jina_api_key, gemini_api_key, summary_collection_name="document_summary", chunk_collection_name="document_chunks"):
        self.llm_client = OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=open_router_api_key,
        )
        self.indices_connector = NiftyIndicesTracker()
        self.youtube_connector = YouTubeConnector(api_key=youtube_api_key)
        self.jina_connector = JinaSearchTool(api_key=jina_api_key)
        self.local_docs_connector = DataRetriever(summary_collection_name=summary_collection_name, chunk_collection_name=chunk_collection_name, gemini_api_key=gemini_api_key)

    def _route_query(self, query):
        system_prompt = """
        You are given an input question and certain tools to use that can be used to ansewer the question. Your job is to select the appropriate tool to use to answer the question. The answer could be more than one tool.

        Output format:
        It should be a json object of the following kind: 
        {{
            "tool_name1": {{
                "tool_args": {{
                    "tool_arg_name1": "tool_arg_value1",
                    "tool_arg_name2": "tool_arg_value2",
                    "tool_arg_name3": "tool_arg_value3"
                }}
            }},
            "tool_name2": {{
                "tool_args": {{
                    "tool_arg_name1": "tool_arg_value1",
                    "tool_arg_name2": "tool_arg_value2",
                    "tool_arg_name3": "tool_arg_value3"
                }}
            }}
        }}

        the response should only contain details of relevant tools

        AVAILABLE TOOLS:

        Indices Tracker:
        this is a tool that can be used to get the value of an index from a given start date to end date with a certain frequency. 
        Arguments:
        index_name: the name of the index to get the value of
        start_date: the start date to get the value of the index
        end_date: the end date to get the value of the index
        frequency: the frequency to get the value of the index this can take the following values daily, weekly, monthly, quaterly, yearly

        YouTube Connector:
        This is a tool that can be used to get the transcript of youtube videos. Use this tool whenb the query is about interviews or commenatries or news etc.
        Arguments:
        query: the query to search for youtube videos

        Jina Web Connector:
        This is a tool that can be used to get the web search results.
        Arguments:
        query: the query to search for web results


        You can respond with multiple tools in the same query.
        """
        
        response = self.llm_client.chat.completions.create(
            model="x-ai/grok-4-fast:free",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        
        # Check for errors in response
        if hasattr(response, 'error') and response.error:
            raise Exception(f"API Error: {response.error}")
            
        if not response.choices or len(response.choices) == 0:
            raise Exception("No response choices returned from API")
        
        return response.choices[0].message.content
        
    def filter_youtube_videos(self, videos, query):
        system_prompt = """
        you are given a list of youtube videos and a query. you need to filter the videos based on the query.

        the videos will have two fields title and video_id. Your job is to use the title of the video to judge the relevancy of the video to the given query and return the list of videos that are relevant to the query.

        while selecting the videos, never consider short videos.

        return the list of videos that are relevant to the query.
        dont include any other text in your response.
        Output format:
        {{
            "videos": [
                {{
                    "video_id": "video_id",
                    "title": "title"
                }}
            ]
        }}

        the output should be a json object with a "videos" key containing a list of video objects.
        """

        input_prompt = f"""
            Videos: {videos}
            Query: {query}
        """
        response = self.llm_client.chat.completions.create(
            model="x-ai/grok-4-fast:free",
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": input_prompt}],
            response_format={"type": "json_object"}
        )
        result = json.loads(response.choices[0].message.content)
        return result.get("videos", [])

    def search(self, query, tools=None):
        if tools:
            tool_selection_json = tools
        else:
            tool_selection_json = self._route_query(query)
        tool_selection = json.loads(tool_selection_json)
        
        result = {}
        for tool_name, tool_config in tool_selection.items():
            tool_args = tool_config.get("tool_args", {})
            tool_name_lower = tool_name.lower().replace(" ", "_")
            
            if tool_name_lower == "indices_tracker":
                result[tool_name] = self.indices_connector.get_data(**tool_args)
            elif tool_name_lower == "youtube_connector":
                videos = self.youtube_connector.video_search(**tool_args)
                filtered_videos = self.filter_youtube_videos(videos, query)
                transcript_dict = {}
                print(filtered_videos)
                for video in filtered_videos:
                    transcript_dict[video["title"]] = self.youtube_connector.get_transcript(video["video_id"])
                result[tool_name] = transcript_dict
            elif tool_name_lower == "jina_web_connector":
                result[tool_name] = self.jina_connector.search(**tool_args)
            else:
                raise ValueError(f"Invalid tool name: {tool_name}")
        
        result["RAG"] = self.local_docs_connector.retrieve(query)
        return result

if __name__ == "__main__":
    load_dotenv()
    data_manager = DataManager(open_router_api_key=os.getenv("OPEN_ROUTER_API_KEY"), youtube_api_key=os.getenv("YOUTUBE_API_KEY"), jina_api_key=os.getenv("JINA_API_KEY"), gemini_api_key=os.getenv("GEMINI_API_KEY"), summary_collection_name="document_summary", chunk_collection_name="document_chunks")
    
    # Test indices tracker
    # print("Testing Indices Tracker:")
    # result1 = data_manager.search("what is the value of nifty 50 from 2024-01-01 to 2024-01-05")
    # print(result1)
    # print()
    
    # # Test web search
    print("Testing Web Search:")
    result2 = data_manager.search("What has been the impact of AI on indian IT sector")
    with open("outputs/data_manager_results.json", "w", encoding='utf-8') as f:
        json.dump(result2, f, indent=4, ensure_ascii=False)
    print(result2)
    print()

    # youtube search
    # print("Testing Youtube Search:")
    # result3 = data_manager.search("what did analyst say in interviews about impact of changes in H1B regulations on indian IT sector")
    # print(result3)
        


        