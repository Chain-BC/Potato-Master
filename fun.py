import discord
import asyncio
from APIs import get_meme, get_wholesomememe, get_dankmeme
from discord.ext import commands


# Fun module, for fun commands
class Fun(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # The meme command
    @commands.hybrid_command(name='meme',
                             description='Get a meme, options are: wholesome and dank. For random leave empty',
                             aliases=['memes'],
                             help='Wholesome, Dank, or Random')
    async def memes(self, ctx, memetype: str = ''):
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
    @commands.command(name='thehelp', description='The TRUE help command.', hidden=True)
    async def nohelp(self, ctx):
        await ctx.channel.send('No help for you sucka!!!1!')

    # Fight command, in the future it will be much different.
    @commands.command(name='fight')
    async def fight(self, ctx, who: discord.User = None):
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

            msg = await self.bot.wait_for("message", check=check, timeout=120)
            if msg.content.lower() == 'fight back':
                await ctx.send('Is stinky ==> {}'.format(author.mention))
            else:
                await ctx.send('{} gave up!'.format(who.mention))
        else:
            await ctx.send('Mention someone to fight in the command.')


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Fun(bot))
