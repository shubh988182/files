# 💼 Daily Job Digest — Setup Guide

A Streamlit app that fetches 100 real jobs daily from LinkedIn, Indeed & Naukri,
compares every job against your resume, and shows your match % + missing skills.

---

## 1. Get your FREE API Key (2 minutes)

1. Go to: https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch
2. Sign up for a free RapidAPI account
3. Click **Subscribe to Test** → select the **Free plan** (500 requests/month)
4. Copy your API key from the header section

> 500 requests/month = ~16 fetches/day of 5 pages each (≈50 jobs per fetch).
> For 100 jobs/day, use 10 pages per fetch = ~10 fetches/month budget carefully.

---

## 2. Run Locally

```bash
# Clone or download this folder, then:
pip install -r requirements.txt
streamlit run app.py
```

Open http://localhost:8501 in your browser.

---

## 3. Deploy FREE on Streamlit Cloud (Always On)

1. Push this folder to a **GitHub repository** (public or private)
2. Go to https://share.streamlit.io
3. Sign in with GitHub
4. Click **New app** → select your repo → set main file to `app.py`
5. Click **Deploy** — your app will be live in ~2 minutes

Your app URL will be: `https://your-app-name.streamlit.app`

> You do NOT need to expose your API key in GitHub.
> In Streamlit Cloud → App settings → **Secrets**, add:
> ```
> RAPIDAPI_KEY = "your_key_here"
> ```
> Then in app.py the key field auto-fills from secrets (already handled).

---

## 4. How to Use Daily

| Step | Action |
|------|--------|
| 1 | Paste your RapidAPI key in the sidebar |
| 2 | Upload your resume PDF |
| 3 | Set role = "Full Stack Developer", location = "India" |
| 4 | Click **Fetch Today's Jobs** |
| 5 | Sort by Match % — apply to top matches first |
| 6 | Export to CSV to track your applications |

---

## 5. Understanding the Match Score

| Score | Meaning |
|-------|---------|
| 80–100% | Strong match — apply immediately |
| 60–79%  | Good match — worth applying |
| Below 60% | Skill gap — check missing skills and learn them |

The **Missing Skills** (red tags) tell you exactly what to learn next.

---

## 6. Free Tier Limits

| Platform | Limit |
|----------|-------|
| Streamlit Cloud | Unlimited free hosting |
| JSearch RapidAPI Free | 500 requests/month |
| Requests per fetch | 5 pages = ~50 jobs |

---

## 7. Folder Structure

```
job_digest/
├── app.py            ← Main Streamlit app
├── requirements.txt  ← Python dependencies
└── README.md         ← This file
```
