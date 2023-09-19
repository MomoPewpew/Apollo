import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot

COG_NAME = "threedinpainting"

class threedinpainting(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        self.enabled = False
        super().__init__()

    @app_commands.command(
        name="3dinpainting",
        description = "Bring an image to life with a 3D animation"
    )
    @app_commands.describe(
        url = "The URL to the original image. This must end in .png, .jpg, .jpeg or .bmp",
        num_frames = "Total frame count. Default 240. Video length = num_frames / fps",
        fps = "Frames per second. Default 40.",
    )
    @app_commands.choices(style=
        [
            app_commands.Choice(name="Dolly Zoom-In", value="/plugins/3d-photo-inpainting/dolly_zoom_in.yml")
        ]
    )
    async def command_style_3dinpainting(
        self,
        interaction: discord.Interaction,
        url: str,
        style: app_commands.Choice[str] = "/plugins/3d-photo-inpainting/dolly_zoom_in.yml",
        num_frames: int = 240,
        fps: int = 40
    ) -> None:
        await self.function_style_3dinpainting(
            interaction,
            url,
            style,
            num_frames,
            fps
        )

    async def function_style_3dinpainting(self, interaction: discord.Interaction, url: str, style: str, num_frames: int, fps: int) -> None:
        if not self.bot.task_manager.is_url_image(url):
            await interaction.response.send_message("The URL that you have provided does not appear to be an image.", ephemeral=True)
            return

        await self.bot.task_manager.task_command_main(interaction, 600, None, None, "3dInPainting", f"python3 {self.bot.daedalusBasePath}/daedalus.py --function ThreeDInPaint --sourceURL \"{url}\" --args \"#arg#num_frames {num_frames} #arg#fps {fps} #arg#config {self.bot.daedalusBasePath}{style}\"")

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(threedinpainting(bot))