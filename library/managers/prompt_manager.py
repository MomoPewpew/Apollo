from ..db import db
from .. import bot
import discord

class Prompt_manager(object):
    def __init__(self, bot: bot) -> None:
        self.bot = bot

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
        return db.column("SELECT promptString FROM prompts WHERE userID = ? AND promptTags LIKE ?",
            userID,
            "%," + tag_name + ",%",
        )
    
    def get_promptID(self, userID: int, promptString: str) -> bool:
        return db.field("SELECT promptID FROM prompts WHERE userID = ? AND promptString = ?",
            userID,
            promptString
        )