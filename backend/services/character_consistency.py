from __future__ import annotations

import re


class CharacterConsistencyService:
    """Builds a compact identity lock that is injected into every scene prompt."""

    def build_identity_lock(self, character_description: str | None, style: str) -> str:
        if not character_description:
            return ""
        cleaned = re.sub(r"\s+", " ", character_description).strip()
        if not cleaned:
            return ""
        return (
            "CHARACTER IDENTITY LOCK: Keep the same character identity in every scene. "
            f"Reference description: {cleaned}. "
            f"Visual style: {style}. Preserve face, hair, age, body proportions, clothing colors and distinctive accessories. "
            "Do not redesign, age, recolor, or replace the character between scenes."
        )

    def enrich_prompt(self, prompt: str, identity_lock: str) -> str:
        if not identity_lock:
            return prompt
        return f"{identity_lock}\nSCENE DIRECTION: {prompt}"
