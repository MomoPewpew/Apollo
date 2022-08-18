import discord
from discord import app_commands
from discord.ext.commands import Cog

COG_NAME = "dream"

class Dream(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Turn a text prompt into an image with Stable Diffusion"
    )
    async def command_dream(
        self, interaction: discord.Interaction,
        prompt: str=""
    ) -> None:
        await self.function_dream(
            interaction,
            prompt
        )

    async def function_dream(self, interaction: discord.Interaction, prompt: str) -> None:
        return

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Dream(bot))