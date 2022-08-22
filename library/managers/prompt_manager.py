from ..db import db
from .. import bot

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

    def get_prompts(self, userID: int, tag_name: str) -> list[str]:
        return db.record("SELECT promptString FROM prompts WHERE userID = ? AND promptTags LIKE ?",
            userID,
            "%," + tag_name + ",%",
        )