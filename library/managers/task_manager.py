import math
import os
import time
from typing import Any, Union
from ..db import db
from datetime import datetime
from .. import bot
import discord
from discord.ui import Button
from . import prompt_manager
import ciso8601

class Task_manager(object):
    def __init__(self, bot: bot) -> None:
        self.bot = bot

    async def respond(self, interaction: discord.Interaction, promptType: str, promptString: str, queue_estimate: int) -> None:
        if db.field("SELECT taskID FROM tasks WHERE taskID = 1") == None:
            taskID = 1
        else:
            taskID = db.field("SELECT MAX(taskID) FROM tasks") + 1

        if self.bot.instance_manager.all_instances_stopping():
            returnString = f"All instances are currently cooling down, so task `{taskID}` will be processed in a couple of minutes."
        else:
            mins = math.ceil(queue_estimate / 60)
            if mins > 1: append = "s"
            else: append = ""
            returnString = f"Task `{taskID}` will be processed and should be done in `{mins} minute{append}`."

        if (promptType is not None and promptString is not None):
            userID = self.bot.user_manager.get_user_id(interaction.user)

            promptID = db.field("SELECT MAX(promptID) FROM prompts") + 1
            promptTags = self.bot.user_manager.get_tags_active_csv(userID)

            self.bot.prompt_manager.add_prompt(promptType, promptString, userID)

            if (promptTags == ","):
                returnStrings += f"\nThe prompt \"{promptString}\" was saved to your user but you had no active tags."
            else:
                returnStrings += f"\nThe prompt \"{promptString}\" was saved to your user under the tags `" + promptTags[1:-1] + "`"
            
            returnString += "\nIf you would like to delete this prompt from your history then press the delete button."

            button = Delete_button(self.bot.prompt_manager, promptID)

            await interaction.response.send_message(content=returnString, button=button, ephemeral = True)
        else:
            await interaction.response.send_message(content=returnString, ephemeral = True)

    async def start_task_backlog(self):
        db.execute("UPDATE tasks SET server = NULL, timeSent = NULL WHERE timeReceived IS NULL")
        taskIDs = db.column("SELECT taskID FROM tasks WHERE timeSent is NULL")
        if len(taskIDs) > 0:
            print("A task backlog has been found. Begin processing...")
            index, boot_new = await self.bot.instance_manager.get_most_available_instance()

            if boot_new:
                await self.bot.instance_manager.start_ec2(index)

            await self.task_loop(index)

    async def add_task(self, receiveType: str, userID: int, channelID: int, instructions: str, estimatedTime: int, boot_new: bool) -> None:
        db.execute("INSERT INTO tasks (receiveType, userID, channelID, instructions, estimatedTime) VALUES (?, ?, ?, ?, ?)",
            receiveType,
            userID,
            channelID,
            instructions,
            estimatedTime
        )

        if boot_new:
            index = self.bot.instance_manager.get_random_instance()
            if index >= 0:
                await self.bot.instance_manager.start_ec2(index)
                await self.task_loop(index)
            else:
                print("Apollo tried to start a new instance even though none was available. Please reach out to a developer.")
        else:
            index = self.bot.instance_manager.get_available_instance()
            if index >= 0:
                await self.task_loop(index)

    async def simulate_server_assignment(self) -> Union[int, bool]:
        ##This function does not actually assign a server. It simply tries to predict what server will be handling the task, how long this will take, and it decides whether a new server will need to be booted
        boot_estimate = 45
        boot_new = False
        await self.bot.instance_manager.update_instance_statuses()

        if self.bot.instance_manager.must_boot():
            queue_estimate = boot_estimate
            boot_new = True

        queue_estimate = -1

        queue_estimates = self.get_queue_estimates()

        if len(self.bot.instance_manager.get_active_list()) < 1:
            for estimate in queue_estimates:
                queue_estimate += estimate
        else:
            for index in self.bot.instance_manager.get_active_list():
                if queue_estimate < queue_estimates[index] or queue_estimate == -1:
                    if self.bot.instance_manager.is_instance_booting(index):
                        queue_estimate += boot_estimate
                    queue_estimate += queue_estimates[index]

        if (queue_estimate == -1 or queue_estimate > 180) and self.bot.instance_manager.should_boot():
            return boot_estimate, True

        return queue_estimate, boot_new

    def get_queue_estimates(self) -> list[int]:
        estimatedTimes = db.column("SELECT estimatedTime FROM tasks WHERE timeReceived is NULL")
        servers = db.column("SELECT server FROM tasks WHERE timeReceived is NULL")
        timeSents = db.column("SELECT timeSent FROM tasks WHERE timeReceived is NULL")

        queueTimes = []
        estimatedTimesRemaining = []

        for append in range(self.bot.instance_manager.get_total_instances()):
            queueTimes.append(0)

        if len(servers) > 0:
            for i in range(len(servers)):
                if servers[i] is not None:
                    id = servers[i]
                    if self.bot.instance_manager.is_instance_listed(id):
                        index = self.bot.instance_manager.get_instance_index(id)

                        queueTimes[index] += max((estimatedTimes[i] - int(datetime.utcnow().timestamp() - time.mktime(ciso8601.parse_datetime(timeSents[i]).timetuple()))), 2)
                else:
                    estimatedTimesRemaining.append(estimatedTimes[i])
        else:
            for estimatedTime in estimatedTimes:
                estimatedTimesRemaining.append(estimatedTime)

        i = 0
        for taskTime in estimatedTimesRemaining:
            if len(self.bot.instance_manager.get_active_list()) < 1:
                queueTimes[0] += taskTime
            else:
                timeTemp = -1
                for index in self.bot.instance_manager.get_active_list():
                    if queueTimes[index] < timeTemp or timeTemp == -1:
                        timeTemp = queueTimes[index]
                        i = index
                
                queueTimes[i] += taskTime

        return queueTimes

    async def task_loop(self, index: int) -> None:
        taskIDs = db.column("SELECT taskID FROM tasks WHERE timeSent is NULL")
        if len(taskIDs) < 1:
            self.bot.instance_manager.instance_statuses[index] = "available"
            return
        
        taskID = taskIDs[0]
        self.bot.instance_manager.instance_statuses[index] = "busy"

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        db.execute("UPDATE tasks SET server = ?, timeSent = ? WHERE taskID = ?",
            self.bot.instance_manager.get_instance_id(index),
            datetime.utcnow(),
            taskID
        )

        await self.bot.instance_manager.send_command(index, instructions)

        await self.receive_task_output(index, taskID)

        await self.task_loop(index)

    def send_idle_work(self, index: int) -> None:
        return ##TODO: Make this

    async def receive_task_output(self, index: int, taskID: int) -> None:
        await self.bot.instance_manager.download_output(index)

        receiveType, userID, channelID = db.record("SELECT receiveType, userID, channelID FROM tasks WHERE taskID = ?",
            taskID
        )

        db.execute("UPDATE tasks SET timeReceived = ? WHERE taskID = ?",
            datetime.utcnow(),
            taskID
        )

        path = os.path.join("./out/", f"instance_{index}")

        if not os.path.exists(path):
            print(f"The corresponding output folder for instance {index} does not exist.")
            return

        fileCount = 0
        file_path = ""
        for filename in os.listdir(path):
            file_path_temp = os.path.join(path, filename)
            if os.path.isfile(file_path_temp):
                file_path = file_path_temp
                file_name = filename
                fileCount += 1

        if fileCount != 1:
            await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Something went wrong with task {taskID}")
            db.execute("UPDATE tasks SET output = ? WHERE taskID = ?",
                "Error",
                taskID
            )
            return

        embed, file = await eval('self.receive_' + receiveType + '(taskID, file_path, file_name)')

        if file == None:
            await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Here is the output for task `{taskID}`",embed=embed)
        else:
            message = await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Here is the output for task `{taskID}`",embed=embed, file=file)

            db.execute("UPDATE tasks SET output = ? WHERE taskID = ?",
                message.embeds[0].image.url,
                taskID
            )

    async def receive_image(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File]:
        embed = discord.Embed(title="Image", description=f"Task `{taskID}`", color=0x00ff00)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        return embed, file
    
    async def receive_prompt(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File]:
        ##TODO: Read file
        output_txt = ""

        embed = discord.Embed(title="Image", description=f"Task {taskID}", color=0x00ff00)

        db.execute("UPDATE tasks SET output = ? WHERE taskID = ?",
            output_txt,
            taskID
        )

        return embed, None

class Delete_button(Button):
    def __init__(self, prompt_manager: prompt_manager.Prompt_manager, promptID: int):
        super().__init__(label="Delete", style=discord.ButtonStyle.red)
        self.prompt_manager = prompt_manager
        self.promptID = promptID
    async def callback(self, interaction: discord.Interaction) -> Any:
        self.prompt_manager.remove_prompt(self.promptID)
        self.disabled = True
        interaction.response.send_message(content="This prompt has been deleted.")