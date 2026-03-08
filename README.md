<div align="center">

# 🎙️ TranscribeAI

**AI Meeting & Lecture Assistant** — transcribe, summarize, chat, and extract action items from any audio.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Whisper](https://img.shields.io/badge/OpenAI-Whisper-412991?logo=openai)](https://github.com/openai/whisper)
[![React](https://img.shields.io/badge/React-19-61DAFB?logo=react)](https://react.dev)

</div>

---

## What It Does

Upload audio/video → AI transcribes with timestamps → generates summary, answers questions about the content, and extracts action items from meetings. Built as a SaaS with user accounts, usage tracking, and plan tiers.

---

## Architecture

```
┌──────────┐       ┌──────────────────────────────────────────┐
│  Browser │       │           TranscribeAI Backend           │
│  (React) │◄─────►│                                          │
│  :5173   │       │  FastAPI (:8000)                         │
└──────────┘       │  ├── /api/v1/*          → Legacy API     │
                   │  ├── /api/v2/auth       → JWT Auth       │
                   │  ├── /api/v2/jobs       → Job Management │
                   │  ├── /api/v2/jobs/:id/* → AI Features    │
                   │  └── /health            → System Status  │
                   │                                          │
                   │  Services:                               │
                   │  • Whisper STT (transcription)           │
                   │  • Groq LLM (summary, chat, actions)     │
                   │  • Edge TTS (text-to-speech)             │
                   │  • SQLite DB (users, jobs, AI data)      │
                   └──────────────────────────────────────────┘
```

---

## Features

- **AI Transcription** — Whisper models with per-segment confidence scores, 99+ languages
- **AI Summary** — Auto-generated summaries with key points (standard / meeting / lecture modes)
- **AI Chat** — Ask questions about your transcript, get answers with timestamp references
- **Action Items** — Extract tasks, assignees, deadlines from meetings
- **User Auth** — JWT-based registration/login with plan tiers (free/pro/enterprise)
- **Usage Tracking** — Monthly minute quotas with enforcement
- **Export** — SRT subtitles, TXT, JSON
- **Text-to-Speech** — 300+ voices via Edge TTS

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | React 19 + TypeScript + Vite |
| Backend | FastAPI + Pydantic v2 + SQLAlchemy |
| STT | OpenAI Whisper |
| LLM | Groq API (Llama 3.3 70B) |
| TTS | Edge TTS |
| Database | SQLite (MVP) |
| Auth | JWT + bcrypt |

---

## Quick Start

```bash
git clone https://github.com/your-username/TranscribeAi.git
cd TranscribeAi
cp .env.example .env    # Add your GROQ_API_KEY
./scripts/dev.sh        # Auto-creates venv, installs deps, starts both services
```

- **Web UI**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs

### Manual Setup

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
cd backend && ../.venv/bin/uvicorn app.main:app --reload
cd frontend && npm install && npm run dev
```

---

## API

### V2 (SaaS)

```
POST   /api/v2/auth/register
POST   /api/v2/auth/login
GET    /api/v2/auth/me

POST   /api/v2/jobs/              Upload + transcribe
GET    /api/v2/jobs/              List jobs
GET    /api/v2/jobs/dashboard     Usage stats
GET    /api/v2/jobs/:id           Job detail
DELETE /api/v2/jobs/:id           Delete job

GET    /api/v2/jobs/:id/summary            AI summary
POST   /api/v2/jobs/:id/summary/regenerate Regenerate
POST   /api/v2/jobs/:id/chat               Ask question
GET    /api/v2/jobs/:id/chat/history        Chat history
GET    /api/v2/jobs/:id/actions             Action items
POST   /api/v2/jobs/:id/actions/extract     Extract actions
PATCH  /api/v2/jobs/:id/actions/:aid        Update action
```

### V1 (Legacy)

```
POST   /api/v1/transcribe/              Upload audio
GET    /api/v1/transcribe/status/:id    Poll status
GET    /api/v1/export/:id?format=srt    Download SRT/TXT/JSON
POST   /api/v1/tts/generate             Text-to-speech
GET    /api/v1/tts/voices               List voices
```

---

## Project Structure

```
TranscribeAi/
├── backend/app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   ├── schemas.py
│   ├── api/
│   │   ├── v1/endpoints/      (transcribe, export, tts)
│   │   └── v2/endpoints/      (auth, jobs, ai)
│   └── services/
│       ├── transcription_service.py
│       ├── auth_service.py
│       ├── llm_service.py
│       ├── summary_service.py
│       ├── chat_service.py
│       ├── action_service.py
│       ├── srt_service.py
│       └── tts_service.py
├── frontend/src/
│   ├── App.tsx
│   ├── services/api.ts
│   └── index.css
├── scripts/
│   ├── dev.sh
│   └── setup.sh
├── .env.example
├── requirements.txt
└── README.md
```

---

## License

MIT
