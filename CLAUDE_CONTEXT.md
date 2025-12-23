# Claude Code Context - Vision Platform

> **Start each session with**: "Read CLAUDE_CONTEXT.md and continue from where we left off"

---

## Project Overview

**Project Name**: Enterprise Multimodal Vision Platform
**Type**: Production-ready SaaS API for document and video intelligence
**Target Market**: Enterprise clients, developers, robotics applications

### Value Proposition
A unified API that combines:
- **Document Intelligence** - Mistral OCR 3 for best-in-class document processing
- **Real-time Robotics Vision** - Groq's ~50ms latency for robotics applications
- **Multi-Agent Architecture** - LangGraph supervisor pattern for intelligent routing
- **Enterprise Security** - JWT + API Key authentication

---

## Current Status: Production-Ready MVP

| Phase | Status | Description |
|-------|--------|-------------|
| 1. Document Intelligence | ✅ Complete | Mistral OCR 3, table extraction, classification |
| 2. Multi-Agent System | ✅ Complete | LangGraph supervisor + specialist agents |
| 3. Model Optimization | ✅ Complete | Cost-optimized model selection per agent |
| 4. Authentication | ✅ Complete | JWT + API Key security |
| 5. Video/Robotics Agent | 🔜 Next | Groq Llama 3.2 Vision (~50ms latency) |
| 6. Async Jobs | ⏳ Pending | Celery + Redis for long-running tasks |
| 7. Deployment | ⏳ Pending | Docker, CI/CD, cloud deployment |

---

## Architecture

### Multi-Agent System (LangGraph 2025 Patterns)

```
                    User Request
                         ↓
         ┌───────────────────────────────┐
         │     SUPERVISOR AGENT          │
         │     (gpt-4o-mini - $0.15/1M)  │
         │     Fast routing decisions    │
         └───────────────────────────────┘
                         ↓
         ┌───────────────┴───────────────┐
         ↓                               ↓
┌─────────────────────┐     ┌─────────────────────┐
│   DOCUMENT AGENT    │     │   VIDEO AGENT       │
│                     │     │                     │
│ mistral-large-latest│     │ llama-3.2-11b-vision│
│ + Mistral OCR 3     │     │ (Groq - ~50ms)      │
│                     │     │                     │
│ Capabilities:       │     │ Capabilities:       │
│ • OCR extraction    │     │ • Real-time vision  │
│ • Table detection   │     │ • Face detection    │
│ • Classification    │     │ • Object detection  │
│ • PDF processing    │     │ • Robotics support  │
└─────────────────────┘     └─────────────────────┘
```

### Model Configuration (Cost & Latency Optimized)

| Agent | Model | Provider | Latency | Cost | Use Case |
|-------|-------|----------|---------|------|----------|
| Supervisor | gpt-4o-mini | OpenAI | ~100ms | $0.15/1M | Routing |
| Document | mistral-large-latest | Mistral | ~500ms | ~$2/1M | OCR reasoning |
| Video | llama-3.2-11b-vision | Groq | **~50ms** | $0.18/1M | Robotics |
| OCR | mistral-ocr-2512 | Mistral | ~1s | $2/1000 pages | Text extraction |

---

## Project Structure

```
Project-4_Vision&Langchain/
├── api/                              # FastAPI Application
│   ├── main.py                       # App entry + auth + lifespan
│   ├── routers/
│   │   ├── health.py                 # Health probes (public)
│   │   ├── documents.py              # OCR endpoints (protected)
│   │   └── agent.py                  # Multi-agent endpoints (protected)
│   └── schemas/
│       ├── base.py
│       └── documents.py
├── config/
│   └── settings.py                   # Pydantic Settings (all config)
├── src/
│   ├── agents/                       # LangGraph Multi-Agent System
│   │   ├── __init__.py               # Public exports
│   │   ├── base.py                   # AgentState, constants
│   │   ├── orchestrator.py           # get_multi_agent_system()
│   │   ├── supervisor.py             # Routing agent (gpt-4o-mini)
│   │   ├── document_agent.py         # Mistral LLM + OCR tools
│   │   └── video_agent.py            # Groq Vision (Phase 2)
│   ├── auth/                         # Authentication Module
│   │   ├── __init__.py
│   │   ├── models.py                 # User, Token, TokenData
│   │   ├── utils.py                  # JWT, password hashing
│   │   ├── dependencies.py           # FastAPI auth deps
│   │   └── router.py                 # /auth endpoints
│   ├── clients/                      # API Client Singletons
│   │   ├── mistral_client.py         # Mistral OCR client
│   │   └── groq_client.py            # Groq low-latency client
│   └── tools/
│       └── mistral_ocr_tools.py      # @tool decorated OCR functions
├── test_images/                      # Test documents
├── .env                              # API keys & auth config
├── requirements.txt                  # All dependencies
├── CLAUDE_CONTEXT.md                 # This file
├── DEVELOPMENT_LOG.md                # Detailed history
└── README.md                         # User documentation
```

---

## API Endpoints

### Authentication (Public)
```
POST /api/v1/auth/login     → Login with username/password (JSON)
POST /api/v1/auth/token     → OAuth2 token endpoint (form data)
GET  /api/v1/auth/me        → Get current user info
GET  /api/v1/auth/verify    → Verify token validity
POST /api/v1/auth/api-key   → Generate API key (admin only)
GET  /api/v1/auth/status    → Auth system status
```

### Health (Public)
```
GET  /api/v1/health/        → Health status
GET  /api/v1/health/live    → Liveness probe
GET  /api/v1/health/ready   → Readiness probe
```

### Agent (Protected - Requires Auth)
```
POST /api/v1/agent/chat     → Chat with multi-agent system
POST /api/v1/agent/stream   → Stream responses (SSE)
GET  /api/v1/agent/status   → Agent status + model info
POST /api/v1/agent/reset    → Reset memory (admin only)
```

### Documents (Protected - Requires Auth)
```
POST /api/v1/documents/ocr       → OCR text extraction
POST /api/v1/documents/tables    → Table extraction
POST /api/v1/documents/classify  → Document classification
POST /api/v1/documents/analyze   → Full analysis pipeline
POST /api/v1/documents/pdf       → Multi-page PDF
POST /api/v1/documents/upload    → File upload
GET  /api/v1/documents/status    → Service status
```

---

## Authentication

### Methods
1. **JWT Token** - For user applications
   ```
   Authorization: Bearer eyJ0eXAi...
   ```

2. **API Key** - For service-to-service
   ```
   X-API-Key: vp_abc123...
   ```

### Default Credentials (Development)
```
Username: admin
Password: admin123
```

### How to Login
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

Response:
```json
{"access_token": "eyJ...", "token_type": "bearer"}
```

---

## Environment Variables (.env)

```bash
# API Keys
OPENAI_API_KEY=sk-proj-...
MISTRAL_API_KEY=...
GROQ_API_KEY=gsk_...

# Authentication
SECRET_KEY=your_32_byte_hex_key          # openssl rand -hex 32
ACCESS_TOKEN_EXPIRE_MINUTES=30
API_KEY=vp_your_static_api_key
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=$2b$12$...           # bcrypt hash
AUTH_ENABLED=True
```

---

## Quick Start Commands

```bash
# Navigate to project
cd "C:\Users\samde\Langchain_Projects\Project-4_Vision&Langchain"

# Activate venv (Windows)
.\.venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run API server
uvicorn api.main:app --reload --port 8000

# Test authentication
python test_authentication.py

# Test document intelligence
python test_document_intelligence.py

# Access Swagger UI
http://localhost:8000/docs
```

---

## Key Design Patterns Implemented

### 1. Singleton Pattern (API Clients)
```python
# src/clients/mistral_client.py
_client = None
def get_mistral_client():
    global _client
    if _client is None:
        _client = Mistral(api_key=os.getenv("MISTRAL_API_KEY"))
    return _client
```

### 2. LangGraph Multi-Agent (2025 Patterns)
```python
# Uses create_agent from langchain.agents (NOT deprecated create_react_agent)
# Uses system_prompt parameter (NOT deprecated state_modifier)
from langchain.agents import create_agent

agent = create_agent(
    model=llm,
    tools=TOOLS,
    system_prompt="You are a specialist..."
)
```

### 3. FastAPI Dependencies (Auth)
```python
from src.auth.dependencies import require_auth

@router.post("/protected")
async def endpoint(user: User = Depends(require_auth)):
    return {"user": user.username}
```

### 4. Pydantic Settings (Config)
```python
class Settings(BaseSettings):
    OPENAI_API_KEY: str
    model_config = SettingsConfigDict(env_file=".env")
```

---

## Lessons Learned

### Technical
1. **bcrypt 5.x incompatible with passlib** - Use bcrypt>=4.0.0,<5.0.0
2. **LangChain 2025 migration** - create_react_agent is deprecated, use create_agent
3. **Groq for robotics** - ~50ms latency vs ~200ms OpenAI, 2.6x faster
4. **Windows encoding** - Use sys.stdout.reconfigure(encoding='utf-8')
5. **Pydantic Settings** - Use explicit .env path with load_dotenv()

### Architecture
1. **Cost optimization** - Use cheap models for routing (gpt-4o-mini), expensive for reasoning
2. **Separation of concerns** - Supervisor routes, specialists execute
3. **Singleton clients** - Avoid repeated instantiation of expensive API clients
4. **Auth flexibility** - Support both JWT (users) and API keys (services)

---

## Next Steps

### Immediate (Phase 5: Video/Robotics)
1. Implement video tools in `src/tools/video_tools.py`
2. Add frame extraction with OpenCV
3. Integrate MediaPipe face detection
4. Complete video_agent_node with Groq Vision
5. Add `/api/v1/video/*` endpoints

### Near-term (Phase 6-7)
1. Async job processing with Celery + Redis
2. Docker containerization
3. CI/CD pipeline
4. Cloud deployment (AWS/GCP/Azure)

### Enterprise Features
1. Rate limiting per API key
2. Usage tracking and billing
3. Multi-tenant support
4. Audit logging
5. Prometheus metrics

---

## Marketing & Client Considerations

### Target Clients
1. **Enterprise** - Document processing at scale
2. **Robotics Companies** - Real-time vision with ~50ms latency
3. **SaaS Platforms** - Embedded document intelligence
4. **Developers** - Easy REST API integration

### Unique Selling Points
1. **Best-in-class OCR** - Mistral OCR 3 outperforms GPT-4o, Google, Azure
2. **Low-latency vision** - Groq's ~50ms for real-time robotics
3. **Intelligent routing** - AI supervisor routes to optimal specialist
4. **Production-ready** - Auth, health checks, structured logging

### Pricing Model (Suggested)
| Tier | Requests/Month | Price |
|------|---------------|-------|
| Free | 100 | $0 |
| Starter | 1,000 | $29/mo |
| Pro | 10,000 | $99/mo |
| Enterprise | Unlimited | Custom |

---

## Files to Know

| File | Purpose |
|------|---------|
| `config/settings.py` | All configuration, model selection |
| `src/agents/orchestrator.py` | Main entry point for multi-agent system |
| `src/agents/supervisor.py` | Routing logic |
| `src/auth/dependencies.py` | Auth middleware |
| `api/main.py` | FastAPI app setup |
| `requirements.txt` | All dependencies |

---

## Testing Commands

```bash
# Test auth system
python test_authentication.py

# Test document intelligence
python test_document_intelligence.py

# Test Mistral OCR
python test_mistral_ocr.py

# Verify configuration
python config/settings.py
```

---

*Last Updated: December 2024 - Authentication complete, ready for Video/Robotics Phase*
