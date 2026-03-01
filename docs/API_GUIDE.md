# TranscribeAI - Hướng dẫn sử dụng API

## Giới thiệu

TranscribeAI là hệ thống multi-agent speech-to-text, hỗ trợ nhiều transcription engine chạy song song và merge kết quả thông minh.

### Agents có sẵn

| Agent | Mô tả |
|-------|-------|
| `whisper_raw` | Local Whisper model (faster-whisper) |
| `external_groq` | Groq Cloud API (whisper-large-v3) |

---

## 1. Cài đặt & Chạy Server

### Yêu cầu
- Python 3.11+
- FFmpeg (optional, cho audio conversion)

### Cài đặt

```bash
# Clone project
git clone <repository-url>
cd TranscribeAi

# Tạo virtual environment
python3 -m venv .venv

# Cài pip (nếu cần)
curl -sS https://bootstrap.pypa.io/get-pip.py | .venv/bin/python3

# Cài dependencies
.venv/bin/pip install -r requirements.txt

# Copy và cấu hình .env
cp .env.example .env
# Sửa .env với API keys của bạn
```

### Cấu hình .env

```env
# Groq API (bắt buộc cho external_groq agent)
GROQ_API_KEY=gsk_your_api_key_here

# Whisper model config
WHISPER_MODEL_SIZE=small  # tiny, base, small, medium, large-v2, large-v3
WHISPER_DEVICE=auto       # cpu, cuda, auto

# Redis (optional)
REDIS_URL=redis://user:password@host:port
```

### Chạy Server

```bash
# Sử dụng script
./scripts/run_local.sh

# Hoặc trực tiếp
.venv/bin/python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Server sẽ chạy tại: `http://localhost:8000`

---

## 2. API Endpoints

### Base URL
```
http://localhost:8000
```

### Endpoints

| Method | Endpoint | Mô tả |
|--------|----------|-------|
| GET | `/health` | Health check |
| GET | `/api/v1/agents` | Xem agents health |
| GET | `/api/v1/agents/list` | Liệt kê agents |
| POST | `/api/v1/transcribe` | Upload file & transcribe |
| POST | `/api/v1/transcribe/path` | Transcribe từ server path |

---

## 3. Sử dụng với cURL

### Health Check

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "app": "TranscribeAI",
  "agents": {
    "registered": 2,
    "healthy": 2
  }
}
```

### Liệt kê Agents

```bash
curl http://localhost:8000/api/v1/agents/list
```

**Response:**
```json
{
  "agents": [
    {"name": "whisper_raw", "description": "Local Whisper (small) transcription without context"},
    {"name": "external_groq", "description": "External transcription via GROQ API"}
  ],
  "count": 2
}
```

### Transcribe Audio (Tất cả agents)

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -F "file=@audio.wav"
```

### Transcribe với agents cụ thể

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -F "file=@audio.wav" \
  -F "agents=whisper_raw,external_groq"
```

### Transcribe chỉ với Groq

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -F "file=@audio.wav" \
  -F "agents=external_groq"
```

### Transcribe với language hint

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -F "file=@audio.wav" \
  -F "language=vi"
```

### Transcribe với merge strategy

```bash
curl -X POST "http://localhost:8000/api/v1/transcribe" \
  -F "file=@audio.wav" \
  -F "strategy=confidence"
```

**Strategies:**
- `confidence` - Merge theo confidence score (default)
- `longest` - Chọn transcript dài nhất
- `first` - Chọn kết quả đầu tiên

---

## 4. Test với Postman

### Import Collection

1. Mở Postman
2. Click **Import** → **Raw text**
3. Paste nội dung sau:

```json
{
  "info": {
    "name": "TranscribeAI API",
    "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json"
  },
  "variable": [
    {
      "key": "baseUrl",
      "value": "http://localhost:8000"
    }
  ],
  "item": [
    {
      "name": "Health Check",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/health"
      }
    },
    {
      "name": "List Agents",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/api/v1/agents/list"
      }
    },
    {
      "name": "Agents Health",
      "request": {
        "method": "GET",
        "url": "{{baseUrl}}/api/v1/agents"
      }
    },
    {
      "name": "Transcribe Audio",
      "request": {
        "method": "POST",
        "url": "{{baseUrl}}/api/v1/transcribe",
        "body": {
          "mode": "formdata",
          "formdata": [
            {
              "key": "file",
              "type": "file",
              "src": ""
            },
            {
              "key": "language",
              "value": "vi",
              "type": "text",
              "disabled": true
            },
            {
              "key": "agents",
              "value": "whisper_raw,external_groq",
              "type": "text",
              "disabled": true
            },
            {
              "key": "strategy",
              "value": "confidence",
              "type": "text",
              "disabled": true
            }
          ]
        }
      }
    }
  ]
}
```

### Hướng dẫn test từng bước

#### Step 1: Health Check
1. Chọn request **Health Check**
2. Click **Send**
3. Verify response có `"status": "ok"`

#### Step 2: Xem Agents
1. Chọn request **List Agents**
2. Click **Send**
3. Verify có agents `whisper_raw` và `external_groq`

#### Step 3: Transcribe Audio
1. Chọn request **Transcribe Audio**
2. Trong tab **Body**:
   - Click **Select Files** ở row `file`
   - Chọn file audio (wav, mp3, m4a, etc.)
3. (Optional) Enable các params:
   - `language`: `vi`, `en`, `ja`, etc.
   - `agents`: `whisper_raw`, `external_groq`, hoặc cả hai
   - `strategy`: `confidence`, `longest`, `first`
4. Click **Send**

### Postman Screenshots Guide

```
┌─────────────────────────────────────────────────────────────┐
│  POST  │ {{baseUrl}}/api/v1/transcribe          │  Send   │
├─────────────────────────────────────────────────────────────┤
│  Body  │  form-data                                         │
├─────────────────────────────────────────────────────────────┤
│  KEY          │  VALUE                    │  TYPE           │
├───────────────┼───────────────────────────┼─────────────────┤
│  file         │  [Select Files]           │  File           │
│  language     │  vi                       │  Text (disabled)│
│  agents       │  whisper_raw,external_groq│  Text (disabled)│
│  strategy     │  confidence               │  Text (disabled)│
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Response Format

### Transcribe Response

```json
{
  "job_id": "a1b2c3d4",
  "status": "completed",
  "transcript": {
    "segments": [
      {
        "start": 0.0,
        "end": 2.5,
        "text": "Xin chào các bạn",
        "confidence": 0.95,
        "speaker": null
      },
      {
        "start": 2.5,
        "end": 5.0,
        "text": "Hôm nay chúng ta sẽ học về AI",
        "confidence": 0.92,
        "speaker": null
      }
    ],
    "overall_confidence": 0.935,
    "notes": "Merged from 2 agents using confidence strategy. Used: whisper_raw, external_groq"
  },
  "error": null
}
```

### Error Response

```json
{
  "detail": "Unsupported format: .xyz. Supported: wav, mp3, flac, ogg, m4a, mp4, mkv, webm"
}
```

---

## 6. Tích hợp vào Project khác

### Python

```python
import httpx

async def transcribe_audio(file_path: str, language: str = None) -> dict:
    """Transcribe audio using TranscribeAI API."""
    async with httpx.AsyncClient(timeout=300.0) as client:
        with open(file_path, "rb") as f:
            files = {"file": (file_path, f)}
            data = {}
            if language:
                data["language"] = language
            
            response = await client.post(
                "http://localhost:8000/api/v1/transcribe",
                files=files,
                data=data,
            )
        
        response.raise_for_status()
        result = response.json()
        
        if result["status"] == "completed":
            return result["transcript"]
        else:
            raise Exception(result.get("error", "Transcription failed"))

# Sử dụng
import asyncio

async def main():
    transcript = await transcribe_audio("audio.wav", language="vi")
    
    # Lấy full text
    full_text = " ".join(seg["text"] for seg in transcript["segments"])
    print(f"Transcript: {full_text}")
    print(f"Confidence: {transcript['overall_confidence']}")

asyncio.run(main())
```

### JavaScript/TypeScript

```typescript
async function transcribeAudio(
  filePath: string,
  options?: { language?: string; agents?: string[] }
): Promise<TranscriptResult> {
  const formData = new FormData();
  formData.append("file", await Bun.file(filePath));
  
  if (options?.language) {
    formData.append("language", options.language);
  }
  if (options?.agents) {
    formData.append("agents", options.agents.join(","));
  }

  const response = await fetch("http://localhost:8000/api/v1/transcribe", {
    method: "POST",
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Transcription failed: ${response.statusText}`);
  }

  const result = await response.json();
  return result.transcript;
}

// Sử dụng
const transcript = await transcribeAudio("audio.wav", {
  language: "vi",
  agents: ["whisper_raw", "external_groq"],
});

const fullText = transcript.segments.map((s) => s.text).join(" ");
console.log(`Transcript: ${fullText}`);
```

### Node.js (với form-data)

```javascript
const FormData = require("form-data");
const fs = require("fs");
const axios = require("axios");

async function transcribeAudio(filePath, language = null) {
  const form = new FormData();
  form.append("file", fs.createReadStream(filePath));
  
  if (language) {
    form.append("language", language);
  }

  const response = await axios.post(
    "http://localhost:8000/api/v1/transcribe",
    form,
    {
      headers: form.getHeaders(),
      timeout: 300000, // 5 minutes
    }
  );

  return response.data.transcript;
}

// Sử dụng
transcribeAudio("audio.wav", "vi").then((transcript) => {
  console.log("Segments:", transcript.segments.length);
  console.log("Confidence:", transcript.overall_confidence);
});
```

---

## 7. Supported Formats

| Format | Extension |
|--------|-----------|
| WAV | .wav |
| MP3 | .mp3 |
| FLAC | .flac |
| OGG | .ogg |
| M4A | .m4a |
| MP4 | .mp4 |
| MKV | .mkv |
| WebM | .webm |

---

## 8. Troubleshooting

### Lỗi "No module named 'fastapi'"
```bash
# Activate venv và cài lại
source .venv/bin/activate
pip install -r requirements.txt
```

### Lỗi "No API key for groq"
```bash
# Thêm GROQ_API_KEY vào .env
echo "GROQ_API_KEY=gsk_your_key_here" >> .env
```

### Lỗi timeout khi transcribe file lớn
```bash
# Tăng timeout trong code hoặc sử dụng async
# Server mặc định timeout 300s (5 phút)
```

### Kiểm tra agents đã load
```bash
curl http://localhost:8000/api/v1/agents
```

---

## 9. Performance Tips

1. **Dùng Groq cho file ngắn (<25MB)** - Nhanh hơn local Whisper
2. **Dùng local Whisper cho file lớn** - Không giới hạn size
3. **Chọn model size phù hợp:**
   - `tiny`: Nhanh nhất, accuracy thấp
   - `small`: Cân bằng (recommended)
   - `medium`: Accuracy cao hơn, chậm hơn
   - `large-v3`: Tốt nhất, cần GPU

---

## 10. API Rate Limits

### Groq API
- Free tier: 10 requests/minute
- Paid: Depends on plan

### Local Whisper
- Không giới hạn
- Performance phụ thuộc CPU/GPU

---

## Contact & Support

- **API Docs**: http://localhost:8000/docs (Swagger UI)
- **ReDoc**: http://localhost:8000/redoc
