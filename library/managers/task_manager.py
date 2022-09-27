import math
import os
import time
from typing import Union
from urllib.request import urlopen
from ..db import db
from datetime import datetime
from .. import bot
import discord
import ciso8601
from .output_manager import Output_manager
from ..cogs import tag

class Task_manager(object):
    def __init__(self, bot: bot) -> None:
        self.bot = bot
        self.output_manager = Output_manager(bot)

    async def task_command_main(self, interaction: discord.Interaction, estimated_time: int, promptType: str, promptString: int, receiveType: str, instructions: str) -> None:
        if "&&" in instructions or "||" in instructions or ";" in instructions:
            await interaction.response.send_message("A potential code injection was detected in the task that you added so it was canceled. Please ensure that none of your instructions include the symbols `&& or || or ;`")
            return

        queue_estimate, boot_new = await self.simulate_server_assignment()

        await self.respond(interaction, promptType, promptString, queue_estimate + estimated_time)

        await self.add_task(receiveType, interaction.user.id, interaction.channel.id, instructions, estimated_time, boot_new)

    async def respond(self, interaction: discord.Interaction, promptType: str, promptString: str, queue_estimate: int) -> None:
        if db.field("SELECT taskID FROM tasks WHERE taskID = 1") == None:
            taskID = 1
        else:
            taskID = db.field("SELECT MAX(taskID) FROM tasks") + 1

        if self.bot.instance_manager.all_instances_stopping():
            returnString1 = f"All instances are currently cooling down, so task `{taskID}` will be processed in a couple of minutes."
        else:
            mins = math.ceil(queue_estimate / 60)
            if mins > 1: append = "s"
            else: append = ""
            returnString1 = f"Task `{taskID}` will be processed and should be done in `{mins} minute{append}`."

        returnString = returnString1

        userID = self.bot.user_manager.get_user_id(interaction.user)
        if (promptType is not None and promptString is not None and not self.bot.user_manager.is_user_privacy_mode(userID)):
            promptTags = self.bot.user_manager.get_tags_active_csv(userID)
            if promptID := self.bot.prompt_manager.get_promptID(userID, promptString) is not None:
                tagsOld = db.field("SELECT promptTags FROM prompts WHERE promptID = ?",
                    promptID
                )

                if tagsOld != promptTags:
                    db.execute("UPDATE prompts SET promptTags = ? WHERE promptID = ?",
                        promptTags,
                        promptID
                    )
                    returnString += f"\nThe prompt `{promptString}` has been updated to match the tags `" + promptTags[1:-1] + "`"
                
                await interaction.response.send_message(content=returnString, ephemeral=True)
            else:
                if db.field("SELECT promptID FROM prompts WHERE promptID = 1") == None:
                    promptID = 1
                else:
                    promptID = db.field("SELECT MAX(promptID) FROM prompts") + 1

                self.bot.prompt_manager.add_prompt(promptType, promptString, userID)

                if (promptTags == ","):
                    returnString += f"\nThe prompt `{promptString}` was saved to your history but you had no active tags."
                else:
                    returnString += f"\nThe prompt `{promptString}` was saved to your history under the tags `" + promptTags[1:-1] + "`"
                
                returnString += "\nIf you would like to delete this prompt from your history then press the `Forget` button."

                await interaction.response.send_message(content=returnString, view=tag.View_forget_prompt(self.bot.prompt_manager, promptID, returnString1), ephemeral=True)
        else:
            await interaction.response.send_message(content=returnString, ephemeral=True)

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
    
    async def cancel_task(self, taskID: int) -> bool:
        taskID, server = db.record("SELECT taskID, server FROM tasks WHERE taskID = ? AND timeReceived is NULL",
            taskID
        )
        if taskID == None: return False

        if server == None:
            db.execute("UPDATE tasks SET server = ?, timeSent = ?, timeReceived = ?, output = ? WHERE taskID = ?",
                "None",
                datetime.utcnow(),
                datetime.utcnow(),
                "Canceled",
                taskID
            )
        else:
            db.execute("UPDATE tasks SET timeReceived = ?, output = ? WHERE taskID = ?",
                datetime.utcnow(),
                "Canceled",
                taskID
            )

        return True

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

    async def receive_task_output(self, index: int, taskID: int) -> None:
        await self.bot.instance_manager.download_output(index)

        receiveType, userID, channelID, output = db.record("SELECT receiveType, userID, channelID, output FROM tasks WHERE taskID = ?",
            taskID
        )

        if output == "Canceled": return

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
            await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Something went wrong with task {taskID}.")
            db.execute("UPDATE tasks SET output = ? WHERE taskID = ?",
                "Error",
                taskID
            )
            return
        
        embed, file, view = await eval('self.output_manager.receive_' + receiveType + '(taskID, file_path, file_name)')

        user: discord.User = self.bot.get_user(int(userID))
        userIDTemp = self.bot.user_manager.get_user_id(user)

        if (self.bot.user_manager.is_user_privacy_mode(userIDTemp)):
            #TODO: Check to see if the file check is actually neccesary?
            if file == None:
                await user.send(f"Here is the output for task `{taskID}`.",embed=embed)
            else:
                await user.send(f"Here is the output for task `{taskID}`.",embed=embed, file=file)
            
            db.execute("UPDATE tasks SET instructions = 'Privacy', output = 'Privacy' WHERE taskID = ?",
                taskID
            )
        else:
            if file == None:
                await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Here is the output for task `{taskID}`.",embed=embed, view=view)
            else:
                message = await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Here is the output for task `{taskID}`.",embed=embed, file=file, view=view)

                image_url = message.embeds[0].image.url

                db.execute("UPDATE tasks SET output = ? WHERE taskID = ?",
                    image_url,
                    taskID
                )

                for child in view.children:
                    if (hasattr(child, "img_url")):
                        child.img_url = image_url

    def is_url_image(self, url) -> bool:
        ##urllib is not allowed to access discord attachments, so we just check the url for those
        if "cdn.discordapp.com/attachments/" in url and (".png" in url or ".jpeg" in url or ".jpg" in url or ".bmp" in url):
            return True

        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/bmp")
        site = urlopen(url)
        meta = site.info()  # get header of the http request
        if meta["content-type"] in image_formats:  # check if the content-type is a image
            return True
        else:
            return False