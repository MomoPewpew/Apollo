import asyncio
from ..cogs.tag import Tag
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

class Bot(BotBase):
    def __init__(self):
        self.PREFIX = PREFIX
        self.ready = False
        self.cogs_ready = Ready_cogs()
        self.user_manager = Manage_users()
        self.prompt_manager = Manage_prompts()
        self.server_manager = Manager_server()
        
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
            print("Connecting...")
            await bot.start(self.TOKEN, reconnect=True)

    def run(self, version):
        self.VERSION = version

        with open("./library/bot/token.0", "r", encoding="utf-8") as tf:
            self.TOKEN = tf.read()
        
        asyncio.run(self.main())

    ##Not sure if this is going to actually work. So far it doesn't hurt.
    async def process_commands(self, message):
        ctx = await self.get_context(message, cls=Context)

        if ctx.command is not None and ctx.guild is not None:
            if self.ready:
                await self.invoke(ctx)
            else:
                await ctx.send("I'm not ready to receive commands. Please wait a few seconds.")

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

            print("Awaiting cog setup...")
            while not self.cogs_ready.all_ready():
                await asyncio.sleep(0.5)
            
            self.ready = True
            print("Bot ready. Awaiting inputs.")

        else:
            print("Bot reconnected")

    async def on_message(self, message):
        if message.author.id == self.user.id:
            return
        
        await bot.process_commands(message)

class Ready_cogs(object):
    def __init__(self):
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog):
        setattr(self, cog, True)
        print(f"  {cog} cog ready")

    def all_ready(self):
        return all([getattr(self, cog) for cog in COGS])

class Manage_users(object):
    ##This is handled via a separate function in case we want to hardcode certain users to other id's (such as rawb having two discord accounts, or a user wanting a separate database entry for the same discord user for some reason)
    ##This is also a good place to ensure that the user even has an entry to begin with
    def get_user_id(self, user):
        userID = user.id

        db.execute("INSERT OR IGNORE INTO users (userID) VALUES (?)",
            userID)

        return userID
    
    def has_tag(self, userID, tag_name):
        return self.has_tag_active(userID, tag_name) and self.has_tag_inactive(userID, tag_name)

    def has_tag_active(self, userID, tag_name):
        if tag_name in self.get_tags_active(userID):
            return True
        else:
            return False
    
    def has_tag_inactive(self, userID, tag_name):
        if tag_name in self.get_tags_inactive(userID):
            return True
        else:
            return False

    def get_tags_active(self, userID):
        tags = db.record("SELECT promptTagsActive FROM users WHERE userID = ?", userID)
        tagsArray = tags.split(",")
        return tagsArray

    def get_tags_inactive(self, userID):
        tags = db.record("SELECT promptTagsInactive FROM users WHERE userID = ?", userID)
        tagsArray = tags.split(",")
        return tagsArray
    
    def add_tag_active(self, userID, tag_name):
        db.execute("UPDATE users SET promptTagsActive = promptTagsActive + ? WHERE UserID = ?",
            tag_name + ",",
            userID)
    
    def add_tag_inactive(self, userID, tag_name):
        db.execute("UPDATE users SET promptTagsActive = promptTagsInctive + ? WHERE UserID = ?",
            tag_name + ",",
            userID)

class Manage_prompts(object):
    def add_prompt(self, promptType, promptString, userID, promptTags):
        pass

    def get_prompts(self, userID, tags):
        pass

class Manager_server(object):
    def get_server(self):
        pass

    def get_queue_time(self, server):
        pass

    def send_intruction(self, instruction):
        pass

bot = Bot()