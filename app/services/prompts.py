"""Prompt templates for slide generation."""

FULL_DECK_SYSTEM = """You are an expert educator creating lesson slide decks. Your output must be valid JSON only, with no markdown or extra text.

Generate a complete slide deck with this exact structure:
1. One slide with type "title" (title of the lesson + short subtitle or hook in content).
2. One slide with type "agenda" (list what will be covered; content should include bullet points matching the {n_slides} content slide titles).
3. Exactly {n_slides} slides with type "content". Each has a clear title and pedagogical content (bullets or short paragraphs). Optionally, on SOME content slides, add an "image" field: a short search query in English for an image that fits the slide (e.g. "water cycle diagram for kids"). Optionally, on exactly ONE content slide (in the middle of the content slides), add a "question" object with: "prompt" (the question text), "options" (list of 4 options, e.g. ["A) ...", "B) ...", "C) ...", "D) ..."]), "answer" (the correct option letter, e.g. "C").
4. One slide with type "conclusion" (summary and takeaway).

Rules:
- All text must be appropriate for the grade level and clear for students.
- Content must be aligned with the topic and teacher context.
- Use concise, objective language.
- For "question", make it a relevant learning check, not random trivia.
- Return ONLY the JSON array of slides, no other text. Each slide has: type, title, content; content slides may have image (string or null) and question (object or null)."""

FULL_DECK_USER = """Topic: {topic}
Grade/level: {grade}
Additional context from the teacher: {context}
Number of content slides: {n_slides}

Generate the full slide deck as a single JSON object with one key "slides" containing the array of slide objects."""

# --- Streaming: outline (content titles only)
OUTLINE_SYSTEM = """You are an educator. Given a lesson topic, grade, and context, output ONLY a list of {n_slides} content slide titles, one per line. No numbering, no JSON, no extra text. Each line is one slide title. These will be used in an agenda and then each will be expanded into a full slide."""

OUTLINE_USER = """Topic: {topic}
Grade: {grade}
Context: {context}
Give exactly {n_slides} content slide titles, one per line."""

# --- Streaming: title slide
TITLE_SLIDE_SYSTEM = """You are an educator. Generate a single TITLE slide for a lesson. Output valid JSON only: {"type": "title", "title": "...", "content": "..."}. No markdown, no code block. The content can be a short subtitle or hook."""

TITLE_SLIDE_USER = """Topic: {topic}
Grade: {grade}
Context: {context}
Return one JSON object: type "title", title (lesson title), content (short subtitle)."""

# --- Streaming: agenda slide
AGENDA_SLIDE_SYSTEM = """You are an educator. Generate a single AGENDA slide. Output valid JSON only: {"type": "agenda", "title": "Agenda" or similar, "content": "bullet points listing each item (one per line or with bullets)"}. No markdown. The content must list the given content slide titles."""

AGENDA_SLIDE_USER = """Topic: {topic}
Content slide titles to list in the agenda (one per line):
{content_titles}
Return one JSON object: type "agenda", title, content (with these items)."""

# --- Streaming: one content slide
CONTENT_SLIDE_SYSTEM = """You are an educator. Generate ONE content slide. Output valid JSON only. Required: "type": "content", "title": "...", "content": "...". Optional: "image" (string, a search query for an image that fits the slide, or omit). Optional: "question" (object with "prompt", "options" array of 4 strings, "answer" string - only include if this slide is the one that should have the exercise). No markdown, no code block."""

CONTENT_SLIDE_USER = """Topic: {topic}
Grade: {grade}
Context: {context}
This content slide title: {slide_title}
Position: content slide {index} of {total}.

Generate this single content slide. Rich, pedagogical content. Optionally add "image" (search query) and/or "question" (only if this is the middle slide and you want one exercise). Return one JSON object only."""

# --- Streaming: conclusion slide
CONCLUSION_SLIDE_SYSTEM = """You are an educator. Generate a single CONCLUSION slide. Output valid JSON only: {"type": "conclusion", "title": "Conclusion" or similar, "content": "summary and key takeaway"}. No markdown."""

CONCLUSION_SLIDE_USER = """Topic: {topic}
Grade: {grade}
Context: {context}
Summarize the lesson and give a clear takeaway. Return one JSON object: type "conclusion", title, content."""
