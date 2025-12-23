# Vision Platform Development Log

> **Purpose**: This document provides context for Claude Code sessions. Start each new session by saying: "Read DEVELOPMENT_LOG.md and continue where we left off."

---

## Project Overview

**Project Name**: Enterprise Multimodal Vision Platform
**Goal**: Build a production-ready, client-facing multimodal vision platform
**Tech Stack**: FastAPI + LangChain + Mistral OCR 3 + MediaPipe + GPT-4o Vision

**End Vision**: A platform clients can use via REST API to:
- Process documents (OCR, classification, data extraction)
- Analyze faces and emotions
- Process video for object detection

---

## Current Status

| Phase | Name | Status | Key Deliverables |
|-------|------|--------|------------------|
| 0-1 | Documents MVP | ✅ DONE | FastAPI + Mistral OCR 3 |
| 1.5 | Codebase Cleanup | 🔜 NEXT | Remove clutter, trim unused code |
| 2 | Video Analysis | ⏳ After cleanup | Video + Face/Emotion/Object Detection |
| 3 | Async Processing | ⏳ Pending | Celery + Redis + Jobs |
| 4 | Multi-Tenant | ⏳ Pending | Auth + Rate Limiting |
| 5 | Client Deployment | ⏳ Future | Docker + CI/CD |

### Key Decision: Video-First Approach
Static image analysis was replaced with video processing. Video is the primary input for:
- Face detection (MediaPipe)
- Emotion analysis (GPT-4o Vision)
- Object detection (GPT-4o Vision)
- People counting

---

## Session 1 Summary (COMPLETED)

### What Was Built

Created a complete FastAPI-based document processing system with Mistral OCR 3.

### Files Created

```
Project-4_Vision&Langchain/
├── .env                              # API keys (OPENAI, MISTRAL)
├── requirements.txt                  # Updated with fastapi, uvicorn, mistralai
├── api/
│   ├── __init__.py
│   ├── main.py                       # FastAPI app with lifespan, CORS, middleware
│   ├── routers/
│   │   ├── __init__.py
│   │   ├── health.py                 # Health check endpoints (/live, /ready)
│   │   └── documents.py              # Document processing endpoints
│   └── schemas/
│       ├── __init__.py
│       ├── base.py                   # Base Pydantic models
│       └── documents.py              # Document request/response schemas
├── config/
│   └── settings.py                   # Pydantic Settings with .env loading
└── src/
    ├── clients/
    │   ├── __init__.py
    │   └── mistral_client.py         # Singleton Mistral client
    └── tools/
        └── mistral_ocr_tools.py      # OCR tools with @tool decorator
```

### API Endpoints Available

```
GET  /                           → API info
GET  /docs                       → Swagger UI (auto-generated)
GET  /api/v1/health/             → Health status
GET  /api/v1/health/live         → Kubernetes liveness probe
GET  /api/v1/health/ready        → Kubernetes readiness probe
POST /api/v1/documents/ocr       → OCR text extraction
POST /api/v1/documents/tables    → Table extraction
POST /api/v1/documents/classify  → Document classification
POST /api/v1/documents/analyze   → Full analysis pipeline
POST /api/v1/documents/pdf       → Multi-page PDF processing
POST /api/v1/documents/upload    → File upload endpoint
GET  /api/v1/documents/status    → Service status
```

### Key Patterns Learned

#### 1. Singleton Pattern
**File**: `src/clients/mistral_client.py`
```python
_client = None
def get_client():
    global _client
    if _client is None:
        _client = ExpensiveResource()
    return _client
```
**Why**: Expensive resources (API clients, DB connections, ML models) should only be instantiated once.

#### 2. @tool Decorator (LangChain)
**File**: `src/tools/mistral_ocr_tools.py`
```python
@tool
def process_document(path: str) -> str:
    """Docstring becomes the tool description for AI agents."""
    return result
```
**Why**: Converts functions into agent-callable tools with automatic schema generation.

#### 3. Pydantic Models
**File**: `api/schemas/*.py`
```python
class Request(BaseModel):
    field: str = Field(..., description="Required field")
```
**Why**: Type-safe validation, automatic API docs, error handling.

#### 4. FastAPI Lifespan
**File**: `api/main.py`
```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup code
    yield
    # Shutdown code
```
**Why**: Modern way to handle app startup/shutdown (initialize resources, cleanup).

#### 5. Health Checks
**File**: `api/routers/health.py`
- `/live` - Is the process running? (Kubernetes restarts if fails)
- `/ready` - Can it handle requests? (Load balancer removes if fails)

#### 6. Pydantic Settings
**File**: `config/settings.py`
```python
class Settings(BaseSettings):
    OPENAI_API_KEY: str = Field(...)
    model_config = SettingsConfigDict(env_file=".env")
```
**Why**: 12-factor app pattern - configuration from environment.

### Issues Resolved

1. **ModuleNotFoundError for langchain_core**
   - Fix: `pip install langchain-core langchain langchain-openai`

2. **API keys showing as NOT SET**
   - Cause: `load_dotenv()` without explicit path
   - Fix: Added explicit path in settings.py:
     ```python
     PROJECT_ROOT = Path(__file__).parent.parent
     ENV_FILE = PROJECT_ROOT / ".env"
     load_dotenv(dotenv_path=ENV_FILE)
     ```

---

## Phase 1.5: Codebase Cleanup (NEXT)

Before implementing the Video Analysis Module, clean up the existing codebase.

### Cleanup Tasks
1. Audit `src/` directory for unused legacy code
2. Remove legacy CLIs: `chat.py`, `ocr_agent.py` (root level)
3. Review `src/agents/` - remove if not integrated with API
4. Consolidate overlapping tool files in `src/tools/`
5. Clean up `requirements.txt` - remove unused deps
6. Update documentation files

### Files to Review for Removal
```
chat.py                    # Legacy CLI
ocr_agent.py               # Legacy CLI (root level)
graph.py                   # Review if still used
MULTI_AGENT_GUIDE.md       # May be outdated
src/agents/                # Review if integrated with API
```

---

## Phase 2: Video Analysis Module (AFTER CLEANUP)

### Overview
A unified video processing module where users upload videos and select what to analyze:
- **Face Detection** - Find faces throughout video (MediaPipe)
- **Emotion Analysis** - Analyze emotions on detected faces (GPT-4o)
- **Object Detection** - Identify objects in frames (GPT-4o)
- **People Counting** - Count and track people

### Learning Objectives
- **OpenCV** - Video loading, frame extraction, image manipulation
- **MediaPipe** - Real-time face detection optimized for video
- **Frame Sampling** - Smart frame selection (not every frame)
- **GPT-4o Vision** - Scene understanding, object detection, emotion analysis
- **Temporal Data** - Timestamped results, tracking across frames

### Files to Create

```
src/processors/
├── __init__.py
├── video_processor.py           # OpenCV video handling
└── video_analysis_pipeline.py   # Main orchestrator

src/models/
├── __init__.py
├── face_detector.py             # MediaPipe face detection
└── vision_analyzer.py           # GPT-4o emotion/object analysis

src/tools/
└── video_tools.py               # LangChain @tool functions

api/routers/
└── video.py                     # Video API endpoints

api/schemas/
└── video.py                     # Pydantic models
```

### Implementation Steps

1. **Install Dependencies**
   ```bash
   pip install opencv-python mediapipe
   ```

2. **Create Video Processor** (`src/processors/video_processor.py`)
   - OpenCV video handling, frame extraction, sampling

3. **Create Face Detector** (`src/models/face_detector.py`)
   - MediaPipe wrapper for video frames

4. **Create Vision Analyzer** (`src/models/vision_analyzer.py`)
   - GPT-4o wrapper for emotion and object detection

5. **Create Video Pipeline** (`src/processors/video_analysis_pipeline.py`)
   - Orchestrates face detection, emotion, objects, people counting

6. **Create Video Tools** (`src/tools/video_tools.py`)
   - LangChain @tool functions

7. **Create Video Schemas** (`api/schemas/video.py`)
   - Pydantic models for requests/responses

8. **Create Video Router** (`api/routers/video.py`)
   - API endpoints

9. **Update Main App** (`api/main.py`)
   - Include video router

### API Endpoints to Add

```
POST /api/v1/video/analyze  → Analyze video (faces, emotions, objects, people)
POST /api/v1/video/upload   → Upload video file
GET  /api/v1/video/info     → Get video metadata
POST /api/v1/video/frames   → Extract specific frames
GET  /api/v1/video/status   → Service status
```

---

## Future Phases (Brief)

### Phase 3: Async Processing
- Celery for background jobs (video processing takes time)
- Redis as message broker
- Job status tracking

### Phase 4: Async Processing
- Celery for background jobs
- Redis as message broker
- Job status tracking
- Files: `workers/celery_app.py`, `workers/tasks/`

### Phase 5: Multi-Tenant & Production
- API key authentication
- Rate limiting middleware
- Per-tenant configuration
- Prometheus metrics

### Phase 6: Client Deployment
- Docker containerization
- Docker Compose for full stack
- CI/CD with GitHub Actions
- Cloud deployment (AWS/GCP/Azure)

---

## Quick Start Commands

### Start Development Server
```bash
cd "C:\Users\samde\Langchain_Projects\Project-4_Vision&Langchain"

# Windows
.\.venv\Scripts\activate

# Linux/WSL
source venv/bin/activate

# Run server
uvicorn api.main:app --reload --port 8000
```

### Verify Setup
1. http://localhost:8000/docs - Swagger UI
2. http://localhost:8000/api/v1/health/ready - Check services
3. http://localhost:8000/api/v1/documents/status - Check Mistral

### Test Configuration
```bash
python config/settings.py
```

---

## Environment Variables (.env)

```
OPENAI_API_KEY=sk-proj-...
MISTRAL_API_KEY=...
```

---

## Dependencies (requirements.txt)

Key packages added:
- `fastapi>=0.109.0` - Web framework
- `uvicorn[standard]>=0.27.0` - ASGI server
- `mistralai>=1.0.0` - Mistral OCR 3
- `python-multipart>=0.0.6` - File uploads
- `structlog>=24.1.0` - Structured logging

To add for Phase 2:
- `mediapipe>=0.10.14` - Face detection
- `opencv-python>=4.9.0` - Image processing

---

## Project Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI Application                     │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   /health   │  │  /documents │  │   /faces    │  (Next) │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│ Mistral OCR 3 │    │   MediaPipe   │    │  GPT-4o Vision │
│   (Documents) │    │    (Faces)    │    │   (Analysis)   │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌───────────────┐
                    │  LangChain    │
                    │    Tools      │
                    └───────────────┘
```

---

## How to Continue Next Session

**Say to Claude Code:**
> "Read DEVELOPMENT_LOG.md and continue where we left off. We're starting Phase 2: Face/Emotion Module."

**What Claude should do:**
1. Read this file for context
2. Install MediaPipe
3. Create face detector model wrapper
4. Create emotion classifier
5. Create face tools
6. Create face schemas
7. Create face API endpoints
8. Update main app

---

## User Preferences

- **Learning Focus**: Understand each concept deeply, not just copy-paste
- **Approach**: Iterative, step-by-step development
- **Documentation**: Explain patterns as we implement them
- **Goal**: Build foundation for future complex enterprise projects

---

*Last Updated: Session 1 completion - Documents MVP done, Face/Emotion module next*
