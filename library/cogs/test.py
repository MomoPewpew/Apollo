from code import interact
import discord
from discord import app_commands
from discord.ext.commands import Cog
from .. import bot

COG_NAME = "test"

class Test(Cog):
    def __init__(self, bot:bot) -> None:
        self.bot = bot
        super().__init__()

    @app_commands.command(
        name="instanceon"
    )
    async def command_instanceon(
        self, interaction: discord.Interaction
    ) -> None:
        self.bot.instance_manager.start_ec2()

    @app_commands.command(
        name="instanceoff"
    )
    async def command_instanceoff(
        self, interaction: discord.Interaction
    ) -> None:
        self.bot.instance_manager.stop_ec2()
    
    @app_commands.command(
        name="testcommand"
    )
    async def command_testcommand(
        self, interaction: discord.Interaction
    ) -> None:
        self.bot.instance_manager.hibernate_ec2()

    @Cog.listener()
    async def on_ready(self) -> None:
        if not self.bot.ready:
            self.bot.cog_manager.ready_up(COG_NAME)

async def setup(bot) -> None:
    await bot.add_cog(Test(bot))