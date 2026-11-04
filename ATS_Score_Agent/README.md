# ATS Score Agent

Local tool that scores a resume against a job description the way a simple ATS keyword parser would, then recommends concrete edits aimed at **90%+**.

It does not send your documents to an external model. Matching is deterministic: required vs preferred skills, title alignment, standard section headings, quantified bullets, and parseability warnings.

## Run

```powershell
cd C:\Users\fvicz\ATS_Score_Agent
uv sync --group dev
uv run ats-score-agent
```

Open [http://127.0.0.1:8765](http://127.0.0.1:8765). Paste a resume and a job description (or upload `.txt`, `.md`, `.pdf`, `.docx`) and click **Score resume**.

Score two files from the CLI:

```powershell
uv run ats-score-agent tests\fixtures\resume_weak.txt tests\fixtures\job.txt
uv run ats-score-agent tests\fixtures\resume_strong.txt tests\fixtures\job.txt
```

## Verify

```powershell
uv run pytest
```

The weak fixture should score well below 90% and list missing required skills. The strong fixture should reach 90%+. Adding a Skills block with the posting’s required terms to the weak resume should raise the score.
