# TranscribeAI

Multi-agent speech-to-text transcription system using MCP-style tools.

## Features

- 🎙️ **Multi-agent transcription** - Combines results from multiple transcription engines
- 🔧 **MCP-style tools** - Modular, extensible tool architecture
- ⚡ **FastAPI backend** - High-performance async REST API
- 🎯 **Confidence-weighted merging** - Intelligent result aggregation

## Project Structure

```
TranscribeAi/
├── app/
│   ├── main.py              # FastAPI entry point
│   ├── config.py            # Environment settings
│   ├── schemas.py           # Pydantic data models
│   ├── api/
│   │   └── transcribe.py    # REST endpoints
│   ├── mcp/
│   │   ├── orchestrator.py  # Agent coordinator
│   │   └── tools/           # Transcription tools
│   │       ├── transcribe_raw.py
│   │       ├── transcribe_context.py
│   │       ├── transcribe_external.py
│   │       └── merge_transcript.py
│   └── services/
│       ├── audio_loader.py  # Audio processing
│       └── storage.py       # File storage
├── scripts/
│   └── run_local.sh         # Local development script
├── tests/
│   └── test_merge.py        # Unit tests
├── requirements.txt
└── .env.example
```

## Requirements

- Python 3.11+
- FFmpeg (for audio processing)

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd TranscribeAi

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
.\venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Copy environment file
cp .env.example .env
# Edit .env with your configuration
```

## Usage

### Development Server

```bash
# Using the run script
chmod +x scripts/run_local.sh
./scripts/run_local.sh

# Or directly with uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `POST` | `/api/v1/transcribe` | Upload audio for transcription |
| `GET` | `/api/v1/transcribe/{job_id}` | Get transcription status/result |
| `DELETE` | `/api/v1/transcribe/{job_id}` | Cancel transcription job |

### Example Request

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@audio.wav" \
  -F "language=en"
```

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_merge.py -v
```

## Configuration

See `.env.example` for available configuration options.

## Architecture

### MCP Tools

The system uses MCP (Model Context Protocol) style tools for transcription:

1. **transcribe_raw** - Local model, no context, high throughput
2. **transcribe_context** - Context-aware with vocabulary hints
3. **transcribe_external** - External API delegation (cloud services)
4. **merge_transcript** - Combines results from multiple agents

### Orchestrator

The `MCPOrchestrator` coordinates multiple transcription agents:
- Parallel execution across agents
- Confidence-weighted result merging
- Graceful error handling and fallbacks

## License

MIT License

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request
