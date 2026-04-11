import os
from groq import Groq
from ..config import get_settings

settings = get_settings()

class AIIntelligence:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL

    async def generate_smart_notes(self, transcript: str) -> str:
        """Transforms raw transcript into structured notes (Notion-style)."""
        if not transcript or len(transcript) < 50:
            return ""

        prompt = f"""
        You are a world-class note-taker. Transform the following raw transcript into structured, aesthetic notes.
        Use:
        - CLEAR HEADINGS for topics
        - BULLET POINTS for details
        - **Bold** for keywords
        
        Keep it concise and professional.
        
        Transcript:
        {transcript}
        
        Output only the formatted notes.
        """
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Groq Error (Smart Notes): {e}")
            return ""

    async def translate_transcript(self, transcript: str, target_lang: str = "Vietnamese") -> str:
        """Translates transcript to target language."""
        if not transcript: return ""

        prompt = f"Translate the following transcript into {target_lang}. Keep the original meaning and professional tone.\n\nTranscript:\n{transcript}"
        
        try:
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            return completion.choices[0].message.content
        except Exception as e:
            print(f"Groq Error (Translation): {e}")
            return ""

# Singleton
ai_brain = AIIntelligence()
