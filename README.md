# ClampsAI

A real-time security monitoring system that uses AI to analyze video feeds and automatically alert emergency services when threats are detected.

## What It Does

ClampsAI continuously monitors video feeds from security cameras, analyzing each 5-second video chunk for potential threats. When a threat is detected (robbery, theft, violence, etc.), the system automatically places an emergency call to alert authorities with a detailed description of what was observed.

## How It Works

### System Architecture

```mermaid
graph TB
    subgraph Frontend["Frontend"]
        UI[Web Application]
        Camera[Multi-camera Video Feeds]
        Recorder[MediaRecorder API]
    end
    
    subgraph Backend["Backend Services"]
        subgraph VideoServer["Video Server (Flask :5002)"]
            VS_API[API Endpoints]
            VS_Service[VideoService]
        end
        
        subgraph ChatServer["Chat Server (FastAPI :8013)"]
            CS_API[Chat Completions API]
        end
        
        subgraph OutboundServer["Outbound Server (Node.js :8000)"]
            OS_API[Outbound Call API]
            OS_WS[WebSocket Handler]
        end
    end
    
    subgraph External["External Services"]
        Gemini[Gemini API<br/>Video Analysis]
        Twilio[Twilio API<br/>Voice Calls]
        ElevenLabs[ElevenLabs<br/>Conversational AI]
    end
    
    UI --> Camera
    Camera --> Recorder
    Recorder -->|POST /save-video| VS_API
    VS_API --> VS_Service
    VS_Service -->|Upload & Analyze| Gemini
    VS_Service -->|Threat Detected| OS_API
    OS_API -->|Initiate Call| Twilio
    Twilio -->|WebSocket Stream| OS_WS
    OS_WS -->|Connect| ElevenLabs
    UI -->|POST /chat/completions| CS_API
    CS_API -->|Query Context| VS_API
    VS_API -->|Get Analysis| Gemini
```

### Video Monitoring & Threat Detection Flow

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant VideoServer
    participant VideoService
    participant Gemini
    
    User->>Frontend: Click "Monitor Security Feeds"
    Frontend->>Frontend: Start MediaRecorder
    loop Every 5 seconds
        Frontend->>Frontend: Record video chunk
        Frontend->>VideoServer: POST /save-video (FormData)
        VideoServer->>VideoServer: Save to ./videos/
        VideoServer->>VideoService: process_video(file_path)
        VideoService->>Gemini: Upload video file
        Gemini-->>VideoService: video_file object
        VideoService->>VideoService: Cache video_file
        VideoService->>Gemini: analyze_video_threat(video_file)
        Note over Gemini: Analyze video clip<br/>Return JSON with:<br/>- threat: 0 or 1<br/>- description: narrative
        Gemini-->>VideoService: {threat: 1, description: "..."}
        alt Threat Detected
            VideoService->>VideoService: make_outbound_call(description)
        end
        VideoService-->>VideoServer: gemini_response
        VideoServer-->>Frontend: JSON response
        Frontend->>Frontend: Display incident card
    end
```

### Emergency Response System

When a threat is detected, the system automatically initiates an emergency call:

```mermaid
flowchart TD
    Start[Video Chunk Uploaded] --> Analyze[Gemini Video Analysis]
    Analyze --> Check{Threat Level?}
    
    Check -->|Threat = 0| NoThreat[Return Normal Response]
    NoThreat --> Display1[Frontend: Green Card]
    
    Check -->|Threat = 1| ThreatDetected[Threat Detected!]
    ThreatDetected --> CallService[CallService.make_outbound_call]
    
    CallService --> PostCall[POST /outbound-call<br/>Outbound Server]
    PostCall --> TwilioCall[Twilio API: Create Call]
    TwilioCall --> TwiML[TwiML Response<br/>WebSocket Stream URL]
    TwiML --> WSConnect[WebSocket Connection<br/>/outbound-media-stream]
    WSConnect --> ElevenLabs[Connect to ElevenLabs<br/>Conversational AI]
    ElevenLabs --> Agent[AI Agent Speaks<br/>Threat Description]
    Agent --> Emergency[Emergency Services<br/>Receives Automated Call]
    
    style ThreatDetected fill:#ff6b6b
    style Emergency fill:#51cf66
```

The AI agent speaks directly to emergency responders, providing a detailed description of the threat detected in the video.

### Chat Interface with Video Context

Users can query the system about what it has observed:

```mermaid
sequenceDiagram
    participant User
    participant Frontend
    participant ChatServer
    participant VideoServer
    participant Gemini
    
    User->>Frontend: "What did you see in the last video?"
    Frontend->>ChatServer: POST /chat/completions
    ChatServer->>ChatServer: Extract user message
    ChatServer->>VideoServer: POST /query
    VideoServer->>VideoServer: Get latest video from cache
    VideoServer->>Gemini: Query video with user question
    Gemini-->>VideoServer: Video analysis response
    VideoServer-->>ChatServer: {response: "..."}
    ChatServer->>ChatServer: Format as chat completion
    loop Stream words
        ChatServer-->>Frontend: SSE chunk (word-by-word)
    end
    Frontend->>User: Display streaming response
```

## Data Flow

```mermaid
flowchart LR
    A[Raw Video Chunk<br/>5 seconds] --> B[Save to Disk<br/>./videos/]
    A --> C[Upload to Gemini]
    C --> D[Video File Object<br/>Cached in Memory]
    D --> E[Threat Analysis]
    E --> F{JSON Response}
    F -->|threat: 0| G[Normal Response]
    F -->|threat: 1| H[Emergency Call]
    H --> I[Automated Call<br/>with Description]
    
    style H fill:#ff6b6b
    style I fill:#ffd43b
```

## Key Components

### Backend Services
- **Video Server** (Flask): Receives video uploads, processes them with Gemini AI, and detects threats
- **Chat Server** (FastAPI): Handles natural language queries about video content
- **Outbound Server** (Node.js): Manages emergency calls via Twilio and ElevenLabs

### External AI Services
- **Google Gemini**: Analyzes video content and detects threats
- **ElevenLabs Conversational AI**: Voice agent that speaks to emergency responders
- **Twilio**: Handles the actual phone call infrastructure

### Frontend
- **Next.js Application** (`clamps/`): React-based web interface for monitoring feeds and viewing incidents
- Records 5-second video chunks continuously
- Displays threat detection results in real-time

## How to Use

1. **Start the backend services:**
   ```bash
   ./start.sh
   ```

2. **Start the frontend:**
   ```bash
   cd clamps
   npm install
   npm run dev
   ```
   Then open `http://localhost:3000` in your browser.

3. **The system will:**
   - Record 5-second video chunks from your camera
   - Analyze each chunk for threats
   - Display results in the interface
   - Automatically call emergency services if a threat is detected

## Configuration

All configuration is managed through environment variables (see `ENV_EXAMPLE.md`):
- API keys for Gemini, Twilio, and ElevenLabs
- Server ports and directories
- Model selection
