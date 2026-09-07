from agents.director_agent import DirectorAgent
from agents.script_agent import ScriptAgent
from agents.storyboard_agent import StoryboardAgent
from agents.prompt_agent import PromptAgent

class PipelineService:
    def __init__(self):
        self.director = DirectorAgent()
        self.script = ScriptAgent()
        self.storyboard = StoryboardAgent()
        self.prompts = PromptAgent()

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
