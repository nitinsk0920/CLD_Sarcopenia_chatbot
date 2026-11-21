# Backend Knowledge Prep (Demo)

This backend utility uses the existing cleaned file:

`src/data/cld_sarcopenia_rag_refined.json`

It does not recreate or re-clean the data. It only:

- loads the file
- validates `topic` and `content` fields
- normalizes topics to canonical categories:
  - `cld`
  - `sarcopenia`
  - `diet`
  - `exercise`
  - `safety`
  - `faq`
- lightly refines spacing
- optionally splits long chunks for embedding

## Run

```powershell
cd "C:\Users\Asus\Documents\New project\backend"
python prepare_knowledge.py
```

## Generated files

- `backend/data/knowledge_ready_for_embedding.json`
- `backend/data/knowledge_retrieval_index.json`
- `backend/data/knowledge_validation_summary.json`

## RAG retrieval layer (local)

The retriever uses:

- Google Gemini Embedding 2 (768 dimensions; API key remains on the backend)
- local vector store (`FAISS`, persistent on disk)
- FAQ-first shortcut before vector retrieval

### Install RAG dependencies

```powershell
cd "C:\Users\Asus\Documents\New project\backend"
pip install -r requirements-rag.txt
```

### Build local vector index

```powershell
cd "C:\Users\Asus\Documents\New project\backend"
python build_rag_index.py
```

Set `GOOGLE_API_KEY` (or `GEMINI_API_KEY`) before building. This is an offline/manual operation; backend startup only loads and validates the prebuilt index. Configure `GEMINI_EMBEDDING_MODEL=gemini-embedding-2` and `GEMINI_EMBEDDING_DIMENSION=768` consistently in local and Render environments. The index and metadata must be committed together after rebuilding.

### Demo retrieval call

```powershell
cd "C:\Users\Asus\Documents\New project\backend"
python demo_retrieve.py "Can I eat eggs or dal?"
```

Vector store path:

- `backend/vector_store/faiss`

## LangGraph + Gemini teaching chatbot

This chatbot pipeline uses nodes for:

- `input_analysis`
- `weak_topic_selection`
- `retrieval` (FAQ-first + top 3 RAG chunks)
- `llm_generation` (Gemini `gemini-2.5-flash`)
- `safety_check`
- `memory_update`
- `final_formatting`

LLM backend:

- Google Gen AI Python SDK
- model: `gemini-2.5-flash` (default)
- TTS model: `gemini-2.5-flash-preview-tts`
- PostgreSQL-backed LangGraph checkpointer when `LANGGRAPH_POSTGRES_URL` is set

### Install backend requirements

```powershell
cd "C:\Users\Asus\Documents\New project\backend"
pip install -r requirements-rag.txt
```

### Start chatbot API (FastAPI)

```powershell
cd "C:\Users\Asus\Documents\New project\backend"
python run_server.py
```

You can also run it from project root:

```powershell
cd "C:\Users\Asus\Documents\New project"
python backend\run_server.py
```

API endpoint:

- `POST http://127.0.0.1:8000/api/chat`
- `POST http://127.0.0.1:8000/api/chat/transcribe`
- `POST http://127.0.0.1:8000/api/chat/audio`

Required / optional environment knobs:

- `GOOGLE_API_KEY` or `GEMINI_API_KEY`
- `GEMINI_MODEL` (default `gemini-2.5-flash`)
- `GEMINI_TTS_MODEL` (default `gemini-2.5-flash-preview-tts`)
- `LANGGRAPH_POSTGRES_URL` for production persistence
- `ALLOW_IN_MEMORY_CHECKPOINTER_FALLBACK=false` to fail startup instead of silently losing conversation state when PostgreSQL is unavailable
- `CHAT_TIMEOUT_SECONDS` (default `60`)
- `GEMINI_TTS_VOICE` (default `Kore`)
- `CHAT_MAX_INPUT_CHARS` (default `2000`)
- `CLINICIAN_APPROVED_RED_FLAGS` (optional; pipe-separated exact phrases supplied by the hospital clinical team; empty by default)

The chatbot guardrails validate inputs before RAG/LLM processing, treat RAG passages as untrusted reference text, and validate generated output. Urgent escalation phrases are intentionally not pre-populated: configure `CLINICIAN_APPROVED_RED_FLAGS` only with phrases and escalation wording approved by the hospital/clinical team.

Example environment file:

- `backend/.env.example`

The checkpointer uses `LANGGRAPH_POSTGRES_URL`, falling back to `DATABASE_URL`. On startup, `PostgresSaver.setup()` creates/updates LangGraph's checkpoint tables. For browser-refresh recovery, the frontend stores only the active session UUID in tab-scoped `sessionStorage`; the backend revalidates it against the authenticated admin and active `patient_sessions` row before returning the saved draft or conversation history. Apply `backend/migrations/2026_11_20_add_patient_session_draft_profile.sql` to Supabase before starting the API if `patient_sessions.draft_profile` is not already present.

Request body:

```json
{
  "session_id": "patient-session-001",
  "question": "Can I eat eggs?",
  "selected_language": "en",
  "patient_context": {
    "age": "55",
    "gender": "Male",
    "dietType": "Mixed",
    "habits": ["Smoking"],
    "languagePreference": "English",
    "digitalLiteracy": "Basic"
  },
  "weak_topic_summary": {
    "rankedWeakTopics": [
      { "topic": "diet", "label": "diet and protein", "mistakes": 2 },
      { "topic": "exercise", "label": "exercise", "mistakes": 1 }
    ]
  }
}
```
