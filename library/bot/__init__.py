from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext.commands import Bot as BotBase
import discord

PREFIX = "/"
OWNER_IDS = [108296164599734272]
##BOZZA_MANSION = discord.Object(id = 1008374239688151111)

class Bot(BotBase):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.guild = None
        self.scheduler = AsyncIOScheduler()

        super().__init__(command_prefix=PREFIX, owner_ids = OWNER_IDS, intents=discord.Intents.default())
    
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
    
    async def on_ready(self):
        if not self.ready:
            print("bot ready")
            self.guild = self.get_guild(1008374239688151111)
            self.ready = True
        else:
            print("bot reconnected")

    async def on_message(self, message):
        pass

bot = Bot()