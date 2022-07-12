# https://github.com/ChainBoy300/Potato-Master-Bot
import os
import discord
import requests
import json

client = discord.Client()


def get_meme():
    response = requests.get("https://meme-api.herokuapp.com/gimme/wholesomememes")
    json_data = json.loads(response.text)
    meme = json_data['url']
    return(meme)


# When bot is ready to go
@client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))


# For %help and %test
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('%help'):
        await message.channel.send('No help for you sucka')

    if message.content.startswith('%test'):
        await message.channel.send('All good')

# MEMESSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS
    if message.content.startswith('%meme'):
        meme = get_meme()
        await message.channel.send(meme)


# Important bot stuff
client.run(os.environ['TOKEN'])
