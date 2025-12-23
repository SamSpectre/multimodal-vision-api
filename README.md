# Enterprise Multimodal Vision Platform

A production-ready, client-facing multimodal vision platform built with FastAPI, LangChain, and modern AI services.

## Features

### Current (Phase 0-1: Documents MVP)
- **Document Processing** via Mistral OCR 3
  - OCR text extraction with markdown output
  - Table detection and extraction
  - Document classification
  - Multi-page PDF processing
- **REST API** with FastAPI
  - Auto-generated Swagger documentation
  - Pydantic request/response validation
  - Health check endpoints (Kubernetes-ready)
- **Enterprise Patterns**
  - Singleton pattern for API clients
  - Environment-based configuration
  - Structured logging

### Coming Soon
- **Face/Emotion Analysis** (Phase 2) - MediaPipe + GPT-4o Vision
- **Video/Object Detection** (Phase 3) - OpenCV + GPT-4o
- **Async Processing** (Phase 4) - Celery + Redis
- **Multi-Tenant Support** (Phase 5) - API keys, rate limiting
- **Docker Deployment** (Phase 6) - CI/CD, monitoring

---

## Quick Start

### 1. Setup Environment
```bash
# Clone and navigate
cd Project-4_Vision&Langchain

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.\.venv\Scripts\activate

# Activate (Linux/Mac)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys
Create a `.env` file:
```env
OPENAI_API_KEY=sk-proj-...
MISTRAL_API_KEY=your_mistral_key
```

### 3. Run the API
```bash
uvicorn api.main:app --reload --port 8000
```

### 4. Access Documentation
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Health Check: http://localhost:8000/api/v1/health/ready

---

## API Endpoints

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/health/` | Health status |
| GET | `/api/v1/health/live` | Liveness probe |
| GET | `/api/v1/health/ready` | Readiness probe |

### Documents
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/documents/ocr` | Extract text from document |
| POST | `/api/v1/documents/tables` | Extract tables |
| POST | `/api/v1/documents/classify` | Classify document type |
| POST | `/api/v1/documents/analyze` | Full analysis pipeline |
| POST | `/api/v1/documents/pdf` | Process multi-page PDF |
| POST | `/api/v1/documents/upload` | Upload file for processing |
| GET | `/api/v1/documents/status` | Service status |

### Faces (Coming in Phase 2)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/faces/detect` | Detect faces in image |
| POST | `/api/v1/faces/emotions` | Analyze emotions |
| POST | `/api/v1/faces/compare` | Compare two faces |
| POST | `/api/v1/faces/analyze` | Full face analysis |

---

## Project Structure

```
Project-4_Vision&Langchain/
├── api/                          # FastAPI Application
│   ├── main.py                   # App entry point
│   ├── routers/                  # API endpoints
│   │   ├── health.py             # Health checks
│   │   └── documents.py          # Document processing
│   └── schemas/                  # Pydantic models
│       ├── base.py               # Base schemas
│       └── documents.py          # Document schemas
├── config/
│   └── settings.py               # Configuration management
├── src/
│   ├── agents/                   # LangChain agents
│   ├── clients/                  # API client singletons
│   │   └── mistral_client.py     # Mistral OCR client
│   ├── tools/                    # LangChain tools
│   │   ├── mistral_ocr_tools.py  # OCR tools
│   │   └── ...
│   └── state/                    # Graph state definitions
├── .env                          # API keys (not in git)
├── requirements.txt              # Dependencies
├── DEVELOPMENT_LOG.md            # Development history
├── CLAUDE_CONTEXT.md             # Quick context for AI sessions
└── README.md                     # This file
```

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| API Framework | FastAPI |
| Validation | Pydantic |
| Document OCR | Mistral OCR 3 |
| Face Detection | MediaPipe (planned) |
| Vision Analysis | GPT-4o |
| Agent Framework | LangChain |
| Task Queue | Celery (planned) |
| Cache | Redis (planned) |

---

## Development

### Verify Configuration
```bash
python config/settings.py
```

### Run Tests
```bash
pytest tests/
```

### Code Style
```bash
ruff check .
ruff format .
```

---

## For Developers (Claude Code Sessions)

Start each new development session by telling Claude Code:
> "Read CLAUDE_CONTEXT.md and continue from where we left off"

For detailed context including patterns learned and full history:
> "Read DEVELOPMENT_LOG.md for full project context"

---

## License

MIT

---

## Legacy CLI Tools

The project includes legacy CLI tools from the original codebase:

```bash
# Vision Agent CLI
python chat.py

# OCR Agent Demo
python ocr_agent.py
```

These demonstrate LangChain v1.0 + LangGraph patterns for vision-centric workflows.
