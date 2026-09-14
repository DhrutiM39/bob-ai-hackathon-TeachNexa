"""
DeepSeek client wrapper for CourseGenie AI.

Responsibilities:
  - Initialise the DeepSeek chat-completions client from Settings.
  - Expose a single high-level method: generate_course_structure()
    that takes a syllabus and returns a validated list of module/topic dicts.
  - Keep all prompt engineering, JSON extraction, and retry logic here
    so callers never touch the SDK directly.

The class is designed to be dependency-injected (see get_deepseek_client in
this module), which makes it trivially mockable in tests.

Uses the `openai` Python SDK pointed at DeepSeek's compatible endpoint.
"""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from backend.app.config import Settings, get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Prompt template
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
        """Return (and lazily create) the OpenAI client pointed at DeepSeek."""
        if self._client is not None:
            return self._client

        try:
            from openai import OpenAI
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "openai is not installed. Run: pip install openai"
            ) from exc

        self._client = OpenAI(
            api_key=self._settings.deepseek_api_key,
            base_url="https://api.deepseek.com",
        )
        logger.info(
            "DeepSeekClient initialised — model=%s",
            self._settings.deepseek_model,
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
        model = self._settings.deepseek_model
        logger.debug("Sending generate request to DeepSeek (%d chars)", len(prompt))

        try:
            response = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=2048,
                temperature=0.2,
            )
        except Exception as exc:
            logger.exception("DeepSeek API call failed")
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


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------
def get_deepseek_client() -> DeepSeekClient:
    """FastAPI dependency — returns a DeepSeekClient backed by app settings."""
    return DeepSeekClient(settings=get_settings())
