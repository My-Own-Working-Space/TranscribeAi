"""Action Items extraction service."""

import logging
from sqlalchemy.orm import Session
from app.models import TranscriptionJob, ActionItem
from app.services.llm_service import llm_service

logger = logging.getLogger("transcribeai.actions")

PROMPT = (
    "Extract ALL action items from the transcript. For each, provide: "
    '"task" (what to do), "assignee" (who, or "Unassigned"), "deadline" (when, or "Not specified"), '
    '"priority" ("low"/"medium"/"high"). Return a JSON array. If none found, return [].'
)


class ActionItemsService:
    def extract_actions(self, db: Session, job: TranscriptionJob) -> list[ActionItem]:
        if not job.transcript:
            return []

        db.query(ActionItem).filter(ActionItem.job_id == job.id).delete()
        db.commit()

        text = job.transcript[:12000]
        try:
            response = llm_service.chat(system_prompt=PROMPT, user_message=f"Transcript:\n\n{text}")
            parsed = llm_service.parse_json_response(response)
            if not isinstance(parsed, list):
                parsed = []

            items = []
            for d in parsed:
                if not isinstance(d, dict) or "task" not in d:
                    continue
                item = ActionItem(
                    job_id=job.id,
                    task_description=d.get("task", ""),
                    assignee=d.get("assignee", "Unassigned"),
                    deadline=d.get("deadline", "Not specified"),
                    priority=d.get("priority", "medium"),
                )
                db.add(item)
                items.append(item)

            db.commit()
            for item in items:
                db.refresh(item)
            logger.info("Extracted %d actions for job %s", len(items), job.id)
            return items
        except Exception as e:
            logger.error("Action extraction failed: %s", e)
            return []


action_service = ActionItemsService()
