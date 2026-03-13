"""OpenRouter LLM client for knowledge extraction."""

import json
import logging

import httpx

from rememberit.config import settings
from rememberit.types import ExtractedKnowledge

logger = logging.getLogger(__name__)

EXTRACTION_PROMPT = """\
You are a knowledge extraction assistant. Given a segment of a developer conversation \
with an AI coding agent, extract ONLY high-value, reusable knowledge fragments.

For each distinct piece of knowledge, output a JSON object with:
- "content": A clear, self-contained summary of the knowledge (1-3 sentences). \
Must be understandable without reading the original conversation.
- "memory_type": One of "semantic" (facts, definitions, API specs), "episodic" (experiences, \
bugs encountered, solutions found), or "procedural" (workflows, best practices, team conventions)
- "importance": Float 0-1 (0.9 for key architectural decisions/API contracts that affect \
multiple components; 0.7 for useful patterns/solutions; 0.5 for general context; \
0.3 for minor details). Be strict — most fragments should be 0.5-0.7.
- "tags": List of relevant technology/domain tags (e.g., ["OAuth", "PKCE", "FastAPI"]). \
Max 5 tags. Use well-known technology names, not filenames.
- "entities": List of SIGNIFICANT entities, each as {"name": "...", "type": "Project|API|Component|TechStack|Config"}
- "relations": List of relations between entities, each as {"source": "...", "target": "...", \
"type": "exposes|depends_on|uses|configured_with"}

Entity extraction rules (IMPORTANT):
- Entities should be meaningful architectural concepts, NOT code artifacts
- GOOD entities: "OAuth Service", "Payment API", "Redis Cache", "PostgreSQL", "User Authentication Module"
- BAD entities (DO NOT extract): filenames (model.py, config.json, utils.ts), \
generic terms (function, variable, file, class, module), \
standard library items (os, sys, json, pathlib), \
routine operations (import, print, logging)
- Entity names should be human-readable descriptive names, not code identifiers
- Max 3 entities per fragment. Only extract entities that are architecturally significant.

Knowledge extraction rules:
- Skip debugging noise, error traces, routine code generation, and simple Q&A
- Skip trivial changes (typo fixes, formatting, import reordering)
- Focus on: WHY decisions were made, architecture patterns, non-obvious solutions, API contracts, \
team conventions, and hard-won debugging insights
- Each fragment must be useful to a developer working on a DIFFERENT project
- If the conversation is mostly routine coding with no reusable knowledge, return an empty list []
- Aim for quality over quantity: 1-3 high-quality fragments is better than 10 low-quality ones

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
