"""Slide deck generation using LangChain and structured output."""

import json
import re
from typing import AsyncIterator

from langchain_core.messages import HumanMessage, SystemMessage

from app.models.schemas import Slide, SlideDeckResponse
from app.services.llm_factory import get_llm
from app.services.prompts import (
    FULL_DECK_SYSTEM,
    FULL_DECK_USER,
    OUTLINE_SYSTEM,
    OUTLINE_USER,
    TITLE_SLIDE_SYSTEM,
    TITLE_SLIDE_USER,
    AGENDA_SLIDE_SYSTEM,
    AGENDA_SLIDE_USER,
    CONTENT_SLIDE_SYSTEM,
    CONTENT_SLIDE_USER,
    CONCLUSION_SLIDE_SYSTEM,
    CONCLUSION_SLIDE_USER,
)


def _strip_markdown_json(text: str) -> str:
    """Remove markdown code block wrapper if present."""
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
    return text.strip()


async def generate_full_deck(topic: str, grade: str, context: str, n_slides: int) -> list[Slide]:
    """Generate the full slide deck in one LLM call (title, agenda, n_slides content, conclusion)."""
    llm = get_llm()
    structured_llm = llm.with_structured_output(SlideDeckResponse)

    system = FULL_DECK_SYSTEM.format(n_slides=n_slides)
    user = FULL_DECK_USER.format(
        topic=topic,
        grade=grade,
        context=context or "(none)",
        n_slides=n_slides,
    )

    messages = [
        SystemMessage(content=system),
        HumanMessage(content=user),
    ]
    result: SlideDeckResponse = await structured_llm.ainvoke(messages)
    return result.slides


async def _parse_slide_from_llm(llm, system: str, user: str) -> Slide:
    """Invoke LLM and parse response as a single Slide."""
    messages = [SystemMessage(content=system), HumanMessage(content=user)]
    response = await llm.ainvoke(messages)
    content = response.content if hasattr(response, "content") else str(response)
    raw = _strip_markdown_json(content)
    data = json.loads(raw)
    return Slide.model_validate(data)


async def generate_slides_stream(
    topic: str, grade: str, context: str, n_slides: int
) -> AsyncIterator[Slide]:
    """Generate slides one by one and yield each (for SSE streaming)."""
    llm = get_llm()
    ctx = context or "(none)"

    # 1. Outline: list of content slide titles
    outline_sys = OUTLINE_SYSTEM.format(n_slides=n_slides)
    outline_user = OUTLINE_USER.format(topic=topic, grade=grade, context=ctx, n_slides=n_slides)
    outline_messages = [SystemMessage(content=outline_sys), HumanMessage(content=outline_user)]
    outline_resp = await llm.ainvoke(outline_messages)
    outline_text = outline_resp.content if hasattr(outline_resp, "content") else str(outline_resp)
    content_titles = [line.strip() for line in outline_text.strip().splitlines() if line.strip()][:n_slides]
    while len(content_titles) < n_slides:
        content_titles.append(f"Point {len(content_titles) + 1}")

    # 2. Title slide
    yield await _parse_slide_from_llm(
        llm,
        TITLE_SLIDE_SYSTEM,
        TITLE_SLIDE_USER.format(topic=topic, grade=grade, context=ctx),
    )

    # 3. Agenda slide
    titles_blob = "\n".join(f"- {t}" for t in content_titles)
    yield await _parse_slide_from_llm(
        llm,
        AGENDA_SLIDE_SYSTEM,
        AGENDA_SLIDE_USER.format(topic=topic, content_titles=titles_blob),
    )

    # 4. Content slides
    middle_index = n_slides // 2
    for i, slide_title in enumerate(content_titles):
        user = CONTENT_SLIDE_USER.format(
            topic=topic,
            grade=grade,
            context=ctx,
            slide_title=slide_title,
            index=i + 1,
            total=n_slides,
        )
        yield await _parse_slide_from_llm(llm, CONTENT_SLIDE_SYSTEM, user)

    # 5. Conclusion slide
    yield await _parse_slide_from_llm(
        llm,
        CONCLUSION_SLIDE_SYSTEM,
        CONCLUSION_SLIDE_USER.format(topic=topic, grade=grade, context=ctx),
    )
