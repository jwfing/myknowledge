"""OpenRouter LLM client for knowledge extraction."""

import json
import logging

import httpx

from myknowledge.config import settings
from myknowledge.types import ExtractedKnowledge

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a knowledge extraction assistant. Given a segment of a developer conversation \
with an AI coding agent, extract structured knowledge fragments.

For each distinct piece of knowledge, output a JSON object with:
- "content": A clear, self-contained summary of the knowledge (1-3 sentences)
- "memory_type": One of "semantic" (facts, definitions, API specs), "episodic" (experiences, \
bugs encountered, solutions found), or "procedural" (workflows, best practices, team conventions)
- "importance": Float 0-1 (0.8+ for key architectural decisions, API contracts; 0.5 for \
general context; 0.3 for minor details)
- "tags": List of relevant technology/domain tags (e.g., ["OAuth", "PKCE", "FastAPI"])
- "entities": List of entities mentioned, each as {"name": "...", "type": "Project|API|Component|TechStack|Config"}
- "relations": List of relations between entities, each as {"source": "...", "target": "...", \
"type": "exposes|depends_on|uses|configured_with"}

Rules:
- Skip debugging noise, error traces, and routine code generation
- Focus on decisions, architecture, API contracts, lessons learned, and configurations
- Each knowledge fragment should be self-contained and useful out of context
- If there is no extractable knowledge, return an empty list

Return ONLY a JSON array of knowledge objects. No explanation or markdown.\
"""


async def extract_knowledge(conversation_text: str) -> list[ExtractedKnowledge]:
    """Call OpenRouter to extract structured knowledge from a conversation segment."""
    if not settings.OPENROUTER_API_KEY:
        logger.warning("OPENROUTER_API_KEY not set, skipping extraction")
        return []

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": settings.OPENROUTER_MODEL,
                    "messages": [
                        {"role": "system", "content": EXTRACTION_PROMPT},
                        {"role": "user", "content": conversation_text},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 4096,
                },
            )
            response.raise_for_status()

        data = response.json()
        content = data["choices"][0]["message"]["content"].strip()

        # Parse JSON response
        # Handle potential markdown code blocks
        if content.startswith("```"):
            content = content.split("\n", 1)[1].rsplit("```", 1)[0]

        fragments = json.loads(content)
        if not isinstance(fragments, list):
            fragments = [fragments]

        results = []
        for f in fragments:
            try:
                results.append(ExtractedKnowledge(**f))
            except Exception as e:
                logger.warning("Failed to parse extracted fragment: %s - %s", f, e)
                continue

        logger.info("Extracted %d knowledge fragments from conversation", len(results))
        return results

    except httpx.HTTPStatusError as e:
        logger.error("OpenRouter API error: %s - %s", e.response.status_code, e.response.text)
        return []
    except json.JSONDecodeError as e:
        logger.error("Failed to parse LLM response as JSON: %s", e)
        return []
    except Exception as e:
        logger.error("Unexpected error during extraction: %s", e)
        return []
