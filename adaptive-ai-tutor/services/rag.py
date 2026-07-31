"""
Lightweight RAG: PDF text -> chunks -> TF-IDF retrieval.
No PyTorch / sentence-transformers, so it's safe on Render's free tier
(512MB RAM) and works fully offline once a PDF is uploaded.
"""
from typing import Dict, List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DOC_STORE: Dict[str, Dict] = {}


def chunk_text(text: str, chunk_size: int = 700) -> List[str]:
    sentences = text.replace("\n", " ").split(". ")
    chunks, current = [], ""
    for sent in sentences:
        if len(current) + len(sent) > chunk_size:
            if current.strip():
                chunks.append(current.strip())
            current = sent + ". "
        else:
            current += sent + ". "
    if current.strip():
        chunks.append(current.strip())
    return chunks


def add_document(doc_id: str, text: str) -> int:
    chunks = [c for c in chunk_text(text) if any(ch.isalnum() for ch in c)]
    if not chunks:
        raise ValueError("No readable text found in this PDF (likely a scanned/image PDF).")

    vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2), max_features=5000)
    try:
        matrix = vectorizer.fit_transform(chunks)
    except ValueError:
        # e.g. a PDF that's just numbers/symbols with no real vocabulary
        raise ValueError("Couldn't index this PDF's text -- try a different file.")

    DOC_STORE[doc_id] = {"chunks": chunks, "vectorizer": vectorizer, "matrix": matrix}
    return len(chunks)


def retrieve(doc_id: str, query: str, top_k: int = 4) -> List[Dict]:
    store = DOC_STORE.get(doc_id)
    if not store:
        return []
    q_vec = store["vectorizer"].transform([query])
    sims = cosine_similarity(q_vec, store["matrix"]).flatten()
    top_idx = sims.argsort()[-top_k:][::-1]
    results = [
        {"text": store["chunks"][i], "score": round(float(sims[i]), 4)}
        for i in top_idx
        if sims[i] > 0.03
    ]
    if not results and len(store["chunks"]) > 0:
        results = [{"text": store["chunks"][0], "score": 0.0}]
    return results
