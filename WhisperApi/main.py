import io
import json
import tempfile
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import StreamingResponse
from faster_whisper import WhisperModel
import uvicorn
from contextlib import asynccontextmanager

model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print("Loading faster-whisper model...")
    model = WhisperModel("small", device="cpu", compute_type="int8")
    print("Model loaded successfully.")
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    file_bytes = await file.read()
    
    def generate_segments():
        temp_path = None
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as temp_audio:
                temp_audio.write(file_bytes)
                temp_path = temp_audio.name
            
            segments, info = model.transcribe(temp_path, beam_size=5)
            
            yield json.dumps({"type": "info", "language": info.language, "probability": info.language_probability}) + "\n"
            
            buffer = []
            current_boundary = 10.0
            
            for segment in segments:
                segment_data = {
                    "start": round(segment.start, 2),
                    "end": round(segment.end, 2),
                    "text": segment.text.strip()
                }
                buffer.append(segment_data)
                
                # If segment end crosses the 10s boundary, yield the buffer
                if segment.end >= current_boundary:
                    combined_text = " ".join([s["text"] for s in buffer])
                    yield json.dumps({
                        "type": "segment",
                        "start": buffer[0]["start"],
                        "end": buffer[-1]["end"],
                        "text": combined_text
                    }) + "\n"
                    buffer = []
                    current_boundary += 10.0
            
            # Yield remaining buffer
            if buffer:
                combined_text = " ".join([s["text"] for s in buffer])
                yield json.dumps({
                    "type": "segment",
                    "start": buffer[0]["start"],
                    "end": buffer[-1]["end"],
                    "text": combined_text
                }) + "\n"
                
        except Exception as e:
            yield json.dumps({"type": "error", "message": str(e)}) + "\n"
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)

    return StreamingResponse(generate_segments(), media_type="application/x-ndjson")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

