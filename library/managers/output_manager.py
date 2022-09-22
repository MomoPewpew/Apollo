from typing import Union
from .. import bot
from ..db import db
import discord
from ..cogs import txt2img, img2img

class Output_manager(object):
    def __init__(self, bot: bot) -> None:
        self.bot = bot

    def get_encoded_argument_from_instructions(self, instructions: str, argument: str) -> str:
        index = instructions.find(f"#arg#{argument}") + len(argument) + 6
        subString = instructions[index:]
        index2 = subString.find("#arg#") if "#arg#" in subString else subString.find("\"")

        return subString[0:index2]

    def get_argument_from_instructions(self, instructions: str, argument: str) -> str:
        index = instructions.find(f"--{argument}") + len(argument) + 3
        subString = instructions[index:]
        index2 = subString.find(" ") if " " in subString else len(subString)

        return subString[0:index2]

    async def receive_image(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Image", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        function = self.get_argument_from_instructions(instructions, "function")
        sourceURL = self.get_argument_from_instructions(instructions, "sourceURL")

        embed.description = f"Function: `{function}`\nSource url: `{sourceURL}"

        return embed, file, None

    async def receive_stablediffusion_txt2img_single(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion txt2img", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        height = int(self.get_encoded_argument_from_instructions(instructions, "H"))
        width = int(self.get_encoded_argument_from_instructions(instructions, "W"))
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_encoded_argument_from_instructions(instructions, "scale"))
        steps = int(self.get_encoded_argument_from_instructions(instructions, "ddim_steps"))
        plms = "#arg#plms" in instructions

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeed: `{seed}`\nScale: `{scale}`\nSteps: `{steps}`\nPLMS: `{plms}`\nModel: `Stable Diffusion 1.4`"

        view = txt2img.View_txt2img_single(self.bot, taskID, prompt, height, width, seed, scale, steps, plms)

        return embed, file, view

    async def receive_stablediffusion_txt2img_batch(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion txt2img Batch", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        height = int(self.get_encoded_argument_from_instructions(instructions, "H"))
        width = int(self.get_encoded_argument_from_instructions(instructions, "W"))
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_encoded_argument_from_instructions(instructions, "scale"))
        plms = "#arg#plms" in instructions

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeeds: `{seed} - {seed + 8}`\nScale: `{scale}`\nSteps: `15`\nPLMS: `{plms}`\nModel: `Stable Diffusion 1.4`"

        view = txt2img.View_txt2img_batch(self.bot, prompt, height, width, seed, scale, plms)

        return embed, file, view

    async def receive_stablediffusion_txt2img_variations(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion txt2img Variations", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        height = int(self.get_encoded_argument_from_instructions(instructions, "H"))
        width = int(self.get_encoded_argument_from_instructions(instructions, "W"))
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        plms = "#arg#plms" in instructions

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeed: `{seed}`\nScales: `3.0 - 11.0`\nSteps: `15`\nPLMS: `{plms}`\nModel: `Stable Diffusion 1.4`"

        view = txt2img.View_txt2img_variations(self.bot, prompt, height, width, seed, plms)

        return embed, file, view

    async def receive_stablediffusion_img2img_single(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion img2img", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        init_img_url = self.get_argument_from_instructions(instructions, "sourceURL")
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_encoded_argument_from_instructions(instructions, "scale"))
        strength = float(self.get_encoded_argument_from_instructions(instructions, "strength"))
        steps = int(self.get_encoded_argument_from_instructions(instructions, "ddim_steps"))

        embed.description = f"Initiation Image: [Link]({init_img_url})\nPrompt: `{prompt}`\nSeed: `{seed}`\nScale: `{scale}`\nStrength: `{strength}`\nSteps: `{steps}`\nModel: `Stable Diffusion 1.4`"

        view = img2img.View_img2img_single(self.bot, taskID, prompt, init_img_url, seed, scale, strength, steps)

        return embed, file, view

    async def receive_stablediffusion_img2img_batch(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion img2img", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        init_img_url = self.get_argument_from_instructions(instructions, "sourceURL")
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_encoded_argument_from_instructions(instructions, "scale"))
        strength = float(self.get_encoded_argument_from_instructions(instructions, "strength"))

        embed.description = f"Initiation Image: [Link]({init_img_url})\nPrompt: `{prompt}`\nSeed: `{seed}`\nScale: `{scale}`\nStrength: `{strength}`\nSteps: `15`\nModel: `Stable Diffusion 1.4`"

        view = img2img.View_img2img_batch(self.bot, prompt, init_img_url, seed, scale, strength)

        return embed, file, view

    async def receive_stablediffusion_img2img_variations(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion img2img", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        init_img_url = self.get_argument_from_instructions(instructions, "sourceURL")
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))

        embed.description = f"Initiation Image: [Link]({init_img_url})\nPrompt: `{prompt}`\nSeed: `{seed}`\nScales: `5.0, 7.5, 10.0`\nStrengths: `0.6, 0.75, 0.9`\nSteps: `15`\nModel: `Stable Diffusion 1.4`"

        view = img2img.View_img2img_variations(self.bot, prompt, init_img_url, seed)

        return embed, file, view

    async def receive_prompt(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        ##TODO: Read file
        output_txt = ""

        embed = discord.Embed(title="Image", description=f"Task {taskID}", color=0x2f3136)

        db.execute("UPDATE tasks SET output = ? WHERE taskID = ?",
            output_txt,
            taskID
        )

        return embed, None, None