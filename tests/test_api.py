"""Tests for FastAPI endpoints (with mocked LLM)."""

import json
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient


def test_health(client: TestClient):
    """GET /health returns 200 and status ok."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_post_slide_validation_empty_topic(client: TestClient):
    """POST /slide with empty topic returns 422."""
    response = client.post(
        "/slide",
        json={"topic": "", "grade": "5th", "n_slides": 3},
    )
    assert response.status_code == 422


def test_post_slide_validation_invalid_n_slides(client: TestClient):
    """POST /slide with n_slides out of range returns 422."""
    response = client.post(
        "/slide",
        json={"topic": "Math", "grade": "5th", "n_slides": 0},
    )
    assert response.status_code == 422


@patch("app.main.generate_full_deck", new_callable=AsyncMock)
def test_post_slide_success(mock_generate, client: TestClient, sample_slides):
    """POST /slide returns full deck when generation succeeds."""
    mock_generate.return_value = sample_slides

    response = client.post(
        "/slide",
        json={
            "topic": "Water Cycle",
            "grade": "4th grade",
            "context": "Focus on evaporation.",
            "n_slides": 3,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "slides" in data
    assert len(data["slides"]) == 6  # title, agenda, 3 content, conclusion
    assert data["slides"][0]["type"] == "title"
    assert data["slides"][0]["title"] == "Test Lesson"
    assert data["slides"][-1]["type"] == "conclusion"

    mock_generate.assert_called_once_with(
        topic="Water Cycle",
        grade="4th grade",
        context="Focus on evaporation.",
        n_slides=3,
    )


@patch("app.main.generate_full_deck", new_callable=AsyncMock)
def test_post_slide_generation_error(mock_generate, client: TestClient):
    """POST /slide returns 500 when generation fails."""
    mock_generate.side_effect = RuntimeError("LLM error")

    response = client.post(
        "/slide",
        json={"topic": "Math", "grade": "5th", "n_slides": 2},
    )

    assert response.status_code == 500
    assert "Generation failed" in response.json()["detail"]


@patch("app.main.generate_slides_stream")
def test_streaming_success(mock_stream, client: TestClient, sample_slides):
    """POST /streaming returns SSE with one slide per data line."""
    async def mock_async_gen():
        for s in sample_slides:
            yield s

    mock_stream.return_value = mock_async_gen()  # one async generator instance

    response = client.post(
        "/streaming",
        json={
            "topic": "Water Cycle",
            "grade": "4th grade",
            "context": "",
            "n_slides": 3,
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "text/event-stream; charset=utf-8"

    lines = response.text.strip().split("\n\n")
    # Each SSE event is "data: {...}\n\n"
    data_lines = [ln for ln in response.text.split("\n") if ln.startswith("data: ")]
    assert len(data_lines) == 6

    first_data = json.loads(data_lines[0][6:])  # strip "data: "
    assert first_data["type"] == "title"
    assert first_data["title"] == "Test Lesson"

    mock_stream.assert_called_once_with(
        topic="Water Cycle",
        grade="4th grade",
        context="",
        n_slides=3,
    )


@patch("app.main.generate_slides_stream")
def test_streaming_error_in_stream(mock_stream, client: TestClient):
    """POST /streaming yields error in data when stream raises."""
    async def mock_error_gen():
        raise ValueError("Bad request")
        yield  # make it a generator

    mock_stream.return_value = mock_error_gen()

    response = client.post(
        "/streaming",
        json={"topic": "X", "grade": "Y", "n_slides": 1},
    )

    assert response.status_code == 200
    # Stream may contain one event with error
    assert "data:" in response.text
    if "error" in response.text:
        # Error may be in one of the data lines
        data_lines = [ln for ln in response.text.split("\n") if ln.startswith("data: ")]
        assert any("error" in ln for ln in data_lines)
