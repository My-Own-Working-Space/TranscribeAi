"""Transcription service — Whisper inference with confidence scoring."""

import logging
import math
import os
import time

import whisper
import torch

from app.config import get_settings

logger = logging.getLogger("transcribeai.transcription")
settings = get_settings()


class TranscriptionService:
    """Manages Whisper model lifecycle and transcription jobs."""

    def __init__(self):
        self.model = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        logger.info("Transcription device: %s", self.device)

    def load_model(self, model_name: str | None = None):
        model_name = model_name or settings.WHISPER_MODEL
        if self.model is None:
            logger.info("Loading Whisper model: %s", model_name)
            self.model = whisper.load_model(model_name, device=self.device)
            logger.info("Whisper model loaded")
        return self.model

    @staticmethod
    def _logprob_to_confidence(avg_logprob: float) -> float:
        return round(math.exp(max(avg_logprob, -1.0)), 4)

    async def process_transcription(self, job_id: str, file_path: str, language: str | None, jobs_dict: dict):
        """Run transcription and update the shared jobs dict (v1 compatibility)."""
        t_start = time.perf_counter()
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0

        try:
            model = self.load_model()
            result = model.transcribe(file_path, language=language, verbose=False)

            segments = []
            conf_sum = 0.0
            for seg in result.get("segments", []):
                conf = self._logprob_to_confidence(seg.get("avg_logprob", -1.0))
                conf_sum += conf
                segments.append({
                    "start": round(seg["start"], 2),
                    "end": round(seg["end"], 2),
                    "text": seg["text"].strip(),
                    "confidence": conf,
                })

            avg_conf = round(conf_sum / len(segments), 4) if segments else 0.0
            proc_time = round(time.perf_counter() - t_start, 2)

            jobs_dict[job_id]["status"] = "completed"
            jobs_dict[job_id]["result"] = {
                "transcript": result["text"].strip(),
                "confidence": avg_conf,
                "segments": segments,
                "processing_time_s": proc_time,
                "file_size_bytes": file_size,
                "model": settings.WHISPER_MODEL,
                "language_detected": result.get("language", language),
            }

            logger.info("Job %s completed in %.2fs (%d segments)", job_id, proc_time, len(segments))

        except Exception as e:
            logger.error("Job %s failed: %s", job_id, e, exc_info=True)
            jobs_dict[job_id]["status"] = "failed"
            jobs_dict[job_id]["error"] = str(e)

        finally:
            if os.path.exists(file_path):
                os.remove(file_path)


transcription_service = TranscriptionService()
