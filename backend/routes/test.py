"""
API routes for the IQ test.

Endpoints:
  POST /api/test/start      – begin a new test session
  POST /api/test/submit     – submit answers, get score + AI analysis
  POST /api/test/invalidate – anti-cheat: mark session terminated
"""

import random
import uuid
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from config import TOTAL_QUESTIONS, TEST_DURATION_SECONDS
from database import get_db
from questions import QUESTION_BANK
from services.scoring import calculate_iq
from services.ai_service import generate_ai_analysis

router = APIRouter(prefix="/api/test", tags=["test"])


# ── Pydantic request/response models ─────────────────────────────────

class SubmitRequest(BaseModel):
    session_id: str
    answers: dict[str, str]
    email: str = None  # Optional email for linking to profile


class InvalidateRequest(BaseModel):
    session_id: str


# ── Helpers ───────────────────────────────────────────────────────────

def _strip_answers(question: dict) -> dict:
    """Return question without the 'correct' key so client never sees it."""
    return {k: v for k, v in question.items() if k != "correct"}


# ── Routes ────────────────────────────────────────────────────────────

@router.post("/start")
async def start_test():
    """Create a new session, pick random questions, store server-side."""
    db = get_db()

    questions = random.sample(QUESTION_BANK, min(TOTAL_QUESTIONS, len(QUESTION_BANK)))

    session_id  = str(uuid.uuid4())
    started_at  = datetime.now(timezone.utc)
    expires_at  = started_at + timedelta(seconds=TEST_DURATION_SECONDS)

    await db.sessions.insert_one({
        "session_id":  session_id,
        "questions":   questions,         # stored with answers
        "started_at":  started_at,
        "expires_at":  expires_at,
        "status":      "active",          # active | submitted | terminated
        "result":      None,
    })

    return {
        "session_id":    session_id,
        "questions":     [_strip_answers(q) for q in questions],
        "time_limit":    TEST_DURATION_SECONDS,
        "expires_at":    expires_at.isoformat(),
    }


@router.post("/submit")
async def submit_test(body: SubmitRequest):
    """Score the test, generate AI analysis, return full result."""
    db = get_db()

    session = await db.sessions.find_one({"session_id": body.session_id})

    if not session:
        raise HTTPException(status_code=404, detail="Session not found. The test may have expired.")

    if session["status"] == "terminated":
        raise HTTPException(status_code=403, detail="Session was terminated due to a rule violation.")

    if session["status"] == "submitted":
        raise HTTPException(status_code=409, detail="Test already submitted.")

    # Check expiry
    if datetime.now(timezone.utc) > session["expires_at"].replace(tzinfo=timezone.utc):
        await db.sessions.update_one(
            {"session_id": body.session_id},
            {"$set": {"status": "terminated"}},
        )
        raise HTTPException(status_code=410, detail="Test session has expired.")

    # Score
    raw_result = calculate_iq(session["questions"], body.answers)

    # AI analysis (async)
    ai_text = await generate_ai_analysis(raw_result)

    result = {**raw_result, "ai_analysis": ai_text}

    if body.email:
        await db.users.update_one(
            {"email": body.email},
            {
                "$set": {
                    "last_iq": result["iq_score"],
                    "last_activity": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
                },
                "$push": {"test_history": {"type": "aptitude", "score": result["iq_score"], "date": datetime.now(timezone.utc)}}
            }
        )

    return result


@router.post("/invalidate")
async def invalidate_session(body: InvalidateRequest):
    """Anti-cheat: mark session as terminated (called client-side on tab switch)."""
    db = get_db()

    res = await db.sessions.update_one(
        {"session_id": body.session_id, "status": "active"},
        {"$set": {"status": "terminated"}},
    )
    return {"ok": res.modified_count > 0}
