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

The demo retriever uses:

- local hashed embeddings (deterministic, lightweight)
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
- `CHAT_TIMEOUT_SECONDS` (default `60`)
- `GEMINI_TTS_VOICE` (default `Kore`)

Example environment file:

- `backend/.env.example`

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
