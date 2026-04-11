import os
import io
import asyncio
from typing import List
import numpy as np
from faster_whisper import WhisperModel
from pydub import AudioSegment
from ..config import get_settings

settings = get_settings()

class StreamingSTT:
    def __init__(self, model_size: str = None):
        if model_size is None:
            model_size = settings.WHISPER_MODEL
        
        # Initialize model (cpu for portability, can be changed to cuda if GPU is available)
        self.model = WhisperModel(model_size, device="cpu", compute_type="int8")
        self.buffer = io.BytesIO()
        self.last_transcript = ""

    async def process_chunk(self, audio_chunk: bytes) -> str:
        """Process a binary audio chunk and return the new transcription text."""
        import tempfile
        
        # Guard against zero-length chunks
        if not audio_chunk: return ""

        # Append chunk to memory buffer
        self.buffer.write(audio_chunk)
        self.buffer.seek(0)
        audio_data = self.buffer.read()
        
        print(f"STT: Buffer size = {len(audio_data)} bytes")
        
        if len(audio_data) < 4000: # Wait for more data to ensure header stability
            return ""

        temp_input = None
        temp_output = None
        
        try:
            # Write current buffer to a temporary file
            with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
                tmp.write(audio_data)
                temp_input = tmp.name
            
            # Use pydub to read. We try to force 'webm' format which uses ffmpeg matroska demuxer
            try:
                audio = AudioSegment.from_file(temp_input, format="webm")
            except Exception as inner_e:
                print(f"STT: Webm parse failed, trying auto: {inner_e}")
                audio = AudioSegment.from_file(temp_input)
            
            # Export to a temporary wav file (PCM 16kHz mono is best for Whisper)
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_wav:
                temp_output = tmp_wav.name
            
            audio.set_frame_rate(16000).set_channels(1).export(temp_output, format="wav")
            
            # Transcription
            stt_engine = get_stt_system()
            segments, info = stt_engine.transcribe(temp_output, beam_size=5)
            
            full_text = " ".join([segment.text for segment in segments]).strip()
            
            # If transcript is too long or same as last, we might be stuck
            if full_text == self.last_transcript and len(audio_data) > 2000000: # 2MB guard
                 print("STT: Buffer too large without new results, resetting...")
                 self.buffer = io.BytesIO()
                 self.last_transcript = ""
                 return ""

            # Simple delta logic
            new_text = ""
            if full_text.startswith(self.last_transcript):
                new_text = full_text[len(self.last_transcript):].strip()
            elif len(full_text) > len(self.last_transcript):
                new_text = full_text # Fallback
            
            self.last_transcript = full_text
            return new_text

        except Exception as e:
            print(f"STT Critical Error: {e}")
            # If we keep failing, clear buffer to allow a fresh start
            if len(audio_data) > 500000:
                print("STT: Clearing corrupted buffer")
                self.buffer = io.BytesIO()
            return ""
        finally:
            if temp_input and os.path.exists(temp_input): os.remove(temp_input)
            if temp_output and os.path.exists(temp_output): os.remove(temp_output)

# Global singleton or factory for the STT system
stt_model = None

def get_stt_system():
    global stt_model
    if stt_model is None:
        stt_model = WhisperModel(settings.WHISPER_MODEL, device="cpu", compute_type="int8")
    return stt_model
