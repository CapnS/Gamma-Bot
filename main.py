from discord.ext import commands
from datetime import datetime
from discord.utils import get
import discord
import asyncpg
import psycopg2
import json
import git
import asyncio
import os
import logging
import logging.handlers
import matplotlib
matplotlib.use('Agg')
try:
    import uvloop
    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    print("uvloop not detected. If you are using a Linux-based system, please make sure to install it.")

JISHAKU_HIDE = 'on'

logger = logging.getLogger()
logger.addHandler(logging.handlers.SysLogHandler())

BETA = os.getenv('DEBUG_MODE') is None

# extensions = [f"cogs.{e.replace('.py','')}" for e in list(os.walk("./cogs"))[0][2] if e.endswith(".py")]
extensions = [
    'cogs.autoresponder',
    'cogs.debug',
    'cogs.eco',
    'cogs.gs',
    'cogs.misc',
    'cogs.music',
    'cogs.logging',
    'cogs.mods',
    'cogs.settings',
    'cogs.tags',
    "jishaku"
]

with open("config/config.json", "rb") as f:
    config = json.loads(f.read())


class CustomContext(commands.Context):
    @property
    def secret(self):
        return "sneak"


description = """
Gamma. A Discord bot written in Python by Xua#9307
You can view Gamma's source here: <https://github.com/XuaTheGrate/Gamma-Bot/>
"""


class Bot(commands.AutoShardedBot):
    def __init__(self):
        super().__init__(command_prefix=self.get_pref, desc=description, reconnect=True)
        self.http.token = "NEIN"
        if not BETA:
            cred = {"user": "gammabot", "password": "gamma", "database": "gammabot", "host": "127.0.0.1"}
        else:
            cred = {"user": "gammabeta", "password": "gamma", "database": "gammabeta", "host": "127.0.0.1"}
        self.db = self.loop.run_until_complete(asyncpg.create_pool(**cred))
        self.reboot = datetime.utcnow()
        self.official = False
        self.session = self.http._session
        self.syncdb_conn = psycopg2.connect(**cred)
        self.syncdb_conn.autocommit = True
        self.syncdb_cur = self.syncdb_conn.cursor()
        self.user_blacklist = {n['guildid']: n['userid'] for n in self.psycopg2_fetch("SELECT * FROM blacklist "
                                                                                      "WHERE userid IS NOT NULL;")}
        self.global_blacklist = [m['userid'] for m in self.psycopg2_fetch("SELECT userid FROM global_blacklist;")]
        self.is_purging = {}
        self.debug = BETA
        self.xua = 455289384187592704
        self.prefixes = {n['guildid']: n['prefix'] for n in self.psycopg2_fetch("SELECT * FROM prefixes;")}
        self.__loaded_modules = []
        self.__failed_modules = []
        self.__legal_immigrants__ = [455289384187592704]

    @staticmethod
    def clean_string(string):
        return string.replace("@", "@\u200b").replace("discord.gg/", "discord\u200b.gg/").replace("```", "\`\`\`")

    # DISCALIMER TO ALL DISCORD.PY USERS
    # I understand that these are blocking calls
    # I must use these in order to set self
    # variables and prevent loop holes

    def psycopg2_fetch(self, query) -> list:
        """ Send a query to the database and return a list of results
        EXAMPLE:

        > psycopg2_fetch("SELECT * FROM prefixes;")
        [{'column_1': 'value_1', 'column_2': 'value_2'}, {...}]

        """
        self.syncdb_cur.execute(query)
        values = self.syncdb_cur.fetchall()
        ret = []
        for v in values:
            n = {}
            for e in range(len(v)):
                n.setdefault(self.syncdb_cur.description[e].name, v[e])
            ret.append(n)
        return ret

    def psycopg2_fetchrow(self, query) -> dict:
        """ Send a query to the database and return a dict of the first row encountered
        EXAMPLE:

        > psycopg2_fetchrow("SELECT * FROM prefixes WHERE guildid=999999;")
        {guildid: 'prefix'}

        """
        self.syncdb_cur.execute(query)
        value = self.syncdb_cur.fetchall()[0]  # we want the first occurence
        ret = {}
        for v in range(len(value)):
            ret.setdefault(self.syncdb_cur.description[v].name, value[v])
        return ret

    def psycopg2_fetchval(self, query):
        """ Send a query to the database and return the first value found
        EXAMPLE:

        > psycopg2_fetchval("SELECT prefix FROM prefixes WHERE guildid=999999;")
        'prefix'

        """
        self.syncdb_cur.execute(query)
        value = self.syncdb_cur.fetchall()
        return value[0][0]

    async def _flush_blacklist(self):
        # -- Blacklisting -- #
        await self.db.execute("DELETE FROM blacklist;")
        await self.db.execute("DELETE FROM global_blacklist;")
        for guildid, userids in self.user_blacklist.items():
            await self.db.execute("INSERT INTO blacklist VALUES ($1, $2);", guildid, userids)
        for userid in self.global_blacklist:
            await self.db.execute("INSERT INTO global_blacklist VALUES ($1);", userid)

    async def _flush_prefixes(self):
        data = await self.db.fetch("SELECT * FROM prefixes;")
        self.prefixes = {}
        for p in data:
            self.prefixes.setdefault(p['guildid'], p['prefix'])

    async def _flush_all(self):
        while not self.is_closed():
            await self._flush_blacklist()
            await self._flush_prefixes()
            now = datetime.utcnow().strftime("%d/%m/%y @ %H:%M")
            await self.send_xua(f"Auto-saved data. {now}")
            await asyncio.sleep(43200)

    async def send_xua(self, content=None, *, embed=None, file=None):
        await self.get_user(455289384187592704).send(content, embed=embed, file=file)

    async def presence_updater(self):
        await self.wait_until_ready()
        while not self.is_closed():
            repo = git.Repo()
            commit = repo.head.commit
            await self.change_presence(activity=discord.Activity(name=f"commit {str(commit)[:7]}",
                                                                 type=discord.ActivityType.listening))
            await asyncio.sleep(600)

    async def is_owner(self, user: discord.Member):
        return user.id in self.__legal_immigrants__

    @staticmethod
    def higher_role(alpha, beta):
        if alpha.guild.owner == alpha:
            return True
        if beta.guild.owner == beta:
            return False
        if alpha.guild.me.top_role.position > beta.top_role.position:
            return alpha.top_role.position > beta.top_role.position
        return False

    async def get_muted_role(self, guild):
        return get(guild.roles,
                   id=(await self.db.fetchval("SELECT roleid FROM muted_roles WHERE guildid=$1;", guild.id)))

    async def get_pref(self, bot, message):
        return self.prefixes.get(message.guild.id) or "g!"

    def run(self, token):
        for extension in extensions:
            try:
                self.load_extension(extension)
                self.__loaded_modules.append(extension)
            except Exception as e:
                self.__failed_modules.append((extension, f"{type(e).__name__}: {e}"))
        super().run(token)

    async def logout(self):
        await self._flush_blacklist()
        await super().logout()

    async def on_message(self, message):
        if message.author.bot:
            return
        if not message.guild:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=f"{self.user} was DMed",
                timestamp=datetime.utcnow()
            )
            embed.set_author(
                name=str(message.author),
                icon_url=message.author.avatar_url_as(format="png")
            )
            embed.add_field(
                name="Content",
                value=f"```py\n{message.clean_content}\n```"
            )
            file = None
            if message.attachments:
                attach = message.attachments[0]
                if attach.height is not None:
                    await attach.save('tmp/png.png')
                    with open('tmp/png.png', 'rb') as f:
                        file = discord.File(f.read(), "image.png")
                    embed.set_image(
                        url="attachment://image.png"
                    )
                else:
                    with open('tmp/'+attach.filename, 'rb') as f:
                        file = discord.File(f.read(), attach.filename)
            await self.send_xua(
                embed=embed,
                file=file
            )
            return
        if message.author.id in self.global_blacklist and not await self.is_owner(message.author):
            return
        try:
            if message.author.id in self.user_blacklist[message.guild.id] and not \
                    (await self.is_owner(message.author) or
                     message.author.permissions_in(message.channel).administrator):
                return
        except KeyError:
            pass
        if message.content == f"<@!{self.user.id}>" or message.content == f"<@{self.user.id}>":
            prefix = await self.get_pref(self, message)
            await message.channel.send(f"My prefix here is `{prefix}`. Use `{prefix}help` for a list of commands.")
            return
        if message.guild.me in message.mentions:
            m = self.get_user(455289384187592704)
            content = f"Gamma Beta was pinged just now by {message.author} in {message.guild}," \
                      f"{message.channel.mention}\n```\n{message.clean_content}\n```"
            await m.send(content, embed=message.embeds[0] if len(message.embeds) > 0 else None)
        if len(message.attachments) > 0:
            await message.attachments[0].save(f"tmp/{message.id}_{message.attachments[0].filename}")
        ctx = await self.get_context(message, cls=CustomContext)
        await self.invoke(ctx)

    async def hourly_update(self):
        while not self.is_closed():
            hour = datetime.now().hour
            await self.db.execute("UPDATE websocket_latency SET ms=$1 WHERE hour=$2;", round(self.latency*1000, 2), hour)
            await asyncio.sleep(3600)

    async def on_ready(self):
        self.official = self.get_guild(483063756948111372) is not None
        self.xua = self.get_user(455289384187592704)
        self.loop.create_task(self.presence_updater())  # updates every 10 minutes
        self.loop.create_task(self._flush_all())  # updates every 12 hours
        self.loop.create_task(self.hourly_update())  # updates every hour
        loaded = '\n'.join(self.__loaded_modules)
        failed = '\n'.join([f"> {e[0]}\n- {e[1]}" for e in self.__failed_modules])
        await self.send_xua(
            ("-"*20)+"\n"
            f"Bot has connected.\n"
            f"Total guilds: {len(self.guilds)}\n"
            f"Loaded shards: {len(self.shards)}\n"
            f"Total users: {len(self.users)}\n"
            f"Successfully loaded {len(self.__loaded_modules)} modules\n"
            f"```prolog\n{loaded}\n```"
            f"Failed to load {len(self.__failed_modules)} modules\n"
            f"```prolog\n{failed}\n```"
        )
    
    async def on_command_error(self, ctx, exc):
        if isinstance(exc, commands.CommandInvokeError):
            exc = exc.original
        if type(exc) == commands.CheckFailure:
            embed = discord.Embed(color=discord.Color.blurple(), 
                                  description="<:nano_exclamation:483063871360466945> You do not have permission to run"
                                              " this command.")
            await ctx.send(embed=embed)
            return
        if isinstance(exc, commands.CommandNotFound):
            return
        if isinstance(exc, commands.CommandOnCooldown):
            h, r = divmod(exc.retry_after, 3600)
            m, s = divmod(r, 60)
            d, h = divmod(h, 24)
            if d > 0:
                desc = f"Try again in **{round(d)}d {round(h)}h {round(m)}m {round(s)}s**"
            elif h > 0:
                desc = f"Try again in **{round(h)}h {round(m)}m {round(s)}s**"
            elif m > 0:
                desc = f"Try again in **{round(m)}m {round(s)}s**"
            else:
                desc = f"Try again in **{round(s)}s**"
            return await ctx.send(embed=discord.Embed(color=discord.Color.blurple(),
                                                      description=f"<:nano_exclamation:483063871360466945>"
                                                                  f" {desc}"))
        nexc = str(exc)
        embed = discord.Embed(color=discord.Color.blurple(), 
                              description=f"<:nano_exclamation:483063871360466945> {nexc}")
        if self.debug:
            import traceback
            embed.set_footer(text=f"Debug: {type(exc).__name__}")
            await self.send_xua("```py\n"+"".join(traceback.format_exception(type(exc), exc, exc.__traceback__))+"\n```")
        await ctx.send(embed=embed)

    async def get_logging_channel(self, guild):
        data = await self.db.fetchval("SELECT channelid FROM logging WHERE guildid=$1;", guild.id)
        if not data:
            return
        return guild.get_channel(data)

    async def on_message_delete(self, message):
        if self.is_purging.get(message.channel.id):
            return
        channel = await self.get_logging_channel(message.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{message.author}",
            description=f"{message.channel.mention}",
            timestamp=datetime.utcnow()
        )
        attach_file = None
        if len(message.attachments) > 0:
            attach = message.attachments[0]
            if attach.height is not None:
                with open(f"tmp/{message.id}_{attach.filename}", "rb") as f:
                    attach_file = discord.File(f.read(), filename="attachment.png")
                embed.set_image(url="attachment://attachment.png")
            else:
                with open(f"tmp/{message.id}_{attach.filename}", "rb") as f:
                    attach_file = discord.File(f.read(), filename=attach.filename)
        embed.set_author(
            name="Message was deleted",
            icon_url=message.author.avatar_url_as(static_format="png")
        )
        embed.add_field(
            name="Content",
            value=message.content or "No content"
        )
        await channel.send(embed=embed, file=attach_file)

    async def on_message_edit(self, old, new):
        if old.content == new.content:
            return
        channel = await self.get_logging_channel(new.guild)
        if not channel:
            return
        embed = discord.Embed(
            title=f"{new.author}",
            color=discord.Color.blurple(),
            description=f"{new.channel.mention}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="Message was edited",
            icon_url=new.author.avatar_url_as(static_format="png")
        )
        embed.add_field(
            name="Before",
            value=old.content,
            inline=False
        )
        embed.add_field(
            name="After",
            value=new.content,
            inline=False
        )
        await channel.send(embed=embed)

    async def on_member_update(self, old, new):
        channel = await self.get_logging_channel(new.guild)
        if not channel:
            return
        if old.nick != new.nick:
            embed = discord.Embed(
                title=f"{new}",
                timestamp=datetime.utcnow(),
                color=discord.Color.blurple()
            )
            embed.set_author(
                name="Members nickname was changed",
                icon_url=new.avatar_url_as(static_format="png")
            )
            embed.add_field(
                name="Before",
                value=old.nick,
                inline=False
            )
            embed.add_field(
                name="After",
                value=new.nick,
                inline=False
            )
            await channel.send(embed=embed)
        if old.avatar != new.avatar:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=f"{new}",
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=new.avatar_url_as(static_format="png"))
            embed.set_thumbnail(url=old.avatar_url_as(static_format="png"))
            embed.set_author(
                name="Members avatar was updated.",
                icon_url=new.avatar_url_as(static_format="png")
            )
            await channel.send(embed=embed)
        if old.name != new.name or old.discriminator != new.discriminator:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(
                name="Members name was changed",
                icon_url=new.avatar_url_as(static_format="png")
            )
            embed.add_field(
                name="Before",
                value=str(old),
                inline=False
            )
            embed.add_field(
                name="After",
                value=str(new),
                inline=False
            )
            await channel.send(embed=embed)
        if old.roles != new.roles:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                timestamp=datetime.utcnow(),
                title=f"{new}"
            )
            embed.set_author(
                name="Users roles were updated",
                icon_url=new.avatar_url_as(static_format="png")
            )
            for role in old.roles:
                if role not in new.roles:
                    embed.add_field(
                        name="Role Taken",
                        value=f"{role.mention}",
                        inline=False
                    )
            for role in new.roles:
                if role not in old.roles:
                    embed.add_field(
                        name="Role Given",
                        value=f"{role.mention}",
                        inline=False
                    )
            await channel.send(embed=embed)

    async def on_member_remove(self, member):
        channel = await self.get_logging_channel(member.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=str(member),
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="Member left the server",
            icon_url=member.avatar_url_as(static_format="png")
        )
        embed.set_thumbnail(url=member.avatar_url_as(static_format="png"))
        await channel.send(embed=embed)

    async def on_member_join(self, member):
        channel = await self.get_logging_channel(member.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            timestamp=datetime.utcnow(),
            title=str(member)
        )
        embed.set_author(
            name="User joined the server",
            icon_url=member.avatar_url_as(static_format="png")
        )
        embed.set_thumbnail(url=member.avatar_url_as(static_format="png"))
        await channel.send(embed=embed)

    async def on_guild_join(self, guild):
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title="I joined a new guild!",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name=f"{guild.owner}",
            icon_url=guild.owner.avatar_url_as(static_format="png")
        )
        embed.set_thumbnail(
            url=guild.icon_url_as(format="png")
        )
        embed.add_field(
            name="Guild Name",
            value=f"{guild}"
        )
        embed.add_field(
            name="Guild ID",
            value=f"{guild.id}"
        )
        embed.add_field(
            name="Total Members",
            value=f"{guild.member_count}"
        )
        embed.add_field(
            name="Total Channels",
            value=f"{len(guild.channels)}"
        )
        emotes = [str(e) for e in guild.emojis]
        if len("".join(emotes)) > 1024:
            emotes = ['Too many to show']
        embed.add_field(
            name="Custom Emojis",
            value="".join(emotes) or "None",
            inline=False
        )
        roles = [r.name for r in guild.role_hierarchy if not r.is_default()]
        embed.add_field(
            name=f"Total Roles ({len(roles)})",
            value=", ".join(roles),
            inline=False
        )
        try:
            invites = await guild.invites()
        except discord.Forbidden:
            invites = ["None"]
        else:
            invites = invites if invites != [] else ['None']
        embed.add_field(
            name="Invite link",
            value=f"{invites[0]}",
            inline=False
        )
        perms = dict(guild.me.guild_permissions)
        keys = [f.replace("_", " ").title() for f in perms.keys() if perms[f] is True]
        embed.add_field(
            name="Allowed permissions",
            value=", ".join(keys),
            inline=False
        )
        embed.set_footer(
            text="Joined at"
        )
        await self.xua.send(embed=embed)


if __name__ == "__main__":
    if BETA:
        Bot().run(config['betatoken'])
    else:
        Bot().run(config['token'])
