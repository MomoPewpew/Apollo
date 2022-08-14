import discord
from discord.ext import commands
import logging

client = commands.Bot(command_prefix='/', description="This is a Helper Bot")

###Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

###Events
@client.event
async def on_ready():
    print('------')
    print('Logged in as')
    print('{0.user}'.format(client))
    print(client.user.id)
    print('------')

##@bot.listen()
##async def on_message(message):
    ##await bot.process_commands(message)

###Commands
@client.command()
async def ping(ctx):
    await ctx.send('pong')

client.run('TOKENHERE')