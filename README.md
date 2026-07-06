# Resume–JD Matching Tool (IntelliHire Pro)

An enterprise-grade web application designed to evaluate candidate resumes against job descriptions (JD) using advanced AI parsing, semantic alignment, and validation mechanisms.

## 📸 Application Screenshot
![IntelliHire Pro Results](media/Screen%20Shot%202026-07-06%20at%2020.32.50-fullpage.png)

---

## 📌 Project Overview
This project is built for the E2M Solutions Task 2 Practical Assessment. It compares a candidate's resume and a job description (JD) to extract relevant skills, compute a precise match score, highlight capability gaps, list missing keywords, and provide actionable suggestions for improvement.

---

## 🚀 Key Features

1. **Intelligent Match Scoring:** Evaluates semantic similarity and skills overlap to calculate a `Relevance Match` (0-100%) and a `Candidate Score`.
2. **Skill Ecosystem Extraction:** Identifies and displays technical stacks (with proficiency levels), tools, and soft strengths.
3. **Keyword Optimization:** Highlights matched keywords and explicitly flags missing critical skills in red.
4. **Hiring Verdict & Rationale:** Provides a clear hiring status (Hire Immediately, Consider, Reject) along with a detailed evaluation rationale.
5. **Suggestions for Improvement:** Offers actionable advice for candidates to bridge skills gaps.
6. **Input Reference:** Displays the original parsed resume and job description side-by-side at the bottom for easy verification.

---

## 🛠️ Technology Stack
- **Backend:** Python / Django (v5.0+)
- **Frontend:** Vanilla HTML5, CSS3 (Glassmorphism & dark-mode theme), and FontAwesome
- **AI Service:** DeepSeek-V3.2 
- **Deployment:** Vercel (WSGI Serverless integration)

---

## ⚙️ How to Run Locally

### 1. Set Up Environment
Activate the virtual environment:
```bash
.\venv\Scripts\Activate.ps1
```

Install the dependencies:
```bash
pip install -r requirements.txt
```

### 2. Configure API Key
Create a `.env` file in the root directory and add your API KEY

### 3. Start Development Server
```bash
python manage.py runserver
```
Visit **http://127.0.0.1:8000/** in your browser.

---

