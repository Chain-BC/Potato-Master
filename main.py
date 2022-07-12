# https://github.com/ChainBoy300/Potato-Master-Bot
import os
import discord

# Client variable
client = discord.Client()


# When bot is ready to go
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


# When message is sent to bot
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('%test'):
        await message.channel.send('All Good')


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('%help'):
        await message.channel.send('No help for you sucka!')


# Important bot stuff

client.run(os.environ['TOKEN'])
