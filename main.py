from discord.ext import commands
from datetime import datetime
import discord
import asyncpg
import psycopg2
import json
import git
import asyncio

JISHAKU_HIDE = 1

# extensions = [f"cogs.{e.replace('.py','')}" for e in list(os.walk("./cogs"))[0][2] if e.endswith(".py")]
extensions = [
    # 'cogs.autoresponder',
    'cogs.debug',
    'cogs.eco',
    'cogs.misc',
    'cogs.music',
    'cogs.logging',
    # 'cogs.rpg',
    'cogs.mods',
    "jishaku"
]

with open("config/config.json", "rb") as f:
    config = json.loads(f.read())


class CustomContext(commands.Context):
    @property
    def secret(self):
        return "sneak"


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="gb!", desc="Zeta")
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

    async def presence_updater(self):
        await self.wait_until_ready()
        while not self.is_closed():
            repo = git.Repo()
            commit = repo.head.commit
            await self.change_presence(activity=discord.Activity(name=f"commit {str(commit)[:7]}",
                                                                 type=discord.ActivityType.listening))
            await asyncio.sleep(600)

    def run(self, token):
        for extension in extensions:
            try:
                self.load_extension(extension)
                print(f"Successfully loaded {extension}")
            except Exception as e:
                print(f"Error loading extension {extension}\n{type(e).__name__}: {e}")
        super().run(token)

    async def logout(self):
        await self._flush_blacklist()
        await super().logout()

    async def on_message(self, message):
        if message.author.bot:
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
        ctx = await self.get_context(message, cls=CustomContext)
        await self.invoke(ctx)
        # print(ctx.secret)
    
    async def on_ready(self):
        # Officiality
        self.official = self.get_guild(483063756948111372) is not None
        self.loop.create_task(self.presence_updater())
        print("Bot has connected.")
        print(f"Logged in as {self.user}")
        print(f"Total Guilds: {len(self.guilds)}")
    
    async def on_command_error(self, ctx, exc):
        if isinstance(exc, commands.CommandInvokeError):
            exc = exc.original
        if type(exc) == commands.CheckFailure:
            embed = discord.Embed(color=discord.Color.blurple(), 
                                  description="<:nano_exclamation:483063871360466945> You do not have permission to run"
                                              " this command.")
            embed.set_footer(text=f"Debug: {type(exc).__name__}")
            await ctx.send(embed=embed)
            return
        if isinstance(exc, commands.CommandNotFound):
            cmd = ctx.invoked_with
            embed = discord.Embed(color=discord.Color.blurple(), 
                                  description=f"<:nano_exclamation:483063871360466945> Command \"{cmd}\" "
                                              f"does not exist.")
            embed.set_footer(text=f"Debug: {type(exc).__name__}")
            await ctx.send(embed=embed)
            return
        if isinstance(exc, commands.CommandOnCooldown):
            h, r = divmod(exc.retry_after, 3600)
            m, s = divmod(r, 60)
            d, h = divmod(h, 24)
            if d > 0:
                desc = f"Try again in **{round(d)}:{round(h)}:{round(m)}:{round(s)}**"
            elif h > 0:
                desc = f"Try again in **{round(h)}:{round(m)}:{round(s)}**"
            elif m > 0:
                desc = f"Try again in **{round(m)}:{round(s)}**"
            else:
                desc = f"Try again in **{round(s)}**"
            return await ctx.send(embed=discord.Embed(color=discord.Color.blurple(),
                                                      description=f"<:nano_exclamation:483063871360466945>"
                                                                  f" {desc}").set_footer(text="Debug: "
                                                                                              "{type(exc).__name__}"))
        nexc = str(exc)
        embed = discord.Embed(color=discord.Color.blurple(), 
                              description=f"<:nano_exclamation:483063871360466945> {nexc}")
        embed.set_footer(text=f"Debug: {type(exc).__name__}")
        await ctx.send(embed=embed)

    async def get_logging_channel(self, guild):
        data = await self.db.fetchval("SELECT channelid FROM logging WHERE guildid=$1;", guild.id)
        if not data:
            return
        return guild.get_channel(data)

    async def on_message_delete(self, message):
        channel = await self.get_logging_channel(message.guild)
        if not channel:
            return
        if not message.content:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{message.author}",
            description=f"{message.channel.mention}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="Message was deleted",
            icon_url=message.author.avatar_url_as(format="png")
        )
        embed.add_field(
            name="Content",
            value=message.content
        )
        await channel.send(embed=embed)

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
            icon_url=new.author.avatar_url_as(format="png")
        )
        embed.add_field(
            name="Before",
            value=old.content
        )
        embed.add_field(
            name="After",
            value=new.content
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
                icon_url=new.avatar_url_as(format="png")
            )
            embed.add_field(
                name="Before",
                value=old.nick
            )
            embed.add_field(
                name="After",
                value=new.nick
            )
            await channel.send(embed=embed)
        if old.avatar != new.avatar:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=f"{new}",
                timestamp=datetime.utcnow()
            )
            embed.set_image(url=new.avatar_url_as(format="png"))
            embed.set_thumbnail(url=old.avatar_url_as(format="png"))
            embed.set_author(
                name="Members avatar was updated.",
                icon_url=new.avatar_url_as(format="png")
            )
            await channel.send(embed=embed)
        if old.name != new.name or old.discriminator != new.discriminator:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                timestamp=datetime.utcnow()
            )
            embed.set_author(
                name="Members name was changed",
                icon_url=new.avatar_url_as(format="png")
            )
            embed.add_field(
                name="Before",
                value=str(old)
            )
            embed.add_field(
                name="After",
                value=str(new)
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
                icon_url=new.avatar_url_as(format="png")
            )
            for role in old.roles:
                if role not in new.roles:
                    embed.add_field(
                        name="Role Taken",
                        value=f"{role.mention}"
                    )
            for role in new.roles:
                if role not in old.roles:
                    embed.add_field(
                        name="Role Given",
                        value=f"{role.mention}"
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
            icon_url=member.avatar_url_as(format="png")
        )
        embed.set_thumbnail(url=member.avatar_url_as(format="png"))
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
            icon_url=member.avatar_url_as(format="png")
        )
        embed.set_thumbnail(url=member.avatar_url_as(format="png"))
        await channel.send(embed=embed)


if __name__ == "__main__":
    Bot().run(config['betatoken'])
