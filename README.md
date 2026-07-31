# Prometheus AI Tutor

A small AI tutor: ask questions, optionally ground them in an uploaded PDF.

- **Online mode**: paste your own OpenRouter API key in the browser (top of the page).
  It's saved in `localStorage` only — never sent to or stored on the server — and used
  to call **NVIDIA Nemotron 3 Super** (free tier on OpenRouter).
- **Offline mode**: no key needed. If a PDF is uploaded, questions are answered by
  TF-IDF retrieval straight from the document. Without a PDF, a small built-in set of
  AI/ML topic notes answers common questions. This mode also kicks in automatically
  if the OpenRouter call fails or hits its free-tier rate limit, so the app never
  just breaks mid-demo.

## Why it's built this way

The old version depended on CSV catalogs that weren't actually shipped with the code
(gitignored), so every question crashed with `FileNotFoundError`. This rebuild removes
that entire dependency chain — no CSVs, no sentence-transformers/PyTorch (too heavy
for Render's free 512MB tier), no unused templates or a second half-built React
frontend. One Flask app, two small service modules, that's it.

## Run locally

```bash
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

## Deploy on Render (free tier)

1. Push this folder to a GitHub repo.
2. On [render.com](https://dashboard.render.com) → **New → Web Service** → connect the repo.
3. Render will pick up `render.yaml` automatically (or set manually: build command
   `pip install -r requirements.txt`, start command `gunicorn app:app --workers 2 --threads 4 --timeout 120`).
4. No environment variables are required — the API key is entered per-user in the browser.
5. Deploy. First cold start on the free tier can take ~30-60s.

## Notes

- Free OpenRouter accounts get 50 requests/day (1,000/day once you add $10 in credit),
  at 20 requests/minute. The app falls back to offline mode automatically if you hit that.
- In-memory storage (`DOC_STORE`) means an uploaded PDF is lost if the free-tier
  instance restarts or spins down from inactivity — expected behavior for a free deploy,
  not a bug.
