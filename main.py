# https://github.com/ChainBoy300/Potato-Master-Bot
import os
import discord
import random
from APIs import get_meme

# Intents (REQUIRED)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)


# When bot is ready to go
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


# For various commands, will move some of them to / commands.
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    msg = message.content

    if msg.lower().startswith('%help'):
        await message.channel.send('No help for you sucka')

    if msg.lower().startswith('are you a robot?'):
        no = ['No.', 'Nope', 'NO!', 'Please stop asking.', 'EVERYONE keeps asking that, and the answer is NO!']
        await message.channel.send(random.choice(no))

    # MEMES
    if msg.lower().startswith('%meme'):
        await message.channel.send(get_meme())

    # Are you racist?
    if msg.lower().startswith('are you racist?'):
        await message.channel.send('Are you?')

# Important bot stuff
client.run(os.environ['TOKEN'])
