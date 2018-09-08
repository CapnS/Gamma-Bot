from discord.ext import commands
from asyncpg.exceptions import StringDataRightTruncationError as SDRTE
import discord


class Settings:
    """
    Change server configuration.
    Currently changeable: prefix, muted role
    """
    def __init__(self, bot):
        self.bot = bot

    @commands.group(
        description="Base command for all settings.",
        brief="Base command for all settings.",
        invoke_without_command=True
    )
    @commands.has_permissions(manage_guild=True)
    async def settings(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description="<:nano_info:483063870655823873> Use `gb!settings prefix <prefix>` or `gb!settings muted "
                            "<role>` to change settings."
            ),
            delete_after=5
        )

    @settings.command(
        description="Change the current server wide prefix.",
        brief="Change the server wide prefix."
    )
    async def prefix(self, ctx, *, prefix):
        old = await self.bot.db.fetchval("SELECT prefix FROM prefixes WHERE guildid=$1;", ctx.guild.id)
        if not old:
            try:
                await self.bot.db.execute("INSERT INTO prefixes VALUES ($1, $2);", ctx.guild.id, prefix)
            except SDRTE:
                assert False, "Maximum length for prefixes is 3 characters."
        else:
            try:
                await self.bot.db.execute("UPDATE prefixes SET prefix=$1 WHERE guildid=$2;", prefix, ctx.guild.id)
            except SDRTE:
                assert False, "Maximum length for prefixes is 3 characters."
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> Prefix updated to `{prefix}`"
            ),
            delete_after=5
        )


def setup(bot):
    bot.add_cog(Settings(bot))
