# LangChain Vision & OCR Agentic System

Multimodal playground that showcases the **LangChain v1.0 + LangGraph** stack for vision-centric workflows. The repo contains two cooperating agents:

- A general-purpose **vision analysis agent** built with `create_agent()` and tool calling.
- A specialized **OCR/document agent** that chains EasyOCR/Tesseract tools inside a LangGraph-powered loop.

Together they demonstrate how the new LangChain patterns simplify sequential reasoning, tool routing, and memory for complex multimodal tasks.

---

## Highlights
- **LangGraph-native** execution: automatic state tracking, memory, checkpointing.
- **Tool-driven reasoning**: reusable toolset for image metadata, color analysis, quality checks, OCR, layout detection.
- **Multimodal messaging** via base64-encoded image payloads and GPT-4o-compatible prompts.
- **CLI demos** for both the generic vision assistant (`chat.py`) and OCR specialist (`ocr_agent.py`).

---

## Repository Layout
```
Project-4_Vision&Langchain/
├─ config/
│  └─ settings.py             # Env loading, defaults, project paths
├─ graph.py                   # Builds supervisor + specialists (multi-agent system)
├─ chat.py                    # CLI entry point (uses supervisor agent)
├─ ocr_agent.py               # Legacy standalone OCR CLI (optional)
├─ MULTI_AGENT_GUIDE.md       # Notes on LangGraph multi-agent patterns
├─ src/
│  ├─ agents/                 # create_agent-based specialists + supervisor
│  │  ├─ supervisor.py        # Wraps specialists as tools for routing
│  │  ├─ vision_agent.py      # Image properties/colors/quality specialist
│  │  ├─ ocr_agent.py         # OCR/document specialist (EasyOCR/Tesseract)
│  │  └─ qa_agent.py          # Context Q&A specialist (search & summarize tools)
│  ├─ state/
│  │  └─ graph_state.py       # TypedDict state definition for LangGraph
│  └─ tools/
│     ├─ vision_utils.py      # Shared image helpers + multimodal message builder
│     ├─ basic_vision_tools.py# Image metadata/color/quality diagnostics
│     └─ ocr_tools.py         # OCR/text-region/document-structure utilities
├─ checkpoints/               # LangGraph memory snapshots (auto-created)
├─ test_image.png, test_images/   # Sample assets for quick testing
├─ requirements.txt
└─ README.md
```

---

## Prerequisites
- **Python 3.10+** (LangChain v1.0 requirement)
- An OpenAI API key (and optional Anthropic key)
- Basic CV libraries (OpenCV, Pillow, NumPy) installed via `requirements.txt`

---

## Setup
1. (Optional) create & activate a virtual environment:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate   # Windows
   source .venv/bin/activate # macOS/Linux
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the project root:
   ```
   OPENAI_API_KEY=sk-...
   ANTHROPIC_API_KEY=optional
   ```
4. Validate configuration (prints detected keys, paths, models):
   ```bash
   python -m config.settings
   ```

---

## Usage

### Vision Agent CLI
```bash
python chat.py
```
- Drag/drop or type an image path, then ask questions like “analyze this image” or “what are the dominant colors?”
- The agent automatically runs the appropriate tool(s) and keeps conversation memory via LangGraph checkpoints.

### OCR Agent Demo
```bash
python ocr_agent.py
```
Commands inside the demo shell:
- `extract path/to/image.png` – run full-text extraction.
- `analyze path/to/document.jpg` – perform extraction plus layout + structure analysis.
- Any other prompt runs a general OCR Q&A with optional image input.

Both flows support multimodal prompts through `vision_utils.create_vision_message`.

---

## Extending the Graph
1. **Add tools** in `src/tools/`. Decorate with `@tool` to expose them to agents.
2. **Update state** in `src/state/graph_state.py` if you need to persist additional data (e.g., cached OCR payloads, routing flags).
3. **Modify `graph.py`** to:
   - Change the system prompt/routing guidelines.
   - Swap models via `config.settings`.
   - (Advanced) replace `create_agent()` with an explicit `StateGraph` to model custom nodes/edges.
4. **Compose agents** by importing tool lists (e.g., `basic_vision_tools`) or nested runnables inside new LangGraph nodes.

---

## Testing & Samples
- `test_image.png` plus `test_images/` hold quick-check assets for tool development.
- Each tool module includes a `__main__` block you can run directly for smoke tests.
- Add Pytest-based regression tests under `testing/` as you mature the pipeline.

---

## Roadmap Ideas
- Combine the vision and OCR graphs into a single routed LangGraph application.
- Persist checkpoints beyond memory (e.g., SQLite or S3) for longer conversations.
- Add structured outputs (Pydantic models) for document summaries.
- Integrate face/ID detection with MediaPipe (already listed in `requirements.txt`).

Pull requests welcome—happy building! 🚀
