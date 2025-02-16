import os
import time
import threading
import cv2
from collections import deque
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from google import genai

# Flask app setup
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Gemini API setup
GOOGLE_CLIENT = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

# Video storage and context history
VIDEO_HISTORY = deque(maxlen=5)  # Store last 5 videos
VIDEO_DIR = "./video_streams"
os.makedirs(VIDEO_DIR, exist_ok=True)

# OpenCV setup
VIDEO_CAPTURE = cv2.VideoCapture(0)  # Use webcam (0 for default cam)


def process_video(chunk_path):
    """Uploads video to Gemini"""
    try:
        video_file = GOOGLE_CLIENT.files.upload(file=chunk_path)
        return video_file
    except Exception as e:
        print(f"Error uploading video: {e}")
        return None


def query_video(context_videos, query_text):
    """Queries videos with context"""
    try:
        contents = [query_text] + context_videos  # Combine past video history
        response = GOOGLE_CLIENT.models.generate_content(
            model="gemini-2.0-flash", contents=contents
        )
        return response.text
    except Exception as e:
        print(f"Error querying video: {e}")
        return None


def capture_and_upload():
    """Continuously captures 3-second video clips and uploads them"""
    while True:
        timestamp = int(time.time())
        video_path = os.path.join(VIDEO_DIR, f"clip_{timestamp}.mp4")
        
        print(f"Recording {video_path}...")
        
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        out = cv2.VideoWriter(video_path, fourcc, 10.0, (640, 480))
        
        start_time = time.time()
        while time.time() - start_time < 3:  # Record for 3 seconds
            ret, frame = VIDEO_CAPTURE.read()
            if not ret:
                print("Failed to capture frame")
                break
            out.write(frame)
        
        out.release()
        print(f"Saved {video_path}")
        
        video_file = process_video(video_path)
        if video_file:
            VIDEO_HISTORY.append(video_file)
            print(f"Uploaded {video_path}")
        
        time.sleep(3)  # Wait before capturing the next clip


@app.route("/query", methods=["POST"])
def query_endpoint():
    """Query the latest video context"""
    try:
        data = request.get_json()
        if not data or "query" not in data:
            return jsonify({"error": "Query text is required"}), 400

        query_text = data["query"]
        if not VIDEO_HISTORY:
            return jsonify({"error": "No videos available yet"}), 404

        result = query_video(list(VIDEO_HISTORY), query_text)
        return jsonify({"response": result}) if result else jsonify({"error": "Failed to process query"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@socketio.on("message")
def handle_message(data):
    """Handles real-time chat messages with video context"""
    query_text = data.get("query")
    
    if not query_text:
        emit("response", {"error": "Query text is required"})
        return

    if not VIDEO_HISTORY:
        emit("response", {"error": "No video context available yet"})
        return

    result = query_video(list(VIDEO_HISTORY), query_text)
    emit("response", {"response": result} if result else {"error": "Failed to process query"})


if __name__ == "__main__":
    # Start video capture in background
    threading.Thread(target=capture_and_upload, daemon=True).start()
    socketio.run(app, debug=True, port=3000, host="0.0.0.0")