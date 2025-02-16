import os
import time
import ffmpeg  # Keep if needed
from google import genai  # Adjust import if necessary (e.g., "import google.generativeai as genai")
from flask import Flask, request, jsonify
from flask_cors import CORS
import base64  # Keep if needed
from pydantic import BaseModel
import requests
import json
import typing

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
GOOGLE_CLIENT = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
GOOGLE_SUMMARY_CLIENT = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

class VideoAnalysis(BaseModel):
    threat: int
    description: str




# Store preloaded videos
VIDEOS = {}

def process_video(chunk_path):
    """Upload a video file to Gemini"""
    global GOOGLE_CLIENT

    try:
        video_file = GOOGLE_CLIENT.files.upload(file=chunk_path)
        time.sleep(8)
        return video_file  # Fixed: return the correct variable
    except Exception as e:
        print(f"Error uploading video: {e}")
        return None

def query_video(video_file, query_text):
    """Query a video with specific text"""
    try:
        response = GOOGLE_CLIENT.models.generate_content(
            model='gemini-2.0-flash',
            contents=[
                query_text,
                video_file
            ]
        )
        return response.text
    except Exception as e:
        print(f"Error querying video: {e}")
        return None

@app.route('/upsert', methods=['POST'])
def upsert_video():
    """
    Upsert a video file.
    Expects in JSON body:
    - video_path: path to the video file
    """
    start_time = time.time()
    try:
        data = request.get_json()
        if 'video_path' not in data:
            return jsonify({'error': 'video_path is required'}), 400

        video_path = data['video_path']
        
        # Check if video is already processed
        if video_path in VIDEOS:
            return jsonify({
                'message': 'Video already processed',
                'timing': {
                    'total_duration': round(time.time() - start_time, 2)
                }
            }), 200

        video_file = process_video(video_path)

        if video_file:
            # Store the processed video
            VIDEOS[video_path] = video_file
            total_duration = time.time() - start_time
            return jsonify({
                'message': 'Video upserted successfully',
                'timing': {
                    'process_duration': round(process_duration, 2),
                    'total_duration': round(total_duration, 2)
                }
            }), 200
        else:
            return jsonify({'error': 'Failed to upsert video'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/init', methods=['POST'])
def init_videos():
    """
    Initialize by loading all videos from the videos directory.
    Returns the list of successfully loaded videos.
    """
    try:
        videos_dir = './videos'
        if not os.path.exists(videos_dir):
            return jsonify({'error': 'Videos directory not found'}), 404

        loaded_videos = []
        failed_videos = []

        # Clear existing videos
        VIDEOS.clear()
        
        # Load all videos
        for filename in os.listdir(videos_dir):
            if filename.endswith(('.mp4', '.webm', '.avi')):
                video_path = os.path.join(videos_dir, filename)
                
                video_file = process_video(video_path)
                if video_file:
                    VIDEOS[filename] = video_file
                    loaded_videos.append(filename)
                else:
                    failed_videos.append(filename)

        return jsonify({
            'message': 'Videos initialized',
            'loaded_videos': loaded_videos,
            'failed_videos': failed_videos
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/query', methods=['POST'])
def query_endpoint():
    """
    Query a preloaded video with custom text.
    Expects in JSON body:
    - video_name: name of the preloaded video
    - query: text to ask about the video
    """
    try:
        data = request.get_json()
        # if not data or 'video_name' not in data or 'query' not in data:
        #     return jsonify({'error': 'video_name and query are required'}), 400

        # video_name = data['video_name']
        # get the most recent video uploaded (the video names willbe 1.webm, 2.webm, 3.webm, ...)

        video_name = list(VIDEOS.keys())[-1]

        query = data['query']

        if video_name not in VIDEOS:
            return jsonify({'error': f'Video {video_name} not found. Call /init first'}), 404

        result = query_video(VIDEOS[video_name], query)


        if result:
            return jsonify({'response': result})
        else:
            return jsonify({'error': 'Failed to process query'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/process', methods=['POST'])
def process_endpoint():
    """
    API endpoint to process a video file.
    Expects: 
    - video_path: path to the video file
    - query: optional custom query for the video (default is to describe what's on screen)
    """
    start_time = time.time()
    try:
        data = request.get_json()
        if 'video_path' not in data:
            return jsonify({'error': 'video_path is required'}), 400

        video_path = data['video_path']
        if not os.path.exists(video_path):
            return jsonify({'error': f'Video file not found at {video_path}'}), 404

        query = data.get('query', 'Tell me with detail what you see on the screen:')

        # Use cached video if available
        if video_path not in VIDEOS:
            process_start = time.time()
            video_file = process_video(video_path)
            process_duration = time.time() - process_start
            if video_file:
                VIDEOS[video_path] = video_file
            else:
                return jsonify({'error': 'Failed to process video'}), 500
        else:
            video_file = VIDEOS[video_path]
            process_duration = 0  # Video was already processed

        query_start = time.time()
        result = query_video(video_file, query)
        query_duration = time.time() - query_start
        
        if result:
            total_duration = time.time() - start_time
            return jsonify({
                'response': result,
                'timing': {
                    'process_duration': round(process_duration, 2),
                    'query_duration': round(query_duration, 2),
                    'total_duration': round(total_duration, 2),
                    'used_cache': process_duration == 0
                }
            })
        else:
            return jsonify({'error': 'Failed to process query'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


def gemini_call(video_file): 
    """Query a video with specific text"""
    try:
        response = GOOGLE_CLIENT.models.generate_content(
            model='gemini-2.0-flash',
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

        print("RAW GEMINI RESPONSE:", response.text)
        # Parse the response text as JSON
        response_data = json.loads(response.text)
        print("Parsed JSON:", response_data)
        
        threat_bool = response_data.get('threat')
        if threat_bool == 1:
            description = response_data.get('description')
            print("Threat detected:", description)
            make_outbound_call(description)
            
        return response.text
    except Exception as e:
        print(f"Error generating gemini video summary: {e}")
        return None


def ensure_directory(directory):
    """Create directory if it doesn't exist"""
    if not os.path.exists(directory):
        os.makedirs(directory)

def make_outbound_call(response_text):
    url = "https://ccfc-152-44-224-90.ngrok-free.app/outbound-call" #os.getenv('OUTBOUND_URL', 'http://localhost:8000/outbound-call')
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "prompt": "You are calling emergency services. Be short and responsive, you are on the phone the whole time so you are only talking to the emergency responder",
        "first_message": response_text,
        "number": "7377810940"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error making outbound call: {e}")
        return None

@app.route("/save-video", methods=['POST'])
def save_video():
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file in request'}), 400
            
        video = request.files['video']
        if video.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Create storage directory if it doesn't exist
        storage_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'videos'))
        ensure_directory(storage_dir)

        # Use the original filename or generate a timestamp-based name
        filename = video.filename or f'recording-{int(time.time())}.webm'
        file_path = os.path.join(storage_dir, filename)

        # Save the uploaded file
        video.save(file_path)
        
        video_file = process_video(file_path)
        if video_file:
            # Store the processed video
            VIDEOS[file_path] = video_file
            #VIDEOS.append(file_path)
            gemini_response = gemini_call(video_file)
            print("Gemini call done")
            print(gemini_response)

        return jsonify({
            "gemini_response": gemini_response,
            "message": "Video saved successfully",
            "path": file_path,
            "filename": filename
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    # Allow connections from any IP
    app.run(debug=True, port=5002, host='0.0.0.0')
