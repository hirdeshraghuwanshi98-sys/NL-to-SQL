# 🧠 NL-to-SQL — GenAI Project

Ask questions in plain English. Get SQL + results instantly.
**One file. Pure Python. No React. No npm.**

---

## ▶ Run it in 3 steps

### Step 1 — Install (only one library)
```bash
pip install openai
```

### Step 2 — Add your OpenAI API key
Open `app.py` and set line 14:
```python
API_KEY = "sk-your-key-here"
```
Get a key free at: https://platform.openai.com/api-keys

### Step 3 — Run
```bash
python app.py
```
Then open **http://localhost:8080** in your browser. Done ✅

---

## 🔮 What it does
- You type: *"Show top 3 highest paid employees"*
- AI (GPT-4o-mini) generates the SQL
- App runs it on a real SQLite database
- Shows you the results in a table

## 📁 Files
```
app.py            ← The entire app (backend + UI in one file)
requirements.txt  ← Just: openai
README.md         ← This file
```

## 🗄️ Sample Database (built in)
| Table | Columns |
|-------|---------|
| employees | id, name, department, salary, hire_date |
| departments | id, name, budget, location |
| projects | id, name, status, start_date |
| assignments | employee_id, project_id, role, hours_per_week |

## 💡 Example Questions to Try
- *Top 3 highest paid employees*
- *Average salary per department*
- *All active projects*
- *Employees in Engineering with salary above 90000*
- *How many employees per department?*

---

## 🐙 Push to GitHub (impress recruiters)
```bash
git init
git add .
git commit -m "NL-to-SQL GenAI app — plain English to SQL using GPT-4o"
git remote add origin https://github.com/YOUR_USERNAME/nl-to-sql.git
git push -u origin main
```
