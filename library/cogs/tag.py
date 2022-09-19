import discord
from discord.ui import Select, View
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot

import re

COG_NAME = "tag"

class Tag(Cog):
    def __init__(self, bot: bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Add or toggle tags on yourself to help Apollo learn what styles you like for your projects."
    )
    async def command_tag(
        self, interaction: discord.Interaction,
        tag_name: str=""
    ) -> None:
        await self.function_tag(
            interaction,
            tag_name.lower()
        )

    async def function_tag(self, interaction: discord.Interaction, tag_name: str) -> None:
        userID = self.bot.user_manager.get_user_id(interaction.user)

        if tag_name == "":
            if self.bot.user_manager.get_tags_total(userID) < 1:
                await interaction.response.send_message("You have no tags. Use \"/tag <tag_name>\" to add your first tag.", ephemeral=True)
                return

            await self.show_tag_menu(interaction, userID, "These are your tags. Checked tags are currently active.")
        elif not re.match(r"^[a-zA-Z0-9_]*$", tag_name):
            await self.show_tag_menu(interaction, userID, "Tag names may only include alphanumeric characters and underscores. Such as example_tag_2")
        elif self.bot.user_manager.has_tag(userID, tag_name):
            await self.toggle_tag(interaction, userID, tag_name)
        else:
            if self.bot.user_manager.get_tags_total(userID) < 25:
                self.bot.user_manager.add_tag_active(userID, tag_name)
                await self.show_tag_menu(interaction, userID, f"The tag {tag_name} has been added to your user and turned on.")
            else:
                await self.show_tag_menu(interaction, userID, "You may not have more than 25 tags. Please use /tagdel to make room. Your history with the deleted tag will not be deleted and you can add it back later if you want.")

    async def toggle_tag(self, interaction: discord.Interaction, userID: int, tag_name: str) -> None:
        if self.bot.user_manager.has_tag_active(userID, tag_name):
            self.bot.user_manager.remove_tag(userID, tag_name)
            self.bot.user_manager.add_tag_inactive(userID, tag_name)
            await self.show_tag_menu(interaction, userID, f"The tag {tag_name} has been turned off.")
        elif self.bot.user_manager.has_tag_inactive(userID, tag_name):
            self.bot.user_manager.remove_tag(userID, tag_name)
            self.bot.user_manager.add_tag_active(userID, tag_name)
            await self.show_tag_menu(interaction, userID, f"The tag {tag_name} has been turned on.")

    async def show_tag_menu(self, interaction: discord.Interaction, userID: int, description: str) -> None:
        activeTags = self.bot.user_manager.get_tags_active(userID)
        tags = sorted(activeTags + self.bot.user_manager.get_tags_inactive(userID), key=str.lower)

        view = View_tag(self.bot, tags, activeTags)

        await interaction.response.send_message(description, ephemeral=True, view=view)

    @app_commands.command(
        name="tagdel",
        description = "Delete a tag from your user."
    )
    async def command_tagdel(
        self, interaction: discord.Interaction,
        tag_name: str
    ) -> None:
        await self.function_tagdel(
            interaction,
            tag_name.lower()
        )
    
    async def function_tagdel(self, interaction: discord.Interaction, tag_name: str) -> None:
        userID = self.bot.user_manager.get_user_id(interaction.user)
        if self.bot.user_manager.has_tag(userID, tag_name):
            self.bot.user_manager.remove_tag(userID, tag_name)
            await self.show_tag_menu(interaction, userID, f"The tag {tag_name} has been deleted from your user.")
        else:
            await interaction.response.send_message(f"You don't have a tag called {tag_name}.", ephemeral=True)

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Tag(bot))

class View_tag(View):
    def __init__(self, bot: bot, tags: list[str], activeTags: list[str]):
        options = []
        default = False
        for tag in tags:
            if tag != "":
                if tag in activeTags:
                    default = True
                else:
                    default = False
                
                options.append(discord.SelectOption(label=tag, default=default))

        select = Select(
            min_values=0,
            max_values=min(len(tags), 25),
            placeholder="You have no active tags",
            options=options,
            row=0
        )

        async def select_callback(interaction: discord.Interaction):
            activeTags = ","
            inactiveTags = ","

            for tag in tags:
                if tag in select.values:
                    activeTags += f"{tag},"
                else:
                    inactiveTags += f"{tag},"
            
            userID = bot.user_manager.get_user_id(interaction.user)
            bot.user_manager.set_tags(userID, activeTags, inactiveTags)

            view = View_tag(bot, tags, select.values)
            
            await interaction.response.edit_message(content="Your tags have been updated.", view=view)

        select.callback = select_callback

        super().__init__()

        self.add_item(select)