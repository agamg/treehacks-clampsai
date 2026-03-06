"""Flask server for video processing endpoints."""
import os
import sys
import time
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add parent directory to path for imports
backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, backend_dir)
from config import Config
from services.video_service import VideoService
from services.call_service import CallService

Config.validate()

app = Flask(__name__)
CORS(app)

video_service = VideoService()
call_service = CallService()


def ensure_directory(directory: str):
    """Create directory if it doesn't exist."""
    if not os.path.exists(directory):
        os.makedirs(directory)


@app.route('/upsert', methods=['POST'])
def upsert_video():
    """Upsert a video file."""
    start_time = time.time()
    try:
        data = request.get_json()
        if 'video_path' not in data:
            return jsonify({'error': 'video_path is required'}), 400

        video_path = data['video_path']
        
        # Check if video is already processed
        if video_path in video_service.videos:
            return jsonify({
                'message': 'Video already processed',
                'timing': {
                    'total_duration': round(time.time() - start_time, 2)
                }
            }), 200

        video_file = video_service.process_video(video_path)

        if video_file:
            video_service.videos[video_path] = video_file
            total_duration = time.time() - start_time
            return jsonify({
                'message': 'Video upserted successfully',
                'timing': {
                    'total_duration': round(total_duration, 2)
                }
            }), 200
        else:
            return jsonify({'error': 'Failed to upsert video'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/init', methods=['POST'])
def init_videos():
    """Initialize by loading all videos from the videos directory."""
    try:
        videos_dir = Config.VIDEOS_DIR
        if not os.path.exists(videos_dir):
            return jsonify({'error': 'Videos directory not found'}), 404

        loaded_videos = []
        failed_videos = []

        # Clear existing videos
        video_service.videos.clear()
        
        # Load all videos
        for filename in os.listdir(videos_dir):
            if filename.endswith(('.mp4', '.webm', '.avi')):
                video_path = os.path.join(videos_dir, filename)
                
                video_file = video_service.process_video(video_path)
                if video_file:
                    video_service.videos[filename] = video_file
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
    """Query a preloaded video with custom text."""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'query is required'}), 400

        query = data['query']
        
        # Get the most recent video uploaded
        if not video_service.videos:
            return jsonify({'error': 'No videos available. Call /init first'}), 404

        video_name = list(video_service.videos.keys())[-1]
        video_file = video_service.videos[video_name]

        result = video_service.query_video(video_file, query)

        if result:
            return jsonify({'response': result})
        else:
            return jsonify({'error': 'Failed to process query'}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/process', methods=['POST'])
def process_endpoint():
    """API endpoint to process a video file."""
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
        if video_path not in video_service.videos:
            process_start = time.time()
            video_file = video_service.process_video(video_path)
            process_duration = time.time() - process_start
            if video_file:
                video_service.videos[video_path] = video_file
            else:
                return jsonify({'error': 'Failed to process video'}), 500
        else:
            video_file = video_service.videos[video_path]
            process_duration = 0  # Video was already processed

        query_start = time.time()
        result = video_service.query_video(video_file, query)
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


@app.route("/save-video", methods=['POST'])
def save_video():
    """Save and analyze an uploaded video."""
    try:
        if 'video' not in request.files:
            return jsonify({'error': 'No video file in request'}), 400
            
        video = request.files['video']
        if video.filename == '':
            return jsonify({'error': 'No selected file'}), 400

        # Create storage directory if it doesn't exist
        storage_dir = os.path.abspath(Config.VIDEOS_DIR)
        ensure_directory(storage_dir)

        # Use the original filename or generate a timestamp-based name
        filename = video.filename or f'recording-{int(time.time())}.webm'
        file_path = os.path.join(storage_dir, filename)

        # Save the uploaded file
        video.save(file_path)
        
        # Process video
        video_file = video_service.process_video(file_path)
        if video_file:
            video_service.videos[file_path] = video_file
            
            # Analyze for threats
            gemini_response = video_service.analyze_video_threat(video_file)
            
            # If threat detected, make emergency call
            if gemini_response and gemini_response.get('threat') == 1:
                description = gemini_response.get('description', '')
                call_service.make_outbound_call(description)
                print(f"Threat detected: {description}")

        return jsonify({
            "gemini_response": gemini_response,
            "message": "Video saved successfully",
            "path": file_path,
            "filename": filename
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=Config.VIDEO_SERVER_PORT, host='0.0.0.0')
