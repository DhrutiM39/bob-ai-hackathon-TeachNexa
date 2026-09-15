"""
AI client wrapper for CourseGenie AI.

Active provider: Google Gemini (via OpenAI-compatible endpoint).
Legacy provider: DeepSeek (preserved; can be restored by swapping _get_client).

Responsibilities:
  - Initialise the AI chat-completions client from Settings.
  - Expose high-level methods: generate_course_structure(),
    generate_topic_content(), generate_quiz(), generate_revision().
  - Keep all prompt engineering, JSON extraction, and retry logic here
    so callers never touch the SDK directly.

The class is designed to be dependency-injected (see get_deepseek_client in
this module), which makes it trivially mockable in tests.

Uses the `openai` Python SDK pointed at Google Gemini's OpenAI-compatible
endpoint (https://generativelanguage.googleapis.com/v1beta/openai/).
DeepSeek wiring is preserved below and can be restored by swapping _get_client.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from backend.app.config import Settings, get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt templates
# ---------------------------------------------------------------------------
_COURSE_STRUCTURE_PROMPT = """\
You are an expert curriculum designer. Given the syllabus below, produce a \
structured course outline in JSON.

Return ONLY a valid JSON object — no markdown, no explanation, no code fences.

The JSON must have this exact shape:
{{
  "modules": [
    {{
      "title": "<module title>",
      "description": "<one-sentence description>",
      "topics": [
        {{
          "title": "<topic title>",
          "description": "<one-sentence description>"
        }}
      ]
    }}
  ]
}}

Rules:
- Produce between 3 and 8 modules.
- Each module must have between 2 and 6 topics.
- Titles must be concise (max 10 words).
- Descriptions must be a single sentence.
- Do NOT add extra keys.

SYLLABUS:
{syllabus_text}
"""

_TOPIC_CONTENT_PROMPT = """\
You are an expert professor creating rich learning content for university students.
Given the topic title and description below, produce comprehensive learning material in JSON.

Return ONLY a valid JSON object — no markdown, no explanation, no code fences.

The JSON must have this exact shape:
{{
  "title": "<topic title>",
  "objectives": ["<learning objective 1>", "<learning objective 2>", ...],
  "explanation": "<detailed multi-paragraph explanation of the topic>",
  "key_concepts": [
    {{ "term": "<concept name>", "definition": "<clear one-sentence definition>" }}
  ],
  "examples": [
    {{ "title": "<example title>", "content": "<detailed example explanation>" }}
  ],
  "summary": "<concise 2-3 sentence summary>",
  "further_reading": ["<book or resource title>", ...]
}}

Rules:
- Provide 3-5 learning objectives starting with action verbs (Understand, Explain, Apply, etc.).
- The explanation must be at least 3 substantial paragraphs, written in clear academic prose.
- Provide 4-6 key concepts.
- Provide 2-3 concrete examples.
- Provide 2-4 further reading suggestions.
- Do NOT add extra keys.

TOPIC TITLE: {topic_title}
TOPIC DESCRIPTION: {topic_description}
COURSE CONTEXT: {course_title}
"""

_QUIZ_PROMPT = """\
You are an expert professor creating a multiple-choice quiz to assess student understanding.
Given the topic below, produce 5 high-quality MCQ questions in JSON.

Return ONLY a valid JSON object — no markdown, no explanation, no code fences.

The JSON must have this exact shape:
{{
  "title": "<Quiz: topic title>",
  "questions": [
    {{
      "id": "q1",
      "text": "<question text>",
      "options": [
        {{"id": "0", "text": "<option A>"}},
        {{"id": "1", "text": "<option B>"}},
        {{"id": "2", "text": "<option C>"}},
        {{"id": "3", "text": "<option D>"}}
      ],
      "correct_index": <0-3>,
      "explanation": "<why the correct answer is correct>"
    }}
  ]
}}

Rules:
- Produce exactly 5 questions with exactly 4 options each.
- correct_index must be 0, 1, 2, or 3 (integer, not string).
- Questions must vary in difficulty (2 easy, 2 medium, 1 hard).
- Explanations must be clear and educational.
- Do NOT add extra keys.

TOPIC TITLE: {topic_title}
TOPIC DESCRIPTION: {topic_description}
COURSE CONTEXT: {course_title}
"""

_REVISION_PROMPT = """\
You are an expert professor creating revision materials for a complete course.
Given the course title and its modules/topics below, produce structured revision content in JSON.

Return ONLY a valid JSON object — no markdown, no explanation, no code fences.

The JSON must have this exact shape:
{{
  "quick_notes": ["<concise revision bullet 1>", ...],
  "key_takeaways": ["<high-level insight 1>", ...],
  "practice_questions": [
    {{
      "id": "pq1",
      "text": "<question text>",
      "options": [
        {{"id": "0", "text": "<option>"}},
        {{"id": "1", "text": "<option>"}},
        {{"id": "2", "text": "<option>"}},
        {{"id": "3", "text": "<option>"}}
      ],
      "correct_index": <0-3>,
      "explanation": "<why correct>"
    }}
  ],
  "question_bank": [
    {{
      "id": "bq1",
      "text": "<question text>",
      "options": [
        {{"id": "0", "text": "<option>"}},
        {{"id": "1", "text": "<option>"}},
        {{"id": "2", "text": "<option>"}},
        {{"id": "3", "text": "<option>"}}
      ],
      "correct_index": <0-3>,
      "explanation": "<why correct>"
    }}
  ]
}}

Rules:
- Provide 6-10 quick_notes (short, memorable bullets).
- Provide 4-6 key_takeaways (big-picture insights).
- Provide 3-5 practice_questions covering key topics.
- Provide 5-8 question_bank items for deeper assessment.
- All correct_index values must be integers 0-3.
- Do NOT add extra keys.

COURSE TITLE: {course_title}
MODULES AND TOPICS:
{modules_text}
"""


# ---------------------------------------------------------------------------
# DeepSeekClient
# ---------------------------------------------------------------------------
class DeepSeekClient:
    """
    Thin wrapper around DeepSeek's OpenAI-compatible chat completions API.

    Parameters
    ----------
    settings : Settings
        Application settings (injected so tests can pass a fake).
    """

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._client: Any = None  # lazy-initialised on first use

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _get_client(self) -> Any:
        """Return (and lazily create) the OpenAI client pointed at Gemini.

        ACTIVE PROVIDER: Google Gemini (OpenAI-compatible endpoint).
        To restore DeepSeek, replace the OpenAI() call below with:
            self._client = OpenAI(
                api_key=self._settings.deepseek_api_key,
                base_url="https://api.deepseek.com",
            )
        and swap the model references to self._settings.deepseek_model.
        """
        if self._client is not None:
            return self._client

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "openai is not installed. Run: pip install openai"
            ) from exc

        # ── Active: Google Gemini ──────────────────────────────────────────
        self._client = OpenAI(
            api_key=self._settings.gemini_api_key,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        logger.info(
            "AI client initialised — provider=Gemini model=%s",
            self._settings.gemini_model,
        )
        return self._client

    @staticmethod
    def _extract_json(raw: str) -> str:
        """
        Strip any surrounding markdown fences and whitespace from the model
        response so json.loads() can consume it.
        """
        # Remove ```json ... ``` or ``` ... ``` fences
        raw = re.sub(r"^```[a-z]*\s*", "", raw.strip(), flags=re.IGNORECASE)
        raw = re.sub(r"\s*```$", "", raw.strip())
        return raw.strip()

    @staticmethod
    def _validate_structure(data: dict) -> list[dict]:
        """
        Validate the parsed JSON has the expected shape and return the
        modules list.  Raises ValueError with a human-readable message on
        bad structure.
        """
        if not isinstance(data, dict) or "modules" not in data:
            raise ValueError("Model response missing top-level 'modules' key.")

        modules = data["modules"]
        if not isinstance(modules, list) or len(modules) == 0:
            raise ValueError("'modules' must be a non-empty list.")

        for i, mod in enumerate(modules):
            if not isinstance(mod, dict):
                raise ValueError(f"Module {i} is not a dict.")
            if "title" not in mod:
                raise ValueError(f"Module {i} missing 'title'.")
            if "topics" not in mod or not isinstance(mod["topics"], list):
                raise ValueError(f"Module {i} missing or invalid 'topics'.")
            for j, topic in enumerate(mod["topics"]):
                if not isinstance(topic, dict) or "title" not in topic:
                    raise ValueError(
                        f"Module {i}, topic {j} missing 'title'."
                    )

        return modules

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def generate_course_structure(self, syllabus_text: str) -> tuple[list[dict], str]:
        """
        Call DeepSeek with a structured prompt and return a validated
        list of module dicts plus the model_id that was used.

        Parameters
        ----------
        syllabus_text : str
            The raw syllabus to parse.

        Returns
        -------
        modules : list[dict]
            Each dict has keys ``title``, ``description`` (optional),
            and ``topics`` (list of dicts with ``title`` + ``description``).
        model_id : str
            The model that produced the response (for provenance tracking).

        Raises
        ------
        ValueError
            If the model's JSON response cannot be parsed or validated.
        RuntimeError
            If the API call fails.
        """
        prompt = _COURSE_STRUCTURE_PROMPT.format(syllabus_text=syllabus_text)

        client = self._get_client()
        model = self._settings.gemini_model
        logger.debug("Sending generate_course_structure request (%d chars)", len(prompt))

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.2,
            )
        except Exception as exc:
            logger.exception("AI API call failed (generate_course_structure)")
            raise RuntimeError(f"DeepSeek call failed: {exc}") from exc

        raw_text: str = response.choices[0].message.content or ""
        logger.debug("Raw DeepSeek response (%d chars): %.200s…", len(raw_text), raw_text)

        cleaned = self._extract_json(raw_text)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Model returned invalid JSON: {exc}\nRaw response: {raw_text[:500]}"
            ) from exc

        modules = self._validate_structure(data)
        return modules, model

    def generate_topic_content(
        self, topic_title: str, topic_description: str, course_title: str
    ) -> tuple[dict, str]:
        """
        Generate rich learning content for a single topic.

        Returns (content_dict, model_id).  content_dict keys:
        title, objectives, explanation, key_concepts, examples, summary, further_reading.
        """
        prompt = _TOPIC_CONTENT_PROMPT.format(
            topic_title=topic_title,
            topic_description=topic_description or "",
            course_title=course_title,
        )
        client = self._get_client()
        model = self._settings.gemini_model
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3000,
                temperature=0.3,
            )
        except Exception as exc:
            logger.exception("AI API call failed (generate_topic_content)")
            raise RuntimeError(f"DeepSeek call failed: {exc}") from exc

        raw_text: str = response.choices[0].message.content or ""
        cleaned = self._extract_json(raw_text)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Model returned invalid JSON: {exc}\nRaw: {raw_text[:500]}"
            ) from exc

        if not isinstance(data, dict) or "explanation" not in data:
            raise ValueError("Topic content response missing required 'explanation' key.")
        return data, model

    def generate_quiz(
        self, topic_title: str, topic_description: str, course_title: str
    ) -> tuple[dict, str]:
        """
        Generate a 5-question MCQ quiz for a topic.

        Returns (quiz_dict, model_id).  quiz_dict keys: title, questions.
        """
        prompt = _QUIZ_PROMPT.format(
            topic_title=topic_title,
            topic_description=topic_description or "",
            course_title=course_title,
        )
        client = self._get_client()
        model = self._settings.gemini_model
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2500,
                temperature=0.2,
            )
        except Exception as exc:
            logger.exception("AI API call failed (generate_quiz)")
            raise RuntimeError(f"DeepSeek call failed: {exc}") from exc

        raw_text: str = response.choices[0].message.content or ""
        cleaned = self._extract_json(raw_text)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Model returned invalid JSON: {exc}\nRaw: {raw_text[:500]}"
            ) from exc

        if not isinstance(data, dict) or "questions" not in data:
            raise ValueError("Quiz response missing required 'questions' key.")
        return data, model

    def generate_revision(
        self, course_title: str, modules_summary: str
    ) -> tuple[dict, str]:
        """
        Generate revision materials for a course.

        Returns (revision_dict, model_id).
        revision_dict keys: quick_notes, key_takeaways, practice_questions, question_bank.
        """
        prompt = _REVISION_PROMPT.format(
            course_title=course_title,
            modules_text=modules_summary,
        )
        client = self._get_client()
        model = self._settings.gemini_model
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=3500,
                temperature=0.3,
            )
        except Exception as exc:
            logger.exception("AI API call failed (generate_revision)")
            raise RuntimeError(f"DeepSeek call failed: {exc}") from exc

        raw_text: str = response.choices[0].message.content or ""
        cleaned = self._extract_json(raw_text)
        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(
                f"Model returned invalid JSON: {exc}\nRaw: {raw_text[:500]}"
            ) from exc

        if not isinstance(data, dict) or "quick_notes" not in data:
            raise ValueError("Revision response missing required 'quick_notes' key.")
        return data, model


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_deepseek_client() -> DeepSeekClient:
    """FastAPI dependency — returns a DeepSeekClient backed by app settings."""
    return DeepSeekClient(settings=get_settings())
