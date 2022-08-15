from ast import alias
import discord
from discord import app_commands
from discord.ext.commands import Cog
from discord.ext.commands import command

COG_NAME = "tag"

class Tag(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    @app_commands.command(
        name="tag",
        description = "Add or toggle tags on yourself to keep track of what you are currently working on."
    )
    async def command_tag(
        self, interaction: discord.Interaction,
        tagname: str
    ) -> None:
        await interaction.response.send_message( f"Hello!")

    def has_tag(self, user):
        if self.tags_active(user):
            return True
        elif self.tags_inactive(user):
            return True

    def tags_active(self, user):
        tags = "tag"
        return tags

    def tags_inactive(self, user):
        tags = "tag"
        return tags

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Tag(bot))