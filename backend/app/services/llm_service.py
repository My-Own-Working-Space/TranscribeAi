"""LLM service — Groq API wrapper for all AI features."""

import json
import logging

from groq import Groq
from app.config import get_settings

logger = logging.getLogger("transcribeai.llm")
settings = get_settings()


class LLMService:
    """Wrapper around Groq API."""

    MODEL = "llama-3.3-70b-versatile"

    def __init__(self):
        self._client = None

    @property
    def client(self) -> Groq:
        if self._client is None:
            if not settings.GROQ_API_KEY:
                raise RuntimeError("GROQ_API_KEY is not configured")
            self._client = Groq(api_key=settings.GROQ_API_KEY)
        return self._client

    def chat(self, system_prompt: str, user_message: str, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        try:
            resp = self.client.chat.completions.create(
                model=self.MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error("LLM request failed: %s", e)
            raise

    def chat_with_history(self, system_prompt: str, messages: list[dict], temperature: float = 0.3, max_tokens: int = 2048) -> str:
        try:
            all_msgs = [{"role": "system", "content": system_prompt}] + messages
            resp = self.client.chat.completions.create(
                model=self.MODEL,
                messages=all_msgs,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error("LLM chat failed: %s", e)
            raise

    def parse_json_response(self, text: str) -> dict | list:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("[") if "[" in text else text.find("{")
            end = text.rfind("]") + 1 if "]" in text else text.rfind("}") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
            logger.warning("Failed to parse JSON from LLM response")
            return {}


llm_service = LLMService()
