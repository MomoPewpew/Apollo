from discord import Intents
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import Bot as BotBase
from discord.ext.commands import CommandNotFound

from ..db import db

PREFIX = "/"
OWNER_IDS = [108296164599734272]
##BOZZA_MANSION = discord.Object(id = 1008374239688151111)

class Bot(BotBase):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.guild = None
        self.scheduler = AsyncIOScheduler()

        intents = Intents.default()
        intents.members = True

        db.autosave(self.scheduler)
        super().__init__(
            command_prefix=PREFIX,
            owner_ids = OWNER_IDS,
            intents=intents
        )
    
    def run(self, version):
        self.VERSION = version

        with open("./library/bot/token.0", "r", encoding="utf-8") as tf:
            self.TOKEN = tf.read()
        
        print("running bot...")
        super().run(self.TOKEN, reconnect=True)

    async def on_connect(self):
        print("bot connected")

    async def on_disconnect(self):
        print("bot disconnected")
    
    async def on_error(self, err, *args, **kwargs):
        if err == "on_command_error":
            await args[0].send("Something went wrong.")
        
        channel = self.get_channel(1008386261368705024)
        await channel.send("An error has occurred.")
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
            self.ready = True
            print("bot ready")
            self.guild = self.get_guild(1008374239688151111)
            self.scheduler.start()

        else:
            print("bot reconnected")

    async def on_message(self, message):
        pass

bot = Bot()