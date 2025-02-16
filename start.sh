#!/bin/bash

# Function to create a new terminal window and run a command
create_terminal() {
    osascript -e "tell application \"Terminal\"
        do script \"cd $(pwd) && $1\"
    end tell"
}

# Start ngrok first and wait for it to establish tunnels
create_terminal "ngrok start --all --config ./ngrok.yml | tee ngrok_output.log"

# Wait for ngrok to start and capture the URL
sleep 5
NGROK_URL=$(grep -i "url" ngrok_output.log | grep ":8000" | awk '{print $8}')

# Create .env file with all environment variables
cat > .env << EOL
OUTBOUND_URL=$NGROK_URL
GEMINI_API_KEY=AIzaSyB8vu1G5YfHzZw1CkfAHLfFJij81RVthE8
ELEVENLABS_AGENT_ID="0ojjFGcL4FqEZ1hUWuqi"
ELEVENLABS_API_KEY="sk_9f678c37ce932d9d71c81c0210436960817199da8b7dc900"

# Twilio
TWILIO_ACCOUNT_SID="AC6d5c7046005e5afc8e3c92bfebd1ec89"
TWILIO_AUTH_TOKEN="07f3fc2bbba85eb3905da8ba3711c22f"
TWILIO_PHONE_NUMBER="+14435896273"
EOL

# Install Python requirements
create_terminal "source clamps-backend/venv/bin/activate && pip install -r clamps-backend/requirements.txt && pip install fastapi"

# Create terminals for each command with the environment variable
create_terminal "yes | rm -rf clamps-backend/videos/* && echo 'Videos cleared'"
create_terminal "source clamps-backend/venv/bin/activate && source .env && pip install -r clamps-backend/requirements.txt && pip install fastapi && python clamps-backend/main.py"
create_terminal "source clamps-backend/venv/bin/activate && source .env && pip install -r clamps-backend/requirements.txt && pip install fastapi && python clamps-backend/server.py"
create_terminal "source .env && node outbound.js"

echo "Environment variables have been set up in .env file"
