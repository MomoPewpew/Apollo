from ast import alias
from turtle import end_fill
import discord
from discord import app_commands
from discord.ext.commands import Cog
import re

COG_NAME = "tag"

class Tag(Cog):
    def __init__(self, bot) -> None:
        self.bot = bot
    
    @app_commands.command(
        name=COG_NAME,
        description = "Add or toggle tags on yourself to keep track of what you are currently working on."
    )
    async def command_tag(
        self, interaction: discord.Interaction,
        tag_name: str=""
    ) -> None:
        await self.function_tag(
            interaction,
            tag_name
        )

    async def function_tag(self, interaction, tag_name):
        userID = self.bot.user_manager.get_user_id(interaction.user)

        if tag_name == "":
            await interaction.response.send_message( f"This will show the tag menu soon.", ephemeral=True)
            await self.show_tag_menu(userID)
            return
        elif not re.match(r"^[a-zA-Z0-9_]*$", tag_name):
            await interaction.response.send_message( f"Tag names may only include alphanumeric characters and underscores. Such as example_tag_2", ephemeral=True)
            return

        if self.bot.user_manager.has_tag(userID, tag_name):
            await self.toggle_tag(interaction, userID, tag_name)
            await self.show_tag_menu(userID)
        else:
            self.bot.user_manager.add_tag_active(userID, tag_name)
            await interaction.response.send_message( f"The tag " + tag_name + " has been added to your user and activated.", ephemeral=True)
            await self.show_tag_menu(userID)

    async def show_tag_menu(self, userID):
        pass

    async def toggle_tag(self, interaction, userID, tag_name):
        if self.bot.user_manager.has_tag_active(userID, tag_name):
            self.bot.user_manager.remove_tag(userID, tag_name)
            self.bot.user_manager.add_tag_inactive(userID, tag_name)
            await interaction.response.send_message( f"The tag " + tag_name + " has been turned off.", ephemeral=True)
        else:
            self.bot.user_manager.remove_tag(userID, tag_name)
            self.bot.user_manager.add_tag_active(userID, tag_name)
            await interaction.response.send_message( f"The tag " + tag_name + " has been turned on.", ephemeral=True)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Tag(bot))