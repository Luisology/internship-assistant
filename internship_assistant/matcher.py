"""Resume <-> job description matching using a curated keyword list.

The approach is intentionally simple and explainable: normalize both texts,
then check which entries from SKILLS appear in each. Add or remove items
from SKILLS to tune the matcher for your field.
"""

import re

SKILLS = [
    # Programming languages
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "rust",
    "ruby", "swift", "kotlin", "php", "scala", "r", "matlab", "html", "css",
    # Web / frameworks
    "react", "angular", "vue", "node.js", "express", "django", "flask",
    "fastapi", "spring", "rails", "next.js",
    # Data / databases / ML
    "sql", "mysql", "postgresql", "mongodb", "redis", "nosql", "pandas",
    "numpy", "tensorflow", "pytorch", "scikit-learn", "spark", "hadoop",
    "tableau", "power bi", "machine learning", "deep learning", "nlp",
    "computer vision", "data structures", "algorithms",
    # Cloud / devops / tools
    "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins",
    "linux", "bash", "git", "github", "jira", "agile", "scrum",
    "rest", "graphql", "api", "microservices", "oop",
    # Finance / accounting
    "excel", "financial modeling", "pivot table", "vlookup", "valuation",
    "dcf", "comparable companies", "precedent transactions",
    "equity research", "accounting", "financial statements", "gaap", "ifrs",
    "audit", "tax", "bloomberg", "capital markets", "m&a",
    "portfolio management", "investment banking", "corporate finance",
    "risk assessment",
]


def normalize(text):
    """Lowercase; treat punctuation as spaces but keep + # . inside tokens
    (so c++, c#, node.js stay intact). Pads with spaces so a substring
    lookup acts like a whole-token match.
    """
    lower = text.lower()
    # Keep dots only between alphanumerics (e.g. "node.js"); drop sentence dots.
    lower = re.sub(r"(?<![a-z0-9])\.|\.(?![a-z0-9])", " ", lower)
    cleaned = re.sub(r"[^a-z0-9+#.]", " ", lower)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return f" {cleaned} "


def has_skill(skill, normalized_text):
    return f" {skill} " in normalized_text


def compute_match(jd, resume_text):
    """Return (skills_in_jd, matched, missing, score 0-100)."""
    resume_norm = normalize(resume_text)
    jd_norm = normalize(jd)
    skills_in_jd = [s for s in SKILLS if has_skill(s, jd_norm)]
    matched = [s for s in skills_in_jd if has_skill(s, resume_norm)]
    missing = [s for s in skills_in_jd if s not in matched]
    score = round(len(matched) / len(skills_in_jd) * 100) if skills_in_jd else 0
    return skills_in_jd, matched, missing, score
