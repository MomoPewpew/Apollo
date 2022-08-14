from operator import truediv
import discord
from discord import app_commands
import logging

###Finals
BOZZA_MANSION = discord.Object(id = 1008374239688151111)

###Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

##Init
class aclient(discord.Client):
    def __init__(self):
        super().__init__(intents=discord.Intents.default())
        self.synced = False

##Events
    async def on_ready(self):
        await self.wait_until_ready()
        if not self.synced:
            await tree.sync(guild = BOZZA_MANSION)
            self.synced = True
        print(f"We have logged in as {self.user}.")

client = aclient()
tree = app_commands.CommandTree(client)

##Commands
@tree.command(name = "ping", description = "A test command", guild = BOZZA_MANSION)
async def ping(interaction: discord.Interaction, name: str):
    await interaction.response.send_message(f"Hello {name}! I was made with Discord.py!", ephemeral = True)

client.run('TOKENHERE')