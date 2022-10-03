import random
import re
from typing import Any
import discord
from discord import app_commands
from discord.ext.commands import Cog

from ..managers import output_manager
from .. import bot
from discord.ui import View, Button, Modal, Select, TextInput
from ..db import db
from . import img2img

COG_NAME = "txt2img"

class txt2img(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Convert a text prompt into an image"
    )
    @app_commands.describe(
        prompt = "Describe the desired output image. Use commas to separate different parts of your description",
        height = "The height of the output image in pixels. This must be a multiple of 64",
        width = "The width of the output image in pixels. This must be a multiple of 64",
        seed = "The RNG seed. If you want to make something that looks like a previous output, use the same seed",
        scale = "How strictly should I follow your prompt? A lower scale allows me to take more creative liberties",
        steps = "How much time should I spend refining the image? Batches are locked at 15 steps",
        plms = "Use PLMS sampling instead of regular sampling. This will give you a different output",
        batch = "Shall I mass-produce a sample platter of crude images, or a single refined one?",
        model = "What set of training data would you like me to use?"
    )
    @app_commands.choices(model=
        [
            app_commands.Choice(name="Stable Diffusion 1.4", value="/plugins/stable-diffusion/models/ldm/stable-diffusion-v1/sd-v1-4.ckpt")
        ]
    )
    async def command_txt2img(
        self,
        interaction: discord.Interaction,
        prompt: str,
        height: int = 512,
        width: int = 512,
        seed: int = None,
        scale: float = 7.5,
        steps: int = 50,
        plms: bool = True,
        batch: bool = False,
        model: app_commands.Choice[str] = "/plugins/stable-diffusion/models/ldm/stable-diffusion-v1/sd-v1-4.ckpt"
    ) -> None:
        await self.function_txt2img(
            interaction,
            prompt,
            height,
            width,
            seed,
            scale,
            steps,
            plms,
            batch,
            model
        )

    async def function_txt2img(self,
        interaction: discord.Interaction,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool,
        batch: bool,
        model: str
    ) -> None:
        if height %64 != 0 or width %64 != 0:
            await interaction.response.send_message(f"The height and width must be a multiple of 64. Your prompt was `{prompt}`", ephemeral=True)
            return

        seed = int(random.randrange(4294966294)) if seed is None else seed

        plmsString = " #arg#plms" if plms else ""
        if batch:
            await self.bot.task_manager.task_command_main(interaction, 240, "txt2img", prompt, "stablediffusion_txt2img_batch", f"python3 {self.bot.daedalusBasePath}/daedalus.py --function txt2imgBatch --args \"#arg#prompt #qt#{prompt}#qt# #arg#H {height} #arg#W {width} #arg#seed {seed} #arg#scale {scale}{plmsString} #arg#ckpt {self.bot.daedalusBasePath}{model}\"")
        else:
            await self.bot.task_manager.task_command_main(interaction, 180, "txt2img", prompt, "stablediffusion_txt2img_single", f"python3 {self.bot.daedalusBasePath}/daedalus.py --function txt2imgSingle --args \"#arg#prompt #qt#{prompt}#qt# #arg#H {height} #arg#W {width} #arg#seed {seed} #arg#scale {scale} #arg#ddim_steps {steps}{plmsString} #arg#ckpt {self.bot.daedalusBasePath}{model}\"")

    async def function_txt2img_variations(self,
        interaction: discord.Interaction,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        plms: bool,
        model: str
    ) -> None:
        plmsString = " #arg#plms" if plms else ""

        await self.bot.task_manager.task_command_main(interaction, 240, "txt2img", prompt, "stablediffusion_txt2img_variations", f"python3 {self.bot.daedalusBasePath}/daedalus.py --function txt2imgVariations --args \"#arg#prompt #qt#{prompt}#qt# #arg#H {height} #arg#W {width} #arg#seed {seed}{plmsString} #arg#ckpt {self.bot.daedalusBasePath}{model}\"")

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(txt2img(bot))

class View_txt2img_single(View):
    def __init__(self,
        bot: bot,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool,
        model: str
    ):
        txt2imgCog = bot.get_cog("txt2img")
        img2imgCog = bot.get_cog("img2img")

        super().__init__(timeout=None)

        self.add_item(Button_txt2img_retry(txt2imgCog, prompt, height, width, scale, steps, plms, False, model))
        self.add_item(Button_txt2img_revise(txt2imgCog, prompt, height, width, seed, scale, steps, plms, False, model))
        self.add_item(Button_txt2img_iterate(img2imgCog, prompt, scale, model))
        self.add_item(Button_txt2img_batch(txt2imgCog, prompt, height, width, scale, plms, model))
        self.add_item(Button_txt2img_variations(txt2imgCog, prompt, height, width, seed, plms, model))
        self.add_item(output_manager.Select_effects(bot))

class View_txt2img_batch(View):
    def __init__(self,
        bot: bot,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        plms: bool,
        model: str
    ):
        txt2imgCog = bot.get_cog("txt2img")

        super().__init__(timeout=None)

        self.add_item(Button_txt2img_retry(txt2imgCog, prompt, height, width, scale, None, plms, True, model))
        self.add_item(Button_txt2img_revise(txt2imgCog, prompt, height, width, seed, scale, None, plms, True, model))
        self.add_item(Select_txt2img_batch_upscale(txt2imgCog, prompt, height, width, seed, scale, plms, model))
        self.add_item(Select_txt2img_batch_variations(txt2imgCog, prompt, height, width, seed, plms, model))

class View_txt2img_variations(View):
    def __init__(self,
        bot: bot,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        plms: bool,
        model: str
    ):
        txt2imgCog = bot.get_cog("txt2img")

        super().__init__(timeout=None)

        self.add_item(Select_txt2img_variations_upscale(txt2imgCog, prompt, height, width, seed, plms, model))

class Button_txt2img_retry(Button):
    def __init__(self,
        txt2imgCog: txt2img,
        prompt: str,
        height: int,
        width: int,
        scale: float,
        steps: int,
        plms: bool,
        batch: bool,
        model: str
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Retry", emoji="🔁", row=0, custom_id="button_txt2img_retry")
        self.txt2imgCog = txt2imgCog
        self.prompt = prompt
        self.imgHeight = height
        self.imgWidth = width
        self.scale = scale
        self.steps = steps
        self.plms = plms
        self.batch = batch
        self.model = model

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.txt2imgCog.function_txt2img(interaction,
            self.prompt,
            self.imgHeight,
            self.imgWidth,
            None,
            self.scale,
            self.steps,
            self.plms,
            self.batch,
            self.model
        )
        return await super().callback(interaction)

class Button_txt2img_revise(Button):
    def __init__(self,
        txt2imgCog: txt2img,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool,
        batch: bool,
        model: str
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Revise", emoji="✏", row=0, custom_id="button_txt2img_revise")
        self.txt2imgCog = txt2imgCog
        self.prompt = prompt
        self.imgHeight = height
        self.imgWidth = width
        self.seed = seed
        self.scale = scale
        self.steps = steps
        self.plms = plms
        self.batch = batch
        self.model = model

    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.response.send_modal(
            Modal_txt2img_revise(
                self.txt2imgCog,
                self.prompt,
                self.imgHeight,
                self.imgWidth,
                self.seed,
                self.scale,
                self.steps,
                self.plms,
                self.batch,
                self.model
            )
        )
        return await super().callback(interaction)

class Button_txt2img_iterate(Button):
    def __init__(self,
        img2imgCog: img2img.img2img,
        prompt: str,
        scale: float,
        model: str
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Iterate", emoji="↩", row=0, custom_id="button_txt2img_iterate")
        self.img_url: str = ""
        self.img2imgCog = img2imgCog
        self.prompt = prompt
        self.scale = scale
        self.model = model

    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.response.send_modal(
            img2img.Modal_img2img_revise(
                self.img2imgCog,
                self.prompt,
                self.img_url,
                "",
                self.scale,
                0.75,
                50,
                False,
                self.model
            )
        )
        return await super().callback(interaction)

class Button_txt2img_batch(Button):
    def __init__(self,
        txt2imgCog: txt2img,
        prompt: str,
        height: int,
        width: int,
        scale: float,
        plms: bool,
        model: str
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Batch", emoji="🔣", row=0, custom_id="button_txt2img_batch")
        self.txt2imgCog = txt2imgCog
        self.prompt = prompt
        self.imgHeight = height
        self.imgWidth = width
        self.scale = scale
        self.plms = plms
        self.model = model

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.txt2imgCog.function_txt2img(interaction,
            self.prompt,
            self.imgHeight,
            self.imgWidth,
            None,
            self.scale,
            None,
            self.plms,
            True,
            self.model
        )
        return await super().callback(interaction)

class Button_txt2img_variations(Button):
    def __init__(self,
        txt2imgCog: txt2img,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        plms: bool,
        model: str
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Variations", emoji="🔢", row=0, custom_id="button_txt2img_variations")
        self.txt2imgCog = txt2imgCog
        self.prompt = prompt
        self.imgHeight = height
        self.imgWidth = width
        self.seed = seed
        self.plms = plms
        self.model = model

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.txt2imgCog.function_txt2img_variations(interaction,
            self.prompt,
            self.imgHeight,
            self.imgWidth,
            self.seed,
            self.plms,
            self.model
        )
        self.disabled = True
        return await super().callback(interaction)

class Select_txt2img_batch_upscale(Select):
    def __init__(self,
        txt2imgCog: txt2img,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        plms: bool,
        model: str
    ) -> None:
        self.txt2imgCog = txt2imgCog
        self.prompt = prompt
        self.imgHeight = height
        self.imgWidth = width
        self.seed = seed
        self.scale = scale
        self.plms = plms
        self.model = model

        options = []

        for n in range(9):
            options.append(discord.SelectOption(label=f"Upscale image {n + 1}", value=n, emoji="↔"))

        super().__init__(custom_id="select_txt2img_batch_upscale", placeholder="↔ Upscale", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.txt2imgCog.function_txt2img(interaction,
            self.prompt,
            self.imgHeight,
            self.imgWidth,
            self.seed + int(self.values[0]),
            self.scale,
            50,
            self.plms,
            False,
            self.model
        )
        return await super().callback(interaction)

class Select_txt2img_variations_upscale(Select):
    def __init__(self,
        txt2imgCog: txt2img,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        plms: bool,
        model: str
    ) -> None:
        self.txt2imgCog = txt2imgCog
        self.prompt = prompt
        self.imgHeight = height
        self.imgWidth = width
        self.seed = seed
        self.plms = plms
        self.model = model

        options = []

        for n in range(9):
            options.append(discord.SelectOption(label=f"Upscale image {n + 1}", value=n, emoji="↔"))

        super().__init__(custom_id="select_txt2img_variations_upscale", placeholder="↔ Upscale", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.txt2imgCog.function_txt2img(interaction,
            self.prompt,
            self.imgHeight,
            self.imgWidth,
            self.seed,
            1.0 * (float(self.values[0]) + 3.0),
            50,
            self.plms,
            False,
            self.model
        )
        return await super().callback(interaction)

class Select_txt2img_batch_variations(Select):
    def __init__(self,
        txt2imgCog: txt2img,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        plms: bool,
        model: str
    ) -> None:
        self.txt2imgCog = txt2imgCog
        self.prompt = prompt
        self.imgHeight = height
        self.imgWidth = width
        self.seed = seed
        self.plms = plms
        self.model = model

        options = []

        for n in range(9):
            options.append(discord.SelectOption(label=f"Variations on image {n + 1}", value=n, emoji="🔢"))

        super().__init__(custom_id="select_txt2img_batch_variations", placeholder="🔢 Variations", options=options, row=2)

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.txt2imgCog.function_txt2img_variations(interaction,
            self.prompt,
            self.imgHeight,
            self.imgWidth,
            self.seed + int(self.values[0]),
            self.plms,
            self.model
        )
        return await super().callback(interaction)

class Modal_txt2img_revise(Modal):
    def __init__(self,
        txt2imgCog: txt2img,
        prompt: str,
        height: int,
        width: int,
        seed: int,
        scale: float,
        steps: int,
        plms: bool,
        batch: bool,
        model: str
    ) -> None:
        super().__init__(title="Revise txt2img task")
        self.txt2imgCog = txt2imgCog
        self.plms = plms
        self.batch = batch
        self.model = model

        self.promptField = TextInput(label="Prompt", style=discord.TextStyle.paragraph, placeholder="String", default=prompt, required=True)
        self.add_item(self.promptField)
        self.dimensionsField = TextInput(label="Dimensions (width x height)", style=discord.TextStyle.short, placeholder="Integer x Integer (multiples of  64)", default=f"{width}x{height}", required=True)
        self.add_item(self.dimensionsField)
        self.seedField = TextInput(label="Seed", style=discord.TextStyle.short, placeholder="Integer (random if empty)", default=seed, required=False)
        self.add_item(self.seedField)
        self.scaleField = TextInput(label="Scale", style=discord.TextStyle.short, placeholder="Float", default=str(scale), required=True)
        self.add_item(self.scaleField)
        if not self.batch:
            self.stepsField = TextInput(label="Steps", style=discord.TextStyle.short, placeholder="Integer", default=steps, required=True)
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

        await self.txt2imgCog.function_txt2img(interaction,
            prompt,
            height,
            width,
            seed,
            scale,
            steps,
            self.plms,
            self.batch,
            self.model
        )

        return await super().on_submit(interaction)