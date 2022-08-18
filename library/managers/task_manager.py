from ..db import db
from datetime import datetime

class Task_manager(object):
    def __init__(self, bot) -> None:
        self.bot = bot

    def add_task(self, receiveType: str, userID: int, channelID: int, instructions: str, estimatedTime: int) -> None:
        if not self.bot.processing:
            server = self.get_random_server()
            ##TODO: Boot server here
            ##TODO: Ensure that we're listening for http communication?
            self.bot.processing = True

        db.execute("INSERT INTO tasks (receiveType, userID, channelID, instructions) VALUES (?, ?, ?, ?, ?)",
            receiveType,
            userID,
            channelID,
            instructions,
            estimatedTime
        )
    
    def get_random_server() -> str:
        return ##TODO: Write this. While we only have 1 GPU server this can just return that server.

    def send_first_task(self, server: str) -> None:
        taskID, instructions = db.record("SELECT taskID, instructions FROM tasks WHERE timeReceived = NULL AND taskID=(SELECT MIN(taskID) FROM tasks)")

        if taskID == None:
            self.send_idle_task(server)
            return

        ##TODO: Send task here

        db.execute("UPDATE tasks SET server = ?, timeSent = ? WHERE taskID = ?",
            server,
            datetime.utcnow(),
            taskID
        )

    def send_idle_work(self, server: str) -> None:
        return ##TODO: Make this
    
    def get_queue_estimate(self) -> int:
        ##When there's more than one server this will need to be rewritten to something more complicated
        ##TODO: Check if this make any sense at all. It's supposed to return it in seconds.
        queue_estimate = db.record("SELECT SUM(estimatedTime) FROM tasks WHERE timeReceived = NULL")
        queue_estimate -= (datetime.utcnow() - db.record("SELECT timeSent FROM tasks WHERE timeReceived = NULL AND NOT timeSent = NULL")[0])
        return queue_estimate

    def receive_task_output(self, server: str, taskID:int, outputURL: str) -> None:
        self.send_first_task(server)

        db.execute("UPDATE tasks SET outputURL = ?, timeReceived = ? WHERE taskID = ?",
            outputURL,
            datetime.utcnow(),
            taskID
        )

        receiveType, userID, channelID = db.record("SELECT receiveType, userID, channelID FROM tasks WHERE taskID = ?",
            taskID
        )

        if receiveType == "image":
            return ##TODO: Send 
