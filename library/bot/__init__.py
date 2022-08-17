import asyncio
from typing import List
from xmlrpc.client import Boolean
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from glob import glob

import discord
from discord import Intents
from discord.ext.commands import Bot as BotBase, CommandNotFound, Cog, Context, errors

from ..db import db

PREFIX = "/"
APP_ID = 1008367927533244547
OWNER_IDS = [108296164599734272]
COGS = [path.split("\\")[-1][:-3] for path in glob("./library/cogs/*.py")]
GUILDS = [discord.Object(id = 1008374239688151111)]

class Bot(BotBase):
    def __init__(self) -> None:
        self.ready = False
        self.cog_manager = Cog_manager()
        self.user_manager = User_manager()
        self.prompt_manager = Prompt_manager()
        self.task_manager = Task_manager()

        intents = Intents.default()
        intents.members = True

        super().__init__(
            command_prefix = PREFIX,
            application_id = APP_ID,
            owner_ids = OWNER_IDS,
            intents=intents
        )
    
    ###Setup
    def run(self, version: str) -> None:
        self.VERSION = version

        with open("./library/bot/token.0", "r", encoding="utf-8") as tf:
            self.TOKEN = tf.read()
        
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

        else:
            print("Bot reconnected")

    async def on_message(self, message: discord.Message) -> None:
        if message.author.id == self.user.id:
            return
        
        await bot.process_commands(message)

    async def on_error(self, event_method: str, /, *args, **kwargs) -> None:
        if err == "on_command_error":
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

class Cog_manager(object):
    def __init__(self) -> None:
        for cog in COGS:
            setattr(self, cog, False)

    def ready_up(self, cog: Cog) -> None:
        setattr(self, cog, True)
        print(f"  {cog} cog ready")

    def all_ready(self) -> Boolean:
        return all([getattr(self, cog) for cog in COGS])

class User_manager(object):
    ##This is handled via a separate function in case we want to hardcode certain users to other id's (such as rawb having two discord accounts, or a user wanting a separate database entry for the same discord user for some reason)
    ##This is also a good place to ensure that the user even has an entry to begin with
    def get_user_id(self, user: int) -> int:
        userID = user.id

        db.execute("INSERT OR IGNORE INTO users (userID) VALUES (?)",
            userID)

        return userID
    
    def has_tag(self, userID: int, tag_name: str) -> Boolean:
        return self.has_tag_active(userID, tag_name) or self.has_tag_inactive(userID, tag_name)

    def has_tag_active(self, userID: int, tag_name: str) -> Boolean:
        if tag_name in self.get_tags_active(userID):
            return True
        else:
            return False
    
    def has_tag_inactive(self, userID: int, tag_name: str) -> Boolean:
        if tag_name in self.get_tags_inactive(userID):
            return True
        else:
            return False

    def get_tags_active(self, userID: int) -> list[str]:
        tags = db.record("SELECT promptTagsActive FROM users WHERE userID = ?", userID)
        tagsArray = tags[0][1:-1].split(",")
        return tagsArray

    def get_tags_inactive(self, userID: int) -> list[str]:
        tags = db.record("SELECT promptTagsInactive FROM users WHERE userID = ?", userID)
        tagsArray = tags[0][1:-1].split(",")
        return tagsArray
    
    def add_tag_active(self, userID: int, tag_name: str):
        db.execute("UPDATE users SET promptTagsActive = promptTagsActive || ? WHERE UserID = ?",
            tag_name + ",",
            userID)
    
    def add_tag_inactive(self, userID: int, tag_name: str):
        db.execute("UPDATE users SET promptTagsInactive = promptTagsInactive || ? WHERE UserID = ?",
            tag_name + ",",
            userID)
    
    def remove_tag(self, userID: int, tag_name: str):
        db.execute("UPDATE users SET promptTagsActive = replace(promptTagsActive, ?, ',') WHERE promptTagsActive LIKE ? AND UserID = ?",
            "," + tag_name + ",",
            "%," + tag_name + ",%",
            userID)
        
        db.execute("UPDATE users SET promptTagsInactive = replace(promptTagsInactive, ?, ',') WHERE promptTagsInactive LIKE ? AND UserID = ?",
            "," + tag_name + ",",
            "%," + tag_name + ",%",
            userID)

class Prompt_manager(object):
    def add_prompt(self, promptType: str, promptString: str, userID: int, promptTags: str) -> None:
        pass

    def get_prompts(self, userID: int, tags: List[str]) -> List[str]:
        pass

class Task_manager(object):
    def add_task(self, receiveType: str, userID: int, channelID: int, instruction: str) -> None:
        pass

bot = Bot()