from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi
import os
from dotenv import load_dotenv

class YouTubeConnector:
    def __init__(self, api_key):
        self.api_key = api_key
        self.youtube = build('youtube', 'v3', developerKey=self.api_key)
        self.transcript_api = YouTubeTranscriptApi()

    def video_search(self, query, max_results=15):
        search_response = self.youtube.search().list(
            q=query,
            part='snippet',
            maxResults=max_results,
            type='video',
            regionCode="IN",
            videoDuration="long"
        ).execute()
        videos = (search_response.get('items', []))
        video_list = []
        for item in videos:
            video_data = {
                'title': item['snippet']['title'],
                'video_id': item['id']['videoId'],
            }
            video_list.append(video_data)

        return video_list

    def get_transcript(self, video_id):
        try:
            transcript_dict = self.transcript_api.fetch(video_id)
            transcript = " ".join([t.text for t in transcript_dict])
            return transcript
        except Exception as e:
            return str(e)

if __name__ == "__main__":
    load_dotenv()
    youtube_tool = YouTubeConnector(api_key=os.getenv("YOUTUBE_API_KEY"))
    # videos = youtube_tool.video_search("impact of new H1B rules on infosys")
    # print(videos)
    transcript = youtube_tool.get_transcript("PDTF-xRvOwo")
    print(transcript)