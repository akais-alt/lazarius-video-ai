class VoiceAgent:
    """Local TTS adapter. Piper integration will be added next."""

    async def synthesize(self, text: str, voice: str | None = None):
        return {"status": "pending", "text": text, "voice": voice}
