"""Job storage: CSV I/O, field extraction, duplicate detection, CSV migration."""

import csv
import os
import re

# ── Field definitions ─────────────────────────────────────────────────────────

# All 25 fields stored in the CSV.
FIELDS = [
    # ── Core (original V1-V4) ─────────────────────────────────────────────
    "company",
    "role",
    "location",
    "application_link",
    "deadline",
    "required_skills",
    "status",
    "notes",
    "job_description",
    # ── Company context (V11 Part A) ──────────────────────────────────────
    "company_context",
    # ── Prioritization (V11 Part D) ───────────────────────────────────────
    "interest_level",        # Low / Medium / High
    "role_category",         # SWE / Data / Finance / etc.
    "sponsorship_info",      # free text
    "application_deadline",  # ISO date; separate from legacy 'deadline'
    # ── Pipeline timeline (V11 Part F) ───────────────────────────────────
    "date_added",            # ISO date, auto-set on save
    "date_applied",          # ISO date
    "response_date",         # ISO date
    "source",                # LinkedIn / Handshake / Company Website / etc.
    # ── Networking (V11 Part G) ───────────────────────────────────────────
    "follow_up_date",
    "contact_name",
    "contact_email_or_linkedin",
    "last_contacted_date",
    "networking_status",     # Not Started / Contact Found / Message Sent / ...
]

# The original 9 fields — used by the CLI so it doesn't prompt for 25 fields.
CORE_FIELDS = [
    "company", "role", "location", "application_link", "deadline",
    "required_skills", "status", "notes", "job_description",
]

# Label patterns for import-from-text extraction (line-anchored, case-insensitive).
LABEL_PATTERNS = {
    "company": [
        r"^company\s*[-:]\s*(.+)$",
        r"^(?:employer|organization|firm)\s*[-:]\s*(.+)$",
    ],
    "role": [
        r"^(?:role|position|title|job\s*title|opening|job)\s*[-:]\s*(.+)$",
    ],
    "location": [
        r"^location\s*[-:]\s*(.+)$",
        r"^(?:city|office|site|work\s*location)\s*[-:]\s*(.+)$",
    ],
    "deadline": [
        r"^(?:deadline|apply\s*by|due|application\s*deadline|closes?|closing\s*date|end\s*date)\s*[-:]\s*(.+)$",
    ],
    "required_skills": [
        r"^(?:required\s*skills?|skills?\s*required|skills?|requirements?|qualifications?|must\s*have|minimum\s*qualifications?)\s*[-:]\s*(.+)$",
    ],
}

SPONSORSHIP_KEYWORDS = [
    "sponsor", "work authorization", "work authoriz",
    "visa", "opt", "cpt", "h-1b", "h1b",
    "authorized to work", "eligible to work",
    "must be authorized", "cannot sponsor", "will not sponsor",
    "lawfully authorized", "us citizen", "permanent resident",
]


# ── CSV helpers ───────────────────────────────────────────────────────────────

def ensure_csv(path):
    """Create the CSV with full headers if it does not exist."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    if not os.path.exists(path):
        with open(path, "w", newline="") as f:
            csv.writer(f).writerow(FIELDS)


def migrate_csv(path):
    """Add any columns missing from an existing CSV while preserving all data.

    Safe to call at startup — no-ops if the file is already up to date.
    """
    if not os.path.exists(path):
        return
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        existing_fields = reader.fieldnames or []
        rows = list(reader)

    missing = [f for f in FIELDS if f not in existing_fields]
    if not missing:
        return  # already current

    migrated = []
    for row in rows:
        new_row = {f: "" for f in FIELDS}
        for f in existing_fields:
            if f in FIELDS:
                new_row[f] = row.get(f, "") or ""
        migrated.append(new_row)

    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(migrated)


def read_jobs(path):
    ensure_csv(path)
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    return [{field: row.get(field, "") or "" for field in FIELDS} for row in rows]


def write_jobs(jobs, path):
    ensure_csv(path)
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(jobs)


def is_blank_job(job):
    return not any((job.get(f) or "").strip() for f in FIELDS)


# ── Duplicate detection ───────────────────────────────────────────────────────

def find_duplicate(job, existing_jobs):
    """Return the index of an existing job that looks like a duplicate, or None."""
    company = (job.get("company") or "").strip().lower()
    role    = (job.get("role") or "").strip().lower()
    link    = (job.get("application_link") or "").strip()

    for i, existing in enumerate(existing_jobs):
        ec = (existing.get("company") or "").strip().lower()
        er = (existing.get("role") or "").strip().lower()
        el = (existing.get("application_link") or "").strip()

        if company and role and ec == company and er == role:
            return i
        if link and el and el == link:
            return i
    return None


# ── Extraction helpers ────────────────────────────────────────────────────────

def extract_first_match(text, patterns):
    for line in text.splitlines():
        line = line.strip()
        for pat in patterns:
            m = re.match(pat, line, re.IGNORECASE)
            if m:
                return m.group(1).strip()
    return ""


def detect_skills_in_text(raw):
    """Return comma-separated skills found in raw text via the matcher's SKILLS list."""
    try:
        from internship_assistant.matcher import SKILLS, normalize, has_skill
        norm = normalize(raw)
        found = [s for s in SKILLS if has_skill(s, norm)]
        return ", ".join(found) if found else ""
    except Exception:
        return ""


def detect_sponsorship_note(raw):
    """Return a warning note if sponsorship/work-auth keywords appear."""
    raw_lower = raw.lower()
    for kw in SPONSORSHIP_KEYWORDS:
        if kw in raw_lower:
            return (
                "⚠️ Sponsorship/work authorization info detected — "
                "check the posting for details."
            )
    return ""


def extract_job_from_text(raw):
    """Extract structured job fields from a free-form job posting string."""
    job = {field: "" for field in FIELDS}

    for field, patterns in LABEL_PATTERNS.items():
        job[field] = extract_first_match(raw, patterns)

    url_match = re.search(r"https?://\S+", raw)
    if url_match:
        job["application_link"] = url_match.group(0).rstrip(".,;)")

    if not job["required_skills"]:
        job["required_skills"] = detect_skills_in_text(raw)

    sponsorship_note = detect_sponsorship_note(raw)
    if sponsorship_note and not job["notes"]:
        job["notes"] = sponsorship_note

    job["job_description"] = raw
    job["status"] = job["status"] or "Saved"

    return job
