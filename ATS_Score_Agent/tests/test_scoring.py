from pathlib import Path

from ats_score_agent.scoring import score_resume

FIXTURES = Path(__file__).parent / "fixtures"


def _load(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8")


def test_weak_resume_is_below_target():
    result = score_resume(_load("resume_weak.txt"), _load("job.txt"))
    assert result["score"] < 70
    assert "python" in result["missing_required"]
    assert result["recommendations"]
    assert any("keyword" in r["title"].lower() for r in result["recommendations"])


def test_strong_resume_reaches_target():
    result = score_resume(_load("resume_strong.txt"), _load("job.txt"))
    assert result["score"] >= 90
    assert not result["missing_required"]
    assert "python" in result["matched_keywords"]


def test_adding_required_keywords_raises_score():
    job = _load("job.txt")
    weak = score_resume(_load("resume_weak.txt"), job)["score"]
    improved_resume = _load("resume_weak.txt") + """

Skills
Python, FastAPI, PostgreSQL, AWS, Docker, Kubernetes, REST, CI/CD
"""
    improved = score_resume(improved_resume, job)["score"]
    assert improved > weak
