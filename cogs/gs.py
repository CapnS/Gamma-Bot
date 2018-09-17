from discord.ext import commands
from datetime import datetime
import discord


GSGuild = 479413987633528842
GSWelcome = 479491025296031764
AnnouncementRole = 491148481726251009
DevelopmentRole = 491148324976590848
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
        self.announcements_role = None
        self.development_role = None
        self.feeds = ("announcements", "development")
        self.bot.loop.create_task(self.__ainit__())

    async def __ainit__(self):
        await self.bot.wait_until_ready()
        self.gs = self.bot.get_guild(GSGuild)
        self.wc = self.gs.get_channel(GSWelcome)
        self._invite_cache = {invite.code: invite.uses for invite in await self.gs.invites()}
        self.announcements_role = discord.utils.get(self.gs.roles, id=AnnouncementRole)
        self.development_role = discord.utils.get(self.gs.roles, id=DevelopmentRole)

    async def _update_inv_cache(self):
        self._invite_cache = {invite.code: invite.uses for invite in await self.gs.invites()}

    async def update_recent_joined(self, member):
        data = await self.db.fetch("SELECT * FROM new_users ORDER BY joined DESC;")
        if len(data) < 5:
            # append a new user
            await self.db.execute("INSERT INTO new_users VALUES ($1, $2);", member.id, datetime.utcnow())
        else:
            # delete last user
            await self.db.execute("DELETE FROM new_users WHERE userid IN (SELECT userid FROM new_users "
                                  "ORDER BY joined DESC LIMIT 1);")
            await self.db.execute("INSERT INTO new_users VALUES ($1, $2);", member.id, datetime.utcnow())

    @staticmethod
    async def __local_check(ctx):
        return ctx.guild.id == GSGuild

    async def on_member_join(self, member):
        if member.guild.id != 479413987633528842:
            return
        await self._update_inv_cache()
        await self.wc.send(WelcomeMessage.replace("%usermention%", member.mention))
        # await self.update_recent_joined(member)

    @commands.command(
        description="Subscribe to a news feed. This only applies to the Gamma Support guild.",
        brief="Subscribe to a news feed."
    )
    async def sub(self, ctx, feed=None):
        assert feed is not None, "Valid subscriptions: `announcements`, `development`"
        assert feed in self.feeds, "Invalid subscription."
        if hasattr(self, f"{feed}_role"):
            role = getattr(self, f"{feed}_role")
            if role in ctx.author.roles:
                await ctx.author.remove_roles(role)
                sub = "Unsubbed from"
            else:
                await ctx.author.add_roles(role)
                sub = "Subbed to"
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"<:nano_check:484247886461403144> {sub} `{feed.title()}`"
                )
            )

    @commands.command(
        description="View your current subscriptions. Only applicable to the Gamma Support guild.",
        brief="View your current subscriptions."
    )
    async def subs(self, ctx):
        roles = ctx.author.roles
        announce = discord.utils.get(roles, name="Announcements")
        develop = discord.utils.get(roles, name="Development")
        s = []
        if announce:
            s.append("Announcements")
        if develop:
            s.append("Development")
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_info:483063870655823873> You are subbed to {' and '.join(s)}." if s else
                "<:nano_info:483063870655823873> You are not subscribed to any feeds."
            )
        )


def setup(bot):
    bot.add_cog(GammaSupport(bot))
