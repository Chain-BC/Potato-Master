# https://github.com/ChainBoy300/Potato-Master-Bot
import os
import discord
import random
import typing
import logging
import pymongo
from discord.ext import commands


# Initialize the Bot
class Bot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.all()
        super().__init__(command_prefix=commands.when_mentioned_or('$$'), intents=intents)


# BOT and USER
bot = Bot()
user = bot.user

# Modules: fun, hg, dev
modules = ['fun', 'hg']  # These will be all ENABLED by default


# When bot is ready to go
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    for module in modules:  # Loads all modules one by one until it cannot (big shocker)
        await bot.load_extension(module)
        print(f'{module.capitalize()} has loaded.')


@bot.event
async def on_guild_join(guild):
    # Database
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")

    # Guild Data
    guild_database = mongo_client[f"storage_{guild.id}"]
    configs_collection = guild_database["configs"]
    initial_hg_config = [
        {"_id": 0, "guild": guild.name},
        {"_id": 1, "running": False},
        {"_id": 2, "stopping": False},
        {"_id": 3, "force_stopping": False},
        {"_id": 4, "only_custom_messages": False}
    ]
    configs_collection.insert_many(initial_hg_config)


# COMMAND RELATING TO MODULES HERE
@bot.hybrid_command(name='modmod', description='Reload, unload or load modules.')
@commands.guild_only()
@commands.has_role('Potato Master MASTER')
async def modify_modules(ctx: commands.Context, opt: typing.Literal["reload", "unload", "load"], value: str = None):
    if opt == 'reload':
        if value is None or value == '':
            for module in modules:
                await bot.reload_extension(module)
                await ctx.send(f'{module.capitalize()} reloaded.', ephemeral=True)
        else:
            await bot.reload_extension(value)
            await ctx.send(f"{value.capitalize()} reloaded.", ephemeral=True)
    elif opt == 'load':
        await bot.load_extension(value)
        await ctx.send(f"{value.capitalize()} loaded.", ephemeral=True)
    elif opt == 'unload':
        await bot.unload_extension(value)
        await ctx.send(f"{value.capitalize()} unloaded.", ephemeral=True)


@bot.hybrid_command(name='sync', description='Sync globally or to the current server.')
@commands.guild_only()
@commands.has_role('Potato Master MASTER')
async def sync_commands(ctx: commands.Context, opt: typing.Literal['global', 'current']):
    if opt == 'global':
        synced = await bot.tree.sync()
        await ctx.send(f"Synced {len(synced)} commands globally.", ephemeral=True)
    elif opt == 'current':
        synced = await bot.tree.sync(guild=discord.Object(id=ctx.guild.id))
        await ctx.send(f"Synced {len(synced)} commands to the current guild.", ephemeral=True)


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
