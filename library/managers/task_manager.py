from ..db import db

class Task_manager(object):
    def __init__(self, bot) -> None:
        self.bot = bot

    def add_task(self, receiveType: str, userID: int, channelID: int, instructions: str, estimatedTime: int) -> None:
        db.execute("INSERT OR INTO tasks (receiveType, userID, channelID, instructions) VALUES (?, ?, ?, ?, ?)",
            receiveType,
            userID,
            channelID,
            instructions,
            estimatedTime
        )

        if not self.bot.working:
            self.boot_gpu_server
    
    def boot_gpu_server():
        pass