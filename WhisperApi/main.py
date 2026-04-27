import io
from fastapi import FastAPI, UploadFile, File, HTTPException
from faster_whisper import WhisperModel
import uvicorn
from contextlib import asynccontextmanager

# Load model globally efficiently using CTranslate2
# CPU setup (can be switched to cuda if GPU is present)
model = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global model
    print("Loading faster-whisper model...")
    # 'small' is good for local fast test. 'medium' or 'large-v3' can be swapped here via env.
    model = WhisperModel("small", device="cpu", compute_type="int8")
    print("Model loaded successfully.")
    yield
    print("Shutting down...")

app = FastAPI(lifespan=lifespan)

@app.post("/transcribe")
async def transcribe_audio(file: UploadFile = File(...)):
    if not file:
        raise HTTPException(status_code=400, detail="No file uploaded")
    
    # Read the audio bytes directly into memory
    file_bytes = await file.read()
    audio_data = io.BytesIO(file_bytes)
    
    # Transcribe
    try:
        # We can pass file-like objects to faster-whisper (need to verify) or save to temp.
        # It's safer to save to temp file since faster-whisper underlying C library prefers paths
        import tempfile
        import os
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".ogg") as temp_audio:
            temp_audio.write(file_bytes)
            temp_path = temp_audio.name
            
        segments, info = model.transcribe(temp_path, beam_size=5)
        
        # Generator to list string
        text = " ".join([segment.text for segment in segments])
        
        os.remove(temp_path)
        
        return {
            "text": text.strip(),
            "language": info.language,
            "language_probability": info.language_probability
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
