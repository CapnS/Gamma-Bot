from discord.ext import commands
from discord.ext.commands import clean_content
from HelpPaginator import HelpPaginator
from datetime import datetime
from SimplePaginator import SimplePaginator
import discord
import psutil
import json
import speedtest
import asyncio
import random
import logging
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import os
import custom_encoder

logger = logging.getLogger(__name__)
process = psutil.Process()


class ArgParser(commands.Converter):
    async def convert(self, ctx, argument):
        try:
            arg = argument.lstrip(" --").split(" --")
            values = {}
            for a in arg:
                f = a.split("=")
                if len(f) == 2:
                    key, value = f
                else:
                    key = f[0]
                    value = ""
                if value.isdigit():
                    value = int(value)
                else:
                    if value.lower() in ('yes', 'y', 'true', 'on', 'enable'):
                        value = True
                    elif value.lower() in ('no', 'n', 'false', 'off', 'disable'):
                        value = False
                values.setdefault(key, value)
            return values
        except Exception as e:
            raise commands.BadArgument(f"Parsing failed.\n{type(e).__name__}: {e}")


class Misc:
    def __init__(self, bot):
        self.bot = bot
        self.spec_perms = ['administrator', 'ban_members', 'deafen_members', 'kick_members', 'manage_channels',
                           'manage_emojis', 'manage_guild', 'manage_messages', 'manage_nicknames', 'manage_roles',
                           'manage_webhooks', 'mention_everyone', 'move_members', 'mute_members',
                           'view_audit_log']

    @staticmethod
    def time_difference(alpha, beta):
        delta = alpha - beta
        hours, remainder = divmod(int(delta.total_seconds()), 3600)
        minutes, seconds = divmod(remainder, 60)
        days, hours = divmod(hours, 24)
        return f"**{days}**d, **{hours}**h, **{minutes}**m, **{seconds}**s"
    
    @commands.command(
        description="Check my latency to Discords web sockets.",
        brief="Check my connection time.",
        aliases=["pong"]
    )
    async def ping(self, ctx):
        await ctx.send(embed=discord.Embed(color=discord.Color.blurple(),
                                           description=f":ping_pong: **{round(self.bot.latency*1000)}**ms"))
    
    @commands.command(
        aliases=["?", "h"],
        description="A help command designed to view help on your commands.",
        brief="View help on a command."
    )
    async def help(self, ctx, command=None):
        try:
            if command is None:
                p = await HelpPaginator.from_bot(ctx)
            else:
                entity = self.bot.get_cog(command) or self.bot.get_command(command)        
                if entity.hidden:
                    await ctx.send(embed=discord.Embed(description=f"<:nano_exclamation:483063871360466945> Command"
                                                                   f" \"{command}\" does not exist.",
                                                       color=discord.Color.blurple()))
                    return
                if entity is None:
                    clean = command.replace('@', '@\u200b')
                    return await ctx.send(f'Command or category "{clean}" not found.')
                elif isinstance(entity, commands.Command):
                    p = await HelpPaginator.from_command(ctx, entity)
                else:
                    p = await HelpPaginator.from_cog(ctx, entity)
            await p.paginate()
        except AttributeError:
            await ctx.send(embed=discord.Embed(description=f"<:nano_exclamation:483063871360466945> Command"
                                                           f" \"{command}\" does not exist.",
                                               color=discord.Color.blurple()))

    @commands.command(
        aliases=['echo'],
        description="Relay a message back to you.",
        brief="Repeat a message."
    )
    async def say(self, ctx, *, message):
        d = await clean_content().convert(ctx, message)
        await ctx.send(d)

    @commands.command(
        aliases=["statistics"],
        description="Use this command to view detailed statistics about Gamma.",
        brief="View stats about Gamma."
    )
    async def stats(self, ctx):
        users = set(m.name for m in self.bot.get_all_members() if m.status != discord.Status.offline)
        cmds = len(self.bot.commands)
        for c in self.bot.commands:
            if isinstance(c, commands.Group):
                cmds += len(c.commands)
        if self.bot.official:
            cmd = r'git show -s HEAD --format="[{0}](https://github.com/XuaTheGrate/Gamma-Bot/commit/%H){1}{2}%s' \
                  r'{1}(%cr)"'
            if os.name == "posix":
                cmd = cmd.format(r"\`%h\`", r"\`\`\`", "fix\n")
            else:
                cmd = cmd.format(r"`%h`", r"```", "fix\n")
            try:
                rev = os.popen(cmd).read().strip()
            except OSError:
                rev = "An internal error occured while fetching the latest data."
            desc = f"""**Invite / Support**

<:nano_hammer:483063870672338964> Release: **Pre-Release**
<:nano_stopwatch:483063870819401749> Uptime: {self.time_difference(datetime.utcnow(), self.bot.reboot)}
<:nano_signal:483070937466404870> Response Time: **{int(self.bot.latency*1000)}ms**
<:nano_house:483063870450040864> Guilds: **{len(self.bot.guilds)}**
<:nano_jewel:483063870793973762> Shards: **{self.bot.shard_count}**
<:nano_people:483063870739709983> Users: **{len(users)}** Online
<:nano_cpu:483063870693310485> CPU Usage: **{process.cpu_percent()}%**
<:nano_task:483063870827659275> Memory Usage (MB): **{int(process.memory_info()[0]/1024/1024)}MB**
<:nano_chart:483063870433263637> Memory Usage (%): **{int((int(process.memory_info()[0]/1024/1024)/750)*100)}%**
<:nano_exclamation:483063871360466945> Commands: **{cmds}**
<:nano_gear:483063870538252288> Cogs: **{len(self.bot.cogs)}**
<:nano_info:483063870655823873> Latest Commit: {rev}
"""
        else:
            desc = f"""**Invite / Support**

:hammer: Release: **Pre-Release**
:stopwatch: Uptime: {self.time_difference(datetime.utcnow(), self.bot.reboot)}
:signal_strength: Response Time: **{int(self.bot.latency*1000)}ms**
:house: Guilds: **{len(self.bot.guilds)}**
:diamonds: Shards: **{self.bot.shard_count}**
:family_mwgb: Users: **{len(users)}** Online
:computer: CPU Usage: **{process.cpu_percent()}%**
:ram: Memory Usage (MB): **{int(process.memory_info()[0]/1024/1024)}MB**
:chart_with_upwards_trend: Memory Usage (%): **{int((int(process.memory_info()[0]/1024/1024)/150)*100)}%**
:exclamation: Commands: **{cmds}**
:gear: Cogs: **{len(self.bot.cogs)}**
"""
        embed = discord.Embed(
            color=discord.Color.blurple(),
            description=desc
        )
        embed.set_author(name=f"{self.bot.user} Statistics", icon_url=self.bot.user.avatar_url_as(static_format="png"))
        await ctx.send(embed=embed)

    @commands.command(
        aliases=['cfact'],
        description='Give me a random cat fact.',
        brief="Cat fact"
    )
    async def catfact(self, ctx, _id: int=None):
        url = "http://api.levi506.net/fact/animal/cat"
        if not _id:
            async with self.bot.session.get(url) as resp:
                assert resp.status == 200, "Connection failed."
                data = await resp.text()
                data = json.loads(data)
                await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"{data['id']}. {data['fact']}"
                    )
                )
        else:
            async with self.bot.session.get(url+"?id="+str(_id)) as resp:
                assert resp.status == 200, "Connection failed."
                data = await resp.text()
                data = json.loads(data)
                await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"{data['id']}. {data['fact']}"
                    )
                )

    @commands.command(
        name="serverinfo",
        aliases=['sinfo', 'guildinfo', 'ginfo'],
        description="View detailed information about the guild.",
        brief="View info about the guild."
    )
    async def server_info(self, ctx):
        color = 0
        while color == 0:
            color = random.choice(ctx.guild.role_hierarchy).color.value
        embed = discord.Embed(
            color=color
        )
        embed.set_author(
            name=ctx.guild.name,
            icon_url=ctx.guild.icon_url_as(format="png")
        )
        embed.set_thumbnail(
            url=ctx.guild.icon_url_as(format="png")
        )
        embed.add_field(
            name="Server Owner",
            value=f"{ctx.guild.owner.mention} {ctx.guild.owner}"
        )
        embed.add_field(
            name="Server Region",
            value=f"{str(ctx.guild.region).title()}"
        )
        embed.add_field(
            name="Verification Level",
            value=str(ctx.guild.verification_level).title()
        )
        embed.add_field(
            name="Created At",
            value=ctx.guild.created_at.strftime("%d/%m/%y @ %I:%M%p")
        )
        mems = [m.id for m in ctx.guild.members if not m.bot]
        bots = [m.id for m in ctx.guild.members if m.bot]
        embed.add_field(
            name="Member Count",
            value=f"{len(mems)} Members | {len(bots)} Bots"
        )
        embed.add_field(
            name="Role Count",
            value=str(len(ctx.guild.roles))
        )
        embed.add_field(
            name="Text Channel Count",
            value=str(len([c.id for c in ctx.guild.text_channels]))
        )
        embed.add_field(
            name="Emote Count",
            value=str(len(ctx.guild.emojis))
        )
        embed.set_footer(text=f"ID: {ctx.guild.id}")
        await ctx.send(embed=embed)

    @staticmethod
    def do_st():
        s = speedtest.Speedtest()
        s.get_best_server()
        dl = s.download()
        ul = s.upload()
        return dl, ul

    @commands.command(
        description="Run a speedtest to view my download/upload speed.",
        brief="Run a speedtest."
    )
    @commands.cooldown(1, 600)
    async def speedtest(self, ctx):
        async with ctx.typing():
            dl, ul = await self.bot.loop.run_in_executor(None, self.do_st)
            await ctx.send(f":arrow_down: Download: **{int(dl/1024/1024)}** MB/s"
                           f"\n:arrow_up: Upload: **{int(ul/1024/1024)}** MB/s")

    @commands.command(
        aliases=['todo'],
        description="View my trello board / to do list.",
        brief="View my trello board / to do list."
    )
    async def trello(self, ctx):
        await ctx.send("View my Trello board here: <https://trello.com/b/IAbwYujm/gamma-bot>")

    @commands.command(
        description="Send you an invite link to my support server.",
        brief="Message you a support link."
    )
    async def support(self, ctx):
        try:
            await ctx.author.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="<:nano_info:483063870655823873> [Click here to join the Support Guild]"
                                "(https://discordapp.com/invite/JBQ2BEa)"
                )
            )
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="<:nano_check:484247886461403144> Check your DM's for the link."
                )
            )
        except discord.Forbidden:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="<:nano_info:483063870655823873> [Click here to join the Support Guild]"
                                "(https://discordapp.com/invite/JBQ2BEa)"
                )
            )

# https://discordapp.com/api/oauth2/authorize?client_id=478437101122224128&permissions=8&scope=bot

    @commands.command(
        description="Send you a link to invite me to your server.",
        brief="Message you my invite link."
    )
    async def invite(self, ctx, *, args: ArgParser=None):
        if hasattr(args, "get"):  # if arguments were supplied
            if args.get("no-dm") is not None:
                if args.get("no-perms") is not None:
                    await ctx.send(
                        embed=discord.Embed(
                            color=discord.Color.blurple(),
                            description="[Use this link to invite me](https://discordapp.com/api/oauth2/authorize?"
                                        "client_id=478437101122224128&permissions=0&scope=bot)"
                        )
                    )
                else:
                    await ctx.send(
                        embed=discord.Embed(
                            color=discord.Color.blurple(),
                            description="[Use this link to invite me](https://discordapp.com/api/oauth2/authorize?"
                                        "client_id=""478437101122224128&permissions=8&scope=bot)"
                        )
                    )
            else:
                if args.get("no-perms") is not None:
                    try:
                        await ctx.author.send(
                            embed=discord.Embed(
                                color=discord.Color.blurple(),
                                description="[Use this link to invite me](https://discordapp.com/api/oauth2/authorize?"
                                            "client_id=478437101122224128&permissions=0&scope=bot)"
                            )
                        )
                        await ctx.send("\U0001f44c")
                    except:
                        assert False, "Something went wrong, try `invite --no-perms --no-dm`."
                else:
                    try:
                        await ctx.author.send(
                            embed=discord.Embed(
                                color=discord.Color.blurple(),
                                description="[Use this link to invite me](https://discordapp.com/api/oauth2/authorize?"
                                            "client_id=478437101122224128&permissions=8&scope=bot)"
                            )
                        )
                        await ctx.send("\U00014f4c")
                    except:
                        assert False, "Something went wrong, try `invite --no-dm`."
        else:  # send link to author with perms
            try:
                await ctx.author.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description="[Use this link to invite me](https://discordapp.com/api/oauth2/authorize?"
                                    "client_id=478437101122224128&permissions=8&scope=bot)"
                    )
                )
                await ctx.send("\U0001f44c")
            except:
                await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description="[Use this link to invite me](https://discordapp.com/api/oauth2/authorize?"
                                    "client_id=478437101122224128&permissions=8&scope=bot)"
                    )
                )

    @commands.command(
        description="Check the guilds user/bot count.",
        brief="Check the guilds user/bot count."
    )
    async def usercount(self, ctx):
        mems = ctx.guild.members
        online = set([m.id for m in mems if m.status == discord.Status.online and not m.bot])
        idle = set([m.id for m in mems if m.status == discord.Status.idle and not m.bot])
        dnd = set([m.id for m in mems if m.status == discord.Status.dnd and not m.bot])
        offline = set([m.id for m in mems if m.status == discord.Status.offline and not m.bot])
        bots = set([m.id for m in mems if m.bot])
        await ctx.send(
            embed=discord.Embed(
                description=f"""<:nano_info:483063870655823873> {ctx.guild} Users

<:online:487129880014880770> {len(online)}
<:idle:487129880274796554> {len(idle)}
<:dnd:487129881231228948> {len(dnd)}
<:offline:487129880320802835> {len(offline)}
\U0001f916 {len(bots)}""",
                color=discord.Color.blurple()
            )
        )

    @commands.command(
        description="Get a lit of all the roles in the current guild.",
        brief="Get all roles of the guild."
    )
    async def roles(self, ctx):
        roles = [role.mention for role in ctx.guild.role_hierarchy if not role.is_default()]
        if len(roles) > 15:
            await SimplePaginator(entries=roles, color=0x7289da, title=f"{ctx.guild} Roles", length=15).paginate(ctx)
        else:
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    title=f"{ctx.guild} Roles",
                    description="\n".join(roles)
                )
            )

    @commands.command(
        aliases=['rinfo'],
        description="Get detailed information about a certain role.",
        brief="Get a role information."
    )
    async def roleinfo(self, ctx, *, _role: discord.Role):
        colorz = _role.color if _role.color.value > 0 else discord.Color(value=16777215)
        color = str(colorz).replace("#", "").lower()
        link = f"https://via.placeholder.com/100/{color}/{color}"
        embed = discord.Embed(
            color=colorz,
            title=f"{_role}"
        )
        embed.add_field(name="Colour", value=f"{_role.color}")
        embed.add_field(name="User Count", value=f"{len(_role.members)}")
        embed.add_field(name="Role ID", value=f"{_role.id}")
        embed.add_field(name="Created At", value=f"""{_role.created_at.strftime("%d/%m/%y @ %H:%M%p")}""")
        perms = dict(_role.permissions)
        allowed = [d.replace('_',' ').title() for d in perms.keys() if perms[d] is True and d in self.spec_perms]
        if allowed:
            embed.add_field(name="Permissions", value=", ".join(allowed))
        embed.set_thumbnail(url=link)
        embed.set_footer(text=f"Belongs to {_role.guild}", icon_url=_role.guild.icon_url_as(format="png"))
        await ctx.send(embed=embed)

    @commands.command(
        aliases=["feedback", "suggest"],
        description="Send feedback about Gamma, whether its a bug or something nice.",
        brief="Send feedback about Gamma."
    )
    async def bugreport(self, ctx, *, feedback=None):
        if not feedback:
            m = await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="<:nano_info:483063870655823873> What is your feedback?"
                )
            )
            try:
                msg = await self.bot.wait_for("message", check=lambda _m: _m.author == ctx.author, timeout=15.0)
            except asyncio.TimeoutError:
                await m.delete()
            else:
                ch = self.bot.get_channel(479506510842560523)
                data = msg.content
                await ch.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"```\n{data}\n```",
                        timestamp=datetime.utcnow()
                    ).set_author(
                        name="New feedback recieved.",
                        icon_url=ctx.author.avatar_url_as(static_format="png")
                    ).set_footer(text=f"From {ctx.author}")
                )
                await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description="<:nano_check:484247886461403144> Your feedback has been recieved."
                    )
                )
        else:
            ch = self.bot.get_channel(479506510842560523)
            data = feedback
            await ch.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"```\n{data}\n```",
                    timestamp=datetime.utcnow()
                ).set_author(
                    name="New feedback recieved.",
                    icon_url=ctx.author.avatar_url_as(static_format="png")
                ).set_footer(text=f"From {ctx.author}")
            )
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="<:nano_check:484247886461403144> Your feedback has been recieved."
                )
            )

    @commands.command(
        description="View Gamma's source code on Github.com",
        brief="View Gamma's source code."
    )
    async def source(self, ctx):
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description="[View my source code here](https://github.com/XuaTheGrate/Gamma-Bot/)"
            )
        )

    @commands.command(
        description="View detailed information about a member.",
        brief="View information about someone."
    )
    async def userinfo(self, ctx, *, user: discord.Member=None):
        user = user or ctx.author
        col = user.color if user.color.value > 0 else discord.Color(16777215)
        embed = discord.Embed(title="User information", description=f"<@{user.id}>", color=col)
        embed.set_author(name=f"{user}", icon_url=f"{user.avatar_url_as(format='png')}")
        embed.set_thumbnail(url=f"{user.avatar_url_as(format='png')}")
        reg_time = user.created_at.strftime("%a %d %b, %Y")
        embed.add_field(name='Registered', value=f'{reg_time}', inline=True)
        join_time = user.joined_at.strftime("%a %d %b, %Y")
        embed.add_field(name='Joined', value=f'{join_time}', inline=True)
        pos = sorted(user.guild.members, key=lambda m: m.joined_at).index(user) + 1
        embed.add_field(name='Join Pos', value=f'{pos}', inline=True)
        embed.add_field(name='Status', value=f'{user.status}'.title(), inline=True)
        roles = [r.mention for r in user.roles if not r.is_default()]
        if not len(" ".join(roles)) > 1000:
            embed.add_field(name=f'Roles ({len(roles)})', value=f'{" ".join(roles) or "None"}', inline=False)
        else:
            embed.add_field(name=f'Roles ({len(roles)})', value='Too long to display.', inline=False)
        perms = dict(user.guild_permissions)
        allowed = [d.replace('_', ' ').title() for d in perms.keys() if perms[d] is True and d in self.spec_perms]
        if allowed:
            embed.add_field(name="Permissions", value=", ".join(allowed))
        embed.set_footer(text=f"ID: {user.id}")
        await ctx.send(embed=embed)

    @staticmethod
    def _mpl_generate(stuff):
        plt.clf()
        plt.cla()
        plt.close()
        matplotlib.rc('axes', edgecolor='w')
        hours = [e for e in range(0, 24)]
        ping = [s['ms'] for s in stuff]
        plt.plot(hours, ping, color="white")
        plt.xlabel("Hour of day", color='white')
        plt.ylabel("Ping (ms)", color='white')
        plt.tick_params(axis='x', colors='white')
        plt.tick_params(axis='y', colors='white')
        plt.savefig("tmp/resp.png", transparent=True)

    @commands.command(
        description="View a detailed graph about my connection times.",
        brief="Ping graph."
    )
    async def pinggraph(self, ctx):
        async with ctx.typing():
            record = await self.bot.db.fetch("SELECT * FROM websocket_latency;")
            await self.bot.loop.run_in_executor(None, self._mpl_generate, record)
            with open("tmp/resp.png", 'rb') as f:
                await ctx.send(file=discord.File(f.read(), 'resp.png'))

    @commands.command(hidden=True)
    async def encode(self, ctx, *, data):
        await ctx.send(custom_encoder.compile_string(data, enc=False))

    @commands.command(hidden=True)
    async def encodeb(self, ctx, *, data):
        await ctx.send(custom_encoder.compile_string(data))

    @commands.command(hidden=True)
    async def decode(self, ctx, *, data):
        data = data.encode()
        decode = custom_encoder.decompile_string(data)
        content = await commands.clean_content().convert(ctx, decode)
        await ctx.send(content)

    @commands.command(hidden=True)
    async def argparsetest(self, ctx, *, args: ArgParser):
        await ctx.send(args)

    @commands.command(hidden=True)
    async def nano(self, ctx, value, *, args: ArgParser=None):
        emote = discord.utils.get(self.bot.emojis, name=f"nano_{value}")
        assert emote is not None, "No emote found."
        if args is not None and args.get("raw") is not None:
            await ctx.send(f"\\{emote}")
        else:
            await ctx.send(f"{emote}")


def setup(bot):
    bot.remove_command("help")
    bot.remove_command("?")
    bot.remove_command("h")
    bot.add_cog(Misc(bot))
