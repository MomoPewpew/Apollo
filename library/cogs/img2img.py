import random
import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot

COG_NAME = "img2img"

class img2img(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Convert a text prompt into an image"
    )
    async def command_img2img(
        self,
        interaction: discord.Interaction,
        prompt: str,
        init_img_url: str,
        seed: int = None,
        scale: float = 7.5,
        strength: float = 0.75,
        steps: int = 50,
        batch: bool = False
    ) -> None:
        await self.function_img2img(
            interaction,
            prompt,
            init_img_url,
            seed,
            scale,
            strength,
            steps,
            batch
        )

    async def function_img2img(self,
        interaction: discord.Interaction,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int,
        batch: bool
    ) -> None:
        seed = int(random.randrange(4294966294)) if seed is None else seed
        strength = 0.0 if strength < 0.0 else 1.0 if strength > 1.0 else strength
        if batch:
            await self.bot.task_manager.task_command_main(interaction, 180, "txt2img", prompt, "stablediffusion_img2img_single", f"python3 /home/ubuntu/Daedalus/daedalus.py --function img2imgSingle --args \"#arg#prompt #qt#{prompt}#qt# #arg#init_img {init_img_url} #arg#seed {seed} #arg#scale {scale} #arg#strength {strength} #arg#ddim_steps {steps}\"")
        else:
            await self.bot.task_manager.task_command_main(interaction, 180, "txt2img", prompt, "stablediffusion_img2img_single", f"python3 /home/ubuntu/Daedalus/daedalus.py --function img2imgSingle --sourceURL {init_img_url} --args \"#arg#prompt #qt#{prompt}#qt# #arg#seed {seed} #arg#scale {scale} #arg#strength {strength} #arg#ddim_steps {steps}\"")

    async def function_img2img_variations(self,
        interaction: discord.Interaction,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int,
    ) -> None:
        await self.bot.task_manager.task_command_main(interaction, 180, "txt2img", prompt, "stablediffusion_img2img_single", f"python3 /home/ubuntu/Daedalus/daedalus.py --function img2imgSingle --args \"#arg#prompt #qt#{prompt}#qt# #arg#init_img {init_img_url} #arg#seed {seed} #arg#scale {scale} #arg#strength {strength} #arg#ddim_steps {steps}\"")

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(img2img(bot))