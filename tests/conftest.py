"""Pytest fixtures: client and sample data."""

import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.models.schemas import Slide, SlideQuestion


@pytest.fixture
def client() -> TestClient:
    """FastAPI test client."""
    return TestClient(app)


def make_title_slide() -> Slide:
    return Slide(type="title", title="Test Lesson", content="A short subtitle.")


def make_agenda_slide() -> Slide:
    return Slide(
        type="agenda",
        title="Agenda",
        content="• Point 1\n• Point 2\n• Point 3",
    )


def make_content_slide(index: int, with_image: bool = False, with_question: bool = False) -> Slide:
    data: dict = {
        "type": "content",
        "title": f"Content {index}",
        "content": f"Explanation for content slide {index}.",
    }
    if with_image:
        data["image"] = "search query for slide image"
    if with_question:
        data["question"] = SlideQuestion(
            prompt="What is the correct answer?",
            options=["A) Wrong", "B) Correct", "C) Wrong", "D) Wrong"],
            answer="B",
        )
    return Slide.model_validate(data)


def make_conclusion_slide() -> Slide:
    return Slide(
        type="conclusion",
        title="Conclusion",
        content="Summary and key takeaway.",
    )


@pytest.fixture
def sample_slides(n_slides: int = 3) -> list[Slide]:
    """Minimal deck: title, agenda, n_slides content, conclusion."""
    slides = [
        make_title_slide(),
        make_agenda_slide(),
    ]
    for i in range(n_slides):
        slides.append(make_content_slide(i + 1, with_question=(i == n_slides // 2)))
    slides.append(make_conclusion_slide())
    return slides


@pytest.fixture
def slide_request_payload() -> dict:
    """Valid request body for POST /slide and POST /streaming."""
    return {
        "topic": "Water Cycle",
        "grade": "4th grade",
        "context": "Focus on evaporation.",
        "n_slides": 3,
    }
