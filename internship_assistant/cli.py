"""Interactive CLI for the Internship Assistant.

Run with:  python3 -m internship_assistant.cli
"""

import os

from . import tracker, matcher, materials

DATA_DIR = "data"
CSV_PATH = os.path.join(DATA_DIR, "internship_tracker.csv")
RESUME_PATH = os.path.join(DATA_DIR, "resume.txt")
GENERATED_DIR = "generated_materials"

RESUME_HINT = (
    f"Resume not found at {RESUME_PATH}.\n"
    f"Copy the sample resume into place and edit it with your own info:\n"
    f"  cp examples/sample_resume.txt {RESUME_PATH}"
)


def read_multiline(prompt):
    print(prompt)
    print("  (paste below; type END on its own line to finish)")
    lines = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip() == "END":
            break
        lines.append(line)
    return "\n".join(lines)


def pick_job_index(jobs, action_label):
    raw = input(f"\nEnter job number to {action_label}: ").strip()
    try:
        idx = int(raw) - 1
    except ValueError:
        print("Not a valid number.")
        return None
    if not 0 <= idx < len(jobs):
        print("Number out of range.")
        return None
    return idx


def list_jobs():
    jobs = tracker.read_jobs(CSV_PATH)
    if not jobs:
        print("\nNo jobs saved yet.")
        return jobs
    print(f"\n{len(jobs)} job(s) saved:")
    for i, job in enumerate(jobs, 1):
        print(f"\n[{i}] {job['company']} — {job['role']}")
        for field in tracker.FIELDS:
            if field in ("company", "role"):
                continue
            value = job.get(field, "")
            if field == "job_description":
                value = value.replace("\n", " ")
                if len(value) > 80:
                    value = value[:77] + "..."
            print(f"     {field}: {value}")
    return jobs


def add_job():
    print("\nAdd a new job (press Enter to leave a field blank):")
    job = {f: "" for f in tracker.FIELDS}  # initialize all fields
    for field in tracker.CORE_FIELDS:      # only prompt for core fields
        if field == "job_description":
            job[field] = read_multiline(f"  {field}:")
        else:
            job[field] = input(f"  {field}: ").strip()
    if tracker.is_blank_job(job):
        print("All fields are blank — nothing saved.")
        return
    if not (job["company"] or job["role"]):
        confirm = input("Both company and role are blank. Save anyway? (y/N): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
    jobs = tracker.read_jobs(CSV_PATH)
    jobs.append(job)
    tracker.write_jobs(jobs, CSV_PATH)
    print("Job added.")


def import_job_from_text():
    raw = read_multiline("\nImport job from text:")
    if not raw.strip():
        print("Nothing pasted; cancelled.")
        return
    job = tracker.extract_job_from_text(raw)
    print("\nExtracted fields (blank = not found; edit later via 'Edit a job'):")
    for field in tracker.FIELDS:
        value = job[field]
        if field == "job_description":
            preview = value.replace("\n", " ")
            preview = preview[:60] + ("..." if len(preview) > 60 else "")
            print(f"  {field}: [{len(value)} chars] {preview}")
        else:
            print(f"  {field}: {value or '(blank)'}")
    if not (job["company"] or job["role"]):
        confirm = input("\nNeither company nor role was found. Save anyway? (y/N): ").strip().lower()
        if confirm != "y":
            print("Cancelled.")
            return
    jobs = tracker.read_jobs(CSV_PATH)
    jobs.append(job)
    tracker.write_jobs(jobs, CSV_PATH)
    print("\nJob imported.")


def edit_job():
    jobs = tracker.read_jobs(CSV_PATH)
    if not jobs:
        print("\nNo jobs to edit.")
        return
    list_jobs()
    idx = pick_job_index(jobs, "edit")
    if idx is None:
        return
    job = jobs[idx]
    print(f"\nEditing: {job.get('company', '')} — {job.get('role', '')}")
    print("Choose a field to edit:")
    for i, field in enumerate(tracker.FIELDS, 1):
        current = job.get(field, "") or ""
        if field == "job_description":
            preview = current.replace("\n", " ")
            preview = preview[:50] + ("..." if len(preview) > 50 else "")
            print(f"  {i}. {field} [{len(current)} chars]: {preview}")
        else:
            print(f"  {i}. {field}: {current or '(blank)'}")
    raw = input("Field number (or Enter to cancel): ").strip()
    if not raw:
        print("Cancelled.")
        return
    try:
        fidx = int(raw) - 1
    except ValueError:
        print("Not a number.")
        return
    if not 0 <= fidx < len(tracker.FIELDS):
        print("Out of range.")
        return
    field = tracker.FIELDS[fidx]
    if field == "job_description":
        new_value = read_multiline(f"New value for {field}:")
    else:
        new_value = input(f"New value for {field}: ").strip()
    job[field] = new_value
    tracker.write_jobs(jobs, CSV_PATH)
    print(f"Updated {field}.")


def update_status():
    jobs = tracker.read_jobs(CSV_PATH)
    if not jobs:
        print("\nNo jobs to update.")
        return
    list_jobs()
    idx = pick_job_index(jobs, "update")
    if idx is None:
        return
    new_status = input(f"New status (current: {jobs[idx]['status']}): ").strip()
    jobs[idx]["status"] = new_status
    tracker.write_jobs(jobs, CSV_PATH)
    print("Status updated.")


def delete_job():
    jobs = tracker.read_jobs(CSV_PATH)
    if not jobs:
        print("\nNo jobs to delete.")
        return
    list_jobs()
    idx = pick_job_index(jobs, "delete")
    if idx is None:
        return
    confirm = input(f"Delete '{jobs[idx]['company']} — {jobs[idx]['role']}'? (y/N): ").strip().lower()
    if confirm != "y":
        print("Cancelled.")
        return
    removed = jobs.pop(idx)
    tracker.write_jobs(jobs, CSV_PATH)
    print(f"Deleted: {removed['company']} — {removed['role']}")


def analyze_job_match():
    if not os.path.exists(RESUME_PATH):
        print(f"\n{RESUME_HINT}")
        return
    jobs = tracker.read_jobs(CSV_PATH)
    if not jobs:
        print("\nNo jobs to analyze.")
        return
    list_jobs()
    idx = pick_job_index(jobs, "analyze")
    if idx is None:
        return
    jd = jobs[idx].get("job_description", "")
    if not jd.strip():
        print("\nThis job has no job description stored. Re-add it with a description to analyze.")
        return
    with open(RESUME_PATH) as f:
        resume = f.read()
    skills_in_jd, matched, missing, score = matcher.compute_match(jd, resume)
    if not skills_in_jd:
        print("\nNo recognized skills found in the job description.")
        print("(The matcher uses a built-in keyword list. Add more entries to SKILLS in matcher.py if needed.)")
        return
    print(f"\n=== Match for {jobs[idx]['company']} — {jobs[idx]['role']} ===")
    print(f"Score: {score}/100  ({len(matched)} of {len(skills_in_jd)} JD skills found in resume)")
    print(f"Matched skills: {', '.join(matched) if matched else '(none)'}")
    print(f"Missing skills: {', '.join(missing) if missing else '(none)'}")


def generate_application_materials():
    jobs = tracker.read_jobs(CSV_PATH)
    if not jobs:
        print("\nNo jobs to generate materials for.")
        return
    list_jobs()
    idx = pick_job_index(jobs, "generate materials for")
    if idx is None:
        return
    job = jobs[idx]
    jd = job.get("job_description", "")
    matched, missing = [], []
    if os.path.exists(RESUME_PATH) and jd.strip():
        with open(RESUME_PATH) as f:
            resume_text = f.read()
        _, matched, missing, _ = matcher.compute_match(jd, resume_text)
    elif not os.path.exists(RESUME_PATH):
        print(f"\n{RESUME_HINT}")
        print("(Generating with generic personalization for now.)")
    elif not jd.strip():
        print("(This job has no stored description — skill-based personalization will be generic.)")
    name = materials.get_applicant_name(RESUME_PATH)
    resume_text_content = ""
    if os.path.exists(RESUME_PATH):
        with open(RESUME_PATH) as f:
            resume_text_content = f.read()
    written = materials.generate_files(job, matched, missing, name, GENERATED_DIR, resume_text_content)
    for path in written:
        print(f"  wrote {path}")
    print(f"\nGenerated {len(written)} file(s) in {GENERATED_DIR}/")


def main():
    tracker.ensure_csv(CSV_PATH)
    menu = [
        ("Add a job", add_job),
        ("Import job from text", import_job_from_text),
        ("List all jobs", list_jobs),
        ("Edit a job", edit_job),
        ("Update job status", update_status),
        ("Delete a job", delete_job),
        ("Analyze job match", analyze_job_match),
        ("Generate application materials", generate_application_materials),
        ("Exit", None),
    ]
    while True:
        print("\n=== Internship Assistant ===")
        for i, (label, _) in enumerate(menu, 1):
            print(f"  {i}. {label}")
        choice = input("Choose an option: ").strip()
        if choice == str(len(menu)):
            print("Bye.")
            break
        try:
            menu[int(choice) - 1][1]()
        except (ValueError, IndexError):
            print("Invalid choice.")


if __name__ == "__main__":
    main()
