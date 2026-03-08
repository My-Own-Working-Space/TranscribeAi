"""AI Chat service — Q&A over transcripts. Chat history stored in Redis sessions (graceful fallback)."""

import json
import logging
import redis
from sqlalchemy.orm import Session
from app.models import TranscriptionJob
from app.services.llm_service import llm_service
from app.config import get_settings

logger = logging.getLogger("transcribeai.chat")
settings = get_settings()

SYSTEM_PROMPT = (
    "You are an intelligent assistant that answers questions about a transcript. "
    "Answer ONLY based on the transcript content. Reference timestamps when possible (e.g. 'At 2:30...'). "
    "If the answer isn't in the transcript, say so. Respond in the same language as the question."
)

MAX_HISTORY = 20       # Keep last 20 messages per session
SESSION_TTL = 86400    # 24 hours


def _get_redis() -> redis.Redis | None:
    """Get Redis connection. Returns None if connection fails."""
    try:
        r = redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=3)
        r.ping()
        return r
    except Exception as e:
        logger.warning("Redis unavailable, chat will work without history: %s", e)
        return None


def _session_key(job_id: str, user_id: str) -> str:
    return f"chat:{job_id}:{user_id}"


class ChatService:
    def answer_question(self, db: Session, job: TranscriptionJob, user_id: str, question: str) -> dict:
        if not job.transcript:
            raise ValueError("No transcript available")

        # Build transcript context from segments_json
        segments = job.segments_json or []
        if segments:
            context = "\n".join(
                f"[{self._fmt(s['start'])}-{self._fmt(s['end'])}] {s['text']}"
                for s in segments
            )
        else:
            context = job.transcript

        if len(context) > 10000:
            context = context[:10000] + "\n[... truncated ...]"

        # Load recent history from Redis (graceful fallback)
        recent: list[dict] = []
        r = _get_redis()
        if r:
            try:
                key = _session_key(job.id, user_id)
                raw_history = r.get(key)
                recent = json.loads(raw_history) if raw_history else []
            except Exception as e:
                logger.warning("Redis read failed, continuing without history: %s", e)

        # Build LLM messages
        messages = [
            {"role": "user", "content": f"Transcript:\n\n{context}"},
            {"role": "assistant", "content": "I've read the transcript. Ask me anything about it."},
        ]
        for m in recent[-6:]:  # Last 3 exchanges (6 messages)
            messages.append({"role": m["role"], "content": m["content"]})
        messages.append({"role": "user", "content": question})

        answer = llm_service.chat_with_history(system_prompt=SYSTEM_PROMPT, messages=messages)

        # Save to Redis session (graceful — skip if Redis unavailable)
        recent.append({"role": "user", "content": question})
        recent.append({"role": "assistant", "content": answer})
        if len(recent) > MAX_HISTORY:
            recent = recent[-MAX_HISTORY:]
        if r:
            try:
                r.setex(_session_key(job.id, user_id), SESSION_TTL, json.dumps(recent, ensure_ascii=False))
            except Exception as e:
                logger.warning("Redis write failed: %s", e)

        sources = self._find_sources(segments, question)
        return {"answer": answer, "sources": sources}

    def get_history(self, job_id: str, user_id: str) -> list[dict]:
        """Load chat history from Redis session."""
        r = _get_redis()
        if not r:
            return []
        try:
            key = _session_key(job_id, user_id)
            raw = r.get(key)
            if not raw:
                return []
            return json.loads(raw)
        except Exception as e:
            logger.warning("Redis read failed: %s", e)
            return []

    def clear_history(self, job_id: str, user_id: str) -> None:
        """Clear chat session for a job."""
        r = _get_redis()
        if r:
            try:
                r.delete(_session_key(job_id, user_id))
            except Exception as e:
                logger.warning("Redis delete failed: %s", e)

    @staticmethod
    def _fmt(s: float) -> str:
        m, sec = divmod(int(s), 60)
        return f"{m:02d}:{sec:02d}"

    @staticmethod
    def _find_sources(segments: list[dict], question: str) -> list[dict]:
        if not segments:
            return []
        stops = {"the","a","is","are","was","what","how","why","when","where","who","about",
                 "in","on","at","to","for","of","and","or","not","là","của","và","có","không","được","gì","như"}
        kw = set(question.lower().split()) - stops
        if not kw:
            return []
        scored = []
        for s in segments:
            overlap = len(kw & set(s.get("text", "").lower().split()))
            if overlap > 0:
                scored.append({
                    "time": f"{ChatService._fmt(s['start'])}-{ChatService._fmt(s['end'])}",
                    "text": s.get("text", ""),
                    "relevance": overlap,
                })
        scored.sort(key=lambda x: x["relevance"], reverse=True)
        return scored[:3]


chat_service = ChatService()
