import discord
import typing
from discord.ext import commands


# Developer Commands Module
class Dev(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    # SYNC COMMAND
    @commands.command(name='sync_dev')
    @commands.guild_only()
    async def sync(self, ctx: commands.Context,
                   guilds: commands.Greedy[discord.Object],
                   spec: typing.Optional[typing.Literal["~", "*", "^"]] = None) -> None:
        if not guilds:
            if spec == "~":
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "*":
                ctx.bot.tree.copy_global_to(guild=ctx.guild)
                synced = await ctx.bot.tree.sync(guild=ctx.guild)
            elif spec == "^":
                ctx.bot.tree.clear_commands(guild=ctx.guild)
                await ctx.bot.tree.sync(guild=ctx.guild)
                synced = []
            else:
                synced = await ctx.bot.tree.sync()

            await ctx.send(
                f"Synced {len(synced)} commands {'globally' if spec is None else 'to the current guild.'}"
            )
            return

        ret = 0
        for guild in guilds:
            try:
                await ctx.bot.tree.sync(guild=guild)
            except discord.HTTPException:
                pass
            else:
                ret += 1

            await ctx.send(f"Synced the tree to {ret}/{len(guilds)}.")

    # The test command, does nothing
    @commands.hybrid_command(name='test', description="Testing")
    async def test(self, ctx: commands.Context):
        await ctx.send('Test Complete!')


# Add the cog to the bot
async def setup(bot):
    await bot.add_cog(Dev(bot))
