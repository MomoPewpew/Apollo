from typing import Any
from ..db import db
from .. import bot
from discord.ui import Button
import discord

class Prompt_manager(object):
    def __init__(self, bot: bot) -> None:
        self.bot = bot

    async def add_prompt_with_revoke_button(self, interaction: discord.Interaction, promptType: str, promptString: str, userID: int) -> None:
        promptID = db.record("SELECT MAX(promptID) FROM prompts") + 1
        promptTags = self.bot.user_manager.get_tags_active_csv(userID)

        self.add_prompt(promptType, promptString, userID)

        returnString = "The following prompt will be processed: ```" + promptString + "```"
        if (promptTags == ","):
            returnStrings += "\nThis prompt was saved to your user but you had no active tags."
        else:
            returnStrings += "\nThis prompt was saved to your user under the tags ```" + promptTags[1:-1] + "```"
        
        returnString += "\nIf you would like to delete this prompt from your history then press the delete button."

        button = Button(self, promptID)

        await interaction.response.send_message(content=returnString, button=button, ephemeral = True)

    def add_prompt(self, promptType: str, promptString: str, userID: int) -> None:
        promptTags = self.bot.user_manager.get_tags_active_csv(userID)

        db.execute("INSERT INTO prompts (promptType, promptString, userID, promptTags) VALUES (?, ?, ?, ?)",
            promptType,
            promptString,
            userID,
            promptTags,
        )

    def remove_prompt(self, promptID: int) -> None:
        db.execute("DELETE FROM prompts WHERE promptID = ?",
            promptID
        )

    def get_prompts(self, userID: int, tag_name: str) -> list[str]:
        return db.record("SELECT promptString FROM prompts WHERE userID = ? AND promptTags LIKE ?",
            userID,
            "%," + tag_name + ",%",
        )

class Delete_button(Button):
    def __init__(self, prompt_manager: Prompt_manager, promptID: int):
        super().__init__(label="Delete", style=discord.ButtonStyle.red)
        self.prompt_manager = prompt_manager
        self.promptID = promptID
    async def callback(self, interaction: discord.Interaction) -> Any:
        self.prompt_manager.remove_prompt(self.promptID)
        self.disabled = True
        interaction.response.send_message(content="This prompt has been deleted.")