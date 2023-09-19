import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot
from ..db import db

COG_NAME = "administration"

class administration(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="cancel",
        description = "Cancel an ongoing task"
    )
    @app_commands.describe(
        taskid = "The ID of the task that you want to cancel. If it didn't give you one then it cannot be canceled"
    )
    async def command_cancel(
        self,
        interaction: discord.Interaction,
        taskid: int
    ) -> None:
        if await self.bot.task_manager.cancel_task(taskid):
            await interaction.response.send_message(f"Task `{taskid}` has been canceled.", ephemeral=True)
        else:
            await interaction.response.send_message(f"Task `{taskid}` is not currently ongoing.", ephemeral=True)

    @app_commands.command(
        name="privacy",
        description = "Enable or disable privacy mode. Outputs will be sent to our DM's"
    )
    @app_commands.describe(
        privacy = "True will turn privacy mode on. False will turn privacy mode off."
    )
    async def command_privacy(
        self,
        interaction: discord.Interaction,
        privacy: bool
    ) -> None:
        userID = self.bot.user_manager.get_user_id(interaction.user)
        if privacy:
            db.execute("UPDATE users SET privacy = 1 WHERE UserID = ?",
                userID
            )
            await interaction.response.send_message("Privacy mode has been enabled. Future messages will be sent to your DM's.", ephemeral=True)
        else:
            db.execute("UPDATE users SET privacy = 0 WHERE UserID = ?",
                userID
            )
            await interaction.response.send_message("Privacy mode has been disabled.", ephemeral=True)

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(administration(bot))