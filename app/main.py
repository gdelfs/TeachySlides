"""FastAPI application: slide deck generation API."""

import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models.schemas import SlideDeckRequest, SlideDeckResponse, Slide
from app.services.slides_service import generate_full_deck, generate_slides_stream


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Optional: validate LLM config on first request (lazy)."""
    yield


app = FastAPI(
    title="Teachy Slides API",
    description="AI-powered lesson slide deck generation. Generates title, agenda, content slides, and conclusion from topic, grade, and context.",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health():
    """Health check."""
    return {"status": "ok"}


@app.post(
    "/slide",
    response_model=SlideDeckResponse,
    summary="Generate full slide deck",
    description="Returns the entire slide deck at once: 1 title + 1 agenda + n_slides content + 1 conclusion.",
)
async def post_slide(request: SlideDeckRequest) -> SlideDeckResponse:
    """
    **Input (body):**
    - `topic`: subject of the lesson
    - `grade`: students' year/level
    - `context`: optional extra details from the teacher
    - `n_slides`: number of content slides (default 5)

    **Output:** JSON with `slides`: list of slide objects (type, title, content; optional image, question).
    """
    try:
        slides = await generate_full_deck(
            topic=request.topic,
            grade=request.grade,
            context=request.context,
            n_slides=request.n_slides,
        )
        return SlideDeckResponse(slides=slides)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {e!s}")


@app.post(
    "/streaming",
    summary="Stream slides one by one",
    description="Returns the presentation slide by slide via Server-Sent Events (SSE). Each event is a JSON object of one slide.",
)
async def streaming_slides(request: SlideDeckRequest):
    """
    **Input (body):** Same as `POST /slide`: topic, grade, context, n_slides.

    **Output:** Server-Sent Events (SSE) stream. Each event:
    - `event`: `"slide"`
    - `data`: JSON string of one slide object (type, title, content; optional image, question).

    **How to consume (example):**
    - JavaScript: `const es = new EventSource('/streaming');` — but EventSource only supports GET. So use fetch with ReadableStream or a library that supports POST + SSE.
    - Python: use `httpx` or `requests` with `stream=True` and parse SSE lines.
    - Or use fetch + body (POST) and read the stream; each line starting with `data: ` is one slide JSON.

    This endpoint uses **POST** and streams the response body as SSE. Client should POST the body (JSON) and read the response as a stream; each line `data: {...}` is one slide.
    """
    async def event_stream():
        try:
            async for slide in generate_slides_stream(
                topic=request.topic,
                grade=request.grade,
                context=request.context,
                n_slides=request.n_slides,
            ):
                # SSE: "data: " + JSON + double newline
                data = slide.model_dump_json()
                yield f"data: {data}\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
