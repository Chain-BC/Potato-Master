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

# Current Modules: fun, hg,
modules = ['fun', 'hg']  # These will be all ENABLED by default


# When bot is ready to go
@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    for module in modules:  # Loads all modules one by one until it cannot (big shocker)
        try:
            await bot.load_extension(module)
        except commands.ExtensionFailed:
            print(f'{module.capitalize()} failed to load!')
            raise commands.ExtensionFailed
        else:
            print(f'{module.capitalize()} has loaded.')


@bot.event
async def on_guild_join(guild):
    # Database
    mongo_client = pymongo.MongoClient("mongodb://localhost:27017/")

    # Guild Data
    guild_database = mongo_client[f"storage_{guild.id}"]
    configs_collection = guild_database["configs"]
    initial_hg_config = [
            {"guild": guild.name},
            {"running": False},
            {"stopping": False},
            {"user_changeable": {
                "day_msg": 'Day {day} incoming!',
                "recover_msg": 'Has recovered from their wounds!',
                "revive_msg": 'Has revived!',
                "only_custom_messages": False
            }}
        ]
    for dictionary in initial_hg_config:
        filter_dict = tuple(dictionary.items())
        filter_dict = {f"{filter_dict[0][0]}": {"$exists": True}}
        configs_collection.update_one(filter_dict, {"$set": dictionary}, upsert=True)


# COMMAND RELATING TO MODULES HERE
@bot.hybrid_command(name='module', description='Reload, unload or load modules.')
@commands.guild_only()
async def modify_modules(ctx: commands.Context, opt: typing.Literal["reload", "unload", "load"], value: str = None):
    discord_id = os.environ['DISCORD_ID']  # IF SELF HOSTING, SET discord_id TO YOUR DISCORD ID
    if ctx.author.id == int(discord_id):
        if opt == 'load':
            try:
                await bot.load_extension(value)
            except commands.ExtensionFailed:
                await ctx.send(f"{value.capitalize()} failed to load!", ephemeral=True)
                raise commands.ExtensionFailed
            except commands.ExtensionNotFound:
                await ctx.send("No such extension.", ephemeral=True)
                raise commands.ExtensionNotFound
            except commands.ExtensionAlreadyLoaded:
                await ctx.send(f"{value.capitalize()} was already loaded.", ephemeral=True)
                raise commands.ExtensionAlreadyLoaded
            except commands.NoEntryPointError:
                await ctx.send("Module not set up correctly.", ephemeral=True)
                raise commands.NoEntryPointError
            else:
                modules.append(value)
                await ctx.send(f"{value.capitalize()} loaded.", ephemeral=True)
        elif opt == 'unload':
            try:
                await bot.unload_extension(value)
            except commands.ExtensionNotFound:
                await ctx.send("No such extension.", ephemeral=True)
                raise commands.ExtensionNotFound
            except commands.ExtensionNotLoaded:
                await ctx.send(f"{value.capitalize()} was not loaded or does not exist.", ephemeral=True)
                raise commands.ExtensionNotLoaded
            else:
                modules.remove(value)
                await ctx.send(f"{value.capitalize()} unloaded.", ephemeral=True)
        else:
            if value is None or value == '':
                for module in modules:
                    try:
                        await bot.reload_extension(module)
                    except commands.ExtensionFailed:
                        await ctx.send(f"{module.capitalize()} failed to reload!", ephemeral=True)
                        raise commands.ExtensionFailed
                    except commands.ExtensionNotFound:
                        await ctx.send(f"{module.capitalize()} not found! Did you delete it by accident?",
                                       ephemeral=True)
                        raise commands.ExtensionNotFound
                    except commands.NoEntryPointError:
                        await ctx.send("Module not set up correctly.", ephemeral=True)
                        raise commands.NoEntryPointError
                    else:
                        await ctx.send(f"{module.capitalize()} reloaded.", ephemeral=True)
            else:
                try:
                    await bot.reload_extension(value)
                except commands.ExtensionFailed:
                    await ctx.send(f"{value.capitalize()} failed to reload!", ephemeral=True)
                    raise commands.ExtensionFailed
                except commands.ExtensionNotLoaded:
                    await ctx.send(f"{value.capitalize()} was not loaded!", ephemeral=True)
                    raise commands.ExtensionNotLoaded
                except commands.ExtensionNotFound:
                    await ctx.send(f"{value.capitalize()} not found! Did you delete it by accident?", ephemeral=True)
                    raise commands.ExtensionNotFound
                except commands.NoEntryPointError:
                    await ctx.send("Module not set up correctly.", ephemeral=True)
                    raise commands.NoEntryPointError
                else:
                    await ctx.send(f"{value.capitalize()} reloaded.", ephemeral=True)
    else:
        await ctx.send('You are not allowed to do this!', ephemeral=True)


@bot.hybrid_command(name='sync', description='Sync globally or to the current server.')
@commands.guild_only()
async def sync_commands(ctx: commands.Context, opt: typing.Literal['global', 'current']):
    discord_id = os.environ['DISCORD_ID']  # IF SELF HOSTING, SET discord_id TO YOUR DISCORD ID
    if ctx.author.id == int(discord_id):
        if opt == 'global':
            synced = await bot.tree.sync()
            await ctx.send(f"Synced {len(synced)} commands globally.", ephemeral=True)
        else:
            synced = await bot.tree.sync(guild=discord.Object(id=ctx.guild.id))
            await ctx.send(f"Synced {len(synced)} commands to the current guild.", ephemeral=True)
    else:
        await ctx.send('You are not allowed to do this!', ephemeral=True)


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
handler = logging.FileHandler(filename='../discord.log', encoding='utf-8', mode='w')
bot.run(os.environ['TOKEN'], log_handler=handler)
# log_level=logging.DEBUG ^ for extra useful logging
