import re
from typing import Any, Union

from .. import bot
from ..db import db
import discord
from ..cogs import txt2img, img2img, threedinpainting
from discord.ui import View, Select, Modal, TextInput

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
        if model == "/plugins/stable-diffusion/models/ldm/stable-diffusion-v1/sd-v1-4.ckpt":
            return "Stable Diffusion 1.4"
        else:
            return "Unknown"

    def get_3d_inpaint_style_from_config(self, config: str) -> str:
        if config == "/plugins/3d-photo-inpainting/dolly_zoom_in.yml":
            return "Dolly Zoom-In"
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
        sourceURL = self.get_argument_from_instructions(instructions, "sourceURL")[1:-1]

        embed.description = f"Source Image: [Link]({sourceURL})\nFunction: `{function}`"

        view = View_image(self.bot)

        return embed, file, view

    async def receive_stablediffusion_txt2img_single(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        height = int(self.get_encoded_argument_from_instructions(instructions, "H"))
        width = int(self.get_encoded_argument_from_instructions(instructions, "W"))
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_encoded_argument_from_instructions(instructions, "scale"))
        steps = int(self.get_encoded_argument_from_instructions(instructions, "ddim_steps"))
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt").replace(self.bot.daedalusBasePath, "")
        plms = "#arg#plms" in instructions

        return self.receive_stablediffusion_txt2img_single_Objects(file_path, filename, prompt, height, width, seed, scale, steps, plms, model)

    def receive_stablediffusion_txt2img_single_Objects(self, file_path: str, filename: str, prompt: str, height: int, width: int, seed: int, scale: float, steps: int, plms: bool, model: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion txt2img", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeed: `{seed}`\nScale: `{scale}`\nSteps: `{steps}`\nPLMS: `{plms}`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = txt2img.View_txt2img_single(self.bot, prompt, height, width, seed, scale, steps, plms, model)

        return embed, file, view

    async def receive_stablediffusion_txt2img_batch(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        height = int(self.get_encoded_argument_from_instructions(instructions, "H"))
        width = int(self.get_encoded_argument_from_instructions(instructions, "W"))
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_encoded_argument_from_instructions(instructions, "scale"))
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt").replace(self.bot.daedalusBasePath, "")
        plms = "#arg#plms" in instructions

        return self.receive_stablediffusion_txt2img_batch_Objects(file_path, filename, prompt, height, width, seed, scale, 15, plms, model)

    def receive_stablediffusion_txt2img_batch_Objects(self, file_path: str, filename: str, prompt: str, height: int, width: int, seed: int, scale: float, steps: int, plms: bool, model: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion txt2img Batch", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeeds: `{seed} - {seed + 8}`\nScale: `{scale}`\nSteps: `{steps}`\nPLMS: `{plms}`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = txt2img.View_txt2img_batch(self.bot, prompt, height, width, seed, scale, plms, model)

        return embed, file, view

    async def receive_stablediffusion_txt2img_variations(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        height = int(self.get_encoded_argument_from_instructions(instructions, "H"))
        width = int(self.get_encoded_argument_from_instructions(instructions, "W"))
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt").replace(self.bot.daedalusBasePath, "")
        plms = "#arg#plms" in instructions

        return self.receive_stablediffusion_txt2img_variations_Objects(file_path, filename, prompt, height, width, seed, 15, plms, model)

    def receive_stablediffusion_txt2img_variations_Objects(self, file_path: str, filename: str, prompt: str, height: int, width: int, seed: int, steps: int, plms: bool, model: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion txt2img Variations", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        embed.description = f"Prompt: `{prompt}`\nDimensions: `{width}x{height}`\nSeed: `{seed}`\nScales: `3.0 - 11.0`\nSteps: `{steps}`\nPLMS: `{plms}`\nModel: `{self.get_model_name_from_ckpt(model)}`"

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
        init_img_url = self.get_argument_from_instructions(instructions, "sourceURL")[1:-1]
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_encoded_argument_from_instructions(instructions, "scale"))
        strength = float(self.get_encoded_argument_from_instructions(instructions, "strength"))
        steps = int(self.get_encoded_argument_from_instructions(instructions, "ddim_steps"))
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt").replace(self.bot.daedalusBasePath, "")

        embed.description = f"Initiation Image: [Link]({init_img_url})\nPrompt: `{prompt}`\nSeed: `{seed}`\nScale: `{scale}`\nStrength: `{strength}`\nSteps: `{steps}`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = img2img.View_img2img_single(self.bot, prompt, init_img_url, seed, scale, strength, steps, model)

        return embed, file, view

    async def receive_stablediffusion_img2img_batch(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="Stable Diffusion img2img Batch", color=0x2f3136)
        file = discord.File(file_path, filename=filename)
        embed.set_image(url=f"attachment://{filename}")

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        prompt = self.get_encoded_argument_from_instructions(instructions, "prompt")[4:-5]
        init_img_url = self.get_argument_from_instructions(instructions, "sourceURL")[1:-1]
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        scale = float(self.get_encoded_argument_from_instructions(instructions, "scale"))
        strength = float(self.get_encoded_argument_from_instructions(instructions, "strength"))
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt").replace(self.bot.daedalusBasePath, "")

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
        init_img_url = self.get_argument_from_instructions(instructions, "sourceURL")[1:-1]
        seed = int(self.get_encoded_argument_from_instructions(instructions, "seed"))
        model = self.get_encoded_argument_from_instructions(instructions, "ckpt").replace(self.bot.daedalusBasePath, "")

        embed.description = f"Initiation Image: [Link]({init_img_url})\nPrompt: `{prompt}`\nSeed: `{seed}`\nScales: `5.0, 7.5, 10.0`\nStrengths: `0.6, 0.75, 0.9`\nSteps: `15`\nModel: `{self.get_model_name_from_ckpt(model)}`"

        view = img2img.View_img2img_variations(self.bot, prompt, init_img_url, seed, model)

        return embed, file, view

    async def receive_3dInPainting(self, taskID: int, file_path: str, filename: str) -> Union[discord.Embed, discord.File, discord.ui.View]:
        embed = discord.Embed(title="3D Inpainting", color=0x2f3136)
        file = discord.File(file_path, filename=filename)

        instructions = db.field("SELECT instructions FROM tasks WHERE taskID = ?",
            taskID
        )

        sourceURL = self.get_argument_from_instructions(instructions, "sourceURL")[1:-1]
        style = self.get_encoded_argument_from_instructions(instructions, "config").replace(self.bot.daedalusBasePath, "")
        num_frames = int(self.get_encoded_argument_from_instructions(instructions, "num_frames"))
        fps = int(self.get_encoded_argument_from_instructions(instructions, "fps"))

        embed.description = f"Source Image: [Link]({sourceURL})\nStyle: `{self.get_3d_inpaint_style_from_config(style)}`\nnum_frames: `{num_frames}`\nfps: `{fps}`"

        return embed, file, None

class View_image(View):
    def __init__(self,
        bot: bot
    ):
        super().__init__(timeout=None)

        self.add_item(Select_effects(bot))

class Select_effects(Select):
    def __init__(self,
        bot: bot
    ) -> None:
        self.bot = bot
        self.img_url: str = ""

        options = [
            discord.SelectOption(label="upscale_real-esrgan", value="realesrgangan", emoji="↔", description="General purpose upscaling"),
            discord.SelectOption(label="upscale_gfpgan", value="gfpgan", emoji="↔", description="Upscaling with AI face correction"),
            discord.SelectOption(label="style_arcane", value="arcanegan", emoji="🎨", description="Convert into the art style of the animated series Arcane"),
            discord.SelectOption(label="3dinpainting", value="3dinpainting", emoji="📦", description="Dolly Zoom-In effect"),
        ]

        super().__init__(custom_id="select_effects", placeholder="🔮 Process image", options=options, row=1, disabled=True)

    async def callback(self, interaction: discord.Interaction) -> Any:
        if self.values[0] == "arcanegan":
            await self.bot.get_cog("style").function_style_arcane(interaction, self.img_url)
        elif self.values[0] == "realesrgangan":
            await self.bot.get_cog("upscale").function_style_realesrgan(interaction, self.img_url)
        elif self.values[0] == "gfpgan":
            await self.bot.get_cog("upscale").function_style_gfpgan(interaction, self.img_url)
        elif self.values[0] == "3dinpainting":
            cog = self.bot.get_cog("threedinpainting")
            modal = Modal_3dinpainting(cog, self.img_url)
            await interaction.response.send_modal(modal)
        
        return await super().callback(interaction)

class Modal_3dinpainting(Modal):
    def __init__(self,
        threedinpaintingCog: threedinpainting.threedinpainting,
        img_url: str
    ) -> None:
        super().__init__(title="3D Inpainting")
        self.threedinpaintingCog = threedinpaintingCog
        self.img_url = img_url

        options = [
            discord.SelectOption(label="Dolly Zoom-In", value="/plugins/3d-photo-inpainting/dolly_zoom_in.yml", default=True)
        ]

        #self.styleSelect = Select(placeholder="style", options=options)
        #self.add_item(self.styleSelect)
        self.num_framesField = TextInput(label="num_frames", style=discord.TextStyle.short, placeholder="Integer", default=240, required=True)
        self.add_item(self.num_framesField)
        self.fpsField = TextInput(label="fps", style=discord.TextStyle.short, placeholder="Integer", default=40, required=True)
        self.add_item(self.fpsField)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        pattern2 = re.compile("^[0-9]+$")
        if self.num_framesField.value != "" and not pattern2.match(self.num_framesField.value):
            await interaction.response.send_message("num_frames must be a positive integer", ephemeral=True)
            return

        num_frames = int(self.num_framesField.value)

        if self.fpsField.value != "" and not pattern2.match(self.fpsField.value):
            await interaction.response.send_message("num_frames must be a positive integer", ephemeral=True)
            return

        fps = int(self.fpsField.value)

        await self.threedinpaintingCog.function_style_3dinpainting(
            interaction,
            self.img_url,
            "/plugins/3d-photo-inpainting/dolly_zoom_in.yml",
            num_frames,
            fps
        )
            
        return await super().on_submit(interaction)