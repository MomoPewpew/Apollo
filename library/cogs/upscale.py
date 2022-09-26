import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot

COG_NAME = "upscale"

class upscale(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="upscale_real-esrgan",
        description = "General purpose image upscaling"
    )
    @app_commands.describe(
        url = "The URL to the original image. This must end in .png, .jpg, .jpeg or .bmp"
    )
    async def command_style_realesrgan(
        self,
        interaction: discord.Interaction,
        url: str
    ) -> None:
        await self.function_style_realesrgan(
            interaction,
            url
        )

    async def function_style_realesrgan(self, interaction: discord.Interaction, url: str) -> None:
        if not self.bot.task_manager.is_url_image(url):
            await interaction.response.send_message("The URL that you have provided does not appear to be an image.", ephemeral=True)
            return

        await self.bot.task_manager.task_command_main(interaction, 20, None, None, "image", f"python3 /home/ubuntu/Daedalus/daedalus.py --function realesrgangan --sourceURL \"{url}\"")
    
    @app_commands.command(
        name="upscale_gfpgan",
        description = "Upscaling with face correction"
    )
    @app_commands.describe(
        url = "The URL to the original image. This must end in .png, .jpg, .jpeg or .bmp"
    )
    async def command_style_gfpgan(
        self,
        interaction: discord.Interaction,
        url: str
    ) -> None:
        await self.function_style_gfpgan(
            interaction,
            url
        )

    async def function_style_gfpgan(self, interaction: discord.Interaction, url: str) -> None:
        if not self.bot.task_manager.is_url_image(url):
            await interaction.response.send_message("The URL that you have provided does not appear to be an image.", ephemeral=True)
            return

        await self.bot.task_manager.task_command_main(interaction, 20, None, None, "image", f"python3 /home/ubuntu/Daedalus/daedalus.py --function realesrgangan --sourceURL \"{url}\" --args \"#arg#face_enhance\"")

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(upscale(bot))