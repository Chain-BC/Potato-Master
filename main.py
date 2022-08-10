# https://github.com/ChainBoy300/Potato-Master-Bot
import asyncio
import os
import discord
import random
import logging
from discord.ext import commands
from APIs import get_meme, get_wholesomememe, get_dankmeme

# Intents (REQUIRED)
intents = discord.Intents.all()

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
@bot.command(name='meme', description='Get a meme, options are: wholesome and dank. For random leave empty',
             aliases=['memes'], help='Wholesome, Dank, or Random')
async def memes(ctx, memetype: str = ''):
    if memetype == '' or memetype.lower() == 'random':
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
    else:
        await ctx.channel.send('That is not a supported type of meme!')


# The "Help" command.
@bot.command(name='help?', description='The TRUE help command.', hidden=True)
async def nohelp(ctx):
    await ctx.channel.send('No help for you sucka!!!1!')


# Fight command, in the future it will be much different.
@bot.command(name='fight')
async def fight(ctx, who: discord.User = None):
    # Takes the author of the message, or whoever sends the command.
    author = ctx.author
    if ctx.author.bot:
        return
    if who:
        await ctx.send('IS NOT SMART ==> {}'.format(who.mention))
        await asyncio.sleep(1)
        await ctx.send('Would you like to \'Fight back\' or \'Give up\'?')

        def check(message):
            return message.author == who and message.channel == ctx.channel and \
                   message.content.lower() in ['fight back', 'give up']

        msg = await bot.wait_for("message", check=check, timeout=120)
        if msg.content.lower() == 'fight back':
            await ctx.send('Is stinky ==> {}'.format(author.mention))
        else:
            await ctx.send('{} gave up!'.format(who.mention))
    else:
        await ctx.send('Mention someone to fight in the command.')


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
bot.run(os.environ['TOKEN'], log_handler=handler)
# log_level=logging.DEBUG ^ for extra useful logging
