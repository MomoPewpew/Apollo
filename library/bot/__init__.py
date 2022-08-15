import asyncio
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from glob import glob

import discord
from discord import Intents
from discord import app_commands
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound

from ..db import db

PREFIX = "/"
APP_ID = 1008367927533244547
OWNER_IDS = [108296164599734272]
COGS = [path.split("\\")[-1][:-3] for path in glob("./library/cogs/*.py")]
GUILDS = [discord.Object(id = 1008374239688151111)]

class Ready(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"  {cog} cog ready")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])

class Bot(BotBase):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.cogs_ready = Ready()
        
        self.scheduler = AsyncIOScheduler()

        intents = Intents.default()
        intents.members = True

        db.autosave(self.scheduler)
        super().__init__(
            command_prefix = PREFIX,
            application_id = APP_ID,
            owner_ids = OWNER_IDS,
            intents=intents
        )
    
    async def setup(self):
        for cog in COGS:
            await self.load_extension( f"library.cogs.{cog}")
            print(f"  {cog} cog loaded")
        
        print("Setup complete")

    async def setup_hook(self):
        for guild in GUILDS:
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

    async def main(self):
        async with bot:
            print("Running setup...")
            await self.setup()
            print("Running bot...")
            await bot.start(self.TOKEN, reconnect=True)

    def run(self, version):
        self.VERSION = version

        with open("./library/bot/token.0", "r", encoding="utf-8") as tf:
            self.TOKEN = tf.read()
        
        asyncio.run(self.main())

    async def on_connect(self):
        print("  Bot connected")

    async def on_disconnect(self):
        print("Bot disconnected")
    
    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            await args[0].send("Something went wrong.")
        
        await self.stdout.send("An error has occurred.")
        raise
    
    async def on_command_error(self, ctx, exc):
        if isinstance(exc, CommandNotFound):
            pass
        elif hasattr(exc, "original"):
            raise exc.original
        else:
            raise exc

    async def on_ready(self):
        if not self.ready:
            self.stdout = self.get_channel(1008386261368705024)
            self.scheduler.start()

            while not self.cogs_ready.all_ready():
                await asyncio.sleep(0.5)
            
            self.ready = True
            print("Bot ready. Awaiting inputs.")

        else:
            print("Bot reconnected")

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        
        await self.process_commands(message)

bot = Bot()