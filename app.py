"""
Prometheus AI Tutor -- clean rebuild.

- ONLINE mode: student pastes their own OpenRouter key in the browser
  (stored in localStorage only -- never touches the server's disk/env).
  Uses NVIDIA Nemotron 3 Super (free tier).
- OFFLINE mode: no key needed. Answers straight from an uploaded PDF
  (TF-IDF) or a small built-in topic dictionary. Always works.
"""
import os
import uuid

from flask import Flask, jsonify, render_template_string, request

from services import rag
from services.tutor import answer_question

app = Flask(__name__)
MAX_UPLOAD_MB = 15
app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_MB * 1024 * 1024


# ---------------------------------------------------------------- routes --

@app.route("/")
def index():
    return render_template_string(PAGE)


@app.route("/api/upload", methods=["POST"])
def upload():
    pdf_file = request.files.get("pdf")
    if not pdf_file:
        return jsonify(ok=False, error="No file received."), 400

    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
        text = "".join(page.get_text() for page in doc)
        doc.close()
    except Exception:
        return jsonify(ok=False, error="Couldn't open that file -- is it a valid PDF?"), 400

    doc_id = uuid.uuid4().hex[:12]
    try:
        chunk_count = rag.add_document(doc_id, text)
    except ValueError as e:
        return jsonify(ok=False, error=str(e)), 400

    return jsonify(ok=True, doc_id=doc_id, chunks=chunk_count)


@app.route("/api/ask", methods=["POST"])
def ask():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    doc_id = data.get("doc_id")
    api_key = (data.get("api_key") or "").strip() or None

    if not question:
        return jsonify(ok=False, error="Ask something first."), 400

    context_chunks = rag.retrieve(doc_id, question) if doc_id else []
    result = answer_question(question, api_key, context_chunks)

    return jsonify(ok=True, answer=result["answer"], mode=result["mode"])


@app.route("/healthz")
def healthz():
    return jsonify(ok=True)


# ----------------------------------------------------------------- page --

PAGE = r"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Prometheus &middot; AI Tutor</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,500;9..144,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<style>
  :root{
    --bg-a:#0a1210; --bg-b:#0d1b1c; --bg-c:#131a12;
    --glass:rgba(255,255,255,0.055); --glass-hi:rgba(255,255,255,0.09);
    --border:rgba(255,255,255,0.13); --border-hi:rgba(255,255,255,0.22);
    --flame:#f2b94b; --flame-soft:rgba(242,185,75,0.22); --flame-dim:#c98f2e;
    --text:#eef2ee; --text-dim:#9fb0aa; --text-faint:#657069;
    --ok:#7fd9a6; --err:#e98a8a;
  }
  *{box-sizing:border-box;}
  html,body{height:100%;}
  body{
    margin:0; min-height:100vh; color:var(--text);
    font-family:'Inter',system-ui,sans-serif;
    background:
      radial-gradient(circle at 15% 8%, rgba(242,185,75,0.10), transparent 42%),
      radial-gradient(circle at 85% 0%, rgba(70,140,120,0.14), transparent 45%),
      radial-gradient(circle at 50% 100%, rgba(60,40,20,0.18), transparent 55%),
      linear-gradient(160deg, var(--bg-a), var(--bg-b) 55%, var(--bg-c));
    background-attachment:fixed;
  }
  .wrap{max-width:900px; margin:0 auto; padding:48px 24px 80px;}
  h1,h2,h3{font-family:'Fraunces',serif; font-weight:600; letter-spacing:-0.01em; margin:0;}

  .flame{display:inline-block; width:9px; height:9px; border-radius:50%;
    background:var(--flame); box-shadow:0 0 12px 3px var(--flame-soft);
    animation:flicker 2.6s ease-in-out infinite;}
  @keyframes flicker{0%,100%{opacity:1; transform:scale(1);} 50%{opacity:.7; transform:scale(0.85);}}

  header{display:flex; align-items:baseline; justify-content:space-between; margin-bottom:8px; flex-wrap:wrap; gap:10px;}
  header .brand{display:flex; align-items:center; gap:10px;}
  header h1{font-size:30px;}
  header .tag{color:var(--text-dim); font-size:13px;}
  .modebadge{font-size:11px; padding:5px 12px; border-radius:20px; border:1px solid var(--border);
    background:var(--glass); color:var(--text-dim); letter-spacing:.02em;}
  .modebadge.online{color:var(--ok); border-color:rgba(127,217,166,0.35);}
  .modebadge.offline{color:var(--flame); border-color:rgba(242,185,75,0.35);}

  .glass{
    background:var(--glass); border:1px solid var(--border); border-radius:20px;
    backdrop-filter:blur(18px); -webkit-backdrop-filter:blur(18px);
    padding:22px 24px; margin-top:18px;
  }
  .glass:hover{border-color:var(--border-hi);}

  label.field-label{display:block; font-size:12px; color:var(--text-dim); margin-bottom:8px; letter-spacing:.02em;}
  .keyrow{display:flex; gap:10px; flex-wrap:wrap;}
  input[type=password],input[type=text]{
    flex:1; min-width:220px; background:rgba(0,0,0,0.25); border:1px solid var(--border);
    color:var(--text); border-radius:12px; padding:12px 14px; font-size:14px; font-family:inherit;
    outline:none; transition:border-color .15s;
  }
  input:focus{border-color:var(--flame-dim);}
  button{
    font-family:inherit; font-size:14px; font-weight:500; cursor:pointer;
    border-radius:12px; padding:12px 18px; border:1px solid var(--border);
    background:var(--glass-hi); color:var(--text); transition:all .15s;
  }
  button:hover{border-color:var(--border-hi); transform:translateY(-1px);}
  button.primary{background:var(--flame); color:#241503; border:none; font-weight:600;}
  button.primary:hover{background:#f5c565;}
  button:disabled{opacity:.5; cursor:not-allowed; transform:none;}
  .hint{font-size:12px; color:var(--text-faint); margin-top:9px; line-height:1.5;}
  .hint a{color:var(--text-dim);}

  .dropzone{
    border:1.5px dashed var(--border); border-radius:16px; padding:26px; text-align:center;
    cursor:pointer; transition:border-color .15s, background .15s;
  }
  .dropzone:hover{border-color:var(--flame-dim); background:rgba(242,185,75,0.04);}
  .dropzone .big{font-size:14px; font-weight:500;}
  .dropzone .small{font-size:12px; color:var(--text-faint); margin-top:4px;}
  #uploadStatus{font-size:13px; margin-top:10px; min-height:16px;}

  #chat{height:360px; overflow-y:auto; display:flex; flex-direction:column; gap:14px; padding:6px 2px;}
  .msg{max-width:85%; padding:12px 16px; border-radius:16px; font-size:14px; line-height:1.55; white-space:pre-wrap;}
  .msg .role{font-size:10px; text-transform:uppercase; letter-spacing:.06em; color:var(--text-faint); margin-bottom:4px;}
  .msg.user{align-self:flex-end; background:rgba(242,185,75,0.14); border:1px solid rgba(242,185,75,0.25);}
  .msg.bot{align-self:flex-start; background:rgba(255,255,255,0.05); border:1px solid var(--border);}
  .msg.bot.offline{border-color:rgba(242,185,75,0.3);}

  .askrow{display:flex; gap:10px; margin-top:14px;}
  #question{flex:1;}
  footer{text-align:center; color:var(--text-faint); font-size:12px; margin-top:36px;}
</style>
</head>
<body>
<div class="wrap">

  <header>
    <div class="brand">
      <span class="flame"></span>
      <h1>Prometheus</h1>
    </div>
    <span class="modebadge" id="modeBadge">offline &middot; no key set</span>
  </header>
  <div class="tag">A small AI tutor. Bring your own key, or run it fully offline.</div>

  <div class="glass">
    <label class="field-label">OpenRouter API key (optional)</label>
    <div class="keyrow">
      <input type="password" id="apiKey" placeholder="sk-or-v1-...">
      <button class="primary" onclick="saveKey()">Save</button>
      <button onclick="clearKey()">Clear</button>
    </div>
    <div class="hint">
      Stored only in your browser (localStorage) &mdash; never sent anywhere but OpenRouter, never saved on the server.
      Uses NVIDIA Nemotron 3 Super, free on OpenRouter. No key? The tutor still works offline, just less flexibly.
      Get a free key at <a href="https://openrouter.ai/keys" target="_blank" rel="noopener">openrouter.ai/keys</a>.
    </div>
  </div>

  <div class="glass">
    <label class="field-label">Study material (optional)</label>
    <div class="dropzone" onclick="document.getElementById('pdfInput').click()">
      <div class="big">Drop a PDF here, or click to choose one</div>
      <div class="small">Answers will be grounded in it &mdash; works fully offline too</div>
      <input type="file" id="pdfInput" accept=".pdf" style="display:none" onchange="uploadPdf(event)">
    </div>
    <div id="uploadStatus"></div>
  </div>

  <div class="glass">
    <label class="field-label">Ask the tutor</label>
    <div id="chat"></div>
    <div class="askrow">
      <input type="text" id="question" placeholder="Ask about your PDF, or any AI/ML topic..."
             onkeypress="if(event.key==='Enter') ask()">
      <button class="primary" onclick="ask()">Ask</button>
    </div>
  </div>

  <footer>Prometheus AI Tutor &middot; runs on Render's free tier</footer>
</div>

<script>
let docId = null;

function addMsg(role, text, mode){
  const chat = document.getElementById('chat');
  const div = document.createElement('div');
  div.className = 'msg ' + (role === 'user' ? 'user' : 'bot' + (mode === 'offline' ? ' offline' : ''));
  const label = role === 'user' ? 'You' : (mode === 'offline' ? 'Tutor · offline' : 'Tutor · online');
  div.innerHTML = '<div class="role">'+label+'</div><div></div>';
  div.querySelector('div:last-child').textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

function updateBadge(){
  const badge = document.getElementById('modeBadge');
  const key = localStorage.getItem('openrouter_key');
  if (key){
    badge.textContent = 'online · key set';
    badge.className = 'modebadge online';
  } else {
    badge.textContent = 'offline · no key set';
    badge.className = 'modebadge offline';
  }
}

function saveKey(){
  const val = document.getElementById('apiKey').value.trim();
  if (!val) return;
  localStorage.setItem('openrouter_key', val);
  document.getElementById('apiKey').value = '';
  document.getElementById('apiKey').placeholder = 'sk-or-v1-•••• saved';
  updateBadge();
}

function clearKey(){
  localStorage.removeItem('openrouter_key');
  document.getElementById('apiKey').placeholder = 'sk-or-v1-...';
  updateBadge();
}

async function uploadPdf(e){
  const file = e.target.files[0];
  if (!file) return;
  const status = document.getElementById('uploadStatus');
  status.style.color = 'var(--text-dim)';
  status.textContent = 'Processing ' + file.name + '...';

  const form = new FormData();
  form.append('pdf', file);
  try{
    const res = await fetch('/api/upload', {method:'POST', body:form});
    const data = await res.json();
    if (data.ok){
      docId = data.doc_id;
      status.style.color = 'var(--ok)';
      status.textContent = 'Ready — ' + data.chunks + ' chunks indexed from ' + file.name;
      addMsg('bot', "Loaded your PDF (" + data.chunks + " chunks). Ask me anything about it.", 'offline');
    } else {
      status.style.color = 'var(--err)';
      status.textContent = data.error;
    }
  } catch(err){
    status.style.color = 'var(--err)';
    status.textContent = 'Upload failed — try again.';
  }
}

async function ask(){
  const input = document.getElementById('question');
  const question = input.value.trim();
  if (!question) return;
  addMsg('user', question);
  input.value = '';

  const apiKey = localStorage.getItem('openrouter_key') || null;

  try{
    const res = await fetch('/api/ask', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({question, doc_id: docId, api_key: apiKey})
    });
    const data = await res.json();
    if (data.ok){
      addMsg('bot', data.answer, data.mode);
    } else {
      addMsg('bot', data.error || "Something went wrong.", 'offline');
    }
  } catch(err){
    addMsg('bot', 'Network error — is the server running?', 'offline');
  }
}

updateBadge();
addMsg('bot', "Hi! I'm Prometheus. Add an OpenRouter key above for full answers, or just ask me an AI/ML question or upload a PDF — I work offline too.", 'offline');
</script>
</body>
</html>
"""

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
