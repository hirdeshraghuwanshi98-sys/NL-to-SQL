"""
NL-to-SQL GenAI App
====================
Run:  python app.py
Then: open http://localhost:8080

No React. No npm. No frontend setup. Just Python.
"""

import os, json, sqlite3, urllib.request, urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

from dotenv import load_dotenv
load_dotenv()

# ─── CONFIG ──────────────────────────────────────────────────────────────────
# Get FREE key at: https://openrouter.ai → Sign In → Keys → Create Key
# Key looks like: sk-or-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
API_KEY = ""
PORT    = 8080

# ─── SAMPLE DATABASE ─────────────────────────────────────────────────────────
SCHEMA = """
Tables available:
  employees   (id, name, department, salary, hire_date)
  departments (id, name, budget, location)
  projects    (id, name, status, start_date)
  assignments (employee_id, project_id, role, hours_per_week)
"""

SEED_SQL = """
CREATE TABLE employees (id INTEGER PRIMARY KEY, name TEXT, department TEXT, salary REAL, hire_date TEXT);
CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT, budget REAL, location TEXT);
CREATE TABLE projects (id INTEGER PRIMARY KEY, name TEXT, status TEXT, start_date TEXT);
CREATE TABLE assignments (employee_id INTEGER, project_id INTEGER, role TEXT, hours_per_week INTEGER);

INSERT INTO departments VALUES (1,'Engineering',500000,'New York'),(2,'Marketing',200000,'San Francisco'),(3,'HR',150000,'Chicago'),(4,'Sales',300000,'Austin');
INSERT INTO employees VALUES
  (1,'Alice Johnson','Engineering',95000,'2020-03-15'),
  (2,'Bob Smith','Engineering',88000,'2021-06-01'),
  (3,'Carol White','Marketing',72000,'2019-11-20'),
  (4,'David Brown','HR',65000,'2022-01-10'),
  (5,'Eve Davis','Engineering',102000,'2018-08-05'),
  (6,'Frank Miller','Sales',78000,'2021-03-22'),
  (7,'Grace Lee','Marketing',68000,'2023-02-14'),
  (8,'Henry Wilson','Engineering',91000,'2020-09-30');
INSERT INTO projects VALUES (1,'AI Platform','active','2023-01-01'),(2,'Brand Refresh','completed','2023-03-01'),(3,'CRM Integration','active','2023-06-01'),(4,'Data Pipeline','active','2024-01-01');
INSERT INTO assignments VALUES (1,1,'Lead',30),(2,1,'Developer',40),(5,1,'Developer',35),(3,2,'Manager',25),(7,2,'Designer',40),(6,3,'Analyst',20),(8,4,'Engineer',40);
"""

def run_query(sql):
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(SEED_SQL)
    cur = conn.cursor()
    cur.execute(sql)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# ─── AI (OpenRouter — FREE, works in India) ───────────────────────────────────
def ask_ai(question):
    key = API_KEY or os.getenv("OPENROUTER_API_KEY", "")

    system = f"""You are an expert SQL assistant. Convert English questions to SQLite SQL.

{SCHEMA}

Reply ONLY with a JSON object, nothing else:
{{
  "sql": "SELECT ...",
  "explanation": "This query ...",
  "tables": ["employees"]
}}

Rules: read-only SELECT queries only. Add LIMIT 50 for large result sets."""

    payload = json.dumps({
        "model": "openrouter/auto",
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": question}
        ],
        "temperature": 0
    }).encode()

    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
            "HTTP-Referer": "http://localhost:8080",
        }
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        data = json.loads(r.read())

    text = data["choices"][0]["message"]["content"]
    text = text.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
    return json.loads(text)

# ─── HTML UI ──────────────────────────────────────────────────────────────────
HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>NL→SQL — GenAI</title>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Sora:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#080b14;--surface:#0f1320;--card:#141828;--border:#1e2540;
  --accent:#6d6aff;--accent2:#a78bfa;--red:#f87171;
  --text:#e4e8f7;--muted:#5a6080;--mono:'JetBrains Mono',monospace;
}
body{background:var(--bg);color:var(--text);font-family:'Sora',sans-serif;min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:40px 20px}
h1{font-size:clamp(24px,4vw,42px);font-weight:700;background:linear-gradient(135deg,#a78bfa,#6d6aff,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;background-clip:text;margin-bottom:6px;text-align:center}
.subtitle{color:var(--muted);font-size:14px;margin-bottom:40px;text-align:center}
.container{width:100%;max-width:820px}
.schema-bar{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:28px}
.schema-pill{background:var(--card);border:1px solid var(--border);border-radius:20px;padding:5px 14px;font-size:12px;font-family:var(--mono);color:var(--muted)}
.schema-pill span{color:var(--accent2)}
.input-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:24px;margin-bottom:20px;transition:border-color .2s}
.input-card:focus-within{border-color:var(--accent)}
textarea{width:100%;background:none;border:none;outline:none;color:var(--text);font-family:'Sora',sans-serif;font-size:16px;resize:none;line-height:1.7;min-height:80px}
textarea::placeholder{color:var(--muted)}
.input-footer{display:flex;justify-content:space-between;align-items:center;margin-top:16px;padding-top:16px;border-top:1px solid var(--border)}
.hint{font-size:12px;color:var(--muted)}
button.run{background:var(--accent);color:#fff;border:none;border-radius:10px;padding:10px 28px;font-size:14px;font-weight:600;font-family:'Sora',sans-serif;cursor:pointer;transition:all .2s;display:flex;align-items:center;gap:8px}
button.run:hover{background:#8583ff;transform:translateY(-1px)}
button.run:disabled{background:var(--border);color:var(--muted);cursor:not-allowed;transform:none}
.ex-label{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:1px;margin-bottom:10px}
.examples{display:flex;flex-wrap:wrap;gap:8px;margin-bottom:28px}
.ex-btn{background:var(--card);border:1px solid var(--border);border-radius:8px;padding:7px 13px;font-size:13px;color:var(--muted);cursor:pointer;transition:all .15s;font-family:'Sora',sans-serif}
.ex-btn:hover{border-color:var(--accent);color:var(--text)}
.result-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;overflow:hidden;margin-bottom:20px;animation:fadeUp .3s ease}
@keyframes fadeUp{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}
.tabs{display:flex;border-bottom:1px solid var(--border)}
.tab{padding:12px 20px;font-size:13px;font-weight:600;color:var(--muted);cursor:pointer;border-bottom:2px solid transparent;transition:all .15s;background:none;border-top:none;border-left:none;border-right:none;font-family:'Sora',sans-serif}
.tab.active{color:var(--accent);border-bottom-color:var(--accent)}
.tab-panel{display:none;padding:20px}
.tab-panel.active{display:block}
pre.sql{background:var(--bg);border:1px solid var(--border);border-radius:10px;padding:16px;overflow-x:auto;font-family:var(--mono);font-size:13px;line-height:1.8;position:relative}
.copy-btn{position:absolute;top:10px;right:10px;background:var(--card);border:1px solid var(--border);color:var(--muted);border-radius:6px;padding:4px 10px;font-size:11px;cursor:pointer;font-family:'Sora',sans-serif}
.kw{color:#c792ea;font-weight:600}.tb{color:#82aaff}.st{color:#c3e88d}.nm{color:#f78c6c}
.table-wrap{overflow-x:auto;border-radius:10px;border:1px solid var(--border)}
table{width:100%;border-collapse:collapse;font-size:13px}
th{background:#0a0e1a;padding:10px 14px;text-align:left;color:var(--accent2);font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:.5px;border-bottom:1px solid var(--border);white-space:nowrap}
td{padding:9px 14px;border-bottom:1px solid var(--border);font-family:var(--mono);color:#c8cad6}
tr:last-child td{border-bottom:none}
tr:nth-child(even) td{background:rgba(255,255,255,.02)}
.null{color:var(--muted);font-style:italic}
.row-count{font-size:12px;color:var(--muted);margin-top:10px}
.explanation{font-size:14px;line-height:1.8;color:#9ca3c4}
.tables-used{display:flex;gap:8px;flex-wrap:wrap;margin-top:16px}
.tbl-badge{background:#1a1550;color:var(--accent2);border-radius:6px;padding:4px 12px;font-size:12px;font-family:var(--mono)}
.error-card{background:#1a0a0a;border:1px solid #5a1a1a;border-radius:12px;padding:16px 20px;color:var(--red);font-size:14px;margin-bottom:20px;animation:fadeUp .3s ease}
.spinner{width:16px;height:16px;border:2px solid rgba(255,255,255,.2);border-top-color:#fff;border-radius:50%;animation:spin .7s linear infinite}
@keyframes spin{to{transform:rotate(360deg)}}
.warn{background:#1a1200;border:1px solid #5a4000;border-radius:12px;padding:14px 18px;color:#fbbf24;font-size:13px;margin-bottom:24px;line-height:1.6}
.warn code{background:#2a2000;padding:2px 6px;border-radius:4px;font-family:var(--mono)}
</style>
</head>
<body>
<div class="container">
  <h1>Natural Language → SQL</h1>
  <p class="subtitle">Ask questions in plain English. Powered by OpenRouter (Llama 3.1) — Free & Fast.</p>

  <div class="warn" id="warn" style="display:none">
    ⚠️ No API key set. Open <code>app.py</code>, set <code>API_KEY = "sk-or-..."</code> and restart.
    Get free key at <strong>openrouter.ai</strong>
  </div>

  <div class="schema-bar">
    <div class="schema-pill"><span>employees</span> · id, name, department, salary, hire_date</div>
    <div class="schema-pill"><span>departments</span> · id, name, budget, location</div>
    <div class="schema-pill"><span>projects</span> · id, name, status, start_date</div>
    <div class="schema-pill"><span>assignments</span> · employee_id, project_id, role, hours_per_week</div>
  </div>

  <div class="ex-label">Try an example</div>
  <div class="examples">
    <button class="ex-btn" onclick="useExample(this)">Top 3 highest paid employees</button>
    <button class="ex-btn" onclick="useExample(this)">Average salary per department</button>
    <button class="ex-btn" onclick="useExample(this)">All active projects</button>
    <button class="ex-btn" onclick="useExample(this)">Employees in Engineering with salary above 90000</button>
    <button class="ex-btn" onclick="useExample(this)">How many employees per department?</button>
    <button class="ex-btn" onclick="useExample(this)">Show all employees hired after 2021</button>
  </div>

  <div class="input-card">
    <textarea id="q" placeholder="e.g. Show me employees in Engineering sorted by salary..." rows="3"
      onkeydown="if(event.key==='Enter'&&!event.shiftKey){event.preventDefault();run()}"></textarea>
    <div class="input-footer">
      <span class="hint">Press Enter to run · Shift+Enter for new line</span>
      <button class="run" id="runBtn" onclick="run()">
        <span id="btnIcon">▶</span>
        <span id="btnText">Generate SQL</span>
      </button>
    </div>
  </div>

  <div id="error" class="error-card" style="display:none"></div>
  <div id="result" class="result-card" style="display:none">
    <div class="tabs">
      <button class="tab active" onclick="switchTab('results',this)">Results <span id="rowBadge"></span></button>
      <button class="tab" onclick="switchTab('sql',this)">SQL</button>
      <button class="tab" onclick="switchTab('info',this)">Explanation</button>
    </div>
    <div id="tab-results" class="tab-panel active"></div>
    <div id="tab-sql" class="tab-panel">
      <div style="position:relative">
        <pre class="sql" id="sqlBlock"></pre>
        <button class="copy-btn" onclick="copySql()">Copy</button>
      </div>
    </div>
    <div id="tab-info" class="tab-panel">
      <div class="explanation" id="explainBlock"></div>
      <div class="tables-used" id="tablesBlock"></div>
    </div>
  </div>
</div>

<script>
fetch('/api?q=__ping__').then(r=>r.json()).then(d=>{
  if(d.no_key) document.getElementById('warn').style.display='block';
}).catch(()=>{});

function useExample(btn){ document.getElementById('q').value=btn.textContent; run(); }

function switchTab(name,btn){
  document.querySelectorAll('.tab').forEach(t=>t.classList.remove('active'));
  document.querySelectorAll('.tab-panel').forEach(p=>p.classList.remove('active'));
  btn.classList.add('active');
  document.getElementById('tab-'+name).classList.add('active');
}

function highlightSQL(sql){
  const kws=/\b(SELECT|FROM|WHERE|JOIN|LEFT|RIGHT|INNER|ON|GROUP BY|ORDER BY|HAVING|LIMIT|AS|AND|OR|NOT|IN|LIKE|IS|NULL|COUNT|SUM|AVG|MAX|MIN|DISTINCT|BY|ASC|DESC|CASE|WHEN|THEN|ELSE|END|ROUND|COALESCE)\b/gi;
  return sql
    .replace(kws,m=>`<span class="kw">${m}</span>`)
    .replace(/\b(employees|departments|projects|assignments)\b/gi,m=>`<span class="tb">${m}</span>`)
    .replace(/'([^']*)'/g,(_,p)=>`<span class="st">'${p}'</span>`)
    .replace(/\b(\d+(?:\.\d+)?)\b/g,m=>`<span class="nm">${m}</span>`);
}

async function run(){
  const q=document.getElementById('q').value.trim();
  if(!q) return;
  const btn=document.getElementById('runBtn');
  document.getElementById('btnIcon').innerHTML='<div class="spinner"></div>';
  document.getElementById('btnText').textContent='Thinking...';
  btn.disabled=true;
  document.getElementById('error').style.display='none';
  document.getElementById('result').style.display='none';
  try{
    const res=await fetch('/api?q='+encodeURIComponent(q));
    const data=await res.json();
    if(data.error){
      document.getElementById('error').textContent='⚠️ '+data.error;
      document.getElementById('error').style.display='block';
    } else {
      document.getElementById('sqlBlock').innerHTML=highlightSQL(data.sql);
      const rows=data.results||[];
      document.getElementById('rowBadge').textContent=rows.length?`(${rows.length})`:'';
      if(rows.length>0){
        const cols=Object.keys(rows[0]);
        let html='<div class="table-wrap"><table><thead><tr>';
        cols.forEach(c=>html+=`<th>${c}</th>`);
        html+='</tr></thead><tbody>';
        rows.forEach(row=>{
          html+='<tr>';
          cols.forEach(c=>{const v=row[c];html+=v===null?'<td><span class="null">NULL</span></td>':`<td>${v}</td>`;});
          html+='</tr>';
        });
        html+=`</tbody></table></div><div class="row-count">${rows.length} row${rows.length!==1?'s':''} returned</div>`;
        document.getElementById('tab-results').innerHTML=html;
      } else {
        document.getElementById('tab-results').innerHTML='<div style="color:var(--muted);text-align:center;padding:20px">No rows returned</div>';
      }
      document.getElementById('explainBlock').textContent=data.explanation;
      document.getElementById('tablesBlock').innerHTML=(data.tables||[]).map(t=>`<span class="tbl-badge">${t}</span>`).join('');
      document.getElementById('result').style.display='block';
      switchTab('results',document.querySelector('.tab'));
    }
  } catch(e){
    document.getElementById('error').textContent='⚠️ Network error — is the server running?';
    document.getElementById('error').style.display='block';
  } finally {
    document.getElementById('btnIcon').textContent='▶';
    document.getElementById('btnText').textContent='Generate SQL';
    btn.disabled=false;
  }
}

function copySql(){
  navigator.clipboard.writeText(document.getElementById('sqlBlock').textContent);
  document.querySelector('.copy-btn').textContent='✓ Copied';
  setTimeout(()=>document.querySelector('.copy-btn').textContent='Copy',1500);
}
</script>
</body>
</html>"""

# ─── HTTP SERVER ──────────────────────────────────────────────────────────────
class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        print(f"  {args[0]} {args[1]}")

    def send_json(self, data, status=200):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", len(body))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)

        if parsed.path == "/" or parsed.path == "":
            body = HTML.encode()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", len(body))
            self.end_headers()
            self.wfile.write(body)
            return

        if parsed.path == "/api":
            params = parse_qs(parsed.query)
            question = params.get("q", [""])[0].strip()

            if question == "__ping__":
                key = API_KEY or os.getenv("OPENROUTER_API_KEY", "")
                self.send_json({"no_key": not bool(key)})
                return

            if not question:
                self.send_json({"error": "No question provided"})
                return

            key = API_KEY or os.getenv("OPENROUTER_API_KEY", "")
            if not key:
                self.send_json({"error": "API key not set. Open app.py and set API_KEY = 'sk-or-...'"})
                return

            try:
                ai = ask_ai(question)
                sql = ai.get("sql", "")
                explanation = ai.get("explanation", "")
                tables = ai.get("tables", [])
                try:
                    results = run_query(sql)
                except Exception as e:
                    results = []
                    explanation += f"\n\nNote: query error — {e}"
                self.send_json({"sql": sql, "explanation": explanation, "tables": tables, "results": results})
            except Exception as e:
                self.send_json({"error": str(e)})
            return

        self.send_response(404)
        self.end_headers()


# ─── START ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    key = API_KEY or os.getenv("OPENROUTER_API_KEY", "")
    print()
    print("  🧠 NL-to-SQL GenAI App")
    print("  ─────────────────────────────────")
    if key and not key.endswith("_HERE"):
        print(f"  ✅ API key found ({key[:10]}...)")
    else:
        print("  ⚠️  No API key! Open app.py and set API_KEY")
        print("      Get FREE key: openrouter.ai")
    print(f"  🌐 Open: http://localhost:{PORT}")
    print("  ─────────────────────────────────")
    print()
    PORT = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("", PORT), Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n  Stopped.")
