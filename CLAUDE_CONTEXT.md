# Claude Code Quick Context

> **Start each session with**: "Read CLAUDE_CONTEXT.md and continue from where we left off"

## Project: Enterprise Multimodal Vision Platform

**Stack**: FastAPI + LangGraph + Mistral (LLM + OCR 3) + OpenCV + MediaPipe + GPT-4o Vision

## Current Status: Phase 2 Ready - Video Analysis

### Completed
- **Phase 0-1**: FastAPI + Mistral OCR 3 document processing
- **Phase 1.5**: Codebase cleanup
- **Document Agent**: LangGraph agent with Mistral LLM + OCR tools

### Clean Architecture
```
Project-4_Vision&Langchain/
├── api/                          # FastAPI Application
│   ├── main.py                   # App entry point
│   ├── routers/
│   │   ├── health.py             # Health endpoints
│   │   ├── documents.py          # Direct OCR endpoints
│   │   └── agent.py              # Document Intelligence Agent endpoints
│   └── schemas/
│       ├── base.py
│       └── documents.py
├── config/
│   └── settings.py               # Pydantic Settings
├── src/
│   ├── agents/
│   │   └── document_agent.py     # LangGraph Document Agent (Mistral)
│   ├── clients/
│   │   └── mistral_client.py     # Singleton Mistral OCR client
│   └── tools/
│       └── mistral_ocr_tools.py  # @tool decorated OCR functions
├── .env                          # API keys
├── requirements.txt
└── test_mistral_ocr.py
```

### API Endpoints

**Health**
```
GET  /api/v1/health/              → Health status
GET  /api/v1/health/live          → Liveness probe
GET  /api/v1/health/ready         → Readiness probe
```

**Documents (Direct OCR)**
```
POST /api/v1/documents/ocr        → Text extraction
POST /api/v1/documents/tables     → Table extraction
POST /api/v1/documents/classify   → Classification
POST /api/v1/documents/analyze    → Full pipeline
POST /api/v1/documents/pdf        → Multi-page PDF
POST /api/v1/documents/upload     → File upload
GET  /api/v1/documents/status     → Service status
```

**Agent (LangGraph Document Intelligence)**
```
POST /api/v1/agent/chat           → Chat with agent
POST /api/v1/agent/stream         → Stream responses (SSE)
GET  /api/v1/agent/status         → Agent status
POST /api/v1/agent/reset          → Reset memory
```

### Agent Architecture
```
User Query
    ↓
┌─────────────────────────────────┐
│  LangGraph create_react_agent   │
│  ┌───────────────────────────┐  │
│  │   Mistral Large LLM       │  │
│  │   (Reasoning & Routing)   │  │
│  └───────────────────────────┘  │
│              ↓                  │
│  ┌───────────────────────────┐  │
│  │   Mistral OCR 3 Tools     │  │
│  │   • process_document_ocr  │  │
│  │   • extract_tables        │  │
│  │   • process_pdf           │  │
│  │   • analyze_document      │  │
│  └───────────────────────────┘  │
└─────────────────────────────────┘
    ↓
Response
```

### Run Commands
```bash
# Windows
cd "C:\Users\samde\Langchain_Projects\Project-4_Vision&Langchain"
.\.venv\Scripts\activate
pip install -r requirements.txt  # Install langchain-mistralai
uvicorn api.main:app --reload --port 8000

# Test agent
curl -X POST http://localhost:8000/api/v1/agent/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "What documents can you process?"}'
```

### Next Steps: Phase 2 - Video Analysis

1. Uncomment `mediapipe` in requirements.txt
2. Create `src/processors/video_processor.py`
3. Create `src/models/face_detector.py`
4. Create `src/models/vision_analyzer.py` (GPT-4o)
5. Create `api/routers/video.py`

### Key Patterns
- **Singleton**: `src/clients/mistral_client.py`
- **LangGraph Agent**: `src/agents/document_agent.py`
- **@tool Decorator**: `src/tools/mistral_ocr_tools.py`
- **FastAPI Lifespan**: `api/main.py`

---

## Roadmap
| Phase | Status |
|-------|--------|
| 0-1 Documents | Done |
| 1.5 Cleanup | Done |
| Agent Integration | Done |
| 2 Video Analysis | Next |
| 3 Async Jobs | Pending |
| 4 Multi-Tenant | Pending |
| 5 Deployment | Pending |
