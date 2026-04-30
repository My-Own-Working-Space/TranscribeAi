<div align="center">

# 🎙️ TranscribeAI Pro

**Professional AI Transcription & Intelligence Platform**  
*Powered by .NET 9, Local Whisper Turbo, and Multi-Agent LLM Intelligence*

[![.NET 9](https://img.shields.io/badge/.NET-9.0-512BD4?logo=dotnet)](https://dotnet.microsoft.com)
[![FastAPI](https://img.shields.io/badge/Whisper--API-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com)
[![Groq](https://img.shields.io/badge/LLM-Groq-orange)](https://groq.com)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

</div>

---

## 🚀 Overview

TranscribeAI Pro is a high-performance, full-stack application designed for secure and accurate transcription and summarization. It features a hybrid architecture combining a **local Whisper engine** for 100% private transcription and a **Groq-powered Multi-Agent LLM pipeline** for advanced summarization and action item extraction.

### Core Workflow
1. **Secure Upload**: Drag-and-drop media files (MP4, MP3, etc.).
2. **Local Transcription**: Real-time 10-second batch processing via a local FastAPI Whisper service.
3. **Interactive Player**: Click any transcript timestamp to instantly seek the video/audio player.
4. **AI Intelligence**: Multi-agent summary generation, key insight extraction, and meeting action item tracking.
5. **Universal Search**: Full-text search across all your project transcripts.

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| **Web UI** | ASP.NET Core 9 Razor Pages |
| **Styling** | Vanilla CSS (Premium Modern UI) |
| **Real-time** | SignalR (Live transcription updates) |
| **STT Engine** | Faster-Whisper (Python FastAPI wrapper) |
| **LLM Pipeline** | Groq Llama 3.3 70B (Generator-Reviewer-Refiner architecture) |
| **Database** | PostgreSQL (Supabase) / SQLite |
| **Background** | .NET Worker Service (Job Queue) |

---

## 📦 Project Structure

```text
TranscribeAi/
├── TranscribeAi.Web/            # ASP.NET Core 9 Razor Pages (Main Hub)
├── TranscribeAi.Worker/         # Background Service (STT/LLM Processing)
├── TranscribeAi.Services/       # Business Logic & AI Orchestration
├── TranscribeAi.DataAccessLayer/# EF Core Repositories & DB Context
├── TranscribeAi.BusinessObject/ # Shared Entities & DTOs
├── WhisperApi/                  # Python FastAPI Service (Faster-Whisper STT)
└── README.md
```

---

## ⚙️ Setup & Installation

### 1. Requirements
- [.NET 9 SDK](https://dotnet.microsoft.com/download/dotnet/9.0)
- [Python 3.10+](https://www.python.org/) (for Local Whisper)
- [FFmpeg](https://ffmpeg.org/) (installed and in PATH)

### 2. Configure Environment
Create a `.env` file in the root directory:
```env
# Database
ConnectionStrings__DefaultConnection="Host=...;Database=..."

# Groq API
Groq__ApiKey="gsk_..."

# Transcription Provider (Local or Groq)
TranscribeAi__Provider="Local"
TranscribeAi__LocalWhisperUrl="http://127.0.0.1:8000/transcribe"
```

### 3. Run Whisper API
```bash
cd WhisperApi
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 4. Run Web Application
```bash
cd TranscribeAi.Web
dotnet run
```
*Access the app at `http://localhost:10000`*

---

## 🌟 Key Features

- **Real-time 10s Batching**: Text appears every 10 seconds of audio, reducing wait time for long files.
- **Deep Media Integration**: Video player synced with transcript timestamps.
- **Smart Summarization**: Advanced 3-pass AI pipeline ensures the highest summary accuracy.
- **Action Items**: Automatically identifies "Who needs to do What and When" from your recordings.
- **Project Management**: Organize recordings with names and descriptions.

---

## 📄 License
This project is licensed under the MIT License.
