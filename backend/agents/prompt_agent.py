class PromptAgent:
    def build_video_prompt(self, scene: dict, style: str = "cinematic"):
        base = scene.get("visual_prompt", "")
        return f"{base}, {style}, coherent motion, natural camera movement, detailed environment"
