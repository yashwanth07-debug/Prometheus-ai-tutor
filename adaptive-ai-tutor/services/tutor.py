"""
Two modes, always one of them works:
  1. ONLINE  -- caller supplies an OpenRouter API key (entered in the
     browser, never stored server-side). Uses NVIDIA Nemotron 3 Super
     (free tier on OpenRouter).
  2. OFFLINE -- no key, or the API call failed/rate-limited. Answers
     from the uploaded PDF (TF-IDF extractive) or a small built-in
     topic-notes dictionary. No external calls, can't fail from the
     network being down.
"""
from typing import Dict, List, Optional

import requests

from services.topics import best_topic_note

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "nvidia/nemotron-3-super-120b-a12b:free"


class TutorError(Exception):
    """Raised with a message that's safe to show the user directly."""


def call_openrouter(api_key: str, question: str, context_chunks: List[str]) -> str:
    system = (
        "You are a friendly, direct AI tutor inside a study app. "
        "Answer clearly, keep it focused, and give one concrete next step. "
        "If context from the student's document is provided, ground your answer in it."
    )
    context = "\n---\n".join(context_chunks[:4]) if context_chunks else ""
    user = f"Context from the student's document:\n{context}\n\nQuestion: {question}" if context else question

    try:
        resp = requests.post(
            OPENROUTER_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://render.com",
                "X-Title": "Prometheus AI Tutor",
            },
            json={
                "model": MODEL,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user},
                ],
                "temperature": 0.4,
                "max_tokens": 700,
            },
            timeout=45,
        )
    except requests.exceptions.RequestException as e:
        raise TutorError(f"Couldn't reach OpenRouter ({e.__class__.__name__}). Switched to offline mode for this answer.")

    if resp.status_code == 401:
        raise TutorError("That API key was rejected by OpenRouter. Double-check it, or clear it to use offline mode.")
    if resp.status_code == 429:
        raise TutorError("OpenRouter's free-tier rate limit was hit. Switched to offline mode for this answer -- try again shortly.")
    if not resp.ok:
        raise TutorError(f"OpenRouter returned an error ({resp.status_code}). Switched to offline mode for this answer.")

    data = resp.json()
    try:
        return data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError):
        raise TutorError("OpenRouter returned an unexpected response. Switched to offline mode for this answer.")


def offline_answer(question: str, context_chunks: List[Dict]) -> str:
    if context_chunks:
        best = context_chunks[0]["text"]
        return f"From your document:\n\n{best}"
    return best_topic_note(question)


def answer_question(question: str, api_key: Optional[str], context_chunks: List[Dict]) -> Dict:
    chunk_texts = [c["text"] for c in context_chunks]

    if api_key:
        try:
            answer = call_openrouter(api_key, question, chunk_texts)
            return {"answer": answer, "mode": "online"}
        except TutorError as e:
            fallback = offline_answer(question, context_chunks)
            return {"answer": f"{e}\n\n{fallback}", "mode": "offline"}

    return {"answer": offline_answer(question, context_chunks), "mode": "offline"}
