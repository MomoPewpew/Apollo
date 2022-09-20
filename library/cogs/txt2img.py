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
        plms: bool = True,
        batch: bool = False
    ) -> None:
        await self.function_txt2img(
            interaction,
            prompt,
            height,
            width,
            seed,
            scale,
            steps,
            plms,
            batch
        )

    async def function_txt2img(self,
        interaction: discord.Interaction,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool,
        batch: bool
    ) -> None:
        if height %64 != 0 or width %64 != 0:
            await interaction.response.send_message(f"The height and width must be a multiple of 64. Your prompt was `{prompt}`", ephemeral=True)
            return

        seed = int(random.randrange(4294966294)) if seed is None else seed

        plmsString = " #arg#plms" if plms else ""
        if batch:
            await self.bot.task_manager.task_command_main(interaction, 240, "txt2img", prompt, "stablediffusion_txt2img_batch", f"python3 /home/ubuntu/Daedalus/daedalus.py --function txt2imgGrid --args \"#arg#prompt #qt#{prompt}#qt# #arg#H {height} #arg#W {width} #arg#seed {seed} #arg#scale {scale}{plmsString}\"")
        else:
            await self.bot.task_manager.task_command_main(interaction, 180, "txt2img", prompt, "stablediffusion_txt2img_single", f"python3 /home/ubuntu/Daedalus/daedalus.py --function txt2imgSingle --args \"#arg#prompt #qt#{prompt}#qt# #arg#H {height} #arg#W {width} #arg#seed {seed} #arg#scale {scale} #arg#ddim_steps {steps}{plmsString}\"")

    async def function_txt2img_variations(self,
        interaction: discord.Interaction,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        plms: bool
    ) -> None:
        plmsString = " #arg#plms" if plms else ""

        await self.bot.task_manager.task_command_main(interaction, 240, "txt2img", prompt, "stablediffusion_txt2img_variations", f"python3 /home/ubuntu/Daedalus/daedalus.py --function txt2imgVariations --args \"#arg#prompt #qt#{prompt}#qt# #arg#H {height} #arg#W {width} #arg#seed {seed}{plmsString}\"")

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(txt2img(bot))