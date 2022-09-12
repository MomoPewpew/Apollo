from code import interact
import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot

COG_NAME = "arcane"

class Arcane(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Convert an image at the provided URL into the animation style of Arcane"
    )
    async def command_arcane(
        self,
        interaction: discord.Interaction,
        url: str
    ) -> None:
        await self.function_arcane(
            interaction,
            url
        )

    async def function_arcane(self, interaction: discord.Interaction, url: str) -> None:
        queue_estimate, boot_new = await self.bot.task_manager.simulate_server_assignment()

        estimated_time = 20

        instructions = f"python3 /home/ubuntu/Daedalus/daedalus.py --function=arcanegan --sourceURL={url}"

        await self.bot.task_manager.respond(interaction, None, None, queue_estimate + estimated_time)

        await self.bot.task_manager.add_task("image", interaction.user.id, interaction.channel.id, instructions, estimated_time, boot_new)

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Arcane(bot))