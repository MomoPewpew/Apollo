from typing import Any, Union
from .. import bot
from ..db import db
import discord
from ..cogs import txt2img, img2img
from discord.ui import View, Select, Modal

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
    
    def get_model_name_from_ckpt(self, model: str) -> str:
        if model == "/home/ubuntu/Daedalus/plugins/stable-diffusion/models/ldm/stable-diffusion-v1/sd-v1-4.ckpt":
            return "Stable Diffusion 1.4"
        else:
            return "Unknown"

    async def receive_image(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Image", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        function = self.get_argument_from_instructions(instructions, "function")
        sourceURL = self.get_argument_from_instructions(instructions, "sourceURL")

        embed.description = f"Source Image: [Link]({sourceURL})\nFunction: `{function}`"

        view = View_image(self.bot, sourceURL)

        return embed, file, view

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
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt")
        plms = "#arg#plms" in instructions

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeed: `{seed}`\nScale: `{scale}`\nSteps: `{steps}`\nPLMS: `{plms}`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = txt2img.View_txt2img_single(self.bot, taskID, prompt, height, width, seed, scale, steps, plms, model)

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
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt")
        plms = "#arg#plms" in instructions

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeeds: `{seed} - {seed + 8}`\nScale: `{scale}`\nSteps: `15`\nPLMS: `{plms}`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = txt2img.View_txt2img_batch(self.bot, prompt, height, width, seed, scale, plms, model)

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
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt")
        plms = "#arg#plms" in instructions

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeed: `{seed}`\nScales: `3.0 - 11.0`\nSteps: `15`\nPLMS: `{plms}`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = txt2img.View_txt2img_variations(self.bot, prompt, height, width, seed, plms, model)

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
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt")

        embed.description = f"Initiation Image: [Link]({init_img_url})\nPrompt: `{prompt}`\nSeed: `{seed}`\nScale: `{scale}`\nStrength: `{strength}`\nSteps: `{steps}`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = img2img.View_img2img_single(self.bot, taskID, prompt, init_img_url, seed, scale, strength, steps, model)

        return embed, file, view

    async def receive_stablediffusion_img2img_batch(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion img2img Batch", color=0x2f3136)
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
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt")

        embed.description = f"Initiation Image: [Link]({init_img_url})\nPrompt: `{prompt}`\nSeed: `{seed}`\nScale: `{scale}`\nStrength: `{strength}`\nSteps: `15`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = img2img.View_img2img_batch(self.bot, prompt, init_img_url, seed, scale, strength, model)

        return embed, file, view

    async def receive_stablediffusion_img2img_variations(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion img2img Variations", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        init_img_url = self.get_argument_from_instructions(instructions, "sourceURL")
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt")

        embed.description = f"Initiation Image: [Link]({init_img_url})\nPrompt: `{prompt}`\nSeed: `{seed}`\nScales: `5.0, 7.5, 10.0`\nStrengths: `0.6, 0.75, 0.9`\nSteps: `15`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = img2img.View_img2img_variations(self.bot, prompt, init_img_url, seed, model)

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

class View_image(View):
    def __init__(self,
        bot: bot,
        taskID: int
    ):
        super().__init__(timeout=None)

        self.add_item(Select_effects(bot, taskID))

class Select_effects(Select):
    def __init__(self,
        bot: bot,
        taskID: int
    ) -> None:
        self.bot = bot
        self.taskID = taskID
        self.img_url: str = ""

        options = [
            discord.SelectOption(label="style_arcane", value="arcanegan", emoji="🎨", description="Convert into the art style of the animated series Arcane"),
            discord.SelectOption(label="upscale_real-esrgan", value="realesrgangan", emoji="↔", description="General purpose upscaling"),
        ]

        super().__init__(custom_id="select_effects", placeholder="🔮 Process image", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> Any:
        if self.img_url == "":
            self.img_url = db.field("SELECT output FROM tasks WHERE taskID = ?",
                self.taskID
            )
        
        if self.values[0] == "arcanegan":
            await self.bot.get_cog("style").function_style_arcane(interaction, self.img_url)
        if self.values[0] == "realesrgangan":
            await self.bot.get_cog("upscale").function_style_realesrgan(interaction, self.img_url)
        
        return await super().callback(interaction)