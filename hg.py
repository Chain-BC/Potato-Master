import discord
from discord import app_commands
from discord.ext import commands


# Hunger Games Module (Currently Placeholder)
class Hg(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name='hg', description='Main Hunger Games command. (PLACEHOLDER)')
    async def hungerGames(self, ctx):
        await ctx.channel.send('PLACEHOLDER')


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Hg(bot))