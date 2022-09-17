import discord
import typing
import asyncio
from APIs import get_meme, get_wholesomememe, get_dankmeme
from discord.ext import commands
from discord import app_commands


# Fun Commands Module
class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # The meme command
    @app_commands.command(name='meme',
                          description='Get a meme, options are: wholesome and dank. For random leave empty',
                          )
    @app_commands.describe(memetype='Kind of Meme')
    @app_commands.rename(memetype='meme_type')
    async def memes(self, interaction: discord.Interaction,
                    memetype: typing.Optional[typing.Literal['random', 'wholesome', 'dank']] = None):
        embed = discord.Embed(color=discord.Colour.blue())
        if memetype is None or memetype == 'random':
            await interaction.response.send_message('Here is your random meme!',
                                                    embed=embed.set_image(url=get_meme()))
        elif memetype == 'wholesome':
            await interaction.response.send_message('Here is your wholesome meme!',
                                                    embed=embed.set_image(url=get_wholesomememe()))
        elif memetype == 'dank':
            await interaction.response.send_message('Here is your dank meme!',
                                                    embed=embed.set_image(url=get_dankmeme()))

    # Fight command, in the future it will be much different.
    @app_commands.command(name='fight', description='Challenge someone\'s sorry self.')
    async def fight(self, interaction: discord.Interaction, who: discord.User):
        author = interaction.user
        if who:
            await interaction.response.send_message('IS NOT SMART ==> {}'.format(who.mention))
            await asyncio.sleep(1)
            await interaction.channel.send('Would you like to \'Fight back\' or \'Give up\'?')

            def check(message):
                return message.author == who and message.channel == interaction.channel and \
                       message.content.lower() in ['fight back', 'give up']

            msg = await self.bot.wait_for("message", check=check, timeout=120)
            if msg.content.lower() == 'fight back':
                await interaction.followup.send('Is stinky ==> {}'.format(author.mention))
            else:
                await interaction.followup.send('{} gave up!'.format(who.mention))


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Fun(bot))
