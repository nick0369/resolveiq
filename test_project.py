"""Edge cases, artifact parity and API behavior, not arbitrary accuracy asserts."""

import json, math
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from inference import predict, validate_artifact
from policy import wilson_lower

ROOT = Path(__file__).parent
MODEL = json.loads((ROOT / "model.json").read_text(encoding="utf-8"))
EXAMPLES = json.loads((ROOT / "examples.json").read_text(encoding="utf-8"))


def test_artifact_schema():
    validate_artifact(MODEL)


def test_corrupt_artifact_rejected():
    with pytest.raises(ValueError):
        validate_artifact({})


def test_empty_wilson():
    assert wilson_lower(0, 0) == 0


def test_wilson_not_point_estimate():
    assert 0.9 < wilson_lower(100, 100) < 1


@pytest.mark.parametrize("case", EXAMPLES)
def test_exported_inference_parity(case):
    assert predict(case["input"], MODEL)["confidence"] == pytest.approx(
        case["expected_confidence"], abs=1e-5
    )


def test_api_contract(tmp_path, monkeypatch):
    import api

    monkeypatch.setattr(api, "DB", tmp_path / "audit.db")
    with TestClient(api.app) as client:
        assert client.get("/ready").status_code == 200
        r = client.post("/predict", json=EXAMPLES[0]["input"])
        assert r.status_code == 200 and r.json()["model_version"] == MODEL["version"]
        assert r.json()["confidence"] == pytest.approx(
            EXAMPLES[0]["expected_confidence"], abs=1e-5
        )
        assert client.post("/predict", json={}).status_code == 422
        assert (
            client.post(
                "/predict", json={**EXAMPLES[0]["input"], "unexpected": 1}
            ).status_code
            == 422
        )
        assert client.get("/assets/not-allowed").status_code == 404
    assert (tmp_path / "audit.db").exists()


def test_empty_or_inconsistent_input():
    bad = (
        {"text": " " * 40}
        if MODEL["task"] == "text"
        else {**EXAMPLES[0]["input"], "limit_bal": 0}
    )
    with pytest.raises(ValueError):
        predict(bad, MODEL)


def test_monitor_without_db(tmp_path):
    from monitor import summarize

    assert summarize(tmp_path / "missing.db")["requests"] == 0


def test_chronology_and_duplicate_control():
    import pandas as pd

    splits = pd.read_csv(ROOT / "split_manifest.csv")
    assert splits.text_hash.is_unique
    assert (
        splits.loc[splits.split == "train", "date"].max()
        < splits.loc[splits.split == "selection", "date"].min()
    )
    assert (
        splits.loc[splits.split == "selection", "date"].max()
        < splits.loc[splits.split == "policy", "date"].min()
    )
    assert (
        splits.loc[splits.split == "policy", "date"].max()
        < splits.loc[splits.split == "test", "date"].min()
    )


def test_unseen_vocabulary_requires_review():
    assert predict({"text": "qzxvwx qzxvwx qzxvwx qzxvwx"}, MODEL)["needs_review"]


def test_negation_preserved():
    from features import normalize

    assert "not" in normalize("I did NOT make this payment.").split()


def test_sql_calendar_spine():
    import sqlite3

    with sqlite3.connect(":memory:") as db:
        db.executescript((ROOT / "schema.sql").read_text())
        db.executemany(
            "INSERT INTO calendar VALUES (?)", [("2026-01-01",), ("2026-01-02",)]
        )
        db.execute(
            "INSERT INTO routing_events VALUES ('a','2026-01-01','v1',0,'Mortgage','Mortgage',5)"
        )
        rows = db.execute(
            "SELECT volume,accepted_precision FROM routing_daily ORDER BY day"
        ).fetchall()
        assert rows == [(1, 1.0), (0, None)]
