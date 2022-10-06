import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from glob import glob

import discord
from discord import Intents
from discord.ext.commands import Bot as BotBase, CommandNotFound, Context, errors

from ..db import db
from ..managers import cog_manager, prompt_manager, task_manager, user_manager, instance_manager, computerender_manager

import logging
import platform

APP_ID = 1008367927533244547
OWNER_IDS = [108296164599734272]
COGS = [path.split("\\" if platform.system() == "Windows" else "/")[-1][:-3] for path in glob("./library/cogs/*.py")]
GUILDS = [discord.Object(id = 1008374239688151111), discord.Object(id = 971479608664924202)]

class Bot(BotBase):
    daedalusBasePath = "/home/ubuntu/Daedalus"

    def __init__(self) -> None:
        self.ready = False
        self.cog_manager = cog_manager.Cog_manager(COGS)
        self.user_manager = user_manager.User_manager()
        self.prompt_manager = prompt_manager.Prompt_manager(self)
        self.task_manager = task_manager.Task_manager(self)
        self.instance_manager = instance_manager.Instance_manager(self)
        self.computerender_manager = computerender_manager.Computerender_manager(self)

        intents = Intents.default()
        intents.members = True

        super().__init__(
            command_prefix = "/",
            application_id = APP_ID,
            owner_ids = OWNER_IDS,
            intents=intents
        )
    
    ###Setup
    def run(self, version: str) -> None:
        self.VERSION = version

        with open("./library/bot/token.0", "r", encoding="utf-8") as tf:
            self.TOKEN = tf.read()
        
        with open("./library/bot/computerender.0", "r", encoding="utf-8") as tf:
            self.COMPUTERENDERKEY = tf.read()
        
        asyncio.run(self.main())
        return super().run()

    async def main(self) -> None:
        async with bot:
            print("Running setup...")
            await self.setup()
            print("Connecting...")
            await bot.start(self.TOKEN, reconnect=True)

    async def setup(self) -> None:
        for cog in COGS:
            await self.load_extension( f"library.cogs.{cog}")
            print(f"  {cog} cog loaded")
        
        print("Setup complete")

    async def setup_hook(self) -> None:
        for guild in GUILDS:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

        return await super().setup_hook()

    ##Not sure if this is going to actually work. So far it doesn't hurt.
    async def process_commands(self, message: discord.Message, /) -> None:
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                await self.invoke(ctx)
            else:
                await ctx.send("I'm not ready to receive commands. Please wait a few seconds.")
        return await super().process_commands(message)

    ###Listeners
    async def on_connect(self) -> None:
        print("  Bot connected")

    async def on_disconnect(self) -> None:
        print("Bot disconnected")

    async def on_ready(self) -> None:
        if not self.ready:
            self.stdout = self.get_channel(1008386261368705024)

            self.scheduler = AsyncIOScheduler(timezone="utc")
            db.autosave(self.scheduler)
            self.scheduler.start()

            print("Awaiting cog setup...")
            while not self.cog_manager.all_ready():
                await asyncio.sleep(0.5)
            
            self.ready = True
            print("Bot ready. Awaiting inputs.")
            
            await self.instance_manager.update_instance_statuses()
            await self.task_manager.start_task_backlog()
        else:
            print("Bot reconnected")
        
    async def on_message(self, message: discord.Message) -> None:
        if message.author.id == self.user.id:
            return
        
        await bot.process_commands(message)
    
    async def on_error(self, event_method: str, /, *args, **kwargs) -> None:
        if event_method == "on_command_error":
            await args[0].send("Something went wrong.")
        
        await self.stdout.send("An error has occurred.")
        raise
    
    async def on_command_error(self, context: Context, exception: errors.CommandError, /) -> None:
        if isinstance(exception, CommandNotFound):
            pass
        elif hasattr(exception, "original"):
            raise exception.original
        else:
            raise exception
        return await super().on_command_error(context, exception)

logging.basicConfig(level=logging.INFO)
bot = Bot()