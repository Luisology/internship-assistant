# Internship Assistant

A local **internship application operating system**: track jobs, score how your resume matches each posting, generate Word-format outreach drafts, and surface the priorities, skill gaps, and follow-ups that actually move your search forward.

Runs entirely on your computer. No internet, no scraping, no paid APIs, no auto-submission. Your resume, jobs, and generated drafts never leave your machine.

---

## Product experience

The app ships with a **polished, SaaS-style Streamlit web interface**:

- **Premium landing page** — gradient hero, glass-card application mockup, feature grid, 4-step workflow, privacy block, footer. First-time visitors see the landing page before entering the app.
- **Local demo sign in / sign up** — passwords are hashed with PBKDF2-SHA256 (200,000 iterations, 16-byte random salt) and stored only in `data/users.json` on your computer. No email is sent. No data leaves your machine. **This is local demo authentication only — for a hosted deployment, plug in a real auth provider.**
- **Continue as Guest** — every auth screen (landing, sign in, sign up) has a guest button. Guest mode is fully featured and identical to the previous version of the app.
- **Authenticated app shell** — top app bar with section breadcrumb and the current user; sidebar navigation grouped by workflow stage (Start · Manage · Follow Through · Export & Safety); Sign Out / Exit Guest from the sidebar.
- **Premium UI primitives** — dark indigo theme, glass cards, gradient buttons, status pills, priority badges, polished metric cards, intentional empty states. Implemented as a single CSS injection at the top of `app.py` plus reusable Python helpers (`hero`, `metric_card`, `pill`, `status_pill`, `priority_pill`, `empty_state`). No JavaScript build step.

> ⚠️ **Local demo authentication only.** No email verification, no password reset, no rate limiting, no MFA. For a production deployment, connect a real auth provider (Auth0, Clerk, Supabase, your own backend, etc.).

The CLI is unchanged and remains the fastest way to do quick edits from a terminal.

---

## What this app helps you answer

1. Which jobs should I prioritize this week?
2. What should I do today?
3. Which applications need a follow-up?
4. Which skills do I keep missing?
5. Why might I not be getting responses?
6. How should I target my resume to a specific job?
7. How do I export everything as normal Word documents and a spreadsheet?

---

## Features

### Streamlit web app (recommended)

| Section | What it does |
|---|---|
| 🏠 **Home Dashboard** | Pipeline counts (Not Started / Applied / Interview / Offer / Rejected), interview rate, recent jobs, 4-step workflow guide |
| 📄 **Resume Setup** | Upload `.pdf` or `.txt`, or paste your resume text. Saved to `data/resume.txt` only on your computer. |
| ➕ **Add / Import Jobs** | Two tabs: fill a form, or paste a full posting and let labeled-line extraction (`Company:`, `Role:`, `Apply by:`, etc.) prefill an editable preview. Includes duplicate detection. |
| 🚀 **Priority Jobs** | Rule-based priority score (0–100) per job using match score, interest level, deadline urgency, sponsorship signals, and current status — every score is explained in plain text. |
| 📅 **Today's Action Plan** | A short, ranked task list ("Apply to X", "Follow up on Y", "Add company context for Z") generated from your tracker state. |
| 💼 **Saved Jobs** | Filter by status, search by keyword, edit any field including **company context**, update status, delete. |
| 🔍 **Analyze Match** | Score your resume against a job description. Shows matched and missing skills. |
| 🎯 **Resume Targeting** | Per-job: relevant resume lines, weak spots, suggested bullet rewrites. **Suggestions are based only on text already in your resume — nothing is fabricated.** |
| ✉️ **Generate Materials** | Creates a cover letter, LinkedIn message, recruiter email, and resume tip sheet. Personalized using matched skills, relevant resume lines, and pasted **company context**. Saved as **`.docx`** (with `.txt` fallback). |
| 🤝 **Networking & Follow-up** | Tracks contact name / link / last contacted / networking status. Surfaces applications that need a polite follow-up; generates follow-up email, LinkedIn nudge, and post-interview thank-you drafts. **Nothing is sent automatically.** |
| 📊 **Skill Gap Dashboard** | Aggregates missing skills across all jobs, groups them (Programming / Data / Finance / Cloud / etc.), and suggests practical next steps per skill. |
| 🩺 **Application Diagnosis** | Detects patterns: low average match, lots saved but few applied, no networking, high rejection rate, etc. Each issue comes with a concrete recommendation. |
| 📥 **Export & Download** | Tracker spreadsheet (`.csv`, opens in Excel / Google Sheets), individual `.docx` files, ZIP of everything, plus on-demand `.docx` reports for Priority, Action Plan, Skill Gap, and Diagnosis. |
| 🔒 **Privacy Note** | Lists every file on disk and what's in it. |

### CLI (terminal menu)

Same data store, same matcher, lighter feature set: add, import-from-text, list, edit, update status, delete, analyze match, generate materials. Good for quick tweaks without opening a browser.

---

## Installation

You need **Python 3.8 or later**.

```bash
git clone https://github.com/YOUR_USERNAME/internship-assistant.git
cd internship-assistant
pip3 install -r requirements.txt
```

`requirements.txt` installs `streamlit` (web UI), `pypdf` (PDF resume extraction), and `python-docx` (Word document export).

If `python-docx` is unavailable, the generator falls back to plain `.txt` automatically — nothing crashes, you just get text files.

---

## How to run

### Web app (recommended)

```bash
python3 -m streamlit run app.py
```

Streamlit opens a browser tab at `http://localhost:8501`.

### CLI

```bash
python3 -m internship_assistant.cli
```

---

## Deployment

### Run locally (recommended for personal use)

```bash
git clone https://github.com/Luisology/internship-assistant.git
cd internship-assistant
pip3 install -r requirements.txt
python3 -m streamlit run app.py
```

This is the **privacy-preserving** way to use the app: your resume and tracker stay on your computer, your demo accounts live only in `data/users.json`, and nothing is uploaded.

### Deploy on Streamlit Community Cloud

The repo is ready for [share.streamlit.io](https://share.streamlit.io). Deploy steps:

1. Sign in to Streamlit Community Cloud with your GitHub account.
2. Click **New app**.
3. Settings to enter:
   - **Repository:** `Luisology/internship-assistant`
   - **Branch:** `main`
   - **Main file path:** `app.py`
   - **Python version:** 3.11 (default — works fine)
4. Click **Deploy**. The first build installs `streamlit`, `pypdf`, and `python-docx` from `requirements.txt` (~1–2 min).
5. The dark theme is picked up automatically from `.streamlit/config.toml`.

> ⚠️ **Privacy note for the cloud demo.** Streamlit Community Cloud is a public, multi-tenant platform. Anyone with your app's URL can interact with the deployed instance. The local-first privacy guarantees in this README **do not apply** to the cloud deployment:
> - Files written to `data/resume.txt`, `data/internship_tracker.csv`, `data/users.json`, and `generated_materials/*` live in the cloud container's filesystem (ephemeral, but readable to the running app instance and any visitor while the app is up).
> - Demo accounts created on the cloud version are visible to other users of the same instance.
> - **For real personal data — your actual resume, your actual job tracker — run locally.** Use the cloud deployment only as a public demo with sample data.
>
> If you do deploy publicly, consider:
> - Wiping `data/` and `generated_materials/` on each restart (Streamlit Cloud restarts containers periodically).
> - Adding a banner to `app.py` warning visitors that data is shared.
> - Disabling Sign Up (point everyone to "Continue as Guest") — easy patch in `render_landing()`.

### Files that ship to the cloud

Everything tracked by git ships. Currently that's:

```
.gitignore
.streamlit/config.toml          # theme only, no secrets
LICENSE
README.md
app.py
data/.gitkeep
examples/sample_resume.txt      # fake "Jane Doe" — safe sample
examples/sample_job_posting.txt # fake "Example Tech Co" — safe sample
generated_materials/.gitkeep
internship_assistant/*.py       # __init__, auth, cli, matcher, materials, priority, tracker
pyproject.toml
requirements.txt
```

Your real resume, real tracker, real users.json, real generated drafts, and `private_local_backup/` are **gitignored** and never reach GitHub or the cloud.

### Secrets

Never commit `.streamlit/secrets.toml` — it's gitignored explicitly. If a future feature needs an API key, set it via Streamlit Cloud's **Settings → Secrets** UI (those secrets stay on Streamlit's servers and are loaded into `st.secrets` at runtime).

---

## Set up your resume

Match scoring and material generation read your resume from `data/resume.txt`.

**In the web app:** open **Resume Setup**, upload a PDF/TXT or paste text — it's saved automatically.

**From the CLI:**
```bash
cp examples/sample_resume.txt data/resume.txt
# then edit data/resume.txt with your real content
```

The first non-blank line is used as your name in generated materials.

---

## Why "company context" matters

Generated cover letters and emails are dramatically more specific when you paste a paragraph or two about the company / team / product into the **Company Context** field on a job. Without it, drafts fall back to generic phrasing. The app explicitly tells you when context is missing.

You enter context in **Add / Import Jobs** or any time afterward via **Saved Jobs → Edit**.

---

## Example workflow

1. **Resume Setup** — upload your resume PDF.
2. **Add / Import Jobs** — paste 5 postings; tab "Import from Text" auto-extracts most fields.
3. For your top 3 jobs, paste a short company description into **Company Context**.
4. **Priority Jobs** — see them ranked with explanations.
5. **Today's Action Plan** — a ranked task list based on your current state.
6. **Analyze Match** for the top one — see matched and missing skills.
7. **Generate Materials** — get four `.docx` drafts. Review and edit before sending.
8. After applying, set status to **Applied** and fill in `date_applied`.
9. A week later, **Networking & Follow-up** highlights anything that needs a nudge.
10. **Skill Gap Dashboard** + **Application Diagnosis** show patterns across your full search.
11. **Export & Download** — pull your tracker `.csv` and a ZIP of all generated documents.

---

## Project structure

```
internship-assistant/
├── app.py                              # Streamlit web app
├── internship_assistant/
│   ├── __init__.py
│   ├── cli.py                          # terminal menu
│   ├── tracker.py                      # CSV I/O, 25-field schema, migration, extraction
│   ├── matcher.py                      # keyword-based resume↔JD scorer
│   ├── materials.py                    # cover letter / LinkedIn / email / suggestions, DOCX writer
│   └── priority.py                     # priority score, action plan, skill gap, diagnosis
├── examples/
│   ├── sample_resume.txt               # fake resume — safe to share
│   └── sample_job_posting.txt          # fake posting — safe to share
├── data/
│   └── .gitkeep                        # your real resume + tracker live here, gitignored
├── generated_materials/
│   └── .gitkeep                        # generated drafts live here, gitignored
├── requirements.txt
├── pyproject.toml
├── LICENSE
├── .gitignore
└── README.md
```

---

## Data model

The tracker CSV stores 25 fields per job. New columns are auto-added to existing CSVs at startup (`tracker.migrate_csv`) — old files keep working without manual migration.

Original 9 fields: `company`, `role`, `location`, `application_link`, `deadline`, `required_skills`, `status`, `notes`, `job_description`.

Added later: `company_context`, `interest_level`, `role_category`, `sponsorship_info`, `application_deadline`, `date_added`, `date_applied`, `response_date`, `source`, `follow_up_date`, `contact_name`, `contact_email_or_linkedin`, `last_contacted_date`, `networking_status`.

CSV is plain text — opens cleanly in Excel, Numbers, or Google Sheets.

---

## How priority scoring works

A transparent rule-based score from 0 to 100. Every score comes with a plain-text explanation of the points contributed by each rule:

- **Resume match** — up to +40 pts
- **Interest level** — High +20 / Medium +10
- **Deadline urgency** — −15 (passed) up to +25 (within 3 days, ⚠️ urgent)
- **Sponsorship concern** — −15 if "cannot sponsor" detected
- **Status** — Offer +10, Interview +5, Applied −5, Rejected −40

Labels: 🔴 High Priority (≥65) · 🟡 Medium (35–64) · 🟢 Low (<35).

Tune the weights by editing `compute_priority_score` in `internship_assistant/priority.py`.

---

## Privacy

This app runs entirely on your computer. **Nothing is uploaded.** The following files are excluded from git via `.gitignore`:

| Pattern | Why excluded |
|---|---|
| `data/resume.txt`, `data/*.txt` | Personal resume |
| `data/internship_tracker.csv` | Real application data |
| `data/users.json` | Local demo accounts (hashed, but still personal) |
| `generated_materials/*.txt`, `*.docx`, `*.pdf`, `*.zip` | Drafts that include your name and company-specific text |
| `private_local_backup/` | Optional local backup folder |
| Root-level `resume.txt`, `resume*.txt`, `internship_tracker.csv` | Legacy paths from earlier versions |
| `.streamlit/` | Local Streamlit config and secrets |

Only files in `examples/` (with fake "Jane Doe" / "Example Tech Co" data) are safe to share.

---

## Limitations

- **No web scraping.** You paste job postings; the app does not fetch URLs.
- **No automatic online research.** Company context only exists if you paste it.
- **No automatic application submission.** No emails or LinkedIn messages are sent. Drafts must be reviewed and sent by you.
- **No paid APIs.** No LLM calls. The matcher uses a curated keyword list — add or remove entries in `internship_assistant/matcher.py` to tune for your field.
- **Quality depends on the context you provide.** Empty company-context boxes produce generic drafts.
- **Generated drafts are starting points.** Always review and edit before sending. Resume suggestions and bullet rewrites must only be used if they accurately reflect your real experience.

---

## Future improvements

- PDF export (DOCX is implemented; PDF is intentionally deferred until it can be done without heavy dependencies)
- Optional local LLM integration for richer drafts (no paid APIs)
- Calendar sync for deadlines and interviews
- Per-job interview prep notes

---

## License

MIT — see [LICENSE](LICENSE).
