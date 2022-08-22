# https://github.com/ChainBoy300/Potato-Master-Bot
import os
import discord
import random
import typing
import logging
from discord.ext import commands


# Initialize the Bot
class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix="$", intents=intents)


# BOT and USER
bot = Bot()
user = bot.user

# Modules
modules = ['fun', 'hg', 'dev']  # These will be all ENABLED by default


# When bot is ready to go
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    for module in modules:  # Loads all modules one by one until it cannot
        await bot.load_extension(module)
        print('%s has loaded.' % module.capitalize())


# COMMAND RELATING TO MODULES HERE
@bot.command(name='modmod', description='Reload, unload or load modules.')
@commands.guild_only()
async def modify_modules(ctx, opt: typing.Literal["reload", "unload", "load"], value=None):
    if opt == 'reload':
        if value is None or value == '':
            for module in modules:
                await bot.reload_extension(module)
                await ctx.send('%s reloaded.' % module.capitalize())
        else:
            await bot.reload_extension(value)
            await ctx.send(value.capitalize() + " reloaded.")
    elif opt == 'load':
        await bot.load_extension(value)
        await ctx.send(value.capitalize() + " loaded.")
    elif opt == 'unload':
        await bot.unload_extension(value)
        await ctx.send(value.capitalize() + " unloaded.")


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
