"""Rule-based priority scoring, skill gap analysis, action planning, and diagnosis.

All logic is transparent and explainable — no ML models.
"""

import os
import re
from datetime import date, datetime

from internship_assistant import matcher

# ── Skill categories ──────────────────────────────────────────────────────────

SKILL_CATEGORIES = {
    "Programming":    ["python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
                       "ruby", "swift", "kotlin", "php", "scala", "r", "matlab"],
    "Web / Frameworks": ["react", "angular", "vue", "node.js", "express", "django", "flask",
                         "fastapi", "spring", "rails", "next.js", "html", "css"],
    "Data / ML":      ["sql", "mysql", "postgresql", "mongodb", "redis", "nosql", "pandas",
                       "numpy", "tensorflow", "pytorch", "scikit-learn", "spark", "hadoop",
                       "machine learning", "deep learning", "nlp", "computer vision",
                       "data structures", "algorithms", "statistics"],
    "Cloud / DevOps": ["aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
                       "linux", "bash", "git", "github", "jira", "agile", "scrum",
                       "rest", "graphql", "api", "microservices", "oop"],
    "Analytics / BI": ["tableau", "power bi", "excel", "pivot table", "vlookup"],
    "Finance":        ["financial modeling", "valuation", "dcf", "comparable companies",
                       "equity research", "accounting", "financial statements", "gaap", "ifrs",
                       "audit", "tax", "bloomberg", "capital markets", "m&a",
                       "portfolio management", "investment banking", "corporate finance",
                       "risk assessment"],
}


def _parse_date(s):
    """Try common date formats. Return date or None."""
    if not s:
        return None
    s = s.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%m-%d-%Y", "%B %d, %Y", "%b %d, %Y",
                "%b %d %Y", "%d %B %Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


# ── Priority scoring ──────────────────────────────────────────────────────────

def compute_priority_score(job, match_score=None):
    """Return (score 0–100, list[str] explanations).

    Transparent rule-based scoring:
      • Resume match    0–40 pts
      • Interest level  0–20 pts
      • Deadline        −15 to +25 pts
      • Sponsorship     −15 pts if concern flagged
      • Status          −40 to +10 pts modifier
    """
    score = 0
    notes = []

    # 1. Resume match (0–40 pts)
    if match_score is not None:
        pts = round(float(match_score) * 0.40)
        score += pts
        notes.append(f"Resume match {match_score}/100 → +{pts} pts")

    # 2. Interest level (0–20 pts)
    interest = (job.get("interest_level") or "").strip().lower()
    if interest == "high":
        score += 20
        notes.append("High interest → +20 pts")
    elif interest == "medium":
        score += 10
        notes.append("Medium interest → +10 pts")

    # 3. Deadline urgency (−15 to +25 pts)
    dl_str = (job.get("application_deadline") or job.get("deadline") or "").strip()
    dl = _parse_date(dl_str)
    if dl:
        days = (dl - date.today()).days
        if days < 0:
            score -= 15
            notes.append(f"Deadline passed ({dl_str}) → −15 pts")
        elif days <= 3:
            score += 25
            notes.append(f"Deadline in {days}d → +25 pts ⚠️ URGENT")
        elif days <= 7:
            score += 18
            notes.append(f"Deadline in {days}d → +18 pts")
        elif days <= 14:
            score += 10
            notes.append(f"Deadline in {days}d → +10 pts")
        elif days <= 30:
            score += 5
            notes.append(f"Deadline in {days}d → +5 pts")

    # 4. Sponsorship concern (−15 pts)
    sponsor = (job.get("sponsorship_info") or "").lower()
    if any(k in sponsor for k in ["cannot sponsor", "will not sponsor", "no sponsor"]):
        score -= 15
        notes.append("Sponsorship concerns → −15 pts")

    # 5. Status modifier
    status = (job.get("status") or "").lower()
    if "offer" in status:
        score += 10
        notes.append("Has offer → +10 pts")
    elif "interview" in status or "final round" in status:
        score += 5
        notes.append("In interview process → +5 pts")
    elif "applied" in status:
        score -= 5
        notes.append("Already applied → −5 pts (de-prioritized for 'to apply' list)")
    elif "rejected" in status or "withdrawn" in status:
        score -= 40
        notes.append("Rejected/Withdrawn → −40 pts")

    return max(0, min(100, score)), notes


def priority_label(score):
    if score >= 65:
        return "🔴 High Priority"
    elif score >= 35:
        return "🟡 Medium Priority"
    else:
        return "🟢 Low Priority"


# ── Skill gap analysis ────────────────────────────────────────────────────────

def compute_skill_gaps(jobs, resume_path):
    """Return {skill: {"count": int, "jobs": [label]}} sorted by count desc."""
    if not os.path.exists(resume_path):
        return {}
    with open(resume_path) as f:
        resume_text = f.read()

    skill_data = {}
    for job in jobs:
        jd = job.get("job_description", "")
        if not jd.strip():
            continue
        _, _, missing, _ = matcher.compute_match(jd, resume_text)
        label = f"{job.get('company', '?')} — {job.get('role', '?')}"
        for skill in missing:
            if skill not in skill_data:
                skill_data[skill] = {"count": 0, "jobs": []}
            skill_data[skill]["count"] += 1
            if label not in skill_data[skill]["jobs"]:
                skill_data[skill]["jobs"].append(label)

    return dict(sorted(skill_data.items(), key=lambda x: x[1]["count"], reverse=True))


def categorize_skill(skill):
    for cat, skills in SKILL_CATEGORIES.items():
        if skill.lower() in skills:
            return cat
    return "Other"


def suggest_skill_action(skill):
    s = skill.lower()
    if s in ("python", "java", "javascript", "typescript", "c++", "c#", "go", "r", "scala"):
        return f"Build a small project in {skill} and add it to your resume under Projects."
    if s in ("sql", "mysql", "postgresql"):
        return "Add a project where you queried and analyzed real data using SQL."
    if s in ("excel", "pivot table", "vlookup"):
        return "Add a bullet showing Excel analysis, pivot tables, or financial modeling."
    if s in ("tableau", "power bi"):
        return f"Create a sample dashboard in {skill} using a public dataset and add it to your portfolio."
    if s in ("financial modeling", "valuation", "dcf"):
        return "Document a case study, course project, or competition that involved financial modeling."
    if s in ("git", "github"):
        return "Mention Git and GitHub explicitly in your Skills section and link your GitHub profile."
    if s in ("machine learning", "deep learning", "nlp"):
        return f"Add a course project, Kaggle entry, or independent project using {skill}."
    if s in ("aws", "azure", "gcp"):
        return f"Complete a free-tier cloud project on {skill} and list it under Projects or Skills."
    if s in ("docker", "kubernetes"):
        return f"Containerize an existing project with {skill} and document the process on GitHub."
    if s in ("accounting", "gaap", "ifrs", "audit"):
        return "Highlight relevant coursework, case competitions, or internship experience involving accounting."
    return f"If you have experience with {skill}, add it explicitly to your Skills section and support it with a bullet."


# ── Today's Action Plan ───────────────────────────────────────────────────────

def generate_action_plan(jobs, resume_path):
    """Return a prioritized list of action task dicts (up to 15)."""
    today = date.today()
    resume_exists = os.path.exists(resume_path)
    tasks = []

    if not resume_exists:
        tasks.append({
            "priority": "high",
            "type": "resume",
            "title": "Save your resume",
            "reason": "No resume found — match analysis and material generation require it.",
            "action": "Go to Resume Setup and paste or upload your resume.",
            "job": "—",
        })

    for job in jobs:
        company = job.get("company") or "Unknown"
        role    = job.get("role") or "Unknown"
        status  = (job.get("status") or "").strip().lower()
        interest = (job.get("interest_level") or "").lower()
        label   = f"{company} — {role}"

        # Urgent deadline
        dl_str = (job.get("application_deadline") or job.get("deadline") or "").strip()
        dl = _parse_date(dl_str)
        if dl:
            days = (dl - today).days
            if 0 <= days <= 3 and status in ("not started", "saved", ""):
                tasks.append({
                    "priority": "high",
                    "type": "urgent",
                    "title": f"⚠️ Apply NOW — deadline in {days}d: {label}",
                    "reason": f"Application deadline is {dl_str}.",
                    "action": "Generate materials and submit your application immediately.",
                    "job": label,
                })

        # High interest, not started
        if interest == "high" and status in ("not started", "saved", ""):
            tasks.append({
                "priority": "high",
                "type": "apply",
                "title": f"Apply to {label}",
                "reason": "High-interest job not yet applied to.",
                "action": "Generate materials (cover letter, email) and submit your application.",
                "job": label,
            })

        # Follow up on applications older than 7 days with no response
        if "applied" in status:
            applied_date = _parse_date(job.get("date_applied") or "")
            if applied_date:
                days_ago = (today - applied_date).days
                if days_ago >= 7 and not (job.get("response_date") or "").strip():
                    tasks.append({
                        "priority": "medium",
                        "type": "followup",
                        "title": f"Follow up on {label}",
                        "reason": f"Applied {days_ago} days ago with no logged response.",
                        "action": "Go to Networking & Follow-up for a follow-up message draft.",
                        "job": label,
                    })

        # No company context on pending jobs
        if not (job.get("company_context") or "").strip() and status in ("not started", "saved", ""):
            tasks.append({
                "priority": "low",
                "type": "context",
                "title": f"Add company context for {label}",
                "reason": "No company context — generated materials will be generic.",
                "action": "Paste the company description or team notes into the Company Context field.",
                "job": label,
            })

        # Blank/stale status
        if not status or status == "saved":
            tasks.append({
                "priority": "low",
                "type": "status",
                "title": f"Update status for {label}",
                "reason": "Status is unclear — hard to prioritize.",
                "action": "Go to Saved Jobs and set a meaningful status.",
                "job": label,
            })

    order = {"high": 0, "medium": 1, "low": 2}
    tasks.sort(key=lambda t: order.get(t["priority"], 2))
    return tasks[:15]


# ── Application diagnosis ─────────────────────────────────────────────────────

def diagnose_applications(jobs, resume_path):
    """Return a list of diagnosis dicts based on tracker data."""
    today = date.today()
    issues = []

    total = len(jobs)
    if total == 0:
        return [{
            "severity": "high",
            "issue": "No jobs saved yet.",
            "detail": "The tracker is empty.",
            "recommendation": "Add at least 5 target jobs using Add / Import Jobs.",
        }]

    statuses = [(j.get("status") or "").lower() for j in jobs]
    applied    = sum(1 for s in statuses if "applied" in s)
    not_started = sum(1 for s in statuses if not s or s in ("not started", "saved"))
    interview  = sum(1 for s in statuses if "interview" in s)
    rejected   = sum(1 for s in statuses if "rejected" in s)

    # Average match score
    avg_score = None
    if os.path.exists(resume_path):
        with open(resume_path) as f:
            resume_text = f.read()
        scores = []
        for job in jobs:
            jd = job.get("job_description", "")
            if jd.strip():
                _, _, _, sc = matcher.compute_match(jd, resume_text)
                scores.append(sc)
        if scores:
            avg_score = sum(scores) / len(scores)

    # Low avg match
    if avg_score is not None and avg_score < 45:
        issues.append({
            "severity": "high",
            "issue": f"Low average match score ({avg_score:.0f}/100).",
            "detail": "Most job descriptions require skills not clearly shown on your resume.",
            "recommendation": "Focus on jobs scoring ≥60. Use Resume Targeting to strengthen weak areas.",
        })

    # Many saved, zero applied
    if not_started > 3 and applied == 0:
        issues.append({
            "severity": "high",
            "issue": f"{not_started} jobs saved but no applications submitted.",
            "detail": "Saving without applying doesn't advance your search.",
            "recommendation": "Pick 2–3 Priority Jobs this week and submit applications.",
        })

    # No follow-ups
    needs_followup = 0
    for job in jobs:
        if "applied" in (job.get("status") or "").lower():
            d = _parse_date(job.get("date_applied") or "")
            if d and (today - d).days >= 7 and not (job.get("response_date") or "").strip():
                needs_followup += 1
    if needs_followup:
        issues.append({
            "severity": "medium",
            "issue": f"{needs_followup} application(s) over 7 days old with no logged response.",
            "detail": "A polite follow-up can meaningfully increase response rates.",
            "recommendation": "Go to Networking & Follow-up for ready-to-use follow-up drafts.",
        })

    # No company context anywhere
    no_context = sum(1 for j in jobs if not (j.get("company_context") or "").strip())
    if no_context == total:
        issues.append({
            "severity": "medium",
            "issue": "No company context added to any job.",
            "detail": "Generated cover letters will be generic without company-specific details.",
            "recommendation": "For your top 3–5 jobs, paste the company description into Company Context.",
        })

    # No networking contacts
    no_contact = sum(1 for j in jobs if not (j.get("contact_name") or "").strip())
    if no_contact == total and applied > 0:
        issues.append({
            "severity": "medium",
            "issue": "No networking contacts recorded.",
            "detail": "Applications with a referral or internal contact have higher interview rates.",
            "recommendation": "For your top 5 companies, find a contact on LinkedIn and send a networking message.",
        })

    # High rejection rate
    if applied >= 3 and rejected / max(applied, 1) > 0.6:
        issues.append({
            "severity": "high",
            "issue": f"High rejection rate ({rejected}/{applied} applications rejected).",
            "detail": "Suggests resume-job mismatch or weak materials.",
            "recommendation": "Run Analyze Match on rejected jobs. Use Resume Targeting to fix weak points.",
        })

    # Many apps, zero interviews
    if applied >= 5 and interview == 0:
        issues.append({
            "severity": "high",
            "issue": f"{applied} applications submitted but no interviews yet.",
            "detail": "Often indicates a resume targeting or personalization issue.",
            "recommendation": (
                "1. Check match scores for submitted jobs. "
                "2. Use Resume Targeting to strengthen bullets. "
                "3. Network with someone at each company."
            ),
        })

    if not issues:
        issues.append({
            "severity": "ok",
            "issue": "No major issues detected.",
            "detail": f"{total} tracked · {applied} applied · {interview} interviews.",
            "recommendation": "Keep applying, follow up, and keep your resume updated.",
        })

    return issues
