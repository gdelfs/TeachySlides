# Teachy Slides – AI Slide Deck Generation Service
By Gabriel Delfino

Backend service in **Python + FastAPI** that generates lesson slide decks from a topic, student grade, and teacher context. Uses **LangChain** for GenAI orchestration and **Pydantic** for typing.

---

## Features

- **POST /slide** – Returns the full slide deck at once (title, agenda, n content slides, conclusion).
- **POST /streaming** – Returns slides one by one via **Server-Sent Events (SSE)** while the rest are still being generated.
- Optional **image** field on content slides (search query for an image).
- Optional **question** (exercise) on one content slide in the middle.
- Configurable LLM: **OpenAI** via env.

---

## Setup

### 1. Clone and enter the repo

```bash
git clone <repo-url> #https://github.com/gdelfs/TeachySlides
cd TeachySlides
```

### 2. Create a virtual environment (recommended)

```bash
python -m venv .venv

# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Copy the example env file and set your API key:

```bash
copy .env.example .env   # Windows
cp .env.example .env   # Linux/macOS
```

Edit `.env`:

```env
# LLM provider: "openai" 
LLM_PROVIDER=openai
# Secret: edit with your api Secret
OPENAI_API_KEY=sk-...

#To get your api Secret:
# Acesses https://platform.openai.com/
# Login.
# Go to API Keys.
# Create or copy a key.
# The api use is not included, even if you have GPT pro (my case)! Careful with billing.
```

---

## Run the server

From the project root:

```bash
python run.py
```

Or:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

- API: **http://localhost:8000**
- Interactive docs: **http://localhost:8000/docs**
- Health: **http://localhost:8000/health**

---

## Tuning for many simultaneous requests

To handle many concurrent requests without overloading the LLM API or the server:

1. **Concurrency limit (semaphore)**  
   At most `MAX_CONCURRENT_GENERATIONS` slide generations run at once (default: 10). Extra requests wait in queue. Set in `.env`:
   ```env
   MAX_CONCURRENT_GENERATIONS=10
   ```

2. **LLM timeout**  
   Each LLM call times out after `LLM_REQUEST_TIMEOUT_SECONDS` (default: 60), so a stuck request does not block the semaphore forever.

3. **Reused LLM client**  
   The LLM client is created once and reused for all requests (no new connection per request).

4. **Optional response cache**  
   Identical requests (same `topic`, `grade`, `context`, `n_slides`) can be served from an in-memory cache to reduce API calls:
   ```env
   CACHE_ENABLED=true
   CACHE_TTL_SECONDS=300
   CACHE_MAX_SIZE=100
   ```
   Cache applies only to **POST /slide** (full deck), not to streaming.

5. **Multiple workers**  
   For CPU headroom, run more Uvicorn workers (each has its own semaphore and cache):
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 2
   ```
   Use with care: each worker uses its own memory and LLM client.

---

## Tests

Install dev dependencies and run pytest:

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

Tests cover:

- **Models** (`tests/test_models.py`): Pydantic validation for `Slide`, `SlideQuestion`, `SlideDeckRequest`, `SlideDeckResponse`.
- **API** (`tests/test_api.py`): Health, POST /slide and POST /streaming with **mocked** LLM (no API key needed).
- **High load** (`tests/test_high_load.py`): 25 concurrent POST /slide and 15 concurrent POST /streaming; verifies semaphore and server stability (no API key needed).

---

## API

### 1. POST /slide – Full deck at once

**Input (JSON body):**

| Field      | Type   | Required | Description                                |
|-----------|--------|----------|--------------------------------------------|
| `topic`   | string | yes      | Subject of the lesson                      |
| `grade`   | string | yes      | Students' year/level (e.g. "5th grade")   |
| `context` | string | no       | Extra details from the teacher             |
| `n_slides`| number | no       | Number of **content** slides (default: 5)  |

**Output:** JSON object with key `slides`: array of slide objects.

**Slide object:**

- `type`: `"title"` \| `"agenda"` \| `"content"` \| `"conclusion"`
- `title`: string
- `content`: string (text on the slide)
- `image`: string \| null (optional; search query for an image)
- `question`: object \| null (optional; only on one content slide)
  - `prompt`: string
  - `options`: string[] (e.g. A, B, C, D)
  - `answer`: string (correct option)

**Example request:**

```bash
curl -X POST http://localhost:8000/slide \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "Water Cycle",
    "grade": "4th grade",
    "context": "Focus on evaporation and condensation.",
    "n_slides": 4
  }'
```

**Example response (structure):**

```json
{
  "slides": [
    {
      "type": "title",
      "title": "The Water Cycle",
      "content": "How water moves around our planet"
    },
    {
      "type": "agenda",
      "title": "Agenda",
      "content": "• Evaporation\n• Condensation\n• Precipitation\n• Collection"
    },
    {
      "type": "content",
      "title": "Evaporation",
      "content": "...",
      "image": "water evaporation from ocean"
    },
    {
      "type": "content",
      "title": "Condensation",
      "content": "..."
    },
    {
      "type": "content",
      "title": "Precipitation",
      "content": "...",
      "question": {
        "prompt": "Where does rain come from?",
        "options": ["A) Ground", "B) Clouds", "C) Sun", "D) Wind"],
        "answer": "B"
      }
    },
    {
      "type": "content",
      "title": "Collection",
      "content": "..."
    },
    {
      "type": "conclusion",
      "title": "Conclusion",
      "content": "..."
    }
  ]
}
```

Total slides = 1 (title) + 1 (agenda) + `n_slides` (content) + 1 (conclusion). For `n_slides=4` that is 7 slides.

---

### 2. POST /streaming – Slides via SSE

**Input:** Same JSON body as `POST /slide` (`topic`, `grade`, `context`, `n_slides`).

**Output:** Response with `Content-Type: text/event-stream`. Each event is one slide:

- Lines of the form `data: <json>` where `<json>` is one slide object (same schema as above).
- Empty line after each event.

**How to consume:**

- **Python (httpx):** POST with `json=payload`, stream the response, read SSE lines via `response.aiter_lines()`, and parse data: `JSON`. events.

**Example in Python:**

Requirement install

```bash
pip install httpx
```

Code

```python
import httpx
import json
import asyncio

payload = {
    "topic": "Dota 2",
    "grade": "8th grade",
    "context": "",
    "n_slides": 5
}

async def main():
    timeout = httpx.Timeout(None)  

    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream(
            "POST",
            "http://localhost:8000/streaming",
            json=payload
        ) as r:
            i=1
            async for line in r.aiter_lines():
                if line and line.startswith("data: "):
                    slide = json.loads(line[6:])
                    if "error" in slide:
                        print("Error:", slide["error"])
                    else:
                        print("\n\nSlide:" + str(i) + " - ", slide["type"],": ", slide["title"])
                        if "content" in slide:
                            print("Content:", slide["content"])

                        if "image" in slide:
                            print("Image:", slide["image"])

                        if "question" in slide:
                            print("Question:", slide["question"])
                    i+=1

asyncio.run(main())

```

---

## Project structure

```
TeachySlides/
├── app/
│   ├── __init__.py
│   ├── config.py          # Settings (env)
│   ├── main.py            # FastAPI app, /slide and /streaming
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py     # Pydantic: Slide, SlideDeckRequest, etc.
│   └── services/
│       ├── __init__.py
│       ├── llm_factory.py # OpenAI
│       ├── prompts.py     # Prompt templates
│       └── slides_service.py  # LangChain: full deck + stream
├── .env.example
├── requirements.txt
├── README.md
└── run.py
```

---

## Tech stack

- **FastAPI** – API
- **LangChain** – Prompts and structured output (full deck); multi-step chain for streaming (outline → title → agenda → content × n → conclusion)
- **Pydantic** – Request/response and slide models
- **pydantic-settings** – Config from `.env`

---