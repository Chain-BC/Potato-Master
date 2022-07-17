# https://github.com/ChainBoy300/Potato-Master-Bot
import os
import discord
import random
import typing
import logging
from discord.ext import commands
from APIs import get_meme, get_wholesomememe, get_dankmeme, get_meirlmeme

# Intents (REQUIRED)
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

# CLIENT
bot = commands.Bot(command_prefix='$', intents=intents)
# USER
user = bot.user


# When bot is ready to go
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))


# The test command, does nothing
@bot.command(name='test')
async def test(ctx):
    await ctx.channel.send('Test Complete!')


# The meme command
@bot.command(name='meme', description='Get a random meme, options are: random, wholesome, dank, and meirl.')
async def memes(ctx, memetype: typing.Optional[str] = ''):
    if memetype is None:
        embed = discord.Embed(title='Here is your random meme!')
        embed.set_image(url=get_meme())
        await ctx.channel.send(embed=embed)
    elif memetype.lower() == 'wholesome':
        embed = discord.Embed(title='Here is your wholesome meme!')
        embed.set_image(url=get_wholesomememe())
        await ctx.channel.send(embed=embed)
    elif memetype.lower() == 'dank':
        embed = discord.Embed(title='Here is your dank meme!')
        embed.set_image(url=get_dankmeme())
        await ctx.channel.send(embed=embed)
    elif memetype.lower() == 'meirl':
        embed = discord.Embed(title='Here is your stupid meme.')
        embed.set_image(url=get_meirlmeme())
        await ctx.channel.send(embed=embed)


# The "Help" command.
@bot.command(name='help?', description='The TRUE help command.', hidden=True)
async def nohelp(ctx):
    await ctx.channel.send('No help for you sucka!!!1!')


# For various interactions with the bot.
@bot.event
async def on_message(message):
    if message.author == user:
        return
    channel = message.channel

    if message.content.lower().startswith('are you a robot?'):
        no = ['No.', 'Nope', 'NO!', 'Please stop asking.', 'EVERYONE keeps asking that, and the answer is NO!']
        await channel.send(random.choice(no))

    await bot.process_commands(message)


# BOT LOGGING AND BOT TOKEN
handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')
bot.run(os.environ['TOKEN'], log_handler=handler, log_level=logging.DEBUG)
