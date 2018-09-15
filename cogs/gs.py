from discord.ext import commands
import discord


GSGuild = 479413987633528842
GSWelcome = 479491025296031764
WelcomeMessage = """
---------------------------------------
Welcome %usermention% to Gamma Support!
Before you can access the main channels, you need to read <#480523282999803906>.
This channel contains critical information about the server, you will definitely want to remember it.

Thanks for joining, and enjoy your stay!
----------------------------------------
"""


class GammaSupport:
    def __init__(self, bot):
        self.bot = bot
        self.db = bot.db
        self._invite_cache = {}
        self.gs = None
        self.wc = None
        self.bot.loop.create_task(self.__ainit__())

    async def __ainit__(self):
        await self.bot.wait_until_ready()
        self.gs = self.bot.get_guild(GSGuild)
        self.wc = self.gs.get_channel(GSWelcome)
        self._invite_cache = {invite.code: invite.uses for invite in await self.gs.invites()}

    async def _update_inv_cache(self):
        self._invite_cache = {invite.code: invite.uses for invite in await self.gs.invites()}

    async def update_recent_joined(self, member):
        data = await self.db.fetch("SELECT * FROM new_users ORDER BY joined DESC;")
        if len(data) < 5:
            pass
        else:
            pass

    @staticmethod
    async def __local_check(ctx):
        return ctx.guild.id == GSGuild

    async def on_member_join(self, member):
        if member.guild.id != 479413987633528842:
            return
        await self._update_inv_cache()
        await self.wc.send(WelcomeMessage.replace("%usermention%", member.mention))
        # await self.


def setup(bot):
    bot.add_cog(GammaSupport(bot))
