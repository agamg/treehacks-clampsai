#!/bin/bash

# Function to create a new terminal window and run a command
create_terminal() {
    osascript -e "tell application \"Terminal\"
        do script \"cd $(pwd) && $1\"
    end tell"
}

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please create a .env file based on ENV_EXAMPLE.md"
    exit 1
fi

# Load environment variables
source .env

# Start ngrok first and wait for it to establish tunnels
if [ -f config/ngrok.yml ] && [ ! -z "$NGROK_AUTH_TOKEN" ]; then
    create_terminal "ngrok start --all --config ./config/ngrok.yml | tee logs/ngrok_output.log"
    sleep 5
    # Try to capture ngrok URL if available
    if [ -f logs/ngrok_output.log ]; then
        NGROK_URL=$(grep -i "url" logs/ngrok_output.log | grep ":8000" | awk '{print $8}' | head -1)
        if [ ! -z "$NGROK_URL" ]; then
            echo "Detected ngrok URL: $NGROK_URL"
            # Update OUTBOUND_URL in .env if ngrok is running
            sed -i '' "s|OUTBOUND_URL=.*|OUTBOUND_URL=$NGROK_URL|" .env
            source .env
        fi
    fi
fi

# Create videos directory if it doesn't exist
mkdir -p backend/videos

# Install Python requirements
if [ -d "backend" ]; then
    create_terminal "cd backend && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
fi

# Install Node.js dependencies for outbound server
if [ -f "backend/package.json" ]; then
    create_terminal "cd backend && npm install"
fi

# Start backend services
echo "Starting backend services..."

# Start video server
create_terminal "cd backend && source venv/bin/activate && source ../.env && python api/video_server.py"

# Start chat server  
create_terminal "cd backend && source venv/bin/activate && source ../.env && python api/chat_server.py"

# Start outbound call server
create_terminal "cd backend && source ../.env && node api/outbound_server.js"

echo "All services started. Check the terminal windows for status."
