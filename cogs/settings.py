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
        prefix = await self.bot.get_pref(self.bot, ctx.message)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_info:483063870655823873> Use `{prefix}settings prefix <prefix>` "
                            f"or `{prefix}settings muted <role>` to change settings."
            ),
            delete_after=30
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

    @settings.command(
        description="Change the current muted role.\nNOTE: Changing the current role will edit all permissions"
                    "overwrites for this role. Removing the role will also clear the overwrites. Use with caution.",
        brief="Change the current muted role."
    )
    async def muted(self, ctx, *, role: discord.Role):
        old = await self.bot.db.fetchval("SELECT roleid FROM muted_roles WHERE guildid=$1;", ctx.guild.id)
        if not old:
            await self.bot.db.execute("INSERT INTO muted_roles VALUES ($1, $2);", ctx.guild.id, role.id)
            for channel in ctx.guild.channels:
                ow_n = discord.PermissionOverwrite(send_messages=False, speak=False)
                await channel.set_permissions(role, overwrite=ow_n)
        else:
            await self.bot.db.execute("UPDATE muted_roles SET roleid=$1 WHERE guildid=$2;", role.id, ctx.guild.id)
            old_r = discord.utils.get(ctx.guild.roles, id=old)
            for channel in ctx.guild.channels:
                ow = dict(channel.overwrites_for(old_r))
                new = {}
                for k in ow.keys():
                    new.setdefault(k, None)
                ow = discord.PermissionOverwrite(**new)
                await channel.set_permissions(old_r, overwrite=ow)
                ow_n = discord.PermissionOverwrite(send_messages=False, speak=False)
                await channel.set_permissions(role, overwrite=ow_n)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description="<:nano_check:484247886461403144> Updated the muted role."
            )
        )


def setup(bot):
    bot.add_cog(Settings(bot))
