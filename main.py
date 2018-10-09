# measurement
import time
start = time.perf_counter()

# discord
from discord.ext import commands
import discord

# data handling
import asyncpg
import json
import asyncio

# utilities
from cogs.utils import checks, context

# extra
import os
import traceback
import psutil
import sys
try:
    import uvloop
    asyncio.set_event_loop_policty(uvloop.EventLoopPolicy())
except ImportError:
    if sys.playform == 'linux':
        print("/!\ The bot is being hosted on a Linux system, but uvloop isnt installed! Please install this to help aid the speed of the bot.")


# configuration
with open("config/database.json", "rb") as f:
    credentials = json.loads(f.read())

with open("config/config.json", "rb") as f:
    config = json.loads(f.read())


class Gamma(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=self.get_pref, reconnect=True)
        self.session = self.http._session
        self.db = None
        self.loaded_extensions = []
        self.failed_extensions = {}
        self.prefixes = {}
        self.blacklist = {}
        self.global_blacklist = []
        self.process = psutil.Process()
        self.loop.create_task(self.__ainit__())
    
    async def __ainit__(self):
        self.db = await asyncpg.create_pool(**credentials)
    
    async def get_pref(self, bot, message):
        return commands.when_mentioned_or(self.prefixes.get(message.guild, config.get("prefix", "g!")))(bot, message)
    
    async def get_context(self, message, **kwargs):
        return await super().get_context(message, cls=context.SuperContext)
        
    def run(self):
        self.load_extensions()
        super().run(config.get("betatoken"))
    
    def load_extensions(self):
        for extension in os.listdir("modules"):
            if extension.endswith(".py"):
                try:
                    self.load_extension(f"modules.{extension.rstrip('.py')}")
                    self.loaded_extensions.append(extension)
                except BaseException as e:
                    self.failed_extensions.setdefault(extension, f"{type(e).__name__}: {e}")
    
    def format_extensions(self):
        return ("- {}".format("\n- ".join(l for l in self.loaded_extensions)), "\n".join((f"- {f}\n> {v}" for f, v in self.failed_extensions.items())))
    
    async def on_ready(self):
        self.get_command("help").hidden = True
        for record in await self.db.fetch("SELECT * FROM prefixes WHERE bot=$1;", self.user.id):
            guild = self.get_guild(record['guildid'])
            if not guild:
                await self.db.execute("DELETE FROM prefixes WHERE bot=$1 AND guildid=$2;", self.user.id, record['guildid'])
                continue
            self.prefixes.setdefault(guild, record['prefix'])
        for record in await self.db.fetch("SELECT * FROM blacklist;"):
            guild = self.get_guild(record['guildid'])
            if not guild:
                continue
            mems = []
            for member in record['userid']:
                member = guild.get_member(member)
                if member:
                    mems.append(member)
            self.blacklist.setdefault(guild, mems)
        for record in await self.db.fetch("SELECT * FROM global_blacklist;"):
            user = self.get_user(record['userid'])
            if user:
                self.global_blacklist.append(user)
        await self.flush_database()
        loaded, failed = self.format_extensions()
        final = time.perf_counter() - start
        await self.get_user(455289384187592704).send(f"Loaded the following:\n```fix\n{loaded}\n```Failed to load the following:\n```fix\n{failed}\n```\n\nConnected in {round(final, 2)} seconds.")
        
    async def flush_database(self):
        flush_begin = time.perf_counter()
        await self.db.execute("DELETE FROM prefixes;")
        await self.db.execute("DELETE FROM blacklist;")
        await self.db.execute("DELETE FROM global_blacklist;")
        for guild, prefix in self.prefixes.items():
            await self.db.execute("INSERT INTO prefixes VALUES ($1, $2);", guild.id, prefix)
        for guild, members in self.blacklist.items():
            await self.db.execute("INSERT INTO blacklist VALUES ($1, $2);", guild.id, [m.id for m in members])
        for user in self.global_blacklist:
            await self.db.execute("INSERT INTO global_blacklist VALUES ($1);", user.id)
    
    def is_blacklisted(self, guild, member):
        blacklist = self.blacklist.get(guild, None)
        if not blacklist:
            return False
        return member in blacklist
        
    def is_global_blacklisted(self, member):
        return member in self.global_blacklist
        

if __name__ == "__main__":
    Gamma().run()