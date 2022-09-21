import random
import re
import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot
from discord.ui import View, Modal

COG_NAME = "img2img"

class img2img(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name=COG_NAME,
        description = "Convert a text prompt into an image"
    )
    async def command_img2img(
        self,
        interaction: discord.Interaction,
        prompt: str,
        init_img_url: str,
        seed: int = None,
        scale: float = 7.5,
        strength: float = 0.75,
        steps: int = 50,
        batch: bool = False
    ) -> None:
        await self.function_img2img(
            interaction,
            prompt,
            init_img_url,
            seed,
            scale,
            strength,
            steps,
            batch
        )

    async def function_img2img(self,
        interaction: discord.Interaction,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int,
        batch: bool
    ) -> None:
        seed = int(random.randrange(4294966294)) if seed is None else seed
        strength = 0.0 if strength < 0.0 else 1.0 if strength > 1.0 else strength
        if batch:
            await self.bot.task_manager.task_command_main(interaction, 180, "txt2img", prompt, "stablediffusion_img2img_single", f"python3 /home/ubuntu/Daedalus/daedalus.py --function img2imgSingle --args \"#arg#prompt #qt#{prompt}#qt# #arg#init_img {init_img_url} #arg#seed {seed} #arg#scale {scale} #arg#strength {strength} #arg#ddim_steps {steps}\"")
        else:
            await self.bot.task_manager.task_command_main(interaction, 180, "txt2img", prompt, "stablediffusion_img2img_single", f"python3 /home/ubuntu/Daedalus/daedalus.py --function img2imgSingle --sourceURL {init_img_url} --args \"#arg#prompt #qt#{prompt}#qt# #arg#seed {seed} #arg#scale {scale} #arg#strength {strength} #arg#ddim_steps {steps}\"")

    async def function_img2img_variations(self,
        interaction: discord.Interaction,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int,
    ) -> None:
        await self.bot.task_manager.task_command_main(interaction, 180, "txt2img", prompt, "stablediffusion_img2img_single", f"python3 /home/ubuntu/Daedalus/daedalus.py --function img2imgSingle --args \"#arg#prompt #qt#{prompt}#qt# #arg#init_img {init_img_url} #arg#seed {seed} #arg#scale {scale} #arg#strength {strength} #arg#ddim_steps {steps}\"")

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(img2img(bot))

class View_img2img_single(View):
    def __init__(self,
        bot: bot,
        taskID: int,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int
    ):
        txt2img = bot.get_cog("txt2img")

        super().__init__(timeout=None)

        #self.add_item(Button__txt2img_retry(txt2img, prompt, height, width, scale, steps, plms, False))
        #self.add_item(Button__txt2img_revise(txt2img, prompt, height, width, seed, scale, steps, plms, False))

class Modal_img2img_revise(Modal):
    def __init__(self,
        img2imgCog,
        prompt: str,
        init_img_url: str,
        seed: int,
        scale: float,
        strength: float,
        steps: int,
        batch: bool
    ) -> None:
        super().__init__(title="Revise img2img task")
        self.img2imgCog = img2imgCog
        self.batch = batch
        self.init_img_url = init_img_url

        self.promptField = discord.ui.TextInput(label="Prompt", style=discord.TextStyle.paragraph, placeholder="String", default=prompt, required=True)
        self.add_item(self.promptField)
        self.seedField = discord.ui.TextInput(label="Seed", style=discord.TextStyle.short, placeholder="Integer (random if empty)", default=seed, required=False)
        self.add_item(self.seedField)
        self.scaleField = discord.ui.TextInput(label="Scale", style=discord.TextStyle.short, placeholder="Float", default=scale, required=True)
        self.add_item(self.scaleField)
        self.strengthField = discord.ui.TextInput(label="Strength", style=discord.TextStyle.short, placeholder="Float", default=strength, required=True)
        self.add_item(self.strengthField)

        if not self.batch:
            self.stepsField = discord.ui.TextInput(label="Steps", style=discord.TextStyle.short, placeholder="Integer", default=steps, required=True)
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

            steps = self.stepsField.value

        if self.init_img_url is None:
            await self.img2imgCog.function_img2img(interaction,
                prompt,
                self.init_img_url,
                seed,
                scale,
                strength,
                steps,
                self.batch
            )
            
        return await super().on_submit(interaction)