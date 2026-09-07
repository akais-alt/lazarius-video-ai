from __future__ import annotations
import re

def build_character_lock(description: str | None, style: str) -> str:
    if not description:
        return ""
    text = re.sub(r"\s+", " ", description).strip()
    return (f"CHARACTER LOCK: {text}. Keep the same face, hair, age, skin tone, body proportions, clothing colors and distinctive accessories in every scene. Visual style: {style}. Never redesign or replace the character.") if text else ""
