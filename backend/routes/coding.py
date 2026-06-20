from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
import random
# pyrefly: ignore [missing-import]
import google.generativeai as genai
import httpx
from datetime import datetime, timezone
from config import GEMINI_API_KEY, NVIDIA_API_KEY, AI_PROVIDER
from coding_questions import CODING_BANK
from database import get_db

router = APIRouter(prefix="/api/coding", tags=["coding"])

genai.configure(api_key=GEMINI_API_KEY)

class CodeSubmission(BaseModel):
    question_id: str
    code: str
    language: str = "python"
    email: str = None  # Optional email for linking

@router.get("/start")
async def get_coding_question():
    # Pick 1 random question for the round
    question = random.choice(CODING_BANK)
    return question

@router.post("/submit")
async def submit_code(submission: CodeSubmission):
    # Find question
    q = next((x for x in CODING_BANK if x["id"] == submission.question_id), None)
    if not q:
        raise HTTPException(status_code=404, detail="Question not found")
        
    db = get_db()
        
    # AI Evaluation Strategy
    prompt = f"""
Evaluate this code for: {q['title']}
Code:
{submission.code}

Output exactly these sections (BE BRIEF, 2 sentences max each):
1. [SCORE]: X/10
2. [FEEDBACK]: Logic/cleanliness critique.
3. [REFACTOR]: Short suggestion or fix.
"""
    
    # AI Evaluation Strategy: Prioritize NVIDIA NIM if key exists
    ai_evaluation = None
    if NVIDIA_API_KEY:
        print(f"DEBUG: Using NVIDIA NIM for {q['title']}")
        try:
            ai_evaluation = await _evaluate_nvidia_coding(prompt)
        except Exception as e:
            print(f"⚠️ NVIDIA Coding Error: {e} — falling back to Gemini")

    if not ai_evaluation:
        print(f"DEBUG: Using Gemini for {q['title']}")
        try:
            if not GEMINI_API_KEY:
                ai_evaluation = "AI evaluation failed: No API keys configured."
            else:
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('models/gemini-2.5-flash')
                response = model.generate_content(prompt)
                ai_evaluation = response.text
        except Exception as e:
            ai_evaluation = f"AI evaluation failed: {str(e)}"

    # Save to history if email provided
    if submission.email and ai_evaluation:
        await db.users.update_one(
            {"email": submission.email},
            {
                "$set": {"coding_rank": "Advanced Candidate", "last_activity": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")},
                "$push": {"test_history": {"type": "coding", "title": q["title"], "date": datetime.now(timezone.utc)}}
            }
        )

    return {
        "question_id": q["id"],
        "title": q["title"],
        "evaluation": ai_evaluation
    }

async def _evaluate_nvidia_coding(prompt):
    url = "https://integrate.api.nvidia.com/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "google/diffusiongemma-26b-a4b-it",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.5,
        "max_tokens": 1024,
        "top_p": 0.95
    }
    
    async with httpx.AsyncClient() as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"].strip()
