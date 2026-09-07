class ScriptAgent:
    def generate(self, prompt: str, duration: int, language: str = "fr"):
        return {
            "language": language,
            "duration": duration,
            "title": "",
            "hook": "",
            "narration": "",
            "scenes": [],
        }
