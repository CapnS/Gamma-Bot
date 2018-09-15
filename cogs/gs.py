from discord.ext import commands
import discord


GSGuild = 479413987633528842


class GammaSupport:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self._invite_cache = {}
        self.gs = None
        self.bot.loop.create_task(self.__ainit__())

    async def __ainit__(self):
        await self.bot.wait_until_ready()
        self.gs = self.bot.get_guild(GSGuild)
        self._invite_cache = {invite.code: invite.uses for invite in await self.gs.invites()}

    async def _update_inv_cache(self):
        self._invite_cache = {invite.code: invite.uses for invite in await self.gs.invites()}

    @staticmethod
    async def __local_check(ctx):
        return ctx.guild.id == GSGuild

    async def on_member_join(self, member):
        if member.guild.id != 479413987633528842:
            return
        await self._update_inv_cache()


def setup(bot):
    bot.add_cog(GammaSupport(bot))
