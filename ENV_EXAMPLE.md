# Environment Variables

Copy this to `.env` in the root directory:

```bash
# API Keys
GEMINI_API_KEY=your_gemini_api_key_here
GROQ_API_KEY=your_groq_api_key_here
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here
ELEVENLABS_AGENT_ID=your_elevenlabs_agent_id_here

# Twilio Configuration
TWILIO_ACCOUNT_SID=your_twilio_account_sid_here
TWILIO_AUTH_TOKEN=your_twilio_auth_token_here
TWILIO_PHONE_NUMBER=your_twilio_phone_number_here

# Server Configuration
VIDEO_SERVER_PORT=5002
CHAT_SERVER_PORT=8013
OUTBOUND_SERVER_PORT=8000
OUTBOUND_URL=http://localhost:8000

# Directories
VIDEOS_DIR=./videos
VIDEO_STREAMS_DIR=./video_streams

# Model Configuration
GEMINI_MODEL=gemini-2.0-flash
GROQ_MODEL=llama-3.3-70b-versatile

# Ngrok Configuration (optional - for exposing servers publicly)
NGROK_AUTH_TOKEN=your_ngrok_auth_token_here
```

**Note:** If using ngrok, also copy `config/ngrok.yml.example` to `config/ngrok.yml` and add your ngrok auth token there.
