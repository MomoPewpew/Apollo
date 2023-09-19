import math
import random
import re
from typing import Any
import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot
from discord.ui import View, Modal, Button, Select, TextInput
from . import txt2img
from ..managers import output_manager

COG_NAME = "img2img"

class img2img(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Convert a text prompt into an image",
        guild_id=0000000000000000000
    )
    @app_commands.describe(
        prompt = "Describe the desired output image. Use commas to separate different parts of your description",
        init_img_url = "The URL to the initiation image. This must end in .png, .jpg, .jpeg or .bmp",
        seed = "The RNG seed. If you want to make something that looks like a previous output, use the same seed",
        scale = "How strictly should I follow your prompt? A lower scale allows me to take more creative liberties",
        strength = "How closely should the output resemble the initiation image? Lower strength means more resemblance",
        steps = "How much time should I spend refining the image? 1-150.",
        batch = "Shall I mass-produce a sample platter of crude images, or a single refined one?",
        model = "What set of training data would you like me to use?"
    )
    @app_commands.choices(model=
        [
            app_commands.Choice(name="Stable Diffusion 1.4", value="/plugins/stable-diffusion/models/ldm/stable-diffusion-v1/sd-v1-4.ckpt")
        ]
    )
    async def command_img2img(
        self,
        interaction: discord.Interaction,
        init_img_url: str,
        prompt: str,
        seed: int = None,
        scale: float = 7.5,
        strength: float = 0.75,
        steps: int = 50,
        batch: bool = False,
        model: app_commands.Choice[str] = "/plugins/stable-diffusion/models/ldm/stable-diffusion-v1/sd-v1-4.ckpt"
    ) -> None:
        await self.function_img2img(
            interaction,
            prompt,
            init_img_url,
            seed,
            scale,
            strength,
            steps,
            batch,
            model
        )

    async def function_img2img(self,
        interaction: discord.Interaction,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int,
        batch: bool,
        model: str
    ) -> None:
        if not self.bot.task_manager.is_url_image(init_img_url):
            await interaction.response.send_message("The URL that you have provided does not appear to be an image.", ephemeral=True)
            return

        if steps is not None and (steps > 150 or steps < 1):
            await interaction.response.send_message(f"The step count may not exceed 150 and must be positive. Your prompt was `{prompt}`", ephemeral=True)
            return

        seed = int(random.randrange(4294966294)) if seed is None else seed
        strength = 0.0 if strength < 0.0 else 1.0 if strength > 1.0 else strength
        if batch:
            await self.bot.task_manager.task_command_main(interaction, 240, "txt2img", prompt, "stablediffusion_img2img_batch", f"python3 {self.bot.daedalusBasePath}/daedalus.py --function img2imgBatch --sourceURL \"{init_img_url}\" --args \"#arg#prompt #qt#{prompt}#qt# #arg#seed {seed} #arg#scale {scale} #arg#strength {strength} #arg#ckpt {self.bot.daedalusBasePath}{model}\"")
        else:
            await self.bot.task_manager.task_command_main(interaction, 180, "txt2img", prompt, "stablediffusion_img2img_single", f"python3 {self.bot.daedalusBasePath}/daedalus.py --function img2imgSingle --sourceURL \"{init_img_url}\" --args \"#arg#prompt #qt#{prompt}#qt# #arg#seed {seed} #arg#scale {scale} #arg#strength {strength} #arg#ddim_steps {steps} #arg#ckpt {self.bot.daedalusBasePath}{model}\"")

    async def function_img2img_variations(self,
        interaction: discord.Interaction,
        prompt: str,
        init_img_url: str,
        seed: int,
        model: str
    ) -> None:
        if not self.bot.task_manager.is_url_image(init_img_url):
            await interaction.response.send_message("The URL that you have provided does not appear to be an image.", ephemeral=True)
            return

        await self.bot.task_manager.task_command_main(interaction, 240, "txt2img", prompt, "stablediffusion_img2img_variations", f"python3 {self.bot.daedalusBasePath}/daedalus.py --function img2imgVariations --sourceURL \"{init_img_url}\" --args \"#arg#prompt #qt#{prompt}#qt# #arg#seed {seed} #arg#ckpt {self.bot.daedalusBasePath}{model}\"")

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(img2img(bot))

class View_img2img_single(View):
    def __init__(self,
        bot: bot,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int,
        model: str
    ):
        img2imgCog = bot.get_cog("img2img")

        super().__init__(timeout=None)

        self.add_item(Button_img2img_retry(img2imgCog, prompt, init_img_url, scale, strength, steps, False, model))
        self.add_item(Button_img2img_revise(img2imgCog, prompt, init_img_url, seed, scale, strength, steps, False, model))
        self.add_item(txt2img.Button_txt2img_iterate(img2imgCog, prompt, scale, model))
        self.add_item(Button_img2img_batch(img2imgCog, prompt, init_img_url, scale, strength, model))
        self.add_item(Button_img2img_variations(img2imgCog, prompt, init_img_url, seed, model))
        self.add_item(output_manager.Select_effects(bot))

class View_img2img_batch(View):
    def __init__(self,
        bot: bot,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        model: str
    ):
        img2imgCog = bot.get_cog("img2img")

        super().__init__(timeout=None)

        self.add_item(Button_img2img_retry(img2imgCog, prompt, init_img_url, scale, strength, None, True, model))
        self.add_item(Button_img2img_revise(img2imgCog, prompt, init_img_url, seed, scale, strength, None, True, model))
        self.add_item(Select_img2img_batch_upscale(img2imgCog, prompt, init_img_url, seed, scale, strength, model))
        self.add_item(Select_img2img_batch_variations(img2imgCog, prompt, init_img_url, seed, model))

class View_img2img_variations(View):
    def __init__(self,
        bot: bot,
        prompt: str,
        init_img_url: str,
        seed: int,
        model: str
    ):
        img2imgCog = bot.get_cog("img2img")

        super().__init__(timeout=None)

        self.add_item(Select_img2img_variations_upscale(img2imgCog, prompt, init_img_url, seed, model))

class Button_img2img_retry(Button):
    def __init__(self,
        img2imgCog: img2img,
        prompt: str,
        init_img_url: str,
        scale: float,
        strength: float,
        steps: int,
        batch: bool,
        model: str
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Retry", emoji="🔁", row=0, custom_id="button_img2img_retry")
        self.img2imgCog = img2imgCog
        self.prompt = prompt
        self.init_img_url = init_img_url
        self.scale = scale
        self.strength = strength
        self.steps = steps
        self.batch = batch
        self.model = model

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.img2imgCog.function_img2img(interaction,
            self.prompt,
            self.init_img_url,
            None,
            self.scale,
            self.strength,
            self.steps,
            self.batch,
            self.model
        )
        return await super().callback(interaction)

class Button_img2img_revise(Button):
    def __init__(self,
        img2imgCog: img2img,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int,
        batch: bool,
        model: str
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Revise", emoji="✏", row=0, custom_id="button_img2img_revise")
        self.img2imgCog = img2imgCog
        self.prompt = prompt
        self.init_img_url = init_img_url
        self.seed = seed
        self.scale = scale
        self.strength = strength
        self.steps = steps
        self.batch = batch
        self.model = model

    async def callback(self, interaction: discord.Interaction) -> Any:
        await interaction.response.send_modal(
            Modal_img2img_revise(
                self.img2imgCog,
                self.prompt,
                self.init_img_url,
                self.seed,
                self.scale,
                self.strength,
                self.steps,
                self.batch,
                self.model
            )
        )
        return await super().callback(interaction)

class Button_img2img_batch(Button):
    def __init__(self,
        img2imgCog: img2img,
        prompt: str,
        init_img_url: str,
        scale: float,
        strength: float,
        model: str
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Batch", emoji="🔣", row=0, custom_id="button_img2img_batch")
        self.img2imgCog = img2imgCog
        self.prompt = prompt
        self.init_img_url = init_img_url
        self.scale = scale
        self.strength = strength
        self.model = model

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.img2imgCog.function_img2img(interaction,
            self.prompt,
            self.init_img_url,
            None,
            self.scale,
            self.strength,
            None,
            True,
            self.model
        )
        return await super().callback(interaction)

class Button_img2img_variations(Button):
    def __init__(self,
        img2imgCog: img2img,
        prompt: str,
        init_img_url: str,
        seed: int,
        model: str
    ) -> None:
        super().__init__(style=discord.ButtonStyle.grey, label="Variations", emoji="🔢", row=0, custom_id="button_img2img_variations")
        self.img2imgCog = img2imgCog
        self.prompt = prompt
        self.init_img_url = init_img_url
        self.seed = seed
        self.model = model

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.img2imgCog.function_img2img_variations(interaction,
            self.prompt,
            self.init_img_url,
            self.seed,
            self.model
        )
        return await super().callback(interaction)

class Select_img2img_batch_upscale(Select):
    def __init__(self,
        img2imgCog: img2img,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        model: str
    ) -> None:
        self.img2imgCog = img2imgCog
        self.prompt = prompt
        self.init_img_url = init_img_url
        self.seed = seed
        self.scale = scale
        self.strength = strength
        self.model = model

        options = []

        for n in range(9):
            options.append(discord.SelectOption(label=f"Upscale image {n + 1}", value=n, emoji="↔"))

        super().__init__(custom_id="select_img2img_batch_upscale", placeholder="↔ Upscale", options=options, row=1)

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.img2imgCog.function_img2img(interaction,
            self.prompt,
            self.init_img_url,
            self.seed + int(self.values[0]),
            self.scale,
            self.strength,
            50,
            False,
            self.model
        )
        return await super().callback(interaction)

class Select_img2img_variations_upscale(Select):
    def __init__(self,
        img2imgCog: img2img,
        prompt: str,
        init_img_url,
        seed: int,
        model: str
    ) -> None:
        self.img2imgCog = img2imgCog
        self.prompt = prompt
        self.init_img_url = init_img_url
        self.seed = seed
        self.model = model

        options = []

        for n in range(9):
            options.append(discord.SelectOption(label=f"Upscale image {n + 1}", value=n, emoji="↔"))

        super().__init__(custom_id="select_img2img_variations_upscale", placeholder="↔ Upscale", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> Any:
        scales = [5.0, 7.5, 10.0]
        strengths = [0.6, 0.75, 0.9]

        row = math.floor(int(self.values[0]) / 3)
        column = (int(self.values[0]) %3)

        await self.img2imgCog.function_img2img(interaction,
            self.prompt,
            self.init_img_url,
            self.seed,
            scales[column],
            strengths[row],
            50,
            False,
            self.model
        )
        return await super().callback(interaction)

class Select_img2img_batch_variations(Select):
    def __init__(self,
        img2imgCog: img2img,
        prompt: str,
        init_img_url: str,
        seed: int,
        model: str
    ) -> None:
        self.img2imgCog = img2imgCog
        self.prompt = prompt
        self.init_img_url = init_img_url
        self.seed = seed
        self. model = model

        options = []

        for n in range(9):
            options.append(discord.SelectOption(label=f"Variations on image {n + 1}", value=n, emoji="🔢"))

        super().__init__(custom_id="select_img2img_batch_variations", placeholder="🔢 Variations", options=options, row=2)

    async def callback(self, interaction: discord.Interaction) -> Any:
        await self.img2imgCog.function_img2img_variations(interaction,
            self.prompt,
            self.init_img_url,
            self.seed + int(self.values[0]),
            self.model
        )
        return await super().callback(interaction)

class Modal_img2img_revise(Modal):
    def __init__(self,
        img2imgCog: img2img,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int,
        batch: bool,
        model: str
    ) -> None:
        super().__init__(title="Revise img2img task")
        self.img2imgCog = img2imgCog
        self.batch = batch
        self.init_img_url = init_img_url
        self.model = model

        self.promptField = TextInput(label="Prompt", style=discord.TextStyle.paragraph, placeholder="String", default=prompt, required=True)
        self.add_item(self.promptField)
        self.seedField = TextInput(label="Seed", style=discord.TextStyle.short, placeholder="Integer (random if empty)", default=seed, required=False)
        self.add_item(self.seedField)
        self.scaleField = TextInput(label="Scale", style=discord.TextStyle.short, placeholder="Float", default=str(scale), required=True)
        self.add_item(self.scaleField)
        self.strengthField = TextInput(label="Strength", style=discord.TextStyle.short, placeholder="Float", default=str(strength), required=True)
        self.add_item(self.strengthField)

        if not self.batch:
            self.stepsField = TextInput(label="Steps", style=discord.TextStyle.short, placeholder="Integer", default=steps, required=True)
            self.add_item(self.stepsField)

    async def on_submit(self, interaction: discord.Interaction) -> None:
        prompt = self.promptField.value

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

        strengthString = self.strengthField.value

        if pattern2.match(strengthString): strengthString += ".0"

        if not pattern3.match(strengthString):
            await interaction.response.send_message("Strength must be a float", ephemeral=True)
            return

        strength = float(strengthString)

        if self.batch:
            steps = None
        else:
            if not pattern2.match(self.stepsField.value):
                await interaction.response.send_message("Steps must be a positive integer", ephemeral=True)
                return

            steps = int(self.stepsField.value)

        await self.img2imgCog.function_img2img(interaction,
            prompt,
            self.init_img_url,
            seed,
            scale,
            strength,
            steps,
            self.batch,
            self.model
        )
            
        return await super().on_submit(interaction)