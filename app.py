"""Streamlit web interface — Internship Assistant.

Run with:  python3 -m streamlit run app.py
"""

import csv as csv_mod
import io
import os
import zipfile
from datetime import date

import streamlit as st

from internship_assistant import tracker, matcher, materials, priority, auth

DATA_DIR      = "data"
CSV_PATH      = os.path.join(DATA_DIR, "internship_tracker.csv")
RESUME_PATH   = os.path.join(DATA_DIR, "resume.txt")
GENERATED_DIR = "generated_materials"

# ── Bootstrap ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Internship Assistant",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        "About": "Internship Assistant — local, privacy-first internship operating system."
    },
)

# ── Premium UI styles ────────────────────────────────────────────────────────
# Single CSS injection. All custom presentation lives here so individual
# sections stay free of inline style strings.
st.markdown(
    """
    <style>
      :root {
        --ia-bg:        #0b1120;
        --ia-surface:   #0f172a;
        --ia-surface-2: #111c33;
        --ia-border:    #1e293b;
        --ia-text:      #e2e8f0;
        --ia-muted:     #94a3b8;
        --ia-accent:    #6366f1;   /* indigo-500 */
        --ia-accent-2:  #818cf8;   /* indigo-400 */
        --ia-success:   #10b981;
        --ia-warning:   #f59e0b;
        --ia-danger:    #ef4444;
        --ia-info:      #38bdf8;
      }

      /* Tighten main content width and add breathing room */
      .block-container { padding-top: 2rem; padding-bottom: 4rem; max-width: 1280px; }

      /* Headings */
      h1, h2, h3, h4 { letter-spacing: -0.01em; }
      h1 { font-weight: 700; }
      h2 { font-weight: 650; }

      /* Sidebar */
      section[data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0b1120 0%, #0f172a 100%);
        border-right: 1px solid var(--ia-border);
      }
      section[data-testid="stSidebar"] .stButton>button {
        width: 100%;
        text-align: left;
        background: transparent;
        border: 1px solid transparent;
        color: var(--ia-text);
        font-weight: 500;
        padding: 0.45rem 0.7rem;
        border-radius: 8px;
        transition: background 0.15s, border 0.15s;
      }
      section[data-testid="stSidebar"] .stButton>button:hover {
        background: rgba(99, 102, 241, 0.08);
        border-color: rgba(99, 102, 241, 0.25);
      }
      section[data-testid="stSidebar"] .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--ia-accent) 0%, var(--ia-accent-2) 100%);
        border-color: var(--ia-accent);
        color: white;
        box-shadow: 0 1px 0 rgba(255,255,255,0.08) inset, 0 6px 18px -6px rgba(99,102,241,0.5);
      }
      .ia-nav-group {
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        color: var(--ia-muted);
        margin: 1.2rem 0 0.4rem 0.25rem;
        text-transform: uppercase;
      }
      .ia-sidebar-brand {
        display: flex; align-items: center; gap: 0.6rem;
        padding: 0.4rem 0 0.6rem;
        font-weight: 700; font-size: 1.15rem;
      }
      .ia-sidebar-brand .ia-dot {
        width: 10px; height: 10px; border-radius: 50%;
        background: var(--ia-accent);
        box-shadow: 0 0 12px var(--ia-accent);
      }
      .ia-sidebar-tagline { color: var(--ia-muted); font-size: 0.82rem; margin-top: -0.4rem; margin-bottom: 0.7rem; }
      .ia-status-row { display: flex; gap: 0.4rem; flex-wrap: wrap; margin: 0.4rem 0 0.7rem; }

      /* Cards */
      .ia-card {
        background: var(--ia-surface);
        border: 1px solid var(--ia-border);
        border-radius: 14px;
        padding: 1.1rem 1.25rem;
        box-shadow: 0 1px 0 rgba(255,255,255,0.03) inset;
        margin-bottom: 0.8rem;
      }
      .ia-card-title { font-size: 0.78rem; color: var(--ia-muted); text-transform: uppercase; letter-spacing: 0.12em; font-weight: 600; }
      .ia-card-value { font-size: 2.0rem; font-weight: 700; line-height: 1.1; margin-top: 0.25rem; }
      .ia-card-sub   { color: var(--ia-muted); font-size: 0.85rem; margin-top: 0.25rem; }

      /* Hero */
      .ia-hero {
        background:
          radial-gradient(1200px 320px at -10% -50%, rgba(99,102,241,0.18), transparent 60%),
          radial-gradient(900px 280px at 110% -10%, rgba(56,189,248,0.12), transparent 60%),
          var(--ia-surface);
        border: 1px solid var(--ia-border);
        border-radius: 18px;
        padding: 2rem 2rem 1.5rem;
        margin-bottom: 1.2rem;
      }
      .ia-hero-eyebrow {
        display: inline-flex; align-items: center; gap: 0.4rem;
        background: rgba(99,102,241,0.12);
        color: var(--ia-accent-2);
        padding: 0.25rem 0.7rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        border: 1px solid rgba(99,102,241,0.3);
      }
      .ia-hero-title    { font-size: 2.4rem; font-weight: 700; margin: 0.7rem 0 0.5rem; line-height: 1.15; }
      .ia-hero-subtitle { color: var(--ia-text); font-size: 1.05rem; max-width: 760px; }
      .ia-hero-tagline  { color: var(--ia-muted); font-size: 0.95rem; margin-top: 0.4rem; }

      /* Pills / badges */
      .ia-pill {
        display: inline-block;
        padding: 0.18rem 0.6rem;
        border-radius: 999px;
        font-size: 0.78rem;
        font-weight: 600;
        border: 1px solid transparent;
      }
      .ia-pill-success { background: rgba(16,185,129,0.12); color: #34d399; border-color: rgba(16,185,129,0.4); }
      .ia-pill-info    { background: rgba(56,189,248,0.12); color: #7dd3fc; border-color: rgba(56,189,248,0.4); }
      .ia-pill-warning { background: rgba(245,158,11,0.12); color: #fbbf24; border-color: rgba(245,158,11,0.4); }
      .ia-pill-danger  { background: rgba(239,68,68,0.12);  color: #fca5a5; border-color: rgba(239,68,68,0.4); }
      .ia-pill-muted   { background: rgba(148,163,184,0.12); color: var(--ia-muted); border-color: rgba(148,163,184,0.3); }
      .ia-pill-accent  { background: rgba(99,102,241,0.15); color: var(--ia-accent-2); border-color: rgba(99,102,241,0.4); }

      /* Empty state */
      .ia-empty {
        text-align: center;
        padding: 3rem 1.5rem;
        background: var(--ia-surface);
        border: 1px dashed var(--ia-border);
        border-radius: 16px;
      }
      .ia-empty-icon  { font-size: 2.4rem; }
      .ia-empty-title { font-size: 1.3rem; font-weight: 700; margin-top: 0.5rem; }
      .ia-empty-text  { color: var(--ia-muted); max-width: 520px; margin: 0.5rem auto 1rem; }

      /* Job row card */
      .ia-job-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0.85rem 1rem;
        background: var(--ia-surface);
        border: 1px solid var(--ia-border);
        border-radius: 12px;
        margin-bottom: 0.5rem;
      }
      .ia-job-row .ia-job-title { font-weight: 600; }
      .ia-job-row .ia-job-meta  { color: var(--ia-muted); font-size: 0.85rem; }

      /* Buttons (main area, not sidebar) */
      .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--ia-accent) 0%, var(--ia-accent-2) 100%);
        border: none;
        font-weight: 600;
        box-shadow: 0 8px 22px -10px rgba(99,102,241,0.65);
      }

      /* Streamlit metric polish */
      div[data-testid="stMetric"] {
        background: var(--ia-surface);
        border: 1px solid var(--ia-border);
        border-radius: 12px;
        padding: 0.9rem 1rem;
      }
      div[data-testid="stMetricLabel"] {
        color: var(--ia-muted);
        font-size: 0.78rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        font-weight: 600;
      }

      /* ── Landing page (V14) ─────────────────────────────────────────────── */
      .landing-shell { padding-top: 0.5rem; }
      .landing-navbar {
        display: flex; align-items: center; justify-content: space-between;
        padding: 0.4rem 0 1.6rem;
        border-bottom: 1px solid rgba(99,102,241,0.1);
        margin-bottom: 1.5rem;
      }
      .landing-brand {
        display: flex; align-items: center; gap: 0.6rem;
        font-size: 1.15rem; font-weight: 700;
      }
      .landing-brand .ia-dot {
        width: 12px; height: 12px; border-radius: 50%;
        background: linear-gradient(135deg, var(--ia-accent), #a78bfa);
        box-shadow: 0 0 18px rgba(167,139,250,0.6);
      }
      .landing-navlinks {
        display: flex; gap: 1.5rem;
        color: var(--ia-muted);
        font-size: 0.9rem;
      }
      .landing-navlinks a {
        color: var(--ia-muted);
        text-decoration: none;
        cursor: pointer;
        transition: color 0.15s;
      }
      .landing-navlinks a:hover { color: var(--ia-accent-2); }

      /* In-page anchor scrolling */
      html { scroll-behavior: smooth; }
      .landing-hero, .section-title { scroll-margin-top: 1rem; }

      /* Hero */
      .landing-hero {
        position: relative;
        background:
          radial-gradient(800px 400px at 0% 0%, rgba(99,102,241,0.18), transparent 60%),
          radial-gradient(700px 350px at 100% 100%, rgba(167,139,250,0.12), transparent 60%);
        border-radius: 24px;
        padding: 2.5rem 0 3rem;
      }
      .landing-eyebrow {
        display: inline-flex; align-items: center; gap: 0.45rem;
        background: rgba(99,102,241,0.12);
        color: #a5b4fc;
        padding: 0.35rem 0.8rem;
        border-radius: 999px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.12em;
        text-transform: uppercase;
        border: 1px solid rgba(99,102,241,0.3);
        margin-bottom: 1rem;
      }
      .landing-title {
        font-size: 3rem; font-weight: 800; line-height: 1.05;
        letter-spacing: -0.02em;
        background: linear-gradient(135deg, #ffffff 0%, #a5b4fc 50%, #c4b5fd 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        margin: 0.4rem 0 1.1rem;
      }
      .landing-subtitle {
        color: var(--ia-text); font-size: 1.1rem;
        max-width: 560px; line-height: 1.55;
        margin-bottom: 1.5rem;
      }

      /* Glass card mockup */
      .glass-card {
        background: linear-gradient(180deg,
                      rgba(30,41,59,0.65) 0%,
                      rgba(15,23,42,0.65) 100%);
        border: 1px solid rgba(148,163,184,0.18);
        border-radius: 20px;
        padding: 1.4rem;
        backdrop-filter: blur(14px);
        -webkit-backdrop-filter: blur(14px);
        box-shadow:
          0 30px 60px -30px rgba(0,0,0,0.7),
          0 0 0 1px rgba(99,102,241,0.06) inset,
          0 1px 0 rgba(255,255,255,0.05) inset;
      }
      .mockup-eyebrow {
        font-size: 0.7rem; color: var(--ia-muted);
        text-transform: uppercase; letter-spacing: 0.15em;
        font-weight: 600; margin-bottom: 0.5rem;
      }
      .mockup-title {
        font-size: 1rem; font-weight: 700; margin-bottom: 1rem;
      }
      .mockup-row {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0.7rem 0;
        border-top: 1px solid rgba(148,163,184,0.1);
      }
      .mockup-row:first-of-type { border-top: none; padding-top: 0; }
      .mockup-row .name { font-weight: 600; }
      .mockup-row .role { color: var(--ia-muted); font-size: 0.85rem; }
      .mockup-metrics {
        display: flex; gap: 0.8rem;
        margin-top: 1.2rem; padding-top: 1.2rem;
        border-top: 1px solid rgba(148,163,184,0.15);
      }
      .mockup-metric {
        flex: 1; text-align: center;
        background: rgba(99,102,241,0.08);
        border: 1px solid rgba(99,102,241,0.18);
        border-radius: 10px;
        padding: 0.7rem 0.4rem;
      }
      .mockup-metric .v { font-size: 1.4rem; font-weight: 700; color: #a5b4fc; }
      .mockup-metric .l { font-size: 0.7rem; color: var(--ia-muted); text-transform: uppercase; letter-spacing: 0.08em; }

      /* Section title */
      .section-title {
        font-size: 1.75rem; font-weight: 700;
        letter-spacing: -0.01em;
        margin: 3rem 0 0.4rem;
      }
      .section-subtitle {
        color: var(--ia-muted); font-size: 1rem;
        max-width: 640px; margin-bottom: 1.5rem;
      }

      /* Feature card */
      .feature-card {
        background: var(--ia-surface);
        border: 1px solid var(--ia-border);
        border-radius: 16px;
        padding: 1.4rem;
        height: 100%;
        transition: border-color 0.15s, transform 0.15s;
      }
      .feature-card:hover {
        border-color: rgba(99,102,241,0.5);
        transform: translateY(-2px);
      }
      .feature-icon {
        width: 42px; height: 42px;
        display: flex; align-items: center; justify-content: center;
        background: linear-gradient(135deg, rgba(99,102,241,0.15), rgba(167,139,250,0.15));
        border: 1px solid rgba(99,102,241,0.3);
        border-radius: 12px;
        font-size: 1.3rem;
        margin-bottom: 0.9rem;
      }
      .feature-title { font-size: 1.05rem; font-weight: 700; margin-bottom: 0.3rem; }
      .feature-body  { color: var(--ia-muted); font-size: 0.9rem; line-height: 1.5; }

      /* Workflow step */
      .workflow-step {
        background: var(--ia-surface);
        border: 1px solid var(--ia-border);
        border-radius: 14px;
        padding: 1.2rem 1.1rem;
        height: 100%;
      }
      .workflow-num {
        display: inline-flex; align-items: center; justify-content: center;
        width: 32px; height: 32px;
        background: linear-gradient(135deg, var(--ia-accent), #a78bfa);
        color: white;
        border-radius: 10px;
        font-weight: 700;
        margin-bottom: 0.7rem;
        box-shadow: 0 6px 18px -8px rgba(99,102,241,0.7);
      }
      .workflow-title { font-weight: 700; margin-bottom: 0.25rem; }
      .workflow-body  { color: var(--ia-muted); font-size: 0.9rem; }

      /* Privacy block */
      .privacy-block {
        background: linear-gradient(135deg, rgba(16,185,129,0.06), rgba(56,189,248,0.06));
        border: 1px solid rgba(16,185,129,0.25);
        border-radius: 18px;
        padding: 1.6rem;
        margin-top: 1rem;
      }
      .privacy-grid {
        display: grid;
        grid-template-columns: repeat(2, 1fr);
        gap: 0.8rem;
        margin-top: 1rem;
      }
      .privacy-item {
        display: flex; gap: 0.7rem; align-items: flex-start;
        padding: 0.8rem;
        background: rgba(15,23,42,0.6);
        border: 1px solid rgba(148,163,184,0.12);
        border-radius: 10px;
      }
      .privacy-item .check { color: #34d399; font-weight: 700; font-size: 1.1rem; }
      .privacy-item .body  { color: var(--ia-text); font-size: 0.9rem; }

      .landing-footer {
        text-align: center;
        color: var(--ia-muted);
        font-size: 0.85rem;
        padding: 2.5rem 0 1rem;
        border-top: 1px solid var(--ia-border);
        margin-top: 3rem;
      }

      /* Auth forms */
      .auth-card {
        max-width: 440px;
        margin: 1rem auto;
        padding: 2rem;
        background: var(--ia-surface);
        border: 1px solid var(--ia-border);
        border-radius: 18px;
        box-shadow: 0 30px 60px -30px rgba(0,0,0,0.6);
      }
      .auth-title { font-size: 1.6rem; font-weight: 700; text-align: center; margin-bottom: 0.3rem; }
      .auth-subtitle { color: var(--ia-muted); text-align: center; margin-bottom: 1.4rem; font-size: 0.92rem; }
      .auth-warn {
        background: rgba(245,158,11,0.08);
        border: 1px solid rgba(245,158,11,0.3);
        border-radius: 10px;
        padding: 0.7rem 0.9rem;
        color: #fbbf24;
        font-size: 0.82rem;
        margin-bottom: 1rem;
      }

      /* App topbar (after sign-in) */
      .app-topbar {
        display: flex; justify-content: space-between; align-items: center;
        padding: 0.6rem 1rem;
        background: var(--ia-surface);
        border: 1px solid var(--ia-border);
        border-radius: 12px;
        margin-bottom: 1.2rem;
      }
      .app-topbar .left  { display: flex; align-items: center; gap: 0.7rem; }
      .app-topbar .crumb { color: var(--ia-muted); font-size: 0.82rem; text-transform: uppercase; letter-spacing: 0.1em; }
      .app-topbar .who   { color: var(--ia-text); font-size: 0.9rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

tracker.migrate_csv(CSV_PATH)   # add any missing columns to old CSVs
tracker.ensure_csv(CSV_PATH)

# ── Helpers ───────────────────────────────────────────────────────────────────

def load_jobs():
    return tracker.read_jobs(CSV_PATH)

def save_jobs(jobs):
    tracker.write_jobs(jobs, CSV_PATH)

def job_label(job):
    return f"{job.get('company') or 'Unknown'} — {job.get('role') or 'Unknown Role'}"

def resume_exists():
    return os.path.exists(RESUME_PATH)

def read_resume():
    if not resume_exists():
        return ""
    with open(RESUME_PATH) as f:
        return f.read()

def status_emoji(status):
    s = (status or "").lower()
    if "offer" in s:      return "🟢"
    if "interview" in s or "final round" in s: return "🟡"
    if "applied" in s:    return "🔵"
    if "rejected" in s or "withdrawn" in s:   return "🔴"
    return "⚪"

def severity_icon(sev):
    return {"high": "🔴", "medium": "🟡", "low": "🟢", "ok": "✅"}.get(sev, "⚪")

INTEREST_OPTIONS  = ["", "Low", "Medium", "High"]
CATEGORY_OPTIONS  = ["", "SWE", "Data", "Quant", "Finance", "Accounting",
                     "Business Analytics", "Product", "Other"]
SOURCE_OPTIONS    = ["", "LinkedIn", "Handshake", "Company Website",
                     "Referral", "Simplify", "Campus Recruiting", "Other"]
NET_STATUS_OPTIONS = ["Not Started", "Contact Found", "Message Sent",
                      "Replied", "Call Scheduled", "No Response"]
STATUS_PRESETS = ["Not Started", "Saved", "Applied", "Phone Screen",
                  "Interview", "Final Round", "Offer", "Rejected", "Withdrawn"]

# ── UI helpers (cards, pills, hero, etc.) ─────────────────────────────────────

def html(s):
    """Render a raw HTML snippet."""
    st.markdown(s, unsafe_allow_html=True)

def metric_card(col, label, value, sub=None):
    """Render a styled metric card inside a column."""
    sub_html = f'<div class="ia-card-sub">{sub}</div>' if sub else ""
    col.markdown(
        f'<div class="ia-card">'
        f'<div class="ia-card-title">{label}</div>'
        f'<div class="ia-card-value">{value}</div>'
        f'{sub_html}'
        f'</div>',
        unsafe_allow_html=True,
    )

def pill(text, kind="muted"):
    """Inline pill/badge. kind ∈ success | info | warning | danger | accent | muted"""
    return f'<span class="ia-pill ia-pill-{kind}">{text}</span>'

def status_pill(status):
    s = (status or "").lower()
    if "offer" in s:        return pill("Offer", "success")
    if "interview" in s or "final round" in s: return pill("Interview", "warning")
    if "applied" in s:      return pill("Applied", "info")
    if "rejected" in s or "withdrawn" in s:    return pill("Rejected", "danger")
    return pill(status or "Not started", "muted")

def priority_pill(score):
    if score >= 65: return pill(f"High · {score}", "danger")
    if score >= 35: return pill(f"Medium · {score}", "warning")
    return pill(f"Low · {score}", "muted")

def hero(eyebrow, title, subtitle, tagline=None):
    tagline_html = f'<div class="ia-hero-tagline">{tagline}</div>' if tagline else ""
    html(
        f'<div class="ia-hero">'
        f'<span class="ia-hero-eyebrow">{eyebrow}</span>'
        f'<div class="ia-hero-title">{title}</div>'
        f'<div class="ia-hero-subtitle">{subtitle}</div>'
        f'{tagline_html}'
        f'</div>'
    )

def empty_state(icon, title, text, cta_section=None):
    html(
        f'<div class="ia-empty">'
        f'<div class="ia-empty-icon">{icon}</div>'
        f'<div class="ia-empty-title">{title}</div>'
        f'<div class="ia-empty-text">{text}</div>'
        f'</div>'
    )
    if cta_section:
        if st.button(f"➡️  Go to {cta_section}", key=f"empty_cta_{cta_section}", type="primary"):
            navigate_to(cta_section)

def navigate_to(section_name):
    st.session_state.nav_section = section_name
    st.rerun()

# ── Auth state machine ───────────────────────────────────────────────────────
# auth_status ∈ {"landing", "signin", "signup", "main"}
# user        ∈ None | {"name","email","is_guest"}

if "auth_status" not in st.session_state:
    st.session_state.auth_status = "landing"
if "user" not in st.session_state:
    st.session_state.user = None

def go_to(status):
    st.session_state.auth_status = status
    st.rerun()

def sign_out():
    st.session_state.user = None
    st.session_state.auth_status = "landing"
    st.session_state.nav_section = "🏠 Home Dashboard"
    st.rerun()

def enter_guest_mode():
    st.session_state.user = auth.guest_user()
    st.session_state.auth_status = "main"
    st.rerun()

# ── Landing page ─────────────────────────────────────────────────────────────

FEATURES = [
    ("📁", "Application Tracking",     "One spreadsheet of every job — company, role, deadline, status, notes."),
    ("🚀", "Job Priority Scoring",     "Transparent 0–100 score per job from match, deadline, interest, and status."),
    ("🔍", "Resume Match Analysis",    "Quantify how each posting aligns with your resume; see what to add."),
    ("📊", "Skill Gap Dashboard",      "Aggregates missing skills across your search and suggests next steps."),
    ("🤝", "Follow-up Planning",       "Surfaces stale applications and drafts polite follow-up messages."),
    ("✉️", "DOCX Application Materials", "Cover letters, recruiter emails, and LinkedIn drafts as Word files."),
    ("🔒", "Local-first Privacy",      "Resume and tracker stay on your computer. No cloud, no telemetry."),
]

WORKFLOW = [
    ("Save Resume",       "Upload a PDF/TXT or paste text. Used for match scoring and material drafts."),
    ("Add Jobs",          "Manual entry or paste a posting — fields auto-extract."),
    ("Prioritize & Analyze", "See priority scores, today's tasks, and per-job match breakdowns."),
    ("Generate & Follow Up", "Word-format outreach drafts plus follow-up reminders."),
]

PRIVACY_POINTS = [
    "No cloud upload — every file stays in your project folder.",
    "No paid APIs. No third-party tracking.",
    "Resume, tracker, and drafts are gitignored by default.",
    "Local demo accounts hashed with PBKDF2 (200k iters); never plaintext.",
]


def render_landing():
    html('<div class="landing-shell">')

    # Top navbar — visual on left, real Streamlit buttons on right
    nav_l, nav_links, nav_r1, nav_r2, nav_r3 = st.columns([3.5, 4.5, 1, 1, 1.2])
    with nav_l:
        html(
            '<div class="landing-brand">'
            '<span class="ia-dot"></span>'
            '<span>Internship Assistant</span>'
            '</div>'
        )
    with nav_links:
        html(
            '<div class="landing-navlinks">'
            '<a href="#home">Home</a>'
            '<a href="#features">Features</a>'
            '<a href="#workflow">Workflow</a>'
            '<a href="#privacy">Privacy</a>'
            '</div>'
        )
    with nav_r1:
        if st.button("Sign In", key="lnav_signin"):
            go_to("signin")
    with nav_r2:
        if st.button("Sign Up", key="lnav_signup", type="primary"):
            go_to("signup")
    with nav_r3:
        if st.button("Continue as Guest", key="lnav_guest"):
            enter_guest_mode()

    # Hero
    html('<div class="landing-hero" id="home">')
    h_left, h_right = st.columns([1.2, 1])
    with h_left:
        html('<div class="landing-eyebrow">Local · Private · Yours</div>')
        html('<div class="landing-title">Your Internship Search<br>Operating System</div>')
        html(
            '<div class="landing-subtitle">'
            'Track applications, prioritize opportunities, tailor your resume, '
            'and plan follow-ups — all locally, with your data on your computer.'
            '</div>'
        )
        cta1, cta2, cta3 = st.columns([1, 1, 2])
        with cta1:
            if st.button("Get Started →", key="hero_get_started", type="primary", use_container_width=True):
                go_to("signup")
        with cta2:
            if st.button("Try as Guest", key="hero_guest", use_container_width=True):
                enter_guest_mode()
    with h_right:
        html(
            '<div class="glass-card">'
            '<div class="mockup-eyebrow">Recent Applications</div>'
            '<div class="mockup-title">My Pipeline</div>'
            '<div class="mockup-row">'
            '<div><div class="name">Google</div><div class="role">SWE Intern</div></div>'
            f'<div>{pill("Interview", "warning")}</div>'
            '</div>'
            '<div class="mockup-row">'
            '<div><div class="name">Microsoft</div><div class="role">Data Intern</div></div>'
            f'<div>{pill("Applied", "info")}</div>'
            '</div>'
            '<div class="mockup-row">'
            '<div><div class="name">Goldman Sachs</div><div class="role">Summer Analyst</div></div>'
            f'<div>{pill("Materials Ready", "accent")}</div>'
            '</div>'
            '<div class="mockup-metrics">'
            '<div class="mockup-metric"><div class="v">12</div><div class="l">Applied</div></div>'
            '<div class="mockup-metric"><div class="v">5</div><div class="l">High Priority</div></div>'
            '<div class="mockup-metric"><div class="v">3</div><div class="l">Follow-ups</div></div>'
            '</div>'
            '</div>'
        )
    html('</div>')  # /landing-hero

    # Features
    html('<div class="section-title" id="features">Everything you need to run your search</div>')
    html('<div class="section-subtitle">'
         'Built around the questions that actually matter: which jobs first, '
         'what to do today, and where am I getting stuck.</div>')
    fcols = st.columns(3)
    for i, (icon, title, body) in enumerate(FEATURES):
        with fcols[i % 3]:
            html(
                f'<div class="feature-card" style="margin-bottom:1rem;">'
                f'<div class="feature-icon">{icon}</div>'
                f'<div class="feature-title">{title}</div>'
                f'<div class="feature-body">{body}</div>'
                f'</div>'
            )

    # Workflow
    html('<div class="section-title" id="workflow">A 4-step workflow</div>')
    wcols = st.columns(4)
    for i, (title, body) in enumerate(WORKFLOW):
        with wcols[i]:
            html(
                f'<div class="workflow-step">'
                f'<div class="workflow-num">{i+1}</div>'
                f'<div class="workflow-title">{title}</div>'
                f'<div class="workflow-body">{body}</div>'
                f'</div>'
            )

    # Privacy
    html('<div class="section-title" id="privacy">Privacy, by design</div>')
    privacy_items = "".join(
        f'<div class="privacy-item"><span class="check">✓</span><span class="body">{p}</span></div>'
        for p in PRIVACY_POINTS
    )
    html(
        f'<div class="privacy-block">'
        f'<div style="font-weight:700; font-size:1.1rem;">Your data never leaves your computer.</div>'
        f'<div style="color:var(--ia-muted); font-size:0.92rem; margin-top:0.4rem;">'
        f'No accounts on remote servers, no third-party APIs, no telemetry. '
        f'GitHub-safe by default — every personal file is gitignored.'
        f'</div>'
        f'<div class="privacy-grid">{privacy_items}</div>'
        f'</div>'
    )

    # Bottom CTA + footer
    cta_a, cta_b, cta_c = st.columns([1, 1, 1])
    with cta_a:
        if st.button("Create Free Local Account", key="bot_signup", type="primary", use_container_width=True):
            go_to("signup")
    with cta_b:
        if st.button("Sign In", key="bot_signin", use_container_width=True):
            go_to("signin")
    with cta_c:
        if st.button("Continue as Guest", key="bot_guest", use_container_width=True):
            enter_guest_mode()

    html(
        '<div class="landing-footer">'
        'Built for students searching for internships. Local-first, privacy-friendly. '
        'No data is uploaded; accounts are stored as PBKDF2 hashes in <code>data/users.json</code>.'
        '</div>'
    )
    html('</div>')  # /landing-shell


def render_signin():
    html('<div class="auth-card">')
    html('<div class="auth-title">Sign in</div>')
    html('<div class="auth-subtitle">Welcome back. Local accounts only.</div>')
    html(
        '<div class="auth-warn">'
        '⚠ Local demo authentication — no email verification, no recovery. '
        'For a hosted deployment, use a proper auth provider.'
        '</div>'
    )
    with st.form("signin_form", clear_on_submit=False):
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign In", type="primary", use_container_width=True)
        if submitted:
            ok, result = auth.authenticate(email, password)
            if ok:
                st.session_state.user = auth.public_user(result)
                st.session_state.auth_status = "main"
                st.rerun()
            else:
                st.error(result)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Don't have an account? Sign up", key="goto_signup"):
            go_to("signup")
    with c2:
        if st.button("← Back to landing", key="signin_back"):
            go_to("landing")
    if st.button("Continue as Guest", key="signin_guest", use_container_width=True):
        enter_guest_mode()
    html('</div>')


def render_signup():
    html('<div class="auth-card">')
    html('<div class="auth-title">Create your account</div>')
    html('<div class="auth-subtitle">Stored locally on this computer. Free, no email needed for verification.</div>')
    html(
        '<div class="auth-warn">'
        '⚠ Local demo authentication — passwords are hashed with PBKDF2-SHA256 '
        '(200k iterations) and stored in <code>data/users.json</code>. '
        'For a hosted deployment, plug in a real auth provider.'
        '</div>'
    )
    with st.form("signup_form", clear_on_submit=False):
        name = st.text_input("Name", placeholder="Jane Doe")
        email = st.text_input("Email", placeholder="you@example.com")
        password = st.text_input("Password", type="password",
                                 help=f"Minimum {auth.MIN_PASSWORD_LEN} characters.")
        confirm = st.text_input("Confirm password", type="password")
        submitted = st.form_submit_button("Create account", type="primary", use_container_width=True)
        if submitted:
            ok, result = auth.register(name, email, password, confirm)
            if ok:
                st.session_state.user = auth.public_user(result)
                st.session_state.auth_status = "main"
                st.success("Account created — signing you in.")
                st.rerun()
            else:
                st.error(result)

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Already have an account? Sign in", key="goto_signin"):
            go_to("signin")
    with c2:
        if st.button("← Back to landing", key="signup_back"):
            go_to("landing")
    if st.button("Continue as Guest", key="signup_guest", use_container_width=True):
        enter_guest_mode()
    html('</div>')


# ── Auth gate ────────────────────────────────────────────────────────────────
# If the user is not yet inside the app, show landing/signin/signup and stop.
status = st.session_state.auth_status
if status == "landing":
    render_landing(); st.stop()
elif status == "signin":
    render_signin(); st.stop()
elif status == "signup":
    render_signup(); st.stop()
# otherwise status == "main" — fall through to the existing sidebar + sections

# ── Sidebar ───────────────────────────────────────────────────────────────────
NAV_GROUPS = [
    ("Start",          ["🏠 Home Dashboard", "📄 Resume Setup", "➕ Add / Import Jobs"]),
    ("Manage",         ["🚀 Priority Jobs", "📅 Today's Action Plan", "💼 Saved Jobs",
                        "🔍 Analyze Match", "🎯 Resume Targeting"]),
    ("Follow Through", ["✉️ Generate Materials", "🤝 Networking & Follow-up",
                        "📊 Skill Gap Dashboard", "🩺 Application Diagnosis"]),
    ("Export & Safety", ["📥 Export & Download", "🔒 Privacy Note"]),
]
SECTIONS = [s for _, items in NAV_GROUPS for s in items]

if "nav_section" not in st.session_state:
    st.session_state.nav_section = SECTIONS[0]

# Sidebar brand + status
all_jobs = load_jobs()
with st.sidebar:
    html(
        '<div class="ia-sidebar-brand">'
        '<span class="ia-dot"></span>'
        '<span>Internship Assistant</span>'
        '</div>'
        '<div class="ia-sidebar-tagline">Local internship operating system</div>'
    )
    resume_chip = pill("Resume Ready", "success") if resume_exists() else pill("Resume Missing", "warning")
    jobs_chip   = pill(f"{len(all_jobs)} jobs tracked", "accent")
    html(f'<div class="ia-status-row">{resume_chip}{jobs_chip}</div>')

    for group_name, items in NAV_GROUPS:
        html(f'<div class="ia-nav-group">{group_name}</div>')
        for item in items:
            is_active = (st.session_state.nav_section == item)
            if st.button(item, key=f"nav_{item}", type="primary" if is_active else "secondary"):
                navigate_to(item)

    # ── Account block ─────────────────────────────────────────────────
    st.divider()
    user = st.session_state.user or auth.guest_user()
    label = "Guest mode" if user.get("is_guest") else f"Signed in as {user.get('name','')}"
    sub   = "Local · no upload" if user.get("is_guest") else user.get("email","")
    html(
        f'<div style="padding:0.4rem 0.2rem 0.6rem;">'
        f'<div style="font-size:0.85rem; font-weight:600;">{label}</div>'
        f'<div style="font-size:0.75rem; color:var(--ia-muted);">{sub}</div>'
        f'</div>'
    )
    sb_a, sb_b = st.columns(2)
    with sb_a:
        if st.button("← Landing", key="sb_landing", use_container_width=True):
            sign_out() if not user.get("is_guest") else go_to("landing")
    with sb_b:
        if st.button("Sign Out" if not user.get("is_guest") else "Exit Guest", key="sb_signout",
                     use_container_width=True):
            sign_out()

    st.caption("Runs locally · No data uploaded")

section = st.session_state.nav_section

# ── App topbar ────────────────────────────────────────────────────────────────
_user = st.session_state.user or auth.guest_user()
_who = "Guest" if _user.get("is_guest") else _user.get("name", "")
html(
    f'<div class="app-topbar">'
    f'<div class="left">'
    f'<span class="ia-dot" style="display:inline-block; width:8px; height:8px; '
    f'border-radius:50%; background:var(--ia-accent); box-shadow:0 0 10px var(--ia-accent);"></span>'
    f'<strong>Internship Assistant</strong>'
    f'<span class="crumb">›  {section.split(" ", 1)[1] if " " in section else section}</span>'
    f'</div>'
    f'<div class="who">{_who}</div>'
    f'</div>'
)

# ════════════════════════════════════════════════════════════════════════════
# 1. HOME DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
if section == "🏠 Home Dashboard":
    # ── Hero ──────────────────────────────────────────────────────────────
    hero(
        eyebrow="Local · Private · Yours",
        title="Internship Assistant",
        subtitle=(
            "A local, privacy-first internship operating system for tracking applications, "
            "prioritizing jobs, targeting resumes, and preparing outreach."
        ),
        tagline="Organize your search. Know what to do next. Keep your data on your own computer.",
    )

    # Hero CTA buttons
    cta1, cta2, cta3, cta4 = st.columns(4)
    with cta1:
        if st.button("➕  Add a Job", type="primary", use_container_width=True, key="cta_add"):
            navigate_to("➕ Add / Import Jobs")
    with cta2:
        if st.button("🔍  Analyze Resume Match", use_container_width=True, key="cta_match"):
            navigate_to("🔍 Analyze Match")
    with cta3:
        if st.button("✉️  Generate Materials", use_container_width=True, key="cta_gen"):
            navigate_to("✉️ Generate Materials")
    with cta4:
        if st.button("📅  Today's Action Plan", use_container_width=True, key="cta_plan"):
            navigate_to("📅 Today's Action Plan")

    jobs = all_jobs
    total = len(jobs)

    # ── Empty state ───────────────────────────────────────────────────────
    if total == 0:
        st.write("")
        empty_state(
            icon="🚀",
            title="Start your internship search workspace",
            text=(
                "Add your first job posting to unlock priority scoring, resume matching, "
                "outreach drafts, and a daily action plan."
            ),
            cta_section="➕ Add / Import Jobs",
        )
    else:
        statuses = [(j.get("status") or "").lower() for j in jobs]
        not_started_n = sum(1 for s in statuses if not s or s in ("not started", "saved"))
        applied_n     = sum(1 for s in statuses if "applied" in s or "interview" in s or "offer" in s or "rejected" in s)
        interview_n   = sum(1 for s in statuses if "interview" in s or "final round" in s or "offer" in s)
        offer_n       = sum(1 for s in statuses if "offer" in s)

        # ── Compute priority + follow-ups + top missing once ─────────────
        resume_text_dash = read_resume()
        scored = []
        for j in jobs:
            jd = j.get("job_description", "")
            ms = None
            if resume_text_dash and jd.strip():
                _, _, _, ms = matcher.compute_match(jd, resume_text_dash)
            sc, _ = priority.compute_priority_score(j, ms)
            scored.append((sc, j))
        scored.sort(reverse=True, key=lambda x: x[0])
        high_pri_n = sum(1 for sc, _ in scored if sc >= 65)

        # follow-ups due: applied >7d ago, no response
        followups_due = 0
        from datetime import date as _date
        for j in jobs:
            if "applied" in (j.get("status") or "").lower():
                from datetime import datetime as _dt
                d_str = (j.get("date_applied") or "").strip()
                d = None
                for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%B %d, %Y", "%b %d, %Y"):
                    try:
                        d = _dt.strptime(d_str, fmt).date(); break
                    except Exception:
                        pass
                if d and (_date.today() - d).days >= 7 and not (j.get("response_date") or "").strip():
                    followups_due += 1

        # top missing skill
        top_missing = "—"
        if resume_text_dash:
            gaps = priority.compute_skill_gaps(jobs, RESUME_PATH)
            if gaps:
                top_missing = list(gaps.keys())[0]

        interview_rate_str = f"{interview_n/applied_n*100:.0f}%" if applied_n else "—"

        # ── Premium metric cards (Row 1 + Row 2) ─────────────────────────
        st.write("")
        r1c1, r1c2, r1c3, r1c4 = st.columns(4)
        metric_card(r1c1, "Total Jobs",     total,        sub=f"{not_started_n} not started")
        metric_card(r1c2, "High Priority",  high_pri_n,   sub="Score ≥ 65")
        metric_card(r1c3, "Applied",        applied_n,    sub=f"{interview_rate_str} interview rate")
        metric_card(r1c4, "Offers",         offer_n,      sub="Closed wins")

        r2c1, r2c2, r2c3, r2c4 = st.columns(4)
        metric_card(r2c1, "Interviews",      interview_n)
        metric_card(r2c2, "Follow-ups Due",  followups_due, sub="Applied >7 days ago")
        metric_card(r2c3, "Top Missing Skill", top_missing.title() if top_missing != "—" else "—",
                    sub="Across all saved JDs")
        metric_card(r2c4, "Pipeline Health",
                    "🟢 Active" if applied_n > 0 else "🟡 Setup",
                    sub="Apply to advance")

        # ── Today's Focus + Pipeline Snapshot ────────────────────────────
        st.write("")
        col_focus, col_snap = st.columns([1.3, 1])

        with col_focus:
            html('<div class="ia-card"><div class="ia-card-title">Today\'s Focus</div>')
            tasks = priority.generate_action_plan(jobs, RESUME_PATH)[:3]
            if tasks:
                for t in tasks:
                    pri = t.get("priority", "low")
                    p_kind = {"high": "danger", "medium": "warning", "low": "muted"}.get(pri, "muted")
                    html(
                        f'<div style="margin-top:0.7rem; padding-top:0.7rem; '
                        f'border-top:1px solid var(--ia-border);">'
                        f'{pill(pri.title(), p_kind)} &nbsp;'
                        f'<strong>{t.get("title","")}</strong>'
                        f'<div class="ia-card-sub">{t.get("reason","")}</div>'
                        f'<div class="ia-card-sub">→ {t.get("action","")}</div>'
                        f'</div>'
                    )
            else:
                html('<div class="ia-card-sub" style="margin-top:0.6rem;">No focus tasks right now — good place to be.</div>')
            html('</div>')

        with col_snap:
            html('<div class="ia-card"><div class="ia-card-title">Pipeline Snapshot</div>')
            chart_labels = ["Not Started", "Applied", "Interview", "Offer", "Rejected"]
            chart_values = [
                not_started_n,
                sum(1 for s in statuses if "applied" in s and "interview" not in s and "offer" not in s),
                interview_n - offer_n,
                offer_n,
                sum(1 for s in statuses if "rejected" in s),
            ]
            for lbl, val in zip(chart_labels, chart_values):
                bar_pct = (val / max(total, 1)) * 100
                kind = {"Not Started": "muted", "Applied": "info",
                        "Interview": "warning", "Offer": "success",
                        "Rejected": "danger"}.get(lbl, "muted")
                html(
                    f'<div style="margin-top:0.7rem;">'
                    f'<div style="display:flex; justify-content:space-between;">'
                    f'{pill(lbl, kind)}'
                    f'<span style="color:var(--ia-muted); font-size:0.85rem;">{val}</span>'
                    f'</div>'
                    f'<div style="height:6px; background:var(--ia-border); border-radius:3px; margin-top:0.3rem;">'
                    f'<div style="height:100%; width:{bar_pct}%; '
                    f'background:linear-gradient(90deg, var(--ia-accent), var(--ia-accent-2)); '
                    f'border-radius:3px;"></div>'
                    f'</div>'
                    f'</div>'
                )
            html('</div>')

        # ── Recent jobs ───────────────────────────────────────────────────
        st.write("")
        st.subheader("Recent Jobs")
        for job in reversed(all_jobs[-5:]):
            company = job.get("company", "?")
            role    = job.get("role", "?")
            interest = (job.get("interest_level") or "").strip() or "—"
            deadline = job.get("application_deadline") or job.get("deadline") or "—"
            html(
                f'<div class="ia-job-row">'
                f'<div>'
                f'<div class="ia-job-title">{company} — {role}</div>'
                f'<div class="ia-job-meta">Interest: {interest}  ·  Deadline: {deadline}</div>'
                f'</div>'
                f'<div>{status_pill(job.get("status",""))}</div>'
                f'</div>'
            )


# ════════════════════════════════════════════════════════════════════════════
# 2. RESUME SETUP
# ════════════════════════════════════════════════════════════════════════════
elif section == "📄 Resume Setup":
    st.header("📄 Resume Setup")
    st.write(
        "Your resume powers match scoring, material generation, and resume targeting. "
        "It is saved locally to `data/resume.txt` and **never uploaded anywhere**."
    )

    if resume_exists():
        st.success("✅ A resume is saved and ready.")
        if st.checkbox("👁️ Show current resume"):
            with open(RESUME_PATH) as f:
                st.text(f.read())
        st.divider()

    # File upload
    st.subheader("📁 Upload a Resume File")
    st.caption("Accepted: `.txt` plain text  ·  `.pdf` text-based (not scanned)")
    uploaded = st.file_uploader("Choose a resume file", type=["txt", "pdf"], label_visibility="collapsed")

    if uploaded:
        if uploaded.name.lower().endswith(".txt"):
            raw = uploaded.read()
            text = raw.decode("utf-8", errors="replace")
            if not text.strip():
                st.error("The uploaded file is empty.")
            else:
                st.text_area("Preview:", text[:500], height=130, disabled=True)
                if st.button("💾 Save Uploaded Resume (.txt)", type="primary"):
                    os.makedirs(DATA_DIR, exist_ok=True)
                    with open(RESUME_PATH, "w") as f:
                        f.write(text.strip())
                    st.success(f"✅ Resume saved to `{RESUME_PATH}`.")
                    st.rerun()

        elif uploaded.name.lower().endswith(".pdf"):
            try:
                import pypdf
                reader = pypdf.PdfReader(uploaded)
                text = "\n".join(p.extract_text() or "" for p in reader.pages).strip()
                if len(text) < 50:
                    st.error(
                        "PDF text extraction returned almost no text — "
                        "this usually happens with scanned PDFs. "
                        "Please paste your resume text manually below."
                    )
                else:
                    st.text_area("Preview:", text[:500], height=130, disabled=True)
                    if st.button("💾 Save Uploaded Resume (.pdf)", type="primary"):
                        os.makedirs(DATA_DIR, exist_ok=True)
                        with open(RESUME_PATH, "w") as f:
                            f.write(text)
                        st.success("✅ Resume extracted from PDF and saved.")
                        st.rerun()
            except ImportError:
                st.error("Install `pypdf` with `pip3 install pypdf` then restart the app.")
            except Exception as exc:
                st.error(f"Could not read the PDF ({exc}). Please paste text manually below.")

    st.divider()
    st.subheader("✏️ Or Paste Resume Text")
    pasted = st.text_area("Paste your full resume here:", height=300,
                          placeholder="Jane Doe\njane@example.com\n\nSKILLS\nPython, SQL, Git…",
                          key="resume_paste")
    if st.button("💾 Save Pasted Resume", type="primary"):
        if not pasted.strip():
            st.error("Resume text is empty.")
        else:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(RESUME_PATH, "w") as f:
                f.write(pasted.strip())
            st.success("✅ Resume saved.")
            st.rerun()

    st.caption("**Tip:** The first non-blank line is used as your name in generated materials.")


# ════════════════════════════════════════════════════════════════════════════
# 3. ADD / IMPORT JOBS
# ════════════════════════════════════════════════════════════════════════════
elif section == "➕ Add / Import Jobs":
    st.header("➕ Add or Import a Job")
    tab_add, tab_import = st.tabs(["✍️ Add Manually", "📋 Import from Text"])

    # ── Tab: Add manually ─────────────────────────────────────────────────
    with tab_add:
        st.write("Fill in the fields you have. Leave anything blank — you can update it later from **Saved Jobs**.")

        col1, col2 = st.columns(2)
        with col1:
            company          = st.text_input("🏢 Company Name")
            role             = st.text_input("💼 Job Title / Role")
            location         = st.text_input("📍 Location")
            application_link = st.text_input("🔗 Application Link (URL)")
            deadline         = st.text_input("📅 Legacy Deadline field")
            application_deadline = st.text_input("📅 Application Deadline (YYYY-MM-DD)")
        with col2:
            interest_level   = st.selectbox("⭐ Interest Level", INTEREST_OPTIONS)
            role_category    = st.selectbox("🗂️ Role Category", CATEGORY_OPTIONS)
            required_skills  = st.text_input("🛠️ Required Skills (comma-separated)")
            sponsorship_info = st.text_input("🛂 Sponsorship Info")
            source           = st.selectbox("🔍 Source", SOURCE_OPTIONS)
            status           = st.text_input("📌 Status", value="Not Started")

        notes           = st.text_input("📝 Notes")
        job_description = st.text_area("📄 Job Description", height=180,
                                       placeholder="Paste the full JD here for better match scoring…")
        company_context = st.text_area(
            "🏛️ Company Context  *(optional — paste company description, team info, values, etc.)*",
            height=130,
            help="Paste anything from the job page: company mission, team description, product info, culture notes. "
                 "This makes generated cover letters and emails much more specific.",
        )

        if st.button("💾 Save Job", type="primary"):
            job = {f: "" for f in tracker.FIELDS}
            job.update({
                "company": company.strip(), "role": role.strip(),
                "location": location.strip(), "application_link": application_link.strip(),
                "deadline": deadline.strip(), "application_deadline": application_deadline.strip(),
                "required_skills": required_skills.strip(), "status": status.strip(),
                "notes": notes.strip(), "job_description": job_description.strip(),
                "company_context": company_context.strip(),
                "interest_level": interest_level, "role_category": role_category,
                "sponsorship_info": sponsorship_info.strip(), "source": source,
                "date_added": date.today().isoformat(),
            })
            if tracker.is_blank_job(job):
                st.error("⚠️ All fields are blank — fill in at least a company name or role.")
            else:
                jobs = load_jobs()
                dup = tracker.find_duplicate(job, jobs)
                if dup is not None:
                    st.warning(f"⚠️ Similar job already exists: **{job_label(jobs[dup])}**. Check Saved Jobs.")
                else:
                    jobs.append(job)
                    save_jobs(jobs)
                    st.success(f"✅ Saved: **{company or '?'}** — {role or '?'}")

    # ── Tab: Import from text ─────────────────────────────────────────────
    with tab_import:
        st.write(
            "Paste a full job posting. Fields are auto-extracted and shown for editing before saving. "
            "No data is saved until you click **Confirm & Save**."
        )

        if st.session_state.get("_import_ok_msg"):
            st.success(st.session_state.pop("_import_ok_msg"))

        raw = st.text_area("Paste job posting here:", height=280,
                           placeholder="Company: Acme\nRole: Data Analyst Intern\nLocation: Remote\n…",
                           key="import_raw")

        if st.button("🔍 Extract Fields", type="primary"):
            if not raw.strip():
                st.error("Nothing pasted.")
            else:
                st.session_state["import_ext"] = tracker.extract_job_from_text(raw)

        if st.session_state.get("import_ext"):
            ext = st.session_state["import_ext"]
            st.divider()
            st.subheader("✏️ Review & Edit Before Saving")
            st.caption("Auto-filled from the posting — edit anything before clicking Confirm & Save.")

            with st.form("import_form"):
                fi_company  = st.text_input("🏢 Company",           value=ext.get("company", ""))
                fi_role     = st.text_input("💼 Role / Title",       value=ext.get("role", ""))
                fi_location = st.text_input("📍 Location",           value=ext.get("location", ""))
                fi_link     = st.text_input("🔗 Application Link",   value=ext.get("application_link", ""))
                fi_deadline = st.text_input("📅 Deadline",           value=ext.get("deadline", ""))
                fi_app_dl   = st.text_input("📅 Application Deadline (YYYY-MM-DD)", value="")
                fi_skills   = st.text_input("🛠️ Required Skills",   value=ext.get("required_skills", ""),
                                            help="Auto-detected from posting text.")
                fi_interest = st.selectbox("⭐ Interest Level",     INTEREST_OPTIONS)
                fi_category = st.selectbox("🗂️ Role Category",     CATEGORY_OPTIONS)
                fi_sponsor  = st.text_input("🛂 Sponsorship Info",  value="")
                fi_source   = st.selectbox("🔍 Source",             SOURCE_OPTIONS)
                fi_status   = st.text_input("📌 Status",            value=ext.get("status", "Saved"))
                fi_notes    = st.text_input("📝 Notes",             value=ext.get("notes", ""),
                                            help="Sponsorship warnings are auto-added here.")
                fi_context  = st.text_area(
                    "🏛️ Company Context",
                    height=100,
                    help="Paste company description or team info for more personalized materials.",
                )
                with st.expander("📄 Full job description (stored automatically)"):
                    jd = ext.get("job_description", "")
                    st.text(jd[:1200] + ("…" if len(jd) > 1200 else ""))

                submitted = st.form_submit_button("✅ Confirm & Save Job", type="primary")

            if submitted:
                job = {f: "" for f in tracker.FIELDS}
                job.update({
                    "company": fi_company.strip(), "role": fi_role.strip(),
                    "location": fi_location.strip(), "application_link": fi_link.strip(),
                    "deadline": fi_deadline.strip(), "application_deadline": fi_app_dl.strip(),
                    "required_skills": fi_skills.strip(), "status": fi_status.strip() or "Saved",
                    "notes": fi_notes.strip(), "job_description": ext.get("job_description", ""),
                    "company_context": fi_context.strip(),
                    "interest_level": fi_interest, "role_category": fi_category,
                    "sponsorship_info": fi_sponsor.strip(), "source": fi_source,
                    "date_added": date.today().isoformat(),
                })
                if tracker.is_blank_job(job):
                    st.error("All fields blank — nothing saved.")
                else:
                    jobs = load_jobs()
                    dup = tracker.find_duplicate(job, jobs)
                    if dup is not None:
                        st.warning(f"⚠️ Duplicate: **{job_label(jobs[dup])}** already exists. Not saved again.")
                    else:
                        jobs.append(job)
                        save_jobs(jobs)
                        st.session_state["_import_ok_msg"] = (
                            f"✅ Imported: **{job.get('company', '?')}** — {job.get('role', '?')}"
                        )
                        del st.session_state["import_ext"]
                        st.rerun()

        if not (job.get("company_context") if "job" in dir() else True):
            st.info("💡 **Tip:** Paste company description into Company Context for more personalized materials.")


# ════════════════════════════════════════════════════════════════════════════
# 4. PRIORITY JOBS
# ════════════════════════════════════════════════════════════════════════════
elif section == "🚀 Priority Jobs":
    st.header("🚀 Priority Jobs")
    st.write(
        "Jobs ranked by a transparent score: resume match (40 pts) + interest level (20 pts) "
        "+ deadline urgency (25 pts) + sponsorship/status modifiers. "
        "Higher score = act sooner."
    )

    jobs = load_jobs()
    if not jobs:
        st.info("No jobs saved. Add some via **Add / Import Jobs**.")
    else:
        resume_text = read_resume()

        with st.spinner("Computing priority scores…"):
            scored = []
            for job in jobs:
                jd = job.get("job_description", "")
                ms = None
                if resume_text and jd.strip():
                    _, _, _, ms = matcher.compute_match(jd, resume_text)
                sc, notes = priority.compute_priority_score(job, ms)
                scored.append({"job": job, "score": sc, "notes": notes, "match": ms})

        scored.sort(key=lambda x: x["score"], reverse=True)

        # Filters
        col_cat, col_status = st.columns(2)
        with col_cat:
            cats = ["All"] + sorted({x["job"].get("role_category") or "Unknown" for x in scored})
            cat_filter = st.selectbox("Category:", cats, key="pj_cat")
        with col_status:
            sta_filter = st.selectbox("Status:", ["All"] + STATUS_PRESETS, key="pj_status")

        visible = [
            x for x in scored
            if (cat_filter == "All" or (x["job"].get("role_category") or "Unknown") == cat_filter)
            and (sta_filter == "All" or (x["job"].get("status") or "").lower() == sta_filter.lower())
        ]

        st.write(f"Showing **{len(visible)}** of **{len(scored)}** jobs.")

        for item in visible:
            job, sc, notes, ms = item["job"], item["score"], item["notes"], item["match"]
            label = priority.priority_label(sc)
            emoji = status_emoji(job.get("status", ""))

            with st.container():
                col_info, col_score = st.columns([4, 1])
                with col_info:
                    st.markdown(f"**{emoji} {job_label(job)}**")
                    st.caption("  ·  ".join(notes[:4]))
                    if ms is not None:
                        st.caption(f"Resume match: {ms}/100")
                with col_score:
                    st.metric("Score", f"{sc}/100")
                    st.markdown(f"**{label}**")
                st.divider()


# ════════════════════════════════════════════════════════════════════════════
# 5. TODAY'S ACTION PLAN
# ════════════════════════════════════════════════════════════════════════════
elif section == "📅 Today's Action Plan":
    st.header("📅 Today's Action Plan")
    st.write(
        "Generated from your saved jobs. Tasks are ranked by urgency. "
        "Check them off as you complete them — progress resets when you navigate away."
    )

    jobs = load_jobs()
    tasks = priority.generate_action_plan(jobs, RESUME_PATH)

    if not tasks:
        st.success("✅ Nothing urgent right now. Keep applying and following up!")
    else:
        priority_colors = {"high": "🔴", "medium": "🟡", "low": "🟢"}
        for i, task in enumerate(tasks):
            pc = priority_colors.get(task["priority"], "⚪")
            done = st.checkbox(
                f"{pc} **{task['title']}**",
                key=f"task_{i}",
            )
            if not done:
                st.caption(f"Why: {task['reason']}")
                st.caption(f"Action: {task['action']}")
                if task.get("job") and task["job"] != "—":
                    st.caption(f"Job: {task['job']}")
            st.divider()


# ════════════════════════════════════════════════════════════════════════════
# 6. SAVED JOBS
# ════════════════════════════════════════════════════════════════════════════
elif section == "💼 Saved Jobs":
    st.header("💼 Saved Jobs")
    jobs = load_jobs()

    if not jobs:
        st.info("No jobs saved. Go to **Add / Import Jobs**.")
    else:
        # ── Filters ───────────────────────────────────────────────────────
        col_f, col_s = st.columns([1, 2])
        with col_f:
            status_filter = st.selectbox("Filter by status:", ["All"] + STATUS_PRESETS)
        with col_s:
            search = st.text_input("🔎 Search:",
                                   placeholder="company, role, location, skills, notes…")

        filtered = jobs
        if status_filter != "All":
            filtered = [j for j in filtered if (j.get("status") or "").lower() == status_filter.lower()]
        if search.strip():
            q = search.strip().lower()
            filtered = [
                j for j in filtered
                if q in (j.get("company") or "").lower()
                or q in (j.get("role") or "").lower()
                or q in (j.get("location") or "").lower()
                or q in (j.get("required_skills") or "").lower()
                or q in (j.get("notes") or "").lower()
                or q in (j.get("company_context") or "").lower()
            ]

        st.write(f"Showing **{len(filtered)}** of **{len(jobs)}** job(s).")

        if filtered:
            # Summary table
            table_fields = ["company", "role", "location", "application_deadline",
                            "status", "interest_level", "required_skills"]
            st.dataframe(
                [{f: j.get(f, "") for f in table_fields} for j in filtered],
                use_container_width=True
            )

            # Detail cards
            st.subheader("Details")
            for i, job in enumerate(filtered, 1):
                with st.expander(f"{status_emoji(job.get('status',''))} [{i}] {job_label(job)}"):
                    core_fields = [f for f in tracker.FIELDS if f not in ("job_description", "company_context")]
                    for field in core_fields:
                        val = job.get(field, "") or ""
                        st.markdown(f"**{field}:** {val or '*(blank)*'}")
                    if job.get("company_context"):
                        with st.expander("🏛️ Company Context"):
                            st.text(job["company_context"])
                    if job.get("job_description"):
                        with st.expander("📄 Job Description"):
                            st.text(job["job_description"][:800] + ("…" if len(job["job_description"]) > 800 else ""))

        else:
            st.info("No jobs match your filters.")

        labels = [f"{i}. {job_label(j)}" for i, j in enumerate(jobs, 1)]

        # ── Edit job ──────────────────────────────────────────────────────
        st.divider()
        with st.expander("✏️ Edit a Job"):
            to_edit = st.selectbox("Select job to edit:", labels, key="edit_sel")
            idx = labels.index(to_edit)
            job = jobs[idx]
            with st.form("edit_form"):
                ef = {}
                ecol1, ecol2 = st.columns(2)
                with ecol1:
                    ef["company"]          = st.text_input("Company",          value=job.get("company", ""))
                    ef["role"]             = st.text_input("Role",              value=job.get("role", ""))
                    ef["location"]         = st.text_input("Location",          value=job.get("location", ""))
                    ef["application_link"] = st.text_input("Application Link",  value=job.get("application_link", ""))
                    ef["deadline"]         = st.text_input("Deadline",          value=job.get("deadline", ""))
                    ef["application_deadline"] = st.text_input("App Deadline",  value=job.get("application_deadline", ""))
                with ecol2:
                    ef["interest_level"]   = st.selectbox("Interest Level",    INTEREST_OPTIONS,
                                                          index=INTEREST_OPTIONS.index(job.get("interest_level", "") or ""))
                    ef["role_category"]    = st.selectbox("Role Category",     CATEGORY_OPTIONS,
                                                          index=CATEGORY_OPTIONS.index(job.get("role_category", "") or ""))
                    ef["required_skills"]  = st.text_input("Required Skills",  value=job.get("required_skills", ""))
                    ef["sponsorship_info"] = st.text_input("Sponsorship Info", value=job.get("sponsorship_info", ""))
                    ef["source"]           = st.selectbox("Source",            SOURCE_OPTIONS,
                                                          index=SOURCE_OPTIONS.index(job.get("source", "") or ""))
                    ef["status"]           = st.text_input("Status",           value=job.get("status", ""))
                ef["notes"]            = st.text_input("Notes",            value=job.get("notes", ""))
                ef["date_applied"]     = st.text_input("Date Applied",     value=job.get("date_applied", ""))
                ef["response_date"]    = st.text_input("Response Date",    value=job.get("response_date", ""))
                ef["follow_up_date"]   = st.text_input("Follow-up Date",   value=job.get("follow_up_date", ""))
                ef["contact_name"]     = st.text_input("Contact Name",     value=job.get("contact_name", ""))
                ef["contact_email_or_linkedin"] = st.text_input("Contact Email/LinkedIn",
                                                                value=job.get("contact_email_or_linkedin", ""))
                ef["last_contacted_date"] = st.text_input("Last Contacted", value=job.get("last_contacted_date", ""))
                ef["networking_status"] = st.selectbox("Networking Status", [""] + NET_STATUS_OPTIONS,
                                                       index=0)
                ef["job_description"]  = st.text_area("Job Description",   value=job.get("job_description", ""), height=120)
                ef["company_context"]  = st.text_area("Company Context",   value=job.get("company_context", ""), height=100)
                save_edit = st.form_submit_button("💾 Save Changes", type="primary")

            if save_edit:
                for field, val in ef.items():
                    jobs[idx][field] = val.strip() if isinstance(val, str) else val
                save_jobs(jobs)
                st.success("✅ Job updated.")
                st.rerun()

        # ── Quick status update ───────────────────────────────────────────
        st.divider()
        st.subheader("📌 Update Status")
        to_upd = st.selectbox("Job:", labels, key="upd_sel")
        col_a, col_b = st.columns(2)
        with col_a:
            preset = st.selectbox("Quick pick:", ["— choose —"] + STATUS_PRESETS, key="status_preset")
        with col_b:
            custom = st.text_input("Or type:", key="custom_st")
        if st.button("✅ Update Status", type="primary"):
            new_st = custom.strip() or (preset if preset != "— choose —" else "")
            if not new_st:
                st.error("Choose or type a status.")
            else:
                idx = labels.index(to_upd)
                jobs[idx]["status"] = new_st
                if "applied" in new_st.lower() and not jobs[idx].get("date_applied"):
                    jobs[idx]["date_applied"] = date.today().isoformat()
                save_jobs(jobs)
                st.success(f"✅ Status → **{new_st}**")
                st.rerun()

        # ── Delete ────────────────────────────────────────────────────────
        st.divider()
        st.subheader("🗑️ Delete a Job")
        to_del = st.selectbox("Job to delete:", labels, key="del_sel")
        if st.button("🗑️ Delete", type="secondary"):
            idx = labels.index(to_del)
            removed = jobs.pop(idx)
            save_jobs(jobs)
            st.success(f"Deleted: **{job_label(removed)}**")
            st.rerun()


# ════════════════════════════════════════════════════════════════════════════
# 7. ANALYZE MATCH
# ════════════════════════════════════════════════════════════════════════════
elif section == "🔍 Analyze Match":
    st.header("🔍 Analyze Job Match")
    st.write("Compare your resume against a saved job description to see score, matched skills, and gaps.")

    if not resume_exists():
        st.error("No resume found. Go to **Resume Setup** first.")
    else:
        jobs = load_jobs()
        if not jobs:
            st.info("No jobs saved.")
        else:
            labels = [f"{i}. {job_label(j)}" for i, j in enumerate(jobs, 1)]
            sel = st.selectbox("Select a job:", labels)
            job = jobs[labels.index(sel)]

            if st.button("🔍 Run Match Analysis", type="primary"):
                jd = job.get("job_description", "")
                if not jd.strip():
                    st.warning("This job has no stored description — re-add it with a full JD for a meaningful score.")
                else:
                    resume_text = read_resume()
                    skills_in_jd, matched, missing, score = matcher.compute_match(jd, resume_text)

                    if not skills_in_jd:
                        st.warning("No recognized skills found in the JD. Add keywords to `matcher.py` → `SKILLS`.")
                    else:
                        st.subheader(f"Results: {job_label(job)}")
                        c1, c2, c3 = st.columns(3)
                        c1.metric("🎯 Match Score",     f"{score} / 100")
                        c2.metric("✅ Skills Matched",  f"{len(matched)} / {len(skills_in_jd)}")
                        c3.metric("🛠️ Skills to Add",  len(missing))

                        if score >= 70:
                            st.success("Strong match! Your resume covers most required skills.")
                        elif score >= 40:
                            st.warning("Moderate match. Consider adding missing skills to your resume.")
                        else:
                            st.error("Low match. Several key skills are absent from your resume.")

                        if matched:
                            st.success(f"**Skills you have:** {', '.join(matched)}")
                        if missing:
                            st.warning(f"**Skills to build or highlight:** {', '.join(missing)}")
                            st.caption("Go to **Resume Targeting** for specific bullet suggestions.")

                if not (job.get("company_context") or "").strip():
                    st.info("💡 Tip: Add company context in **Saved Jobs → Edit** for more personalized materials.")


# ════════════════════════════════════════════════════════════════════════════
# 8. RESUME TARGETING
# ════════════════════════════════════════════════════════════════════════════
elif section == "🎯 Resume Targeting":
    st.header("🎯 Resume Targeting")
    st.write(
        "For a selected job, see which resume sections are most relevant, "
        "identify weak spots, and get honest bullet improvement suggestions. "
        "**No experience is fabricated — suggestions are based only on your resume.**"
    )
    st.warning(
        "⚠️ Only use these suggestions if they accurately reflect your real experience. "
        "Do not add skills, tools, or metrics you do not actually have."
    )

    if not resume_exists():
        st.error("No resume found. Go to **Resume Setup** first.")
    else:
        jobs = load_jobs()
        if not jobs:
            st.info("No jobs saved.")
        else:
            labels = [f"{i}. {job_label(j)}" for i, j in enumerate(jobs, 1)]
            sel = st.selectbox("Select a job:", labels, key="rt_sel")
            job = jobs[labels.index(sel)]

            if st.button("🎯 Generate Resume Targeting", type="primary"):
                jd = job.get("job_description", "")
                resume_text = read_resume()

                if not jd.strip():
                    st.warning("No job description stored. Re-add this job with a full JD.")
                else:
                    skills_in_jd, matched, missing, score = matcher.compute_match(jd, resume_text)

                    st.subheader(f"Targeting Report: {job_label(job)}")
                    st.metric("Current Match Score", f"{score}/100")

                    # Most relevant resume sections
                    st.subheader("📌 Top Relevant Resume Lines")
                    relevant_lines = materials.extract_relevant_resume_lines(resume_text, matched, max_lines=6)
                    if relevant_lines:
                        for line in relevant_lines:
                            st.markdown(f"✅ {line}")
                    else:
                        st.info("No resume lines clearly mention the matched skills. Make sure your Skills section is explicit.")

                    # Weak spots
                    st.subheader("🚧 Weak Spots for This Role")
                    if missing:
                        for skill in missing[:8]:
                            in_resume = any(skill.lower() in l.lower() for l in resume_text.splitlines())
                            if in_resume:
                                st.markdown(f"🟡 **{skill}** — appears to be in your resume but may not be clearly labeled. Add it to your Skills section.")
                            else:
                                st.markdown(f"🔴 **{skill}** — not found in resume. Add a bullet if you have real experience; otherwise consider a project.")
                    else:
                        st.success("No major skill gaps detected for this role.")

                    # Bullet improvement suggestions
                    st.subheader("✏️ Bullet Improvement Suggestions")
                    st.caption("Based only on your existing resume content — do not use if inaccurate.")
                    if missing:
                        for skill in missing[:5]:
                            in_resume = any(skill.lower() in l.lower() for l in resume_text.splitlines())
                            if in_resume:
                                # Find the existing line
                                for line in resume_text.splitlines():
                                    if skill.lower() in line.lower() and len(line.strip()) > 20:
                                        st.markdown(
                                            f"**{skill}:** Your resume has:\n"
                                            f"> {line.strip()}\n"
                                            f"Strengthen it: add a metric, outcome, or scope "
                                            f"(e.g., dataset size, time saved, tools used)."
                                        )
                                        break
                            else:
                                st.markdown(
                                    f"**{skill}:** No clear evidence in resume. "
                                    f"If true: add a project or course bullet. "
                                    f"If not: *skip this* — do not fabricate."
                                )
                    else:
                        st.success("All recognized JD skills are in your resume. Focus on quantifying your bullets.")

                    # Export as DOCX
                    st.divider()
                    report_content = (
                        f"Resume Targeting Report\n"
                        f"{job_label(job)}\n"
                        f"Match Score: {score}/100\n\n"
                        f"RELEVANT RESUME LINES\n"
                        + ("\n".join(f"• {l}" for l in relevant_lines) if relevant_lines else "None found.\n")
                        + f"\n\nWEAK SPOTS\n"
                        + ("\n".join(f"• {s}" for s in missing) if missing else "None.\n")
                        + f"\n\n⚠️  Only use suggestions that reflect your real experience.\n"
                    )
                    report_path = os.path.join(
                        GENERATED_DIR,
                        materials.safe_filename(f"{job.get('company', 'job')}_{job.get('role', 'role')}_Resume_Targeting") + ".docx"
                    )
                    os.makedirs(GENERATED_DIR, exist_ok=True)
                    ok = materials.write_docx(report_path, f"Resume Targeting — {job_label(job)}", report_content)
                    if ok:
                        with open(report_path, "rb") as f:
                            st.download_button("⬇️ Download Targeting Report (.docx)", f.read(),
                                               file_name=os.path.basename(report_path),
                                               mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    else:
                        st.text_area("Targeting Report (text):", report_content, height=250)


# ════════════════════════════════════════════════════════════════════════════
# 9. GENERATE MATERIALS
# ════════════════════════════════════════════════════════════════════════════
elif section == "✉️ Generate Materials":
    st.header("✉️ Generate Application Materials")
    st.warning(
        "⚠️ Generated drafts are starting points. **Review and edit before sending.** "
        "The quality improves significantly when company context is added."
    )
    st.write(
        "Generates a cover letter, LinkedIn message, recruiter email, and resume tips — "
        "personalized using your resume and any company context you've provided."
    )

    jobs = load_jobs()
    if not jobs:
        st.info("No jobs saved.")
    else:
        labels = [f"{i}. {job_label(j)}" for i, j in enumerate(jobs, 1)]
        sel = st.selectbox("Select a job:", labels)
        job = jobs[labels.index(sel)]

        if not resume_exists():
            st.warning("No resume saved — materials will use generic text. Go to **Resume Setup**.")

        if not (job.get("company_context") or "").strip():
            st.info(
                "💡 **Tip:** Add company context in **Saved Jobs → Edit** for more specific materials. "
                "Paste the company description, team info, or product details from the job page."
            )

        if st.button("✉️ Generate All Materials", type="primary"):
            resume_text = read_resume()
            jd = job.get("job_description", "")
            matched, missing = [], []

            if resume_text and jd.strip():
                _, matched, missing, _ = matcher.compute_match(jd, resume_text)
            elif not jd.strip():
                st.info("No stored job description — personalization will be generic.")

            name = materials.get_applicant_name(RESUME_PATH)
            written = materials.generate_files(job, matched, missing, name, GENERATED_DIR, resume_text)

            docx_written = [p for p in written if p.endswith(".docx")]
            st.success(
                f"✅ Generated {len(written)} file(s)"
                + (f" — {len(docx_written)} as DOCX" if docx_written else "")
                + ". Review each tab before using."
            )

            company  = job.get("company") or "Company"
            role     = job.get("role") or "Role"
            location = job.get("location") or ""
            ctx      = job.get("company_context") or ""

            tab1, tab2, tab3, tab4 = st.tabs([
                "📝 Cover Letter", "💼 LinkedIn Message",
                "📧 Recruiter Email", "🛠️ Resume Tips",
            ])
            with tab1:
                st.text(materials.cover_letter_template(company, role, location, name, matched, resume_text, ctx))
            with tab2:
                st.text(materials.linkedin_template(company, role, name, matched, ctx))
            with tab3:
                st.text(materials.recruiter_email_template(company, role, name, matched, ctx))
            with tab4:
                st.text(materials.resume_suggestions_template(company, role, missing, matched, resume_text))

            st.caption(
                f"Files saved to `{GENERATED_DIR}/`. "
                "Go to **Export & Download** to download DOCX or ZIP."
            )


# ════════════════════════════════════════════════════════════════════════════
# 10. NETWORKING & FOLLOW-UP
# ════════════════════════════════════════════════════════════════════════════
elif section == "🤝 Networking & Follow-up":
    st.header("🤝 Networking & Follow-up")
    st.write(
        "Track your contacts, see which applications need a follow-up, "
        "and get ready-to-edit message drafts. **Messages are never sent automatically.**"
    )

    jobs = load_jobs()
    if not jobs:
        st.info("No jobs saved.")
    else:
        name = materials.get_applicant_name(RESUME_PATH)
        today = date.today()

        # ── Follow-up suggestions ─────────────────────────────────────────
        st.subheader("⏰ Applications Needing Follow-up")
        followups = []
        for job in jobs:
            if "applied" in (job.get("status") or "").lower():
                d = priority._parse_date(job.get("date_applied") or "")
                if d:
                    days_ago = (today - d).days
                    if days_ago >= 7 and not (job.get("response_date") or "").strip():
                        followups.append((job, days_ago))

        if not followups:
            st.success("✅ No overdue follow-ups right now.")
        else:
            for job, days_ago in followups:
                with st.expander(f"📬 {job_label(job)} — applied {days_ago} days ago"):
                    col_email, col_linkedin = st.columns(2)
                    with col_email:
                        st.markdown("**Follow-up Email Draft:**")
                        st.text_area(
                            "Copy and edit before sending:",
                            value=materials.followup_email_template(
                                job.get("company", "Company"),
                                job.get("role", "Role"),
                                name, days_ago,
                            ),
                            height=200,
                            key=f"fu_email_{job_label(job)}",
                        )
                    with col_linkedin:
                        st.markdown("**LinkedIn Follow-up Draft:**")
                        st.text_area(
                            "Copy and edit:",
                            value=materials.linkedin_followup_template(
                                job.get("company", "Company"),
                                job.get("role", "Role"),
                                name,
                            ),
                            height=200,
                            key=f"fu_li_{job_label(job)}",
                        )

        # ── Networking contacts ───────────────────────────────────────────
        st.divider()
        st.subheader("👥 Jobs Needing a Networking Contact")
        no_contact = [j for j in jobs if not (j.get("contact_name") or "").strip()
                      and (j.get("status") or "").lower() in ("not started", "saved", "")]
        if no_contact:
            st.write(f"{len(no_contact)} job(s) have no networking contact recorded:")
            for job in no_contact[:8]:
                st.markdown(f"- **{job_label(job)}** — find a contact on LinkedIn and record them in **Saved Jobs → Edit**.")
        else:
            st.success("✅ All active jobs have a contact recorded.")

        # ── All networking statuses ───────────────────────────────────────
        st.divider()
        st.subheader("📋 All Contacts")
        with_contacts = [j for j in jobs if (j.get("contact_name") or "").strip()]
        if not with_contacts:
            st.info("No contacts recorded yet. Add contact names in **Saved Jobs → Edit**.")
        else:
            for job in with_contacts:
                st.markdown(
                    f"**{job_label(job)}** → Contact: {job.get('contact_name', '?')} "
                    f"({job.get('contact_email_or_linkedin', '—')}) "
                    f"| Net. Status: `{job.get('networking_status', '—')}` "
                    f"| Last contacted: `{job.get('last_contacted_date', '—')}`"
                )

        # ── Thank-you message generator ───────────────────────────────────
        st.divider()
        st.subheader("🙏 Thank-you Message After a Call")
        interview_jobs = [j for j in jobs if "interview" in (j.get("status") or "").lower()]
        if interview_jobs:
            ty_labels = [job_label(j) for j in interview_jobs]
            ty_sel = st.selectbox("Select job:", ty_labels, key="ty_sel")
            ty_job = interview_jobs[ty_labels.index(ty_sel)]
            ty_contact = ty_job.get("contact_name") or ""
            st.text_area(
                "Thank-you draft (edit before sending):",
                value=materials.thankyou_template(
                    ty_job.get("company", "Company"),
                    ty_job.get("role", "Role"),
                    ty_contact, name,
                ),
                height=230,
                key="ty_draft",
            )
        else:
            st.info("No jobs currently in Interview status.")


# ════════════════════════════════════════════════════════════════════════════
# 11. SKILL GAP DASHBOARD
# ════════════════════════════════════════════════════════════════════════════
elif section == "📊 Skill Gap Dashboard":
    st.header("📊 Skill Gap Dashboard")
    st.write(
        "Skills that repeatedly appear in your saved job descriptions but are absent from your resume. "
        "Focus on the top gaps to increase your match scores across multiple jobs."
    )

    if not resume_exists():
        st.error("No resume found. Go to **Resume Setup** first.")
    else:
        jobs = load_jobs()
        if not jobs:
            st.info("No jobs saved.")
        else:
            with st.spinner("Analyzing skill gaps across all jobs…"):
                skill_data = priority.compute_skill_gaps(jobs, RESUME_PATH)

            if not skill_data:
                st.success("✅ No skill gaps detected across your saved jobs — great resume coverage!")
            else:
                top_skills = list(skill_data.items())[:10]

                # Simple bar chart
                chart_data = {sk: data["count"] for sk, data in top_skills}
                st.bar_chart(chart_data)

                # Grouped breakdown
                by_category: dict = {}
                for skill, data in top_skills:
                    cat = priority.categorize_skill(skill)
                    by_category.setdefault(cat, []).append((skill, data))

                for cat, entries in sorted(by_category.items()):
                    st.subheader(f"📂 {cat}")
                    for skill, data in entries:
                        with st.expander(
                            f"**{skill}** — required by **{data['count']}** job(s)"
                        ):
                            st.markdown(f"**Jobs requiring this:** {', '.join(data['jobs'][:5])}")
                            st.markdown(f"**Suggested action:** {priority.suggest_skill_action(skill)}")

                # Export
                st.divider()
                report_lines = ["Skill Gap Report\n" + "="*50]
                for skill, data in top_skills:
                    report_lines.append(
                        f"\n{skill} ({data['count']} jobs)\n"
                        f"  Jobs: {', '.join(data['jobs'][:3])}\n"
                        f"  Action: {priority.suggest_skill_action(skill)}"
                    )
                report_text = "\n".join(report_lines)
                report_path = os.path.join(GENERATED_DIR, "Skill_Gap_Report.docx")
                os.makedirs(GENERATED_DIR, exist_ok=True)
                ok = materials.write_docx(report_path, "Skill Gap Report", report_text)
                if ok:
                    with open(report_path, "rb") as f:
                        st.download_button(
                            "⬇️ Download Skill Gap Report (.docx)", f.read(),
                            file_name="Skill_Gap_Report.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        )


# ════════════════════════════════════════════════════════════════════════════
# 12. APPLICATION DIAGNOSIS
# ════════════════════════════════════════════════════════════════════════════
elif section == "🩺 Application Diagnosis":
    st.header("🩺 Application Diagnosis")
    st.write(
        "Based on your tracker data, this section identifies potential reasons "
        "applications may not be converting — and gives practical next steps."
    )

    jobs = load_jobs()
    issues = priority.diagnose_applications(jobs, RESUME_PATH)

    for issue in issues:
        sev = issue["severity"]
        icon = severity_icon(sev)
        if sev == "ok":
            st.success(f"{icon} **{issue['issue']}**\n\n{issue['detail']}")
        elif sev == "high":
            st.error(f"{icon} **{issue['issue']}**\n\n{issue['detail']}")
        elif sev == "medium":
            st.warning(f"{icon} **{issue['issue']}**\n\n{issue['detail']}")
        else:
            st.info(f"{icon} **{issue['issue']}**\n\n{issue['detail']}")

        if issue.get("recommendation"):
            st.markdown(f"**→ Recommendation:** {issue['recommendation']}")
        st.divider()

    # Export
    report_path = os.path.join(GENERATED_DIR, "Application_Diagnosis.docx")
    os.makedirs(GENERATED_DIR, exist_ok=True)
    report_text = "\n\n".join(
        f"{i['issue']}\n{i['detail']}\n→ {i.get('recommendation','')}"
        for i in issues
    )
    ok = materials.write_docx(report_path, "Application Diagnosis Report", report_text)
    if ok:
        with open(report_path, "rb") as f:
            st.download_button(
                "⬇️ Download Diagnosis Report (.docx)", f.read(),
                file_name="Application_Diagnosis.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )


# ════════════════════════════════════════════════════════════════════════════
# 13. EXPORT & DOWNLOAD
# ════════════════════════════════════════════════════════════════════════════
elif section == "📥 Export & Download":
    st.header("📥 Export & Download")
    st.write("Download your tracker data and all generated materials. Nothing is uploaded.")

    # ── Tracker CSV ───────────────────────────────────────────────────────
    st.subheader("📊 Job Tracker Spreadsheet")
    jobs = load_jobs()
    if not jobs:
        st.info("No jobs saved yet.")
    else:
        buf = io.StringIO()
        writer = csv_mod.DictWriter(buf, fieldnames=tracker.FIELDS)
        writer.writeheader()
        writer.writerows(jobs)
        st.download_button(
            label=f"⬇️ Download tracker spreadsheet (.csv, opens in Excel / Google Sheets)  — {len(jobs)} job(s)",
            data=buf.getvalue(),
            file_name="internship_tracker.csv",
            mime="text/csv",
        )

    st.divider()

    # ── Generated materials ───────────────────────────────────────────────
    st.subheader("✉️ Generated Application Materials")
    os.makedirs(GENERATED_DIR, exist_ok=True)
    all_files = sorted(f for f in os.listdir(GENERATED_DIR)
                       if not f.startswith("."))
    docx_files = [f for f in all_files if f.endswith(".docx")]
    txt_files  = [f for f in all_files if f.endswith(".txt")]

    if not all_files:
        st.info("No generated materials yet. Go to **Generate Materials** to create some.")
    else:
        # DOCX downloads (primary)
        if docx_files:
            st.markdown("**Word Documents (.docx):**")
            for fname in docx_files:
                with open(os.path.join(GENERATED_DIR, fname), "rb") as f:
                    st.download_button(
                        f"⬇️ {fname}", f.read(), file_name=fname,
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        key=f"dl_docx_{fname}",
                    )

        # TXT fallback
        if txt_files:
            with st.expander(f"📄 Text fallback files ({len(txt_files)})"):
                for fname in txt_files:
                    with open(os.path.join(GENERATED_DIR, fname)) as f:
                        content = f.read()
                    st.download_button(
                        f"⬇️ {fname}", content, file_name=fname,
                        mime="text/plain", key=f"dl_txt_{fname}",
                    )

        # ZIP all
        st.divider()
        zip_buf = io.BytesIO()
        with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
            for fname in all_files:
                zf.write(os.path.join(GENERATED_DIR, fname), fname)
        zip_buf.seek(0)
        st.download_button(
            f"📦 Download All {len(all_files)} Files as ZIP",
            zip_buf, file_name="application_materials.zip",
            mime="application/zip", type="primary",
        )

    st.divider()

    # ── Generate reports on demand ────────────────────────────────────────
    st.subheader("📑 Generate & Download Reports")
    jobs = load_jobs()  # fresh after possible CSV changes above

    col_r1, col_r2 = st.columns(2)

    with col_r1:
        if st.button("📊 Generate Priority Report (.docx)"):
            resume_text = read_resume()
            scored = []
            for job in jobs:
                jd = job.get("job_description", "")
                ms = None
                if resume_text and jd.strip():
                    _, _, _, ms = matcher.compute_match(jd, resume_text)
                sc, notes = priority.compute_priority_score(job, ms)
                scored.append((sc, job, notes))
            scored.sort(reverse=True)
            report_text = "Priority Jobs Report\n" + "="*50 + "\n\n"
            for sc, job, notes in scored:
                report_text += (
                    f"{priority.priority_label(sc)}  ({sc}/100)\n"
                    f"{job_label(job)}\n"
                    f"  {chr(10).join(notes)}\n\n"
                )
            rp = os.path.join(GENERATED_DIR, "Priority_Jobs_Report.docx")
            os.makedirs(GENERATED_DIR, exist_ok=True)
            if materials.write_docx(rp, "Priority Jobs Report", report_text):
                with open(rp, "rb") as f:
                    st.download_button("⬇️ Download Priority Report", f.read(),
                                       file_name="Priority_Jobs_Report.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       key="dl_priority")
            else:
                st.text_area("Priority Report:", report_text, height=200)

        if st.button("📅 Generate Action Plan Report (.docx)"):
            tasks = priority.generate_action_plan(jobs, RESUME_PATH)
            report_text = "Today's Action Plan\n" + "="*50 + "\n\n"
            for t in tasks:
                report_text += f"[{t['priority'].upper()}] {t['title']}\nWhy: {t['reason']}\nAction: {t['action']}\n\n"
            rp = os.path.join(GENERATED_DIR, "Action_Plan_Report.docx")
            os.makedirs(GENERATED_DIR, exist_ok=True)
            if materials.write_docx(rp, "Today's Action Plan", report_text):
                with open(rp, "rb") as f:
                    st.download_button("⬇️ Download Action Plan", f.read(),
                                       file_name="Action_Plan_Report.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       key="dl_action")
            else:
                st.text_area("Action Plan:", report_text, height=200)

    with col_r2:
        if st.button("📊 Generate Skill Gap Report (.docx)") and resume_exists():
            skill_data = priority.compute_skill_gaps(jobs, RESUME_PATH)
            report_text = "Skill Gap Report\n" + "="*50 + "\n\n"
            for skill, data in list(skill_data.items())[:15]:
                report_text += (
                    f"{skill}  ({data['count']} jobs)\n"
                    f"  Jobs: {', '.join(data['jobs'][:3])}\n"
                    f"  Action: {priority.suggest_skill_action(skill)}\n\n"
                )
            rp = os.path.join(GENERATED_DIR, "Skill_Gap_Report.docx")
            os.makedirs(GENERATED_DIR, exist_ok=True)
            if materials.write_docx(rp, "Skill Gap Report", report_text):
                with open(rp, "rb") as f:
                    st.download_button("⬇️ Download Skill Gap Report", f.read(),
                                       file_name="Skill_Gap_Report.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       key="dl_skillgap")

        if st.button("🩺 Generate Diagnosis Report (.docx)"):
            issues = priority.diagnose_applications(jobs, RESUME_PATH)
            report_text = "Application Diagnosis Report\n" + "="*50 + "\n\n"
            for iss in issues:
                report_text += f"[{iss['severity'].upper()}] {iss['issue']}\n{iss['detail']}\n→ {iss.get('recommendation','')}\n\n"
            rp = os.path.join(GENERATED_DIR, "Application_Diagnosis.docx")
            os.makedirs(GENERATED_DIR, exist_ok=True)
            if materials.write_docx(rp, "Application Diagnosis", report_text):
                with open(rp, "rb") as f:
                    st.download_button("⬇️ Download Diagnosis Report", f.read(),
                                       file_name="Application_Diagnosis.docx",
                                       mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                                       key="dl_diag")


# ════════════════════════════════════════════════════════════════════════════
# 14. PRIVACY NOTE
# ════════════════════════════════════════════════════════════════════════════
elif section == "🔒 Privacy Note":
    st.header("🔒 Privacy Note")
    st.write("This app runs **entirely on your local computer**. No data is sent anywhere.")

    st.subheader("Where your data lives")
    st.markdown("""
| File | Contents |
|---|---|
| `data/resume.txt` | Your resume text |
| `data/internship_tracker.csv` | All saved job data (25 fields per job) |
| `generated_materials/*.docx` | Cover letters, emails, reports |
| `generated_materials/*.txt` | Plain-text fallback files |
""")

    st.subheader("GitHub safety (.gitignore protects these)")
    st.markdown("""
- `data/resume.txt` and `data/*.txt`
- `data/internship_tracker.csv`
- `generated_materials/*.docx`, `*.txt`, `*.pdf`, `*.zip`
- `private_local_backup/`, `.env`

Only `examples/` (fake sample data) is committed to the repository.
""")

    st.subheader("Limitations")
    st.markdown("""
- No web scraping — all job data must be pasted manually.
- No automatic application submission.
- No AI APIs — all analysis is keyword-based.
- Quality of generated materials depends on the company context and job description you provide.
- Generated drafts must always be reviewed and edited before sending.
""")
