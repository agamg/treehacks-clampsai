"""Configuration management for the backend."""
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Application configuration."""
    
    # API Keys
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
    ELEVENLABS_AGENT_ID = os.getenv("ELEVENLABS_AGENT_ID")
    
    # Twilio Configuration
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")
    
    # Server Configuration
    VIDEO_SERVER_PORT = int(os.getenv("VIDEO_SERVER_PORT", "5002"))
    CHAT_SERVER_PORT = int(os.getenv("CHAT_SERVER_PORT", "8013"))
    OUTBOUND_SERVER_PORT = int(os.getenv("OUTBOUND_SERVER_PORT", "8000"))
    OUTBOUND_URL = os.getenv("OUTBOUND_URL", f"http://localhost:{OUTBOUND_SERVER_PORT}")
    
    # Directories
    VIDEOS_DIR = os.getenv("VIDEOS_DIR", "./videos")
    VIDEO_STREAMS_DIR = os.getenv("VIDEO_STREAMS_DIR", "./video_streams")
    
    # Model Configuration
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
    
    @classmethod
    def validate(cls):
        """Validate that all required configuration is present."""
        required_vars = [
            "GEMINI_API_KEY",
            "TWILIO_ACCOUNT_SID",
            "TWILIO_AUTH_TOKEN",
            "TWILIO_PHONE_NUMBER",
        ]
        missing = [var for var in required_vars if not getattr(cls, var)]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
