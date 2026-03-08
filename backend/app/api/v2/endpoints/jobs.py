"""Job management endpoints — upload, list, detail, delete."""

import logging
import math
import os
import time
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.config import get_settings
from app.database import get_db, SessionLocal
from app.models import TranscriptionJob, User
from app.schemas import JobListResponse, JobDetailResponse, DashboardStats
from app.api.v2.endpoints.auth import get_current_user
from app.services.transcription_service import transcription_service
from app.services.progress_service import set_progress, clear_progress

logger = logging.getLogger("transcribeai.api.jobs")
settings = get_settings()
router = APIRouter()

ALLOWED_EXTENSIONS = {f".{fmt}" for fmt in settings.SUPPORTED_FORMATS}


def _validate_ext(upload: UploadFile):
    ext = os.path.splitext(upload.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail=f"Unsupported format. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}")


async def _background_process(job_id: str, file_path: str, language: str | None, mode: str, user_id: str):
    """Transcribe → save segments → AI post-processing with real progress."""
    db = SessionLocal()
    try:
        job = db.query(TranscriptionJob).filter(TranscriptionJob.id == job_id).first()
        if not job:
            return

        job.status = "processing"
        db.commit()

        # ── Step 1: Load model (5%) ──
        set_progress(job_id, 5, "loading_model", "Đang tải mô hình AI...")
        t0 = time.perf_counter()
        model = transcription_service.load_model()

        # ── Step 2: Audio decoding (10%) ──
        set_progress(job_id, 10, "decoding_audio", "Đang giải mã audio...")
        import whisper
        audio = whisper.load_audio(file_path)
        audio = whisper.pad_or_trim(audio, length=None)  # full audio, no trim
        duration_est = len(audio) / 16000  # 16kHz sample rate

        # ── Step 3: Detect language if needed (15%) ──
        if not language:
            set_progress(job_id, 15, "detecting_language", "Đang nhận diện ngôn ngữ...")
            mel = whisper.log_mel_spectrogram(audio[:480000], n_mels=model.dims.n_mels).to(model.device)
            _, probs = model.detect_language(mel)
            language = max(probs, key=probs.get)

        # ── Step 4: Transcription (20% → 75%) ──
        set_progress(job_id, 20, "transcribing", f"Đang chuyển đổi ({int(duration_est)}s audio)...")

        # Optimized Whisper params for speed
        result = model.transcribe(
            file_path,
            language=language,
            verbose=False,
            fp16=(model.device != "cpu"),
            condition_on_previous_text=False,  # faster, less hallucination
            no_speech_threshold=0.6,
            compression_ratio_threshold=2.4,
        )

        set_progress(job_id, 75, "processing_segments", "Đang xử lý kết quả...")

        # ── Step 5: Process segments (75% → 85%) ──
        segments_data = []
        conf_sum = 0.0
        for i, seg in enumerate(result.get("segments", [])):
            c = round(math.exp(max(seg.get("avg_logprob", -1.0), -1.0)), 4)
            conf_sum += c
            segments_data.append({
                "index": i,
                "start": round(seg["start"], 2),
                "end": round(seg["end"], 2),
                "text": seg["text"].strip(),
                "confidence": c,
            })

        n_seg = len(segments_data)
        ptime = round(time.perf_counter() - t0, 2)

        set_progress(job_id, 85, "saving", "Đang lưu kết quả...")

        # ── Step 6: Save to DB (85% → 90%) ──
        job.transcript = result["text"].strip()
        job.segments_json = segments_data
        job.overall_confidence = round(conf_sum / n_seg, 4) if n_seg else 0.0
        job.processing_time_s = ptime
        job.language_detected = result.get("language", language)
        job.whisper_model = settings.WHISPER_MODEL
        job.status = "completed"
        job.completed_at = datetime.now(timezone.utc)

        if segments_data:
            job.duration_seconds = round(segments_data[-1].get("end", 0), 2)

        db.commit()

        user = db.query(User).filter(User.id == user_id).first()
        if user and job.duration_seconds:
            user.monthly_minutes_used += max(1, int(job.duration_seconds / 60))
            db.commit()

        set_progress(job_id, 90, "ai_summary", "AI đang tóm tắt nội dung...")

        logger.info("Job %s completed in %.2fs (%d segments)", job_id, ptime, n_seg)

        # ── Step 7: AI post-processing (90% → 100%) ──
        try:
            if settings.GROQ_API_KEY:
                from app.services.summary_service import summary_service
                set_progress(job_id, 92, "ai_summary", "Đang tạo bản tóm tắt AI...")
                summary_service.generate_summary(db, job)
                if mode == "meeting":
                    set_progress(job_id, 97, "ai_actions", "Đang trích xuất công việc...")
                    from app.services.action_service import action_service
                    action_service.extract_actions(db, job)
        except Exception as e:
            logger.warning("AI post-processing failed for %s: %s", job_id, e)

        set_progress(job_id, 100, "done", "Hoàn tất!")

    except Exception as e:
        logger.error("Job %s failed: %s", job_id, e, exc_info=True)
        job = db.query(TranscriptionJob).filter(TranscriptionJob.id == job_id).first()
        if job:
            job.status = "failed"
            job.error = str(e)
            db.commit()
        set_progress(job_id, 0, "failed", str(e))
    finally:
        if os.path.exists(file_path):
            os.remove(file_path)
        db.close()
        # Keep progress in Redis briefly for final poll, then auto-expires via TTL


@router.post("/", status_code=201)
async def create_job(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mode: str = Form("standard"),
    language: str = Form(None),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    _validate_ext(file)

    if current_user.monthly_minutes_used >= current_user.monthly_minutes_limit:
        raise HTTPException(
            status_code=429,
            detail=f"Monthly limit reached ({current_user.monthly_minutes_limit} min). Please upgrade your plan.",
        )

    temp_dir = "temp_uploads"
    os.makedirs(temp_dir, exist_ok=True)
    job_id = str(uuid.uuid4())
    safe_name = f"{job_id}_{os.path.basename(file.filename or 'upload')}"
    file_path = os.path.join(temp_dir, safe_name)

    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    total = 0
    try:
        with open(file_path, "wb") as buf:
            while chunk := await file.read(256 * 1024):
                total += len(chunk)
                if total > max_bytes:
                    buf.close()
                    os.remove(file_path)
                    raise HTTPException(status_code=413, detail=f"File exceeds {settings.MAX_FILE_SIZE_MB}MB limit.")
                buf.write(chunk)
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("File save failed: %s", exc)
        raise HTTPException(status_code=500, detail="Failed to save file.")

    job = TranscriptionJob(
        id=job_id, user_id=current_user.id, status="queued",
        original_filename=file.filename, storage_path=file_path,
        file_size_bytes=total, mode=mode,
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(_background_process, job_id, file_path, language, mode, current_user.id)
    return {"job_id": job_id, "status": "queued"}


@router.get("/", response_model=list[JobListResponse])
def list_jobs(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    jobs = (
        db.query(TranscriptionJob)
        .filter(TranscriptionJob.user_id == current_user.id)
        .order_by(TranscriptionJob.created_at.desc())
        .limit(50).all()
    )
    result = []
    for j in jobs:
        data = JobListResponse.model_validate(j)
        data.has_summary = j.summary is not None
        result.append(data)
    return result


@router.get("/dashboard", response_model=DashboardStats)
def get_dashboard(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    total = db.query(func.count(TranscriptionJob.id)).filter(TranscriptionJob.user_id == current_user.id).scalar() or 0
    completed = db.query(func.count(TranscriptionJob.id)).filter(
        TranscriptionJob.user_id == current_user.id, TranscriptionJob.status == "completed"
    ).scalar() or 0
    total_dur = db.query(func.sum(TranscriptionJob.duration_seconds)).filter(
        TranscriptionJob.user_id == current_user.id, TranscriptionJob.status == "completed"
    ).scalar() or 0.0

    return DashboardStats(
        total_jobs=total, completed_jobs=completed,
        total_minutes_transcribed=round(total_dur / 60, 1),
        minutes_used_this_month=current_user.monthly_minutes_used,
        minutes_limit=current_user.monthly_minutes_limit,
        plan=current_user.plan,
    )


@router.get("/{job_id}", response_model=JobDetailResponse)
def get_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(TranscriptionJob).filter(
        TranscriptionJob.id == job_id, TranscriptionJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    data = JobDetailResponse.model_validate(job)
    data.segments = job.segments_json or []
    return data


@router.get("/{job_id}/progress")
def get_job_progress(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """Real-time progress for a processing job — reads from Redis."""
    from app.services.progress_service import get_progress
    job = db.query(TranscriptionJob).filter(
        TranscriptionJob.id == job_id, TranscriptionJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    if job.status == "completed":
        return {"percent": 100, "step": "done", "detail": "Hoàn tất!", "status": "completed"}
    if job.status == "failed":
        return {"percent": 0, "step": "failed", "detail": job.error or "Lỗi", "status": "failed"}
    progress = get_progress(job_id)
    progress["status"] = job.status
    return progress


@router.delete("/{job_id}", status_code=204)
def delete_job(job_id: str, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    job = db.query(TranscriptionJob).filter(
        TranscriptionJob.id == job_id, TranscriptionJob.user_id == current_user.id
    ).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    db.delete(job)
    db.commit()
