from discord.ext import commands
from asyncio import TimeoutError
import discord


class Logging:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        description="The base class for all logging-related commands.",
        brief="Adjust logging-related shit.",
        aliases=['logging_create', 'lognew', 'logcreate', 'lnew', 'lcreate']
    )
    async def logging_new(self, ctx, *, channel: discord.TextChannel=None):
        channel = channel or ctx.channel
        if channel.id in self.bot.logging_channels:
            raise discord.CommandError("This guild already has a logging channel.")
        m = await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_info:483063870655823873> I will turn {channel.mention} into a logging channel."
                            f"\nReact with <:nano_check:484247886461403144> to confirm."
            )
        )
        await m.add_reaction(":nano_check:484247886461403144")

        def check(_r, _u):
            return _u == ctx.author and str(_r) == "<:nano_check:484247886461403144>"

        try:
            await self.bot.wait_for("reaction_add", check=check, timeout=15.0)
        except TimeoutError:
            await m.delete()
            return
        else:
            await m.delete()
            await self.bot.db.execute("INSERT INTO logging VALUES ($1);", channel.id)
            self.bot.logging_channels.append(channel.id)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="<:nano_check:484247886461403144> Success."
                )
            )


def setup(bot):
    bot.add_cog(Logging(bot))
