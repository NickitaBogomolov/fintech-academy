from datetime import UTC, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from dfa_studio.api import create_app, get_studio
from dfa_studio.service import Studio
from dfa_studio.settings import Settings

TEXT = (
    "Хотим привлечь до 300 млн рублей на полгода, номинал 1000 ₽, купон 18% годовых ежемесячно, только квалы"
)
ANSWERS = {
    "min_amount": "100000000",
    "issue_date": "2026-12-15",
    "rounding_mode": "half_up",
    "business_day_rule": "following",
    "early_redemption": False,
}


@pytest.fixture
def client(tmp_path) -> TestClient:
    studio = Studio(Settings(data_dir=tmp_path, slither_enabled=False))
    app = create_app()
    app.dependency_overrides[get_studio] = lambda: studio
    return TestClient(app)


def _complete_draft(client: TestClient) -> dict:
    draft = client.post("/api/drafts", json={"text": TEXT, "inn": "0000000001"}).json()
    answered = client.post("/api/drafts", json={"text": TEXT, "inn": "0000000001", "answers": ANSWERS}).json()
    assert len(draft["questions"]) == 5
    assert answered["questions"] == []
    return answered


def test_meta_lists_fields_and_examples(client) -> None:
    meta = client.get("/api/meta").json()
    assert len(meta["fields"]) == 15
    assert len(meta["examples"]) == 3
    assert meta["provider"] == "Правила, без внешних вызовов"


def test_full_issue_flow(client) -> None:
    draft = _complete_draft(client)
    started = (datetime.now(UTC) - timedelta(seconds=90)).isoformat()
    response = client.post(
        "/api/issues",
        json={"text": TEXT, "values": draft["values"], "started_at": started, "questions_asked": 5},
    )
    assert response.status_code == 200, response.text
    package = response.json()
    assert package["spec"]["issue_number"] == "SVR-001-2026"
    assert package["summary"]["failed"] == 0
    assert package["totals"]["coupon"] == "89.76"
    assert package["metrics"]["from_text"] == 6
    assert package["metrics"]["preparation_seconds"] >= 90

    docx = client.get(f"/api/issues/{package['id']}/files/decision.docx")
    assert docx.status_code == 200
    assert docx.content[:2] == b"PK"

    fault = client.post(f"/api/issues/{package['id']}/faults", json={"fault": "rounding_down"}).json()
    assert fault["caught"] is True
    assert any("1528" in line or "1_528" in line for line in fault["diff"])

    metrics = client.get("/api/metrics").json()
    assert metrics["issues"] == 1
    assert metrics["faults_caught"] == 1

    second = client.post("/api/issues", json={"text": TEXT, "values": draft["values"]}).json()
    assert second["spec"]["issue_number"] == "SVR-002-2026"


def test_invalid_values_return_field_errors(client) -> None:
    draft = _complete_draft(client)
    draft["values"]["min_amount"]["value"] = "900000000"
    response = client.post("/api/issues", json={"text": TEXT, "values": draft["values"]})
    assert response.status_code == 422
    assert "min_amount" in response.json()["fields"]


def test_template_upload_and_preview(client) -> None:
    source = (
        "{#- title: Краткая форма -#}\n# Выпуск {{ spec.issue_number }}\nНоминал {{ spec.nominal | money }} ₽"
    )
    preview = client.post("/api/templates/preview", json={"source": source}).json()
    assert "Номинал 1 000,00 ₽" in preview["document"]
    saved = client.post("/api/templates", json={"id": "short", "source": source})
    assert saved.status_code == 200
    rejected = client.post("/api/templates", json={"id": "bad", "source": "{{ client.name }}"})
    assert rejected.status_code == 422


def test_benchmark_reports_quality(client) -> None:
    result = client.post("/api/benchmark").json()
    assert result["cases"] == 20
    assert result["precision"] == 1.0
    assert result["recall"] > 0.9
