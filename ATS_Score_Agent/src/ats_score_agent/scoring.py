"""Deterministic ATS-style resume vs job-description scoring."""

from __future__ import annotations

import re
from dataclasses import dataclass

from ats_score_agent.keywords import (
    DEGREE_TERMS,
    SECTION_HEADERS,
    SKILL_ALIASES,
    STOPWORDS,
    alias_lookup,
    normalize_text,
)

TARGET_SCORE = 90
ALIAS_TO_CANONICAL = alias_lookup()

_TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9+#.]*(?:[+#])?", re.I)
_YEAR_RE = re.compile(r"(\d+)\s*\+?\s*(?:years|yrs|year)\b", re.I)
_METRIC_RE = re.compile(
    r"(\d[\d,]*\s*%|\$\s*\d[\d,.]*|\b\d[\d,]*\+?\s*(million|billion|k|m)\b|\b\d{1,3}(?:,\d{3})+\b)",
    re.I,
)
_TITLE_HINT_RE = re.compile(
    r"(?:job title|title|position|role)\s*[:\-]\s*(.+)",
    re.I,
)


@dataclass
class KeywordHit:
    term: str
    required: bool
    matched: bool
    evidence: str = ""


@dataclass
class Recommendation:
    priority: str
    title: str
    detail: str
    suggested_text: str
    estimated_gain: int


@dataclass
class ScoreResult:
    score: int
    target: int
    projected_score: int
    breakdown: list[dict]
    matched_keywords: list[str]
    missing_required: list[str]
    missing_preferred: list[str]
    recommendations: list[Recommendation]
    sections_found: list[str]
    warnings: list[str]
    job_title: str
    years_required: int | None


def score_resume(resume_text: str, job_text: str) -> dict:
    result = evaluate(resume_text, job_text)
    return {
        "score": result.score,
        "target": result.target,
        "projected_score": result.projected_score,
        "breakdown": result.breakdown,
        "matched_keywords": result.matched_keywords,
        "missing_required": result.missing_required,
        "missing_preferred": result.missing_preferred,
        "recommendations": [r.__dict__ for r in result.recommendations],
        "sections_found": result.sections_found,
        "warnings": result.warnings,
        "job_title": result.job_title,
        "years_required": result.years_required,
    }


def evaluate(resume_text: str, job_text: str) -> ScoreResult:
    resume = resume_text.strip()
    job = job_text.strip()
    warnings: list[str] = []
    if not resume:
        warnings.append("Resume is empty.")
    if not job:
        warnings.append("Job description is empty.")

    resume_norm = _normalize(resume)
    job_norm = _normalize(job)
    resume_blob = " " + resume_norm + " "
    sections = detect_sections(resume)

    required_terms, preferred_terms = extract_job_terms(job)
    title = extract_job_title(job)
    years_required = extract_years(job)

    required_hits = [_match_term(term, resume_blob, resume_norm, required=True) for term in required_terms]
    preferred_hits = [_match_term(term, resume_blob, resume_norm, required=False) for term in preferred_terms]

    required_cov = _coverage(required_hits)
    preferred_cov = _coverage(preferred_hits) if preferred_hits else 1.0
    title_score = _title_score(title, resume_norm)
    section_score = _section_score(sections)
    quantification = _quantification_score(resume)
    parseability, parse_warnings = _parseability_score(resume)
    warnings.extend(parse_warnings)

    weights = {
        "Required keywords": (0.50, required_cov),
        "Preferred keywords": (0.15, preferred_cov),
        "Title alignment": (0.10, title_score),
        "Resume sections": (0.10, section_score),
        "Quantified impact": (0.08, quantification),
        "ATS parseability": (0.07, parseability),
    }
    raw = sum(weight * value for weight, value in weights.values())
    score = int(round(100 * raw))

    breakdown = [
        {
            "label": label,
            "weight": int(weight * 100),
            "score": int(round(value * 100)),
            "weighted": round(weight * value * 100, 1),
        }
        for label, (weight, value) in weights.items()
    ]

    matched = sorted({h.term for h in required_hits + preferred_hits if h.matched})
    missing_required = [h.term for h in required_hits if not h.matched]
    missing_preferred = [h.term for h in preferred_hits if not h.matched]

    recs = build_recommendations(
        missing_required=missing_required,
        missing_preferred=missing_preferred,
        title=title,
        title_score=title_score,
        sections=sections,
        quantification=quantification,
        years_required=years_required,
        resume=resume,
        warnings=warnings,
    )
    projected = min(99, score + sum(r.estimated_gain for r in recs))
    if score >= TARGET_SCORE:
        recs.insert(
            0,
            Recommendation(
                priority="keep",
                title="You are already at the 90%+ target",
                detail="Tune wording if you want, but keyword coverage is already in a strong ATS range.",
                suggested_text="",
                estimated_gain=0,
            ),
        )
        projected = max(projected, score)

    return ScoreResult(
        score=score,
        target=TARGET_SCORE,
        projected_score=projected,
        breakdown=breakdown,
        matched_keywords=matched,
        missing_required=missing_required,
        missing_preferred=missing_preferred,
        recommendations=recs,
        sections_found=sorted(sections),
        warnings=warnings,
        job_title=title,
        years_required=years_required,
    )


def extract_job_terms(job_text: str) -> tuple[list[str], list[str]]:
    """Return (required, preferred) canonical keywords found in the JD."""
    lines = [ln.strip() for ln in job_text.splitlines() if ln.strip()]
    required: set[str] = set()
    preferred: set[str] = set()
    preferred_mode = False

    for line in lines:
        lower = line.lower()
        if any(k in lower for k in ("nice to have", "preferred", "bonus", "plus:")):
            preferred_mode = True
        if any(k in lower for k in ("required", "must have", "minimum qualifications", "what you will need")):
            preferred_mode = False
        found = _terms_in_text(line)
        if not found:
            continue
        if preferred_mode or "preferred" in lower or "nice to have" in lower:
            preferred.update(found)
        else:
            required.update(found)

    # Anything labeled preferred should not also count as required.
    required -= preferred
    if not required and not preferred:
        required = _terms_in_text(job_text)
    return sorted(required), sorted(preferred)


def extract_job_title(job_text: str) -> str:
    for line in job_text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        hinted = _TITLE_HINT_RE.match(stripped)
        if hinted:
            return _clean_title(hinted.group(1))
        if len(stripped) <= 80 and not stripped.endswith("."):
            return _clean_title(stripped)
    return ""


def extract_years(text: str) -> int | None:
    matches = [int(m.group(1)) for m in _YEAR_RE.finditer(text)]
    return max(matches) if matches else None


def detect_sections(resume: str) -> set[str]:
    found: set[str] = set()
    for line in resume.splitlines():
        key = re.sub(r"[^a-z ]+", " ", line.lower()).strip()
        key = re.sub(r"\s+", " ", key)
        for name, headers in SECTION_HEADERS.items():
            if key in headers or any(key.startswith(h) for h in headers):
                found.add(name)
    # Contact is present if we see an email or phone.
    if re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", resume) or re.search(r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b", resume):
        found.add("contact")
    return found


def build_recommendations(
    *,
    missing_required: list[str],
    missing_preferred: list[str],
    title: str,
    title_score: float,
    sections: set[str],
    quantification: float,
    years_required: int | None,
    resume: str,
    warnings: list[str],
) -> list[Recommendation]:
    recs: list[Recommendation] = []

    if missing_required:
        skills_line = ", ".join(missing_required[:12])
        recs.append(
            Recommendation(
                priority="high",
                title="Add missing required keywords",
                detail=(
                    "ATS scanners look for exact skill terms from the job description. "
                    "Put these in a Skills section and repeat the most important ones in experience bullets."
                ),
                suggested_text=f"Skills: {skills_line}",
                estimated_gain=min(28, 4 * len(missing_required[:7])),
            )
        )
        for term in missing_required[:5]:
            recs.append(
                Recommendation(
                    priority="high",
                    title=f"Prove {term} in a work bullet",
                    detail="Keywords in Skills help parsing; keywords in Experience help ranking.",
                    suggested_text=(
                        f"Delivered production {term} work that improved [metric] by [X%], "
                        f"collaborating with [team] under [constraint]."
                    ),
                    estimated_gain=3,
                )
            )

    if title and title_score < 0.8:
        recs.append(
            Recommendation(
                priority="high",
                title="Mirror the target job title in your headline",
                detail="Many ATS systems compare the resume headline/target role to the posting title.",
                suggested_text=f"{title} | [Your current title] | [City or Remote]",
                estimated_gain=6,
            )
        )

    if "skills" not in sections:
        recs.append(
            Recommendation(
                priority="high",
                title="Add a dedicated Skills section",
                detail="A labeled Skills block is one of the most reliable ATS parse targets.",
                suggested_text="Skills\nPython, SQL, AWS, ...",
                estimated_gain=5,
            )
        )
    if "experience" not in sections:
        recs.append(
            Recommendation(
                priority="high",
                title="Label your work history as Experience",
                detail="Use a standard heading such as Experience or Work Experience.",
                suggested_text="Experience",
                estimated_gain=4,
            )
        )
    if "education" not in sections:
        recs.append(
            Recommendation(
                priority="medium",
                title="Add an Education section heading",
                detail="Even a short Education block helps parsers fill the education field.",
                suggested_text="Education\n[Degree], [School], [Year]",
                estimated_gain=3,
            )
        )
    if "contact" not in sections:
        recs.append(
            Recommendation(
                priority="medium",
                title="Put email and phone on the first lines",
                detail="Plain-text contact details parse more reliably than headers, images, or text boxes.",
                suggested_text="[Name]\n[email] | [phone] | [City] | [LinkedIn URL]",
                estimated_gain=3,
            )
        )

    if quantification < 0.6:
        recs.append(
            Recommendation(
                priority="medium",
                title="Quantify at least 4 experience bullets",
                detail="Numbers survive ATS parsing and give recruiters a reason to keep reading after the keyword match.",
                suggested_text="Reduced API p95 latency 35% by introducing Redis caching for the checkout path.",
                estimated_gain=5,
            )
        )

    if years_required and not _YEAR_RE.search(resume):
        recs.append(
            Recommendation(
                priority="medium",
                title=f"State your years of experience (JD asks for {years_required}+)",
                detail="If you meet the bar, say so in the summary so both ATS and humans can see it.",
                suggested_text=(
                    f"Software engineer with {years_required}+ years building [domain] systems in [stack]."
                ),
                estimated_gain=3,
            )
        )

    if missing_preferred:
        recs.append(
            Recommendation(
                priority="low",
                title="Sprinkle preferred keywords you actually have",
                detail="Do not invent skills. If you have used them, name them the same way the posting does.",
                suggested_text="Additional tools: " + ", ".join(missing_preferred[:8]),
                estimated_gain=min(8, 2 * len(missing_preferred[:4])),
            )
        )

    for warning in warnings:
        if "table" in warning.lower() or "column" in warning.lower():
            recs.append(
                Recommendation(
                    priority="medium",
                    title="Replace multi-column or table layouts",
                    detail=warning,
                    suggested_text="Use a single-column .docx or .pdf with standard headings and bullet lists.",
                    estimated_gain=3,
                )
            )

    # De-duplicate by title while keeping order.
    seen: set[str] = set()
    unique: list[Recommendation] = []
    for rec in recs:
        if rec.title in seen:
            continue
        seen.add(rec.title)
        unique.append(rec)
    return unique


def _terms_in_text(text: str) -> set[str]:
    blob = f" {_normalize(text)} "
    found: set[str] = set()
    # Longest aliases first so "react native" wins over "react".
    for alias in sorted(ALIAS_TO_CANONICAL, key=len, reverse=True):
        if f" {alias} " in blob:
            found.add(ALIAS_TO_CANONICAL[alias])
    for canonical, variants in DEGREE_TERMS.items():
        if any(f" {v} " in blob for v in variants):
            found.add(canonical)
    return found


def _match_term(term: str, resume_blob: str, resume_norm: str, required: bool) -> KeywordHit:
    variants = {normalize_text(v) for v in SKILL_ALIASES.get(term, {term})}
    variants.add(normalize_text(term))
    if term in DEGREE_TERMS:
        variants |= {normalize_text(v) for v in DEGREE_TERMS[term]}
    compact_resume = resume_norm.replace(" ", "")
    for variant in sorted(variants, key=len, reverse=True):
        if f" {variant} " in resume_blob:
            return KeywordHit(term=term, required=required, matched=True, evidence=variant)
        compact = variant.replace(" ", "")
        if any(ch in variant for ch in ".+#") and compact and compact in compact_resume:
            return KeywordHit(term=term, required=required, matched=True, evidence=variant)
    return KeywordHit(term=term, required=required, matched=False)


def _coverage(hits: list[KeywordHit]) -> float:
    if not hits:
        return 1.0
    return sum(1 for h in hits if h.matched) / len(hits)


def _title_score(title: str, resume_norm: str) -> float:
    if not title:
        return 1.0
    tokens = [t for t in _tokenize(title) if t not in STOPWORDS]
    if not tokens:
        return 1.0
    hits = sum(1 for t in tokens if f" {t} " in f" {resume_norm} ")
    return hits / len(tokens)


def _section_score(sections: set[str]) -> float:
    expected = ["contact", "skills", "experience", "education"]
    return sum(1 for name in expected if name in sections) / len(expected)


def _quantification_score(resume: str) -> float:
    bullets = [ln for ln in resume.splitlines() if ln.strip().startswith(("-", "*", "•"))]
    if not bullets:
        bullets = [ln for ln in resume.splitlines() if ln.strip()]
    metric_lines = [ln for ln in bullets if _METRIC_RE.search(ln) or re.search(r"\b\d+\b", ln)]
    return min(1.0, len(metric_lines) / 4.0)


def _parseability_score(resume: str) -> tuple[float, list[str]]:
    warnings: list[str] = []
    score = 1.0
    if resume.count("|") >= 8 or resume.count("\t") >= 8:
        score -= 0.35
        warnings.append("This resume looks multi-column or table-based, which many ATS parsers scramble.")
    if re.search(r"\[image\]|text box|smartart", resume, re.I):
        score -= 0.25
        warnings.append("Remove images, text boxes, and SmartArt; ATS tools often skip them.")
    if len(resume) > 80 and not detect_sections(resume):
        score -= 0.2
        warnings.append("No standard section headings were detected.")
    return max(0.0, score), warnings


def _normalize(text: str) -> str:
    return normalize_text(text)


def _tokenize(text: str) -> list[str]:
    return [m.group(0).lower() for m in _TOKEN_RE.finditer(text)]


def _clean_title(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip(" -:|")
