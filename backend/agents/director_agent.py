class DirectorAgent:
    """Orchestrates the video generation pipeline."""

    def build_plan(self, prompt: str, duration: int, aspect_ratio: str, language: str):
        return {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "language": language,
            "steps": ["script", "storyboard", "visuals", "voice", "subtitles", "render"],
        }
