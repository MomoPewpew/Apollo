import discord
import logging

client = discord.Client()

###Logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))

@client.event
async def on_message(message):
    if message.author == client.user:
        return

##    if message.content.startswith('$hello'):
##        await message.channel.send('Hello!')

client.run('MTAwODM2NzkyNzUzMzI0NDU0Nw.GlBcBh.CWJAZvtmNk8evxKbDnWHzlVL_AwcdgvW1C2SOU')