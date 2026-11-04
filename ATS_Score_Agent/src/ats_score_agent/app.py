"""Local web app and CLI for ATS resume scoring."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from ats_score_agent.extract import ExtractError, extract_text
from ats_score_agent.scoring import score_resume

STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="ATS Score Agent", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


class ScoreRequest(BaseModel):
    resume_text: str = Field(default="", max_length=200_000)
    job_text: str = Field(default="", max_length=200_000)


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/score")
async def api_score(payload: ScoreRequest) -> dict:
    if not payload.resume_text.strip() or not payload.job_text.strip():
        raise HTTPException(status_code=400, detail="Both resume and job description text are required.")
    return score_resume(payload.resume_text, payload.job_text)


@app.post("/api/score-files")
async def api_score_files(
    resume_text: str = Form(default=""),
    job_text: str = Form(default=""),
    resume_file: UploadFile | None = File(default=None),
    job_file: UploadFile | None = File(default=None),
) -> dict:
    resume = resume_text
    job = job_text
    try:
        if resume_file and resume_file.filename:
            resume = extract_text(resume_file.filename, await resume_file.read())
        if job_file and job_file.filename:
            job = extract_text(job_file.filename, await job_file.read())
    except ExtractError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not resume.strip() or not job.strip():
        raise HTTPException(
            status_code=400,
            detail="Provide resume and job description as pasted text or as .txt/.md/.pdf/.docx files.",
        )
    return score_resume(resume, job)


def main() -> None:
    parser = argparse.ArgumentParser(description="Score a resume against a job description.")
    parser.add_argument("resume", nargs="?", help="Path to resume file (.txt, .md, .pdf, .docx)")
    parser.add_argument("job", nargs="?", help="Path to job description file")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--json", action="store_true", help="Print JSON when scoring files")
    args = parser.parse_args()

    if args.resume and args.job:
        resume = Path(args.resume)
        job = Path(args.job)
        result = score_resume(
            extract_text(resume.name, resume.read_bytes()),
            extract_text(job.name, job.read_bytes()),
        )
        if args.json:
            print(json.dumps(result, indent=2))
            return
        _print_cli(result)
        return

    import uvicorn

    print(f"ATS Score Agent running at http://{args.host}:{args.port}")
    uvicorn.run("ats_score_agent.app:app", host=args.host, port=args.port, reload=False)


def _print_cli(result: dict) -> None:
    print(f"ATS score: {result['score']}%  (target {result['target']}%)")
    print(f"Projected after recommended edits: {result['projected_score']}%")
    if result["missing_required"]:
        print("Missing required:", ", ".join(result["missing_required"]))
    print("\nTop recommendations:")
    for rec in result["recommendations"][:8]:
        print(f"- [{rec['priority']}] {rec['title']}")
        if rec["suggested_text"]:
            print(f"    {rec['suggested_text']}")
