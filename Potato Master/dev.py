import typing
import discord
from discord import app_commands
from discord.ext import commands
from hg import MongoDB

"""

    This module is solely for the purpose of developing and testing new commands that could potentially mess up the
    bot or could lead to something going wrong with the core functionality of the bot.
    
    Or just if I want to leave some existing command alone while I make a new version of it here.

"""


# Hunger Games MESSAGES module
class Dev(commands.GroupCog, name='dev', description='Commands in development.'):
    def __init__(self, bot):
        self.bot = bot


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Dev(bot))
