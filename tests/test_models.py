"""Tests for Pydantic models (schemas)."""

import pytest
from pydantic import ValidationError

from app.models.schemas import Slide, SlideQuestion, SlideDeckRequest, SlideDeckResponse


class TestSlideQuestion:
    """SlideQuestion validation."""

    def test_valid_question(self):
        q = SlideQuestion(
            prompt="What is 2+2?",
            options=["3", "4", "5", "6"],
            answer="4",
        )
        assert q.prompt == "What is 2+2?"
        assert q.answer == "4"

    def test_options_min_length(self):
        with pytest.raises(ValidationError):
            SlideQuestion(
                prompt="Only one?",
                options=["A"],
                answer="A",
            )


class TestSlide:
    """Slide validation."""

    def test_valid_title_slide(self):
        s = Slide(type="title", title="Lesson", content="Intro.")
        assert s.type == "title"
        assert s.image is None
        assert s.question is None

    def test_valid_content_slide_with_image_and_question(self):
        s = Slide(
            type="content",
            title="Content",
            content="Text.",
            image="water cycle diagram",
            question=SlideQuestion(
                prompt="Question?",
                options=["A", "B", "C", "D"],
                answer="B",
            ),
        )
        assert s.image == "water cycle diagram"
        assert s.question and s.question.answer == "B"

    def test_invalid_type_rejected(self):
        with pytest.raises(ValidationError):
            Slide(type="invalid", title="X", content="Y")

    def test_empty_title_rejected(self):
        with pytest.raises(ValidationError):
            Slide(type="title", title="", content="X")

    def test_empty_content_rejected(self):
        with pytest.raises(ValidationError):
            Slide(type="title", title="X", content="")


class TestSlideDeckRequest:
    """SlideDeckRequest validation."""

    def test_valid_request(self):
        r = SlideDeckRequest(topic="Math", grade="5th", context="", n_slides=5)
        assert r.topic == "Math"
        assert r.n_slides == 5
        assert r.context == ""

    def test_defaults(self):
        r = SlideDeckRequest(topic="X", grade="Y")
        assert r.context == ""
        assert r.n_slides == 5

    def test_n_slides_bounds(self):
        SlideDeckRequest(topic="X", grade="Y", n_slides=1)
        SlideDeckRequest(topic="X", grade="Y", n_slides=20)
        with pytest.raises(ValidationError):
            SlideDeckRequest(topic="X", grade="Y", n_slides=0)
        with pytest.raises(ValidationError):
            SlideDeckRequest(topic="X", grade="Y", n_slides=21)

    def test_topic_required(self):
        with pytest.raises(ValidationError):
            SlideDeckRequest(topic="", grade="5th")


class TestSlideDeckResponse:
    """SlideDeckResponse validation."""

    def test_valid_response(self, sample_slides):
        r = SlideDeckResponse(slides=sample_slides)
        assert len(r.slides) == 6  # title, agenda, 3 content, conclusion
        assert r.slides[0].type == "title"
        assert r.slides[-1].type == "conclusion"
