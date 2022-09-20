from logging import PlaceHolder
import math
import os
import re
import time
from typing import Any, Union
from ..db import db
from datetime import datetime
from .. import bot
import discord
from discord.ui import Button, View
from . import prompt_manager
import ciso8601

class Task_manager(object):
    def __init__(self, bot: bot) -> None:
        self.bot = bot

    async def task_command_main(self, interaction: discord.Interaction, estimated_time: int, promptType: str, promptString: int, receiveType: str, instructions: str) -> None:
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
        if (promptType is not None and promptString is not None):
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

                await interaction.response.send_message(content=returnString, view=View_forget_prompt(self.bot.prompt_manager, promptID, returnString1), ephemeral=True)
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

    def send_idle_work(self, index: int) -> None:
        return ##TODO: Make this

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

        embed, file, view = await eval('self.receive_' + receiveType + '(taskID, file_path, file_name)')

        if file == None:
            await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Here is the output for task `{taskID}`.",embed=embed, view=view)
        else:
            message = await self.bot.get_channel(channelID).send(f"{self.bot.get_user(userID).mention} Here is the output for task `{taskID}`.",embed=embed, file=file, view=view)

            db.execute("UPDATE tasks SET output = ? WHERE taskID = ?",
                message.embeds[0].image.url,
                taskID
            )

    async def receive_image(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Image", description=f"Task `{taskID}`", color=0x00ff00)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        return embed, file, None
    
    async def receive_stablediffusion(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion", color=0x00ff00)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_argument_from_instructions(instructions, "prompt")[4:-5]
        height = int(self.get_argument_from_instructions(instructions, "H"))
        width = int(self.get_argument_from_instructions(instructions, "W"))
        seed = int(self.get_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_argument_from_instructions(instructions, "scale"))
        steps = int(self.get_argument_from_instructions(instructions, "ddim_steps"))
        plms = "#arg#plms" in instructions

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeed: `{seed}`\nScale: `{scale}`\nSteps: `{steps}`\nPLMS: `{plms}`\nModel: `Stable Diffusion 1.4`"

        view = View_stablediffusion_revision(self.bot, prompt, height, width, seed, scale, steps, plms)

        return embed, file, view

    async def receive_stablediffusion_batch(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion Batch", color=0x00ff00)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_argument_from_instructions(instructions, "prompt")[4:-5]
        height = int(self.get_argument_from_instructions(instructions, "H"))
        width = int(self.get_argument_from_instructions(instructions, "W"))
        seed = int(self.get_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_argument_from_instructions(instructions, "scale"))
        plms = "#arg#plms" in instructions

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nFirst seed: `{seed}`\nScale: `{scale}`\nSteps: `15`\nPLMS: `{plms}`\nModel: `Stable Diffusion 1.4`"

        view = View_stablediffusion_revision_batch(self.bot, prompt, height, width, seed, scale, plms)

        return embed, file, view
    
    def get_argument_from_instructions(self, instructions: str, argument: str) -> str:
        index = instructions.find(f"#arg#{argument}") + len(argument) + 6
        subString = instructions[index:]
        index2 = subString.find("#arg#") if "#arg#" in subString else subString.find("\"")

        return subString[0:index2]

    async def receive_prompt(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        ##TODO: Read file
        output_txt = ""

        embed = discord.Embed(title="Image", description=f"Task {taskID}", color=0x00ff00)

        db.execute("UPDATE tasks SET output = ? WHERE taskID = ?",
            output_txt,
            taskID
        )

        return embed, None, None

class View_forget_prompt(View):
    def __init__(self,
        prompt_manager: prompt_manager.Prompt_manager,
        promptID: int,
        newString: str
    ):
        super().__init__(timeout=None)
        self.add_item(Button_forget_prompt(prompt_manager, promptID, newString))

class Button_forget_prompt(Button):
    def __init__(self,
        prompt_manager: prompt_manager.Prompt_manager,
        promptID: int,
        newString: str
    ) -> None:
        super().__init__(label="Forget", style=discord.ButtonStyle.grey, emoji="❌", custom_id="button_forget_prompt")
        self.prompt_manager = prompt_manager
        self.promptID = promptID
        self.newString = newString

    async def callback(self, interaction: discord.Interaction) -> Any:
        self.prompt_manager.remove_prompt(self.promptID)
        await interaction.response.edit_message(content=self.newString, view=None)

class View_stablediffusion_revision(View):
    def __init__(self,
        bot: bot,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool
    ):
        txt2img = bot.get_cog("txt2img")
        buttonIterate = Button(style=discord.ButtonStyle.grey, label="Iterate", emoji="🔀", row=0, disabled=True)
        buttonBatch = Button(style=discord.ButtonStyle.grey, label="Batch", emoji="🔣", row=0)

        async def buttonIterate_callback(interaction: discord.Interaction) -> None:
            pass

        async def buttonBatch_callback(interaction: discord.Interaction) -> None:
            await txt2img.function_txt2img(interaction,
                prompt,
                height,
                width,
                None,
                scale,
                steps,
                plms,
                True
            )

        buttonIterate.callback = buttonIterate_callback
        buttonBatch.callback = buttonBatch_callback

        super().__init__(timeout=None)

        self.add_item(Button__txt2img_retry(txt2img, prompt, height, width, scale, steps, plms, False))
        self.add_item(Button__txt2img_revise(txt2img, prompt, height, width, seed, scale, steps, plms, False))
        self.add_item(buttonIterate)
        self.add_item(buttonBatch)

class View_stablediffusion_revision_batch(View):
    def __init__(self,
        bot: bot,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        plms: bool
    ):
        txt2img = bot.get_cog("txt2img")

        optionsUpscale = []

        for n in range(9):
            optionsUpscale.append(discord.SelectOption(label=f"Upscale image {n + 1}", value=n))

        selectUpscale = discord.ui.Select(
            placeholder="Upscale",
            options=optionsUpscale,
            row=1
        )

        async def upscale_callback(interaction: discord.Interaction) -> None:
            await txt2img.function_txt2img(interaction,
                prompt,
                height,
                width,
                seed + int(selectUpscale.values[0]),
                scale,
                50,
                plms,
                False
            )

        selectUpscale.callback = upscale_callback

        super().__init__(timeout=None)

        self.add_item(Button__txt2img_retry(txt2img, prompt, height, width, scale, None, plms, True))
        self.add_item(Button__txt2img_revise(txt2img, prompt, height, width, seed, scale, None, plms, True))
        self.add_item(selectUpscale)

class Button__txt2img_retry(Button):
    def __init__(self,
        txt2img, prompt: str,
        height: int,
        width: int,
        scale: float,
        steps: int,
        plms: bool,
        batch: bool
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Retry", emoji="🔁", row=0, custom_id="button_txt2img_retry")
        self.txt2img = txt2img
        self.prompt = prompt
        self.imgHeight = height
        self.imgWidth = width
        self.scale = scale
        self.steps = steps
        self.plms = plms
        self.batch = batch
    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.txt2img.function_txt2img(interaction,
            self.prompt,
            self.imgHeight,
            self.imgWidth,
            None,
            self.scale,
            self.steps,
            self.plms,
            self.batch
        )

class Button__txt2img_revise(Button):
    def __init__(self,
        txt2img,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool,
        batch: bool
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Revise", emoji="✏", row=0, custom_id="button_txt2img_revise")
        self.txt2img = txt2img
        self.prompt = prompt
        self.imgHeight = height
        self.imgWidth = width
        self.seed = seed
        self.scale = scale
        self.steps = steps
        self.plms = plms
        self.batch = batch
    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.response.send_modal(
            Modal_stablediffusion_revise(
                self.txt2img,
                self.prompt,
                self.imgHeight,
                self.imgWidth,
                self.seed,
                self.scale,
                self.steps,
                self.plms,
                self.batch
            )
        )

class Modal_stablediffusion_revise(discord.ui.Modal):
    def __init__(self,
        txt2img,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool,
        batch: bool
    ) -> None:
        super().__init__(title="Revise txt2img task")
        self.txt2img = txt2img
        self.plms = plms
        self.batch = batch

        self.promptField = discord.ui.TextInput(label="Prompt", style=discord.TextStyle.paragraph, placeholder="String", default=prompt, required=True)
        self.add_item(self.promptField)
        self.dimensionsField = discord.ui.TextInput(label="Dimensions (width x height)", style=discord.TextStyle.short, placeholder="Integer x Integer (multiples of  64)", default=f"{width}x{height}", required=True)
        self.add_item(self.dimensionsField)
        self.seedField = discord.ui.TextInput(label="Seed", style=discord.TextStyle.short, placeholder="Integer (random if empty)", default=seed, required=False)
        self.add_item(self.seedField)
        self.scaleField = discord.ui.TextInput(label="Scale", style=discord.TextStyle.short, placeholder="Float", default=str(scale), required=True)
        self.add_item(self.scaleField)
        if not self.batch:
            self.stepsField = discord.ui.TextInput(label="Steps", style=discord.TextStyle.short, placeholder="Integer", default=steps, required=True)
            self.add_item(self.stepsField)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        prompt = self.promptField.value

        pattern1 = re.compile("^[0-9]+x[0-9]+$")
        if not pattern1.match(self.dimensionsField.value):
            await interaction.response.send_message("Dimension field must match format [integer]x[integer]", ephemeral=True)
            return

        index = self.dimensionsField.value.find("x")
        width = int(self.dimensionsField.value[:index])
        height = int(self.dimensionsField.value[(index+1):])

        pattern2 = re.compile("^[0-9]+$")
        if self.seedField.value != "" and not pattern2.match(self.seedField.value):
            await interaction.response.send_message("Seed must be a positive integer or empty", ephemeral=True)
            return

        seed = None if self.seedField.value == "" else int(self.seedField.value)

        scaleString = self.scaleField.value

        if pattern2.match(scaleString): scaleString += ".0"

        pattern3 = re.compile("^[0-9]+\.[0-9]+$")
        if not pattern3.match(scaleString):
            await interaction.response.send_message("Scale must be a float", ephemeral=True)
            return

        scale = float(scaleString)

        if self.batch:
            steps = None
        else:
            if not pattern2.match(self.stepsField.value):
                await interaction.response.send_message("Steps must be a positive integer", ephemeral=True)
                return

            steps = self.stepsField.value

        await self.txt2img.function_txt2img(interaction,
            prompt,
            height,
            width,
            seed,
            scale,
            steps,
            self.plms,
            self.batch
        )

        return await super().on_submit(interaction)