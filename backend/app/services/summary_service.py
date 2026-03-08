"""AI Summary service — multi-agent pipeline: Generate → Review → Refine."""

import json
import logging
from sqlalchemy.orm import Session
from app.models import TranscriptionJob, AISummary
from app.services.llm_service import llm_service

logger = logging.getLogger("transcribeai.summary")

# ── Agent 1: Generator ──────────────────────────────────────────────
GENERATOR_PROMPTS = {
    "standard": (
        "You are a world-class summarizer. Given a transcript, analyze it deeply and produce JSON:\n"
        '{"summary": "2-3 detailed paragraphs covering ALL main topics discussed",\n'
        ' "key_points": ["array of 5-10 specific, factual points with timestamps when relevant"],\n'
        ' "conclusion": "1-2 sentence conclusion with key takeaway"}\n'
        "Rules:\n"
        "- Be SPECIFIC: include names, numbers, dates, quantities mentioned\n"
        "- Reference timestamps (e.g. 'At 02:30, ...') when possible\n"
        "- Cover ALL topics, not just the first part\n"
        "- Use the SAME language as the transcript\n"
        "- Respond ONLY with valid JSON"
    ),
    "meeting": (
        "You are an expert meeting summarizer. Given a meeting transcript, produce JSON:\n"
        '{"summary": "2-3 paragraphs covering all agenda items discussed",\n'
        ' "key_points": ["key decisions, discussion points, and agreements with timestamps"],\n'
        ' "conclusion": "concrete next steps and action items mentioned"}\n'
        "Rules:\n"
        "- Include WHO said what when identifiable\n"
        "- Note all decisions made and agreements reached\n"
        "- Reference timestamps (e.g. 'At 05:10, ...') for key moments\n"
        "- Use the SAME language as the transcript\n"
        "- Respond ONLY with valid JSON"
    ),
    "lecture": (
        "You are an expert lecture summarizer. Given a lecture transcript, produce JSON:\n"
        '{"summary": "2-3 paragraphs covering the lecture content comprehensively",\n'
        ' "key_points": ["main concepts, definitions, examples, and important details"],\n'
        ' "conclusion": "key takeaways for studying"}\n'
        "Rules:\n"
        "- Capture all concepts and definitions mentioned\n"
        "- Include specific examples given by the lecturer\n"
        "- Reference timestamps for key concepts\n"
        "- Use the SAME language as the transcript\n"
        "- Respond ONLY with valid JSON"
    ),
}

# ── Agent 2: Reviewer ───────────────────────────────────────────────
REVIEWER_PROMPT = (
    "You are a critical quality reviewer for AI-generated summaries. "
    "Compare the SUMMARY against the ORIGINAL TRANSCRIPT and evaluate:\n\n"
    "1. **Accuracy**: Are there any factual errors or hallucinations not in the transcript?\n"
    "2. **Completeness**: Are important topics missing? Does it cover all main sections?\n"
    "3. **Specificity**: Does it include specific names, numbers, timestamps, and details?\n"
    "4. **Language**: Is the language natural and same as the transcript?\n\n"
    "Respond with JSON:\n"
    '{"score": 1-10,\n'
    ' "issues": ["list of specific problems found"],\n'
    ' "missing_topics": ["topics from transcript not covered in summary"],\n'
    ' "suggestions": ["specific improvements to make"]}\n'
    "Be STRICT. Score 8+ means excellent quality. Respond ONLY with valid JSON."
)

# ── Agent 3: Refiner ────────────────────────────────────────────────
REFINER_PROMPT = (
    "You are a summary refinement specialist. You will receive:\n"
    "1. An original transcript\n"
    "2. A draft summary (JSON format)\n"
    "3. A review with specific issues and suggestions\n\n"
    "Produce an IMPROVED version of the summary that addresses ALL review feedback.\n"
    "Output the same JSON format:\n"
    '{"summary": "...", "key_points": [...], "conclusion": "..."}\n'
    "Rules:\n"
    "- Fix all accuracy issues identified by the reviewer\n"
    "- Add missing topics the reviewer identified\n"
    "- Make it more specific with names, numbers, timestamps\n"
    "- Keep the same language as the transcript\n"
    "- Respond ONLY with valid JSON"
)

MAX_REVIEW_PASSES = 2
QUALITY_THRESHOLD = 7  # Score >= 7 means good enough


class SummaryService:
    """Multi-agent summary pipeline: Generate → Review → Refine (loop)."""

    def generate_summary(self, db: Session, job: TranscriptionJob, language: str = None) -> AISummary:
        if not job.transcript:
            raise ValueError("No transcript available")

        existing = db.query(AISummary).filter(AISummary.job_id == job.id).first()
        if existing:
            db.delete(existing)
            db.commit()

        text = job.transcript[:12000]
        if len(job.transcript) > 12000:
            text += "\n\n[... truncated ...]"

        # ── Step 1: Generate initial summary ──
        logger.info("[Agent:Generator] Creating summary for job %s (mode=%s, lang=%s)", job.id, job.mode, language)
        gen_prompt = GENERATOR_PROMPTS.get(job.mode or "standard", GENERATOR_PROMPTS["standard"])

        # Inject target language instruction
        if language == "vi":
            gen_prompt += "\n- IMPORTANT: Write the ENTIRE summary in Vietnamese (Tiếng Việt), regardless of transcript language."
        elif language == "en":
            gen_prompt += "\n- IMPORTANT: Write the ENTIRE summary in English, regardless of transcript language."

        raw_response = llm_service.chat(system_prompt=gen_prompt, user_message=f"Transcript:\n\n{text}")
        parsed = llm_service.parse_json_response(raw_response)

        if not isinstance(parsed, dict) or "summary" not in parsed:
            parsed = {"summary": raw_response, "key_points": [], "conclusion": ""}

        review_passes = 0

        # ── Step 2-3: Review → Refine loop ──
        for attempt in range(MAX_REVIEW_PASSES):
            # Reviewer agent evaluates
            logger.info("[Agent:Reviewer] Pass %d for job %s", attempt + 1, job.id)
            review_input = (
                f"=== ORIGINAL TRANSCRIPT ===\n{text}\n\n"
                f"=== AI SUMMARY TO REVIEW ===\n{json.dumps(parsed, ensure_ascii=False)}"
            )
            review_raw = llm_service.chat(
                system_prompt=REVIEWER_PROMPT + (
                    "\n- IMPORTANT: The summary MUST be written in Vietnamese." if language == "vi"
                    else "\n- IMPORTANT: The summary MUST be written in English." if language == "en"
                    else ""
                ),
                user_message=review_input,
                temperature=0.2,
            )
            review = llm_service.parse_json_response(review_raw)

            score = review.get("score", 10) if isinstance(review, dict) else 10
            issues = review.get("issues", []) if isinstance(review, dict) else []
            logger.info(
                "[Agent:Reviewer] Score: %s/10, Issues: %d",
                score, len(issues)
            )

            review_passes += 1

            # If quality is good enough, stop
            if score >= QUALITY_THRESHOLD and len(issues) == 0:
                logger.info("[Pipeline] Quality sufficient (score=%s), skipping refinement", score)
                break

            # Refiner agent improves
            logger.info("[Agent:Refiner] Refining summary (score was %s)", score)
            refine_input = (
                f"=== ORIGINAL TRANSCRIPT ===\n{text}\n\n"
                f"=== DRAFT SUMMARY ===\n{json.dumps(parsed, ensure_ascii=False)}\n\n"
                f"=== REVIEW FEEDBACK ===\n{json.dumps(review, ensure_ascii=False)}"
            )
            refined_raw = llm_service.chat(
                system_prompt=REFINER_PROMPT + (
                    "\n- IMPORTANT: Write the refined summary in Vietnamese." if language == "vi"
                    else "\n- IMPORTANT: Write the refined summary in English." if language == "en"
                    else ""
                ),
                user_message=refine_input,
                temperature=0.25,
            )
            refined = llm_service.parse_json_response(refined_raw)

            if isinstance(refined, dict) and "summary" in refined:
                parsed = refined
                logger.info("[Agent:Refiner] Summary successfully refined")
            else:
                logger.warning("[Agent:Refiner] Failed to parse refined output, keeping previous version")
                break

        # ── Save result ──
        summary = AISummary(
            job_id=job.id,
            summary=parsed.get("summary", raw_response),
            key_points=parsed.get("key_points", []),
            conclusion=parsed.get("conclusion", ""),
            llm_model=llm_service.MODEL,
            review_passes=review_passes,
        )
        db.add(summary)
        db.commit()
        db.refresh(summary)
        logger.info(
            "[Pipeline] Summary saved for job %s (review_passes=%d)",
            job.id, review_passes
        )
        return summary


summary_service = SummaryService()
