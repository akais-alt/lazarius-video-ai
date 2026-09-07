from __future__ import annotations

import re


def build_identity_lock(description: str | None, style: str) -> str:
    if not description:
        return ""
    text = re.sub(r"\s+", " ", description).strip()
    if not text:
        return ""
    return (
        "CHARACTER IDENTITY LOCK: preserve exactly the same character across every scene. "
        f"Character: {text}. Style: {style}. "
        "Keep face, hair, age, skin tone, body proportions, clothing palette and distinctive accessories consistent. "
        "Never redesign or replace the character."
    )
