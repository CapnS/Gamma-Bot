from discord.ext import commands
from utils import errors


def owner_or_permissions(**perms):
    async def predicate(ctx):
        if await ctx.bot.is_owner(ctx.author):
            return True
        return any(getattr(ctx.channel.permissions_for(ctx.author), perm, None) == value for perm, value in perms.items())
    return commands.check(predicate)

def not_blacklisted():
    async def predicate(ctx):
        if ctx.bot.is_blacklisted(ctx.guild, ctx.author):
            raise errors.GuildBlacklistedError(ctx.guild)
        if ctx.bot.is_global_blacklisted(ctx.author):
            raise errors.GlobalBlacklistedError()
        return True
    return commands.check(predicate)
