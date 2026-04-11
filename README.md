# 🎙️ TranscribeAi: Real-Time Meeting Assistant

TranscribeAi is a powerful, locally-hosted meeting assistant and transcription tool. It transforms your browser (Google Meet, YouTube, etc.) into a smart recording studio with real-time transcription and AI-powered note-taking.

> [!WARNING]
> **Current Status: Experimental.** 
> The Chrome Extension is currently in active development. Audio capture stability and UI synchronization may occasionally fail during dynamic page reloads.

---

## 🚀 Key Features

- **Real-Time Transcription**: Powered by `faster-whisper` (Local STT).
- **Notion-Style Sidebar**: A 600px split-view interface for live transcripts and manual notes.
- **Smart Notes (Groq AI)**: Automatically transforms transcripts into structured headings and bullet points using Llama-3 (Groq).
- **Universal Capture**: Works on Google Meet, YouTube, and potentially any browser tab.
- **Export**: Save your meeting notes as clean Markdown (`.md`) files.

---

## 🏗️ Architecture

The project consists of two main components:

1.  **Chrome Extension (Manifest v3)**:
    - Located in `/extension/`.
    - Uses an **Offscreen Document** for `tabCapture` to comply with modern Chrome standards.
    - Injects a responsive sidebar into the webpage.
2.  **Streaming Backend (FastAPI)**:
    - Located in `/backend/`.
    - Handles WebSocket connections and pipes audio data to the transcription engine.
    - Integrates Groq for high-speed AI processing.

---

## 🛠️ Setup Instructions

### 1. Backend (Python 3.10+)
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate  # Or .venv\Scripts\activate on Windows
pip install -r requirements.txt
# Start the server
uvicorn app.main:app --reload
```
*Note: Ensure `ffmpeg` is installed on your system.*

### 2. Extension
1. Open Chrome and go to `chrome://extensions/`.
2. Enable **Developer mode**.
3. Click **Load unpacked** and select the `/extension` folder.
4. Refresh your meeting tab (YouTube or Google Meet).

---

## 🚧 Known Issues & Troubleshooting

- **"Invalid Data" Errors**: Usually caused by starting the recorder before the WebSocket is ready. We've implemented a sync-fix, but if it persists, try stopping and restarting the recording.
- **Sidebar Visibility**: If the sidebar doesn't appear after 3 seconds, click the extension icon and use the popup "Open/Close" button.
- **Latency**: Transcription speed depends on your CPU/GPU performance (tested best with `base` model).

---

## 📜 License
MIT
