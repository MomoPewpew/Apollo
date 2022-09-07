from typing import Any, Union
from ..db import db
from datetime import datetime
from .. import bot
import discord
from discord.ui import Button
from . import prompt_manager

class Task_manager(object):
    def __init__(self, bot: bot) -> None:
        self.bot = bot

    async def respond(self, interaction: discord.Interaction, promptType: str, promptString: str, queue_estimate: int) -> None:
        returnString = "Your task will be processed and should be done in " + str(queue_estimate) + " seconds."
        button = None

        if (promptType is not None and promptString is not None):
            userID = self.bot.user_manager.get_user_id(interaction.user)

            promptID = db.record("SELECT MAX(promptID) FROM prompts") + 1
            promptTags = self.bot.user_manager.get_tags_active_csv(userID)

            self.bot.prompt_manager.add_prompt(promptType, promptString, userID)

            if (promptTags == ","):
                returnStrings += f"\nThe prompt \"{promptString}\" was saved to your user but you had no active tags."
            else:
                returnStrings += f"\nThe prompt \"{promptString}\" was saved to your user under the tags ```" + promptTags[1:-1] + "```"
            
            returnString += "\nIf you would like to delete this prompt from your history then press the delete button."

            button = Delete_button(self, promptID)
        
        if button == None:
            await interaction.response.send_message(content=returnString, ephemeral = True)
        else:
            await interaction.response.send_message(content=returnString, button=button, ephemeral = True)

    def add_task(self, receiveType: str, userID: int, channelID: int, instructions: str, estimatedTime: int) -> None:
        db.execute("INSERT INTO tasks (receiveType, userID, channelID, instructions, estimatedTime) VALUES (?, ?, ?, ?, ?)",
            receiveType,
            userID,
            channelID,
            instructions,
            estimatedTime
        )

    def start(self) -> None:
        index = self.bot.instance_manager.get_random_instance()
        if index >= 0:
            self.bot.instance_manager.start_ec2(index)
            self.bot.processing = True
            self.send_first_task(index)
        else:
            print("Apollo tried to start a new instance even though none was available. Please reach out to a developer.")

    def send_first_task(self, index: int) -> None:
        taskID, instructions = db.record("SELECT taskID, instructions FROM tasks WHERE timeReceived is NULL AND taskID=(SELECT MIN(taskID) FROM tasks)")

        if taskID == None:
            return

        db.execute("UPDATE tasks SET server = ?, timeSent = ? WHERE taskID = ?",
            self.bot.instance_manager.get_instance_id(index),
            datetime.utcnow(),
            taskID
        )

        self.bot.instance_manager.send_command(index, instructions)

        self.receive_task_output(taskID)

        self.send_first_task(index)

    def receive_task_output(self, taskID:int) -> None:
        ##TODO: Refine this
        outputURL = ""

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

    def send_idle_work(self, index: int) -> None:
        return ##TODO: Make this
    
    def simulate_server_assignment(self) -> Union[int, bool]:
        ##This function does not actually assign a server. It simply tries to predict what server will be handling the task, how long this will take, and it decides whether a new server will need to be booted
        boot_new = False
        queue_estimate = -1

        queue_estimates = self.get_queue_estimates()
        
        for instance in self.bot.instance_manager.active_instances:
            if queue_estimate < queue_estimates[instance] or queue_estimate == -1:
                queue_estimate = queue_estimates[instance]

        if (queue_estimate == -1 or queue_estimate > 60) and self.bot.instance_manager.get_total_active() < self.bot.instance_manager.get_total_instances():
            queue_estimate = 60
            boot_new = True

        return queue_estimate, boot_new

    def get_queue_estimates(self) -> list[int]:
        estimatedTimes = db.record("SELECT estimatedTime FROM tasks WHERE timeReceived is NULL")
        servers = db.record("SELECT server FROM tasks WHERE timeReceived is NULL")
        timeSents = db.record("SELECT timeSent FROM tasks WHERE timeReceived is NULL")

        queueTimes = []
        estimatedTimesRemaining = []

        for append in range(self.bot.instance_manager.get_total_instances() + 1):
            queueTimes.append(0)

        if servers != None:
            for i in range(len(servers)):
                id = servers[i]
                if id != None:
                    if self.bot.instance_manager.is_instance_listed(id):
                        index = self.bot.instance_manager.get_instance_index(id)

                        queueTimes[index] += estimatedTimes[i] - max(int(datetime.utcnow().timestamp() - timeSents[i].timestamp()), 2)
                else:
                    estimatedTimesRemaining.append(estimatedTimes[i])

            i = 0
            active_instances = self.bot.instance_manager.active_instances
            for taskTime in estimatedTimesRemaining:
                timeTemp = -1
                for index in active_instances:
                    if queueTimes[index] == 0: queueTimes[index] = 0
                    if queueTimes[index] < timeTemp or timeTemp == -1:
                        timeTemp = queueTimes[index]
                        i = index
                
                queueTimes[i] += taskTime

        return queueTimes

class Delete_button(Button):
    def __init__(self, prompt_manager: prompt_manager.Prompt_manager, promptID: int):
        super().__init__(label="Delete", style=discord.ButtonStyle.red)
        self.prompt_manager = prompt_manager
        self.promptID = promptID
    async def callback(self, interaction: discord.Interaction) -> Any:
        self.prompt_manager.remove_prompt(self.promptID)
        self.disabled = True
        interaction.response.send_message(content="This prompt has been deleted.")