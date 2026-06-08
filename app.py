import streamlit as st
import requests
import json
import re
import time
from datetime import datetime
import pandas as pd
import PyPDF2
import io
from config import JSEARCH_API_KEY

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Daily Job Digest",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.job-card {
    border: 1px solid #e0e0e0;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    background: #ffffff;
}
.match-high   { color: #1D9E75; font-weight: 600; }
.match-medium { color: #378ADD; font-weight: 600; }
.match-low    { color: #888780; font-weight: 600; }
.platform-badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 500;
}
.badge-linkedin { background: #E6F1FB; color: #0C447C; }
.badge-naukri   { background: #FAEEDA; color: #633806; }
.badge-indeed   { background: #EAF3DE; color: #27500A; }
.missing-tag {
    background: #FCEBEB;
    color: #A32D2D;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 12px;
    margin: 2px;
    display: inline-block;
}
.skill-tag {
    background: #EEEDFE;
    color: #3C3489;
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 12px;
    margin: 2px;
    display: inline-block;
}
.stProgress > div > div > div { border-radius: 999px; }
</style>
""", unsafe_allow_html=True)


# ── Helpers ────────────────────────────────────────────────────────────────────

def extract_text_from_pdf(file) -> str:
    reader = PyPDF2.PdfReader(file)
    return " ".join(page.extract_text() or "" for page in reader.pages)


def extract_skills_from_text(text: str) -> list[str]:
    """Pull known tech keywords from any block of text."""
    SKILL_POOL = [
        "python","java","javascript","typescript","react","angular","vue","node.js","nodejs",
        "express","django","flask","fastapi","spring","asp.net",".net","c#","c++","php",
        "ruby","rails","golang","go","rust","kotlin","swift","html","css","sass","bootstrap",
        "tailwind","sql","mysql","postgresql","mongodb","redis","elasticsearch","firebase",
        "aws","azure","gcp","docker","kubernetes","jenkins","github actions","ci/cd","git",
        "rest api","graphql","microservices","kafka","rabbitmq","tensorflow","pytorch",
        "machine learning","deep learning","nlp","data science","pandas","numpy","linux",
        "bash","powershell","agile","scrum","jira","figma","selenium","junit","jest",
        "webpack","vite","redux","next.js","nuxt","flutter","react native","android","ios",
        "xamarin","azure devops","terraform","ansible","nginx","apache","hadoop","spark",
    ]
    text_lower = text.lower()
    return list({s for s in SKILL_POOL if re.search(r'\b' + re.escape(s) + r'\b', text_lower)})


def compute_match(resume_skills: list[str], job_text: str) -> tuple[int, list[str], list[str]]:
    """Return (match_pct, matched_skills, missing_skills)."""
    job_skills = extract_skills_from_text(job_text)
    if not job_skills:
        return 50, [], []
    matched  = [s for s in job_skills if s in resume_skills]
    missing  = [s for s in job_skills if s not in resume_skills]
    pct = int(len(matched) / len(job_skills) * 100)
    return pct, matched, missing


def match_color_class(pct: int) -> str:
    if pct >= 80: return "match-high"
    if pct >= 60: return "match-medium"
    return "match-low"


# ── API: JSearch (RapidAPI) ────────────────────────────────────────────────────

def fetch_jsearch(query: str, location: str, api_key: str, num_pages: int = 5) -> list[dict]:
    """Fetch jobs from JSearch API. Returns normalised job dicts."""
    url = "https://jsearch.p.rapidapi.com/search"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "jsearch.p.rapidapi.com",
    }
    jobs = []
    for page in range(1, num_pages + 1):
        params = {
            "query": f"{query} in {location}",
            "page": str(page),
            "num_pages": "1",
            "date_posted": "today",
        }
        try:
            r = requests.get(url, headers=headers, params=params, timeout=15)
            if r.status_code == 200:
                data = r.json().get("data", [])
                for j in data:
                    jobs.append({
                        "title":       j.get("job_title", ""),
                        "company":     j.get("employer_name", ""),
                        "location":    j.get("job_city", "") or j.get("job_country", ""),
                        "type":        "Remote" if j.get("job_is_remote") else "Onsite",
                        "description": j.get("job_description", ""),
                        "url":         j.get("job_apply_link") or j.get("job_google_link", "#"),
                        "platform":    j.get("job_publisher", "Indeed"),
                        "posted":      j.get("job_posted_at_datetime_utc", ""),
                        "salary":      _salary(j),
                    })
        except Exception:
            pass
        time.sleep(0.3)
    return jobs


def _salary(j: dict) -> str:
    mn = j.get("job_min_salary")
    mx = j.get("job_max_salary")
    cur = j.get("job_salary_currency", "")
    if mn and mx:
        return f"{cur} {int(mn):,} – {int(mx):,}"
    return "Not disclosed"


# ── Sidebar ────────────────────────────────────────────────────────────────────

with st.sidebar:
    st.title("⚙️ Settings")

    st.subheader("🔑 API Key")
    api_key = st.text_input(
        "JSearch RapidAPI Key",
        value=JSEARCH_API_KEY,
        type="password",
        help="Get free key at rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch",
        placeholder="Paste your key here…",
    )
    st.caption("[Get free API key →](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch)")

    st.divider()

    st.subheader("🎯 Job Preferences")
    job_role = st.text_input("Job Role", value="Full Stack Developer")
    location  = st.text_input("Location", value="India")
    platforms = st.multiselect(
        "Platforms",
        ["LinkedIn", "Indeed", "Naukri", "Glassdoor"],
        default=["LinkedIn", "Indeed", "Naukri"],
    )
    job_type  = st.multiselect(
        "Work Type",
        ["Remote", "Hybrid", "Onsite"],
        default=["Remote", "Hybrid", "Onsite"],
    )
    min_match = st.slider("Minimum match %", 0, 100, 50)
    num_pages = st.slider("Pages to fetch (≈10 jobs/page)", 1, 10, 5,
                          help="5 pages ≈ 50 jobs, 10 pages ≈ 100 jobs")

    st.divider()

    st.subheader("📄 Your Resume")
    resume_file = st.file_uploader("Upload PDF resume", type=["pdf"])
    resume_text_manual = st.text_area(
        "Or paste resume text",
        height=120,
        placeholder="Paste skills, experience, tech stack here…",
    )

    fetch_btn = st.button("🔍 Fetch Today's Jobs", type="primary", use_container_width=True)


# ── Extract resume skills ──────────────────────────────────────────────────────

resume_text = ""
if resume_file:
    resume_text = extract_text_from_pdf(resume_file)
elif resume_text_manual.strip():
    resume_text = resume_text_manual

resume_skills = extract_skills_from_text(resume_text) if resume_text else []


# ── Main area ──────────────────────────────────────────────────────────────────

st.title("💼 Daily Job Digest")
st.caption(f"Last refreshed: {datetime.now().strftime('%d %b %Y, %I:%M %p')}")

if resume_skills:
    st.success(f"✅ Resume loaded — detected **{len(resume_skills)} skills**: " +
               ", ".join(f"`{s}`" for s in sorted(resume_skills)[:20]) +
               ("…" if len(resume_skills) > 20 else ""))

# ── Fetch jobs ─────────────────────────────────────────────────────────────────

if "jobs" not in st.session_state:
    st.session_state.jobs = []

if fetch_btn:
    if not api_key:
        st.error("Please enter your JSearch RapidAPI key in the sidebar.")
    else:
        with st.spinner(f"Fetching {job_role} jobs from {location}… (this takes ~10s)"):
            raw_jobs = fetch_jsearch(job_role, location, api_key, num_pages)

        # Compute match for every job
        enriched = []
        for j in raw_jobs:
            full_text = j["title"] + " " + j["description"]
            pct, matched, missing = compute_match(resume_skills, full_text)
            j["match_pct"] = pct
            j["matched_skills"] = matched
            j["missing_skills"] = missing
            enriched.append(j)

        # Filter by type
        if job_type:
            enriched = [j for j in enriched if j["type"] in job_type]

        # Filter by min match (only if resume uploaded)
        if resume_skills:
            enriched = [j for j in enriched if j["match_pct"] >= min_match]

        # Sort best match first
        enriched.sort(key=lambda j: j["match_pct"], reverse=True)

        st.session_state.jobs = enriched
        st.success(f"Found **{len(enriched)} jobs** matching your preferences.")

jobs = st.session_state.jobs

# ── Stats row ──────────────────────────────────────────────────────────────────

if jobs:
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total Jobs", len(jobs))
    col2.metric("Avg Match", f"{int(sum(j['match_pct'] for j in jobs)/len(jobs))}%" if resume_skills else "—")
    col3.metric("Strong Match (≥80%)", sum(1 for j in jobs if j["match_pct"] >= 80) if resume_skills else "—")
    col4.metric("Remote", sum(1 for j in jobs if j["type"] == "Remote"))
    top = jobs[0]["company"] if jobs else "—"
    col5.metric("Top Match", jobs[0]["title"][:20] + "…" if jobs else "—")

    st.divider()

    # ── Filters ───────────────────────────────────────────────────────────────
    fc1, fc2, fc3 = st.columns([2, 2, 2])
    with fc1:
        search_q = st.text_input("🔎 Search jobs", placeholder="e.g. React, .NET, Remote…")
    with fc2:
        sort_by = st.selectbox("Sort by", ["Match %", "Company", "Title"])
    with fc3:
        show_n = st.slider("Jobs to show", 1, max(10, min(200, len(jobs))), min(50, len(jobs)))

    # Apply search filter
    display_jobs = jobs
    if search_q.strip():
        q = search_q.lower()
        display_jobs = [
            j for j in jobs
            if q in j["title"].lower()
            or q in j["company"].lower()
            or q in j["description"].lower()
        ]

    # Sort
    if sort_by == "Company":
        display_jobs = sorted(display_jobs, key=lambda j: j["company"])
    elif sort_by == "Title":
        display_jobs = sorted(display_jobs, key=lambda j: j["title"])
    else:
        display_jobs = sorted(display_jobs, key=lambda j: j["match_pct"], reverse=True)

    display_jobs = display_jobs[:show_n]

    # ── Export ────────────────────────────────────────────────────────────────
    df_export = pd.DataFrame([{
        "Title":    j["title"],
        "Company":  j["company"],
        "Location": j["location"],
        "Type":     j["type"],
        "Match %":  j["match_pct"],
        "Missing":  ", ".join(j["missing_skills"]),
        "Salary":   j["salary"],
        "URL":      j["url"],
        "Platform": j["platform"],
    } for j in display_jobs])

    csv = df_export.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Export to CSV",
        data=csv,
        file_name=f"jobs_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
    )

    st.markdown(f"### Showing {len(display_jobs)} jobs")

    # ── Job cards ─────────────────────────────────────────────────────────────
    for j in display_jobs:
        pct = j["match_pct"]
        with st.container():
            st.markdown(f"""
<div class="job-card">
  <div style="display:flex; justify-content:space-between; align-items:flex-start; flex-wrap:wrap; gap:8px;">
    <div>
      <span style="font-size:16px; font-weight:600;">{j['title']}</span><br>
      <span style="color:#555; font-size:13px;">{j['company']} · {j['location']} · {j['type']}</span>
    </div>
    <div style="text-align:right;">
      <span style="font-size:22px; font-weight:700;" class="{match_color_class(pct)}">{pct}%</span>
      <span style="font-size:11px; color:#888; display:block;">profile match</span>
    </div>
  </div>
  <div style="margin:8px 0 4px;">
    {''.join(f'<span class="skill-tag">{s}</span>' for s in j['matched_skills'][:8])}
  </div>
  {"<div style='margin-top:6px;'><span style='font-size:12px;color:#888;'>Missing: </span>" + ''.join(f'<span class="missing-tag">{s}</span>' for s in j['missing_skills'][:6]) + "</div>" if j['missing_skills'] else ""}
  <div style="margin-top:8px; font-size:12px; color:#888;">
    💰 {j['salary']} &nbsp;|&nbsp; 📅 {j.get('posted','')[:10] or 'Today'} &nbsp;|&nbsp; 🌐 {j['platform']}
  </div>
</div>
""", unsafe_allow_html=True)

            col_a, col_b, col_c = st.columns([1, 1, 4])
            with col_a:
                st.link_button("Apply Now →", j["url"], use_container_width=True)
            with col_b:
                if st.button("📋 View Description", key=f"desc_{j['url'][-20:]}_{pct}"):
                    with st.expander("Job Description", expanded=True):
                        st.write(j["description"][:2000] + ("…" if len(j["description"]) > 2000 else ""))

            st.markdown("---")

# ── Empty state ───────────────────────────────────────────────────────────────
elif not fetch_btn:
    st.info("👈 Configure your preferences in the sidebar and click **Fetch Today's Jobs** to get started.")
    st.markdown("""
    ### How it works
    1. **Get a free API key** from [JSearch on RapidAPI](https://rapidapi.com/letscrape-6bRBa3QguO5/api/jsearch) — free tier gives 500 requests/month (≈ enough for daily use)
    2. **Upload your resume** (PDF) so the app can compare every job against your skills
    3. **Click Fetch** — pulls up to 100 real jobs from LinkedIn, Indeed, Naukri every day
    4. **Apply directly** using the Apply Now button on any job card
    5. **Export to CSV** to track your applications

    ### Free deployment
    Deploy this on [Streamlit Cloud](https://streamlit.io/cloud) — 100% free, always on.
    """)
