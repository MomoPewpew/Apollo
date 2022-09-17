import random
import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot

COG_NAME = "txt2img"

class txt2img(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Convert a text prompt into an image"
    )
    async def command_txt2img(
        self,
        interaction: discord.Interaction,
        prompt: str,
        height: int = 512,
        width: int = 512,
        seed: int = None,
        scale: float = 7.5,
        steps: int = 50,
        plms: bool = True
    ) -> None:
        await self.function_txt2img(
            interaction,
            prompt,
            height,
            width,
            seed,
            scale,
            steps,
            plms
        )

    async def function_txt2img(self,
        interaction: discord.Interaction,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool
    ) -> None:
        if height %64 != 0 or width %64 != 0:
            await interaction.response.send_message("The height and width must be a multiple of 64", ephemeral=True)

        seed = int(random.randrange(4294967294)) if seed is None else seed

        plmsString = " #arg#plms" if plms else ""

        await self.bot.task_manager.task_command_main(interaction, 180, "text2image", prompt, "stablediffusion", f"python3 /home/ubuntu/Daedalus/daedalus.py --function txt2imgSingle --args \"#arg#prompt #qt#{prompt}#qt# #arg#H {height} #arg#W {width} #arg#seed {seed} #arg#scale {scale} #arg#ddim_steps {steps}{plmsString}\"")

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(txt2img(bot))