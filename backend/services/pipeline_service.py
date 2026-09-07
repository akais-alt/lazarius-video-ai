from agents.director_agent import DirectorAgent
from agents.script_agent import ScriptAgent
from agents.storyboard_agent import StoryboardAgent
from agents.prompt_agent import PromptAgent
from services.media_pipeline import MediaPipeline


class PipelineService:
    def __init__(self):
        self.director = DirectorAgent()
        self.script = ScriptAgent()
        self.storyboard = StoryboardAgent()
        self.prompts = PromptAgent()
        self.media = MediaPipeline()

    async def plan(self, prompt: str, duration: int, aspect_ratio: str, language: str, style: str):
        plan = self.director.build_plan(prompt, duration, aspect_ratio, language)
        script = self.script.generate(prompt, duration, language)
        storyboard = self.storyboard.build(script)
        visual_prompts = [self.prompts.build_video_prompt(scene, style) for scene in storyboard]
        return {
            "plan": plan,
            "script": script,
            "storyboard": storyboard,
            "visual_prompts": visual_prompts,
        }

    async def execute(self, prompt: str, duration: int, aspect_ratio: str, language: str, style: str, mode: str = "cloud", quality: str = "720p", progress=None):
        progress = progress or (lambda _p, _s: None)
        plan = await self.plan(prompt, duration, aspect_ratio, language, style)
        progress(8, "planning")
        return await self.media.run(plan, {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "language": language,
            "style": style,
            "mode": mode,
            "quality": quality,
        }, progress)
