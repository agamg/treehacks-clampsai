"""Service for making outbound calls via Twilio."""
from typing import Optional
import requests
import sys
import os

# Add parent directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from config import Config


class CallService:
    """Service for initiating emergency calls."""
    
    @staticmethod
    def make_outbound_call(description: str, phone_number: str = None) -> Optional[dict]:
        """Make an outbound call with the given description."""
        url = f"{Config.OUTBOUND_URL}/outbound-call"
        headers = {"Content-Type": "application/json"}
        payload = {
            "prompt": "You are calling emergency services. Be short and responsive, you are on the phone the whole time so you are only talking to the emergency responder",
            "first_message": description,
            "number": phone_number or "7377810940"  # Default emergency number
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"Error making outbound call: {e}")
            return None
