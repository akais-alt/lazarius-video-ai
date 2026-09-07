from agents.director_agent import DirectorAgent
from agents.script_agent import ScriptAgent
from agents.storyboard_agent import StoryboardAgent
from agents.prompt_agent import PromptAgent
from services.character_consistency import CharacterConsistencyService
from services.media_pipeline import MediaPipeline


class PipelineService:
    def __init__(self):
        self.director = DirectorAgent()
        self.script = ScriptAgent()
        self.storyboard = StoryboardAgent()
        self.prompts = PromptAgent()
        self.character = CharacterConsistencyService()
        self.media = MediaPipeline()

    async def plan(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        language: str,
        style: str,
        character_description: str | None = None,
    ):
        plan = self.director.build_plan(prompt, duration, aspect_ratio, language)
        script = self.script.generate(prompt, duration, language)
        storyboard = self.storyboard.build(script)
        identity_lock = self.character.build_identity_lock(character_description, style)
        visual_prompts = [
            self.character.enrich_prompt(
                self.prompts.build_video_prompt(scene, style),
                identity_lock,
            )
            for scene in storyboard
        ]

        enriched_storyboard = []
        for index, scene in enumerate(storyboard):
            item = dict(scene)
            item["visual_prompt"] = visual_prompts[index]
            enriched_storyboard.append(item)

        return {
            "plan": plan,
            "script": script,
            "storyboard": enriched_storyboard,
            "visual_prompts": visual_prompts,
            "character": {
                "enabled": bool(identity_lock),
                "description": character_description,
                "identity_lock": identity_lock,
            },
        }

    async def execute(
        self,
        prompt: str,
        duration: int,
        aspect_ratio: str,
        language: str,
        style: str,
        mode: str = "cloud",
        quality: str = "720p",
        image_url: str | None = None,
        character_description: str | None = None,
        chain_scenes: bool = False,
        progress=None,
    ):
        progress = progress or (lambda _p, _s: None)
        plan = await self.plan(
            prompt,
            duration,
            aspect_ratio,
            language,
            style,
            character_description,
        )
        progress(8, "planning")
        return await self.media.run(plan, {
            "prompt": prompt,
            "duration": duration,
            "aspect_ratio": aspect_ratio,
            "language": language,
            "style": style,
            "mode": mode,
            "quality": quality,
            "image_url": image_url,
            "character_description": character_description,
            "chain_scenes": chain_scenes,
        }, progress)
