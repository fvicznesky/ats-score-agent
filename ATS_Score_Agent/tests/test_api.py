from fastapi.testclient import TestClient

from ats_score_agent.app import app

client = TestClient(app)


def test_index_serves_ui():
    response = client.get("/")
    assert response.status_code == 200
    assert "ATS Score Agent" in response.text


def test_score_endpoint():
    response = client.post(
        "/api/score",
        json={
            "resume_text": "Jane Doe\njane@x.com\nSkills\nPython FastAPI\nExperience\n- Built APIs",
            "job_text": "Title: Backend Engineer\nRequired:\n- Python\n- FastAPI",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert "score" in body
    assert body["target"] == 90
    assert "python" in body["matched_keywords"]
