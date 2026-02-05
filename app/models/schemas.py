"""Pydantic schemas for request/response and slide structure."""

from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field


class SlideType(str, Enum):
    """Type of slide in the deck."""

    TITLE = "title"
    AGENDA = "agenda"
    CONTENT = "content"
    CONCLUSION = "conclusion"


class SlideQuestion(BaseModel):
    """
    Optional question (exercise) for a content slide.

    - prompt: The question statement, aligned with the lesson.
    - options: List of answer options (e.g. A, B, C, D).
    - answer: The correct option (e.g. "C").
    """

    prompt: str = Field(..., description="Question statement related to the lesson")
    options: list[str] = Field(..., min_length=2, description="Answer options (e.g. A, B, C, D)")
    answer: str = Field(..., description="Correct option letter or text")


class Slide(BaseModel):
    """
    A single slide in the deck.

    - type: One of title, agenda, content, conclusion.
    - title: Slide title.
    - content: Text displayed on the slide (bullets, short paragraphs, etc.).
    - image: Optional search query for an image that fits the slide (content slides only).
    - question: Optional exercise for the slide (content slides only, at most one per deck).
    """

    type: Literal["title", "agenda", "content", "conclusion"]
    title: str = Field(..., min_length=1)
    content: str = Field(..., min_length=1)
    image: str | None = Field(None, description="Search query for an image that fits the slide")
    question: SlideQuestion | None = Field(
        None,
        description="Optional question/exercise for this slide",
    )


class SlideDeckRequest(BaseModel):
    """Request body for slide deck generation."""

    topic: str = Field(..., min_length=1, description="Subject of the lesson")
    grade: str = Field(..., min_length=1, description="Students' year/level")
    context: str = Field(default="", description="Extra details from the teacher")
    n_slides: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Number of content slides (title, agenda, conclusion are extra)",
    )


class SlideDeckResponse(BaseModel):
    """Response: list of slides (title, agenda, n_slides content, conclusion)."""

    slides: list[Slide] = Field(..., description="Ordered list of slides")
