import discord
from discord import app_commands
from discord.ext.commands import Cog
from discord.ui import Button, View
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
            tag_name.lower()
        )

    async def function_tag(self, interaction, tag_name):
        userID = self.bot.user_manager.get_user_id(interaction.user)

        if tag_name == "":
            await self.show_tag_menu(interaction, userID, f"These are your tags. Green tags are active, red tags are not. Click the tag name to toggle it, and the X to delete a tag.")
        elif not re.match(r"^[a-zA-Z0-9_]*$", tag_name):
            await interaction.response.send_message( f"Tag names may only include alphanumeric characters and underscores. Such as example_tag_2", ephemeral=True)
        elif self.bot.user_manager.has_tag_active(userID, tag_name):
            self.bot.user_manager.remove_tag(userID, tag_name)
            self.bot.user_manager.add_tag_inactive(userID, tag_name)
            await self.show_tag_menu(interaction, userID, f"The tag " + tag_name + " has been turned off.")
        elif self.bot.user_manager.has_tag_inactive(userID, tag_name):
            self.bot.user_manager.remove_tag(userID, tag_name)
            self.bot.user_manager.add_tag_active(userID, tag_name)
            await self.show_tag_menu(interaction, userID, f"The tag " + tag_name + " has been turned on.")
        else:
            self.bot.user_manager.add_tag_active(userID, tag_name)
            await self.show_tag_menu(interaction, userID, f"The tag " + tag_name + " has been added to your user and turned on.")

    async def show_tag_menu(self, interaction, userID, description):
        activeTags = self.bot.user_manager.get_tags_active(userID)
        tags = sorted(activeTags + self.bot.user_manager.get_tags_inactive(userID), key=str.lower)

        view = View()
        i = 0
        for tag in tags:
            if tag != "":
                style=discord.ButtonStyle.red
                if tag in activeTags: style=discord.ButtonStyle.green
                button = Button(label=tag, style=style, row=i)
                view.add_item(button)
                button2 = Button(label="X", style=style, row=i)
                view.add_item(button2)
                i += 1

        await interaction.response.send_message(description, view=view, ephemeral=True)

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Tag(bot))