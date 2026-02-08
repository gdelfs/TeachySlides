"""High-load tests: many concurrent requests, semaphore and server stability."""

import asyncio
import time
from unittest.mock import MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.models.schemas import SlideDeckResponse


# Number of concurrent requests and simulated latency (seconds)
CONCURRENT_REQUESTS = 25
MOCK_LLM_LATENCY = 0.05
# With semaphore=10, 25 requests in 3 waves of ~0.05s -> ~0.15s minimum
EXPECTED_MIN_SECONDS = 0.1
EXPECTED_MAX_SECONDS = 10.0


def _make_sample_slides():
    from app.models.schemas import Slide

    return [
        Slide(type="title", title="Load Test", content="Subtitle."),
        Slide(type="agenda", title="Agenda", content="• A\n• B\n• C"),
        Slide(type="content", title="A", content="Content A."),
        Slide(type="content", title="B", content="Content B."),
        Slide(type="content", title="C", content="Content C."),
        Slide(type="conclusion", title="Conclusion", content="Summary."),
    ]


@pytest.fixture
def sample_slides():
    return _make_sample_slides()


def _create_mock_llm(sample_slides):
    """Mock LLM: with_structured_output().ainvoke() sleeps then returns SlideDeckResponse."""
    from unittest.mock import AsyncMock

    async def slow_ainvoke(*args, **kwargs):
        await asyncio.sleep(MOCK_LLM_LATENCY)
        return SlideDeckResponse(slides=sample_slides)

    mock_structured = MagicMock()
    mock_structured.ainvoke = AsyncMock(side_effect=slow_ainvoke)

    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured
    return mock_llm


@pytest.mark.asyncio
async def test_high_load_concurrent_post_slide(sample_slides):
    """
    Many concurrent POST /slide requests complete successfully.
    Exercises the real generate_full_deck (and semaphore) with a mocked LLM.
    """
    mock_llm = _create_mock_llm(sample_slides)

    with patch("app.services.slides_service.get_llm", return_value=mock_llm):
        payload = {"topic": "Load Test", "grade": "5th", "context": "", "n_slides": 3}
        start = time.monotonic()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0,
        ) as client:
            tasks = [client.post("/slide", json=payload) for _ in range(CONCURRENT_REQUESTS)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.monotonic() - start

    # All requests must complete with 200
    successes = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
    failures = [r for r in responses if isinstance(r, Exception) or r.status_code != 200]

    assert len(successes) == CONCURRENT_REQUESTS, (
        f"Expected {CONCURRENT_REQUESTS} successes, got {len(successes)}. "
        f"Failures: {failures[:5]}"
    )
    assert len(failures) == 0, f"Unexpected failures: {failures[:5]}"

    # Total time: with semaphore (default 10), 25 requests in 3 waves of ~0.05s
    assert EXPECTED_MIN_SECONDS <= elapsed <= EXPECTED_MAX_SECONDS, (
        f"Elapsed {elapsed:.2f}s outside expected range [{EXPECTED_MIN_SECONDS}, {EXPECTED_MAX_SECONDS}]"
    )

    # All responses have valid slide deck structure
    for r in successes:
        data = r.json()
        assert "slides" in data
        assert len(data["slides"]) >= 5
        assert data["slides"][0]["type"] == "title"
        assert data["slides"][-1]["type"] == "conclusion"


@pytest.mark.asyncio
async def test_high_load_concurrent_streaming(sample_slides):
    """
    Many concurrent POST /streaming requests complete successfully.
    Mocks generate_slides_stream to return sample slides with small delay.
    """
    async def mock_stream(*args, **kwargs):
        await asyncio.sleep(MOCK_LLM_LATENCY)
        for s in sample_slides:
            yield s

    with patch("app.main.generate_slides_stream", side_effect=mock_stream):
        payload = {"topic": "Stream Load", "grade": "5th", "n_slides": 3}
        start = time.monotonic()

        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
            timeout=30.0,
        ) as client:
            tasks = [client.post("/streaming", json=payload) for _ in range(15)]
            responses = await asyncio.gather(*tasks, return_exceptions=True)

        elapsed = time.monotonic() - start

    successes = [r for r in responses if not isinstance(r, Exception) and r.status_code == 200]
    assert len(successes) == 15, f"Expected 15 successes, got {len(successes)}. Errors: {responses}"
    assert elapsed < EXPECTED_MAX_SECONDS
