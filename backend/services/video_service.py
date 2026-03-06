"""Video processing service using Gemini."""
import os
import sys
import time
import json
from typing import Optional
from google import genai

# Add parent directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from config import Config


class VideoService:
    """Service for processing videos with Gemini."""
    
    def __init__(self):
        self.client = genai.Client(api_key=Config.GEMINI_API_KEY)
        self.videos = {}  # Cache for processed videos
    
    def process_video(self, video_path: str) -> Optional[any]:
        """Upload a video file to Gemini."""
        try:
            video_file = self.client.files.upload(file=video_path)
            time.sleep(8)  # Wait for processing
            return video_file
        except Exception as e:
            print(f"Error uploading video: {e}")
            return None
    
    def query_video(self, video_file, query_text: str) -> Optional[str]:
        """Query a video with specific text."""
        try:
            response = self.client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=[query_text, video_file]
            )
            return response.text
        except Exception as e:
            print(f"Error querying video: {e}")
            return None
    
    def analyze_video_threat(self, video_file) -> Optional[dict]:
        """Analyze video for threats and return structured response."""
        from pydantic import BaseModel
        
        class VideoAnalysis(BaseModel):
            threat: int
            description: str
        
        try:
            response = self.client.models.generate_content(
                model=Config.GEMINI_MODEL,
                contents=(
                    "Analyze the following 5-second video clip and output your response as a JSON object with two keys: "
                    "\"threat\" and \"description\". The \"threat\" key should be a binary variable where 1 indicates that the video "
                    "depicts a disturbing event (such as a robbery, theft, or violence) and 0 indicates otherwise. The "
                    "\"description\" key should contain a three-sentence narrative that vividly captures the events, detailing key "
                    "visual elements and conveying the overall mood with rich, descriptive language.",
                    video_file
                ),
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': VideoAnalysis,
                },
            )
            
            response_data = json.loads(response.text)
            return response_data
        except Exception as e:
            print(f"Error analyzing video threat: {e}")
            return None
