class StoryboardAgent:
    def build(self, script: dict):
        return script.get("scenes", [])
