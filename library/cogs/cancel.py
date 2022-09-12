import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot

COG_NAME = "cancel"

class Cancel(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Cancel an ongoing task"
    )
    async def command_cancel(
        self,
        interaction: discord.Interaction,
        taskid: int
    ) -> None:
        if self.bot.task_manager.cancel_task(taskid):
            await interaction.response.send_message(f"Task `{taskid}` has been canceled.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Task `{taskid}` is not currently ongoing.", ephemeral=True)

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Cancel(bot))