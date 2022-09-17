import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot

COG_NAME = "style_arcane"

class Style_arcane(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Convert an image at the provided URL into the animation style of Arcane"
    )
    async def command_style_arcane(
        self,
        interaction: discord.Interaction,
        url: str
    ) -> None:
        await self.function_style_arcane(
            interaction,
            url
        )

    async def function_arcane(self, interaction: discord.Interaction, url: str) -> None:
        await self.bot.task_manager.task_command_main(interaction, 20, "image", f"python3 /home/ubuntu/Daedalus/daedalus.py --function arcanegan --sourceURL {url}")

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Style_arcane(bot))