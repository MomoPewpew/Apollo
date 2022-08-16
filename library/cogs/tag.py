from ast import alias
import discord
from discord import app_commands
from discord.ext.commands import Cog

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
        tag_name: str=""
    ) -> None:
        await self.function_tag(
            interaction,
            tag_name
        )

    async def function_tag(self, interaction, tag_name):
        userID = self.bot.user_manager.get_user_id(interaction.user)

        if tag_name == "":
            self.show_tag_menu(userID)
        elif self.bot.user_manager.has_tag(userID, tag_name):
            self.toggle_tag(userID, tag_name)
            await interaction.response.send_message( f"The tag " + tag_name + " has been toggled.", ephemeral=True)
            self.show_tag_menu(userID)
        else:
            self.bot.user_manager.add_tag_active(userID, tag_name)
            await interaction.response.send_message( f"The tag " + tag_name + " has been added to your user and activated.", ephemeral=True)
            self.show_tag_menu(userID)

    async def show_tag_menu(self, userID):
        pass

    async def toggle_tag(self, userID, tag_name):
        if self.bot.user_manager.has_tag_active(userID, tag_name):
            pass
        else:
            pass

    @Cog.listener()
    async def on_ready(self):
        if not self.bot.ready:
            self.bot.cogs_ready.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Tag(bot))