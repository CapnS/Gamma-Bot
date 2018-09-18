from discord.ext import commands
from datetime import datetime
from aiohttp.client_exceptions import InvalidURL
import discord
import asyncio
import logging

logger = logging.getLogger(__name__)


class Mods:
    """
    Make sure to use `help <command> to view more information on a certain command.
    This will also view any specified subcommands for that command.
    """
    def __init__(self, bot):
        self.bot = bot

    # Blacklisting related commands

    @commands.command(
        aliases=['bl', 'toggle'],
        description="Blacklist a certain user from using any of my commands.",
        brief="Blacklist a user from my commands."
    )
    @commands.has_permissions(manage_guild=True)
    async def blacklist(self, ctx, *, user: discord.Member):
        if ctx.guild.id not in self.bot.user_blacklist:
            self.bot.user_blacklist.setdefault(ctx.guild.id, list())
        if user.id in self.bot.user_blacklist.get(ctx.guild.id):
            self.bot.user_blacklist[ctx.guild.id].remove(user.id)
            d = f"<:nano_check:484247886461403144> {user} is no longer blacklisted."
            b = "white"
        else:
            self.bot.user_blacklist[ctx.guild.id].append(user.id)
            d = f"<:nano_check:484247886461403144> {user} is now blacklisted."
            b = "black"
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=d
            )
        )
        channel = await self.bot.get_logging_channel(ctx.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{user}",
            timestamp=datetime.utcnow(),
            description=f"**Responsible Moderator**\n{ctx.author}"
        )
        embed.set_author(
            name=f"User was {b}listed",
            icon_url=user.avatar_url_as(static_format="png")
        )
        await channel.send(embed=embed)

    @commands.command(
        aliases=['vbl', 'viewblacklist'],
        description="View a list of people who are blacklisted from using my commands.",
        brief="View the current guilds blacklist."
    )
    @commands.has_permissions(manage_guild=True)
    async def view_blacklist(self, ctx):
        try:
            data = self.bot.user_blacklist.get(ctx.guild.id)
        except KeyError:
            raise commands.CommandError("Guild does not have a blacklist.")
        mems = [str(ctx.guild.get_member(d)) for d in data]
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description="\n".join(mems),
                title=f"{ctx.guild} blacklist"
            ).set_footer(text="Ignores members with Administrator permissions")
        )

    # Message management

    @commands.command(
        aliases=['prune', 'clear'],
        description="Purge a set number of messages from a channel.",
        brief="Purge some messages."
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def purge(self, ctx, amount: int, user: discord.Member=None):
        amount = amount + 1
        try:
            self.bot.is_purging[ctx.channel.id] = True
        except KeyError:
            self.bot.is_purging.setdefault(ctx.channel.id, True)
        if user:
            def check(message):
                return message.author == user
            m = await ctx.channel.purge(limit=amount, check=check)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"<:nano_check:484247886461403144> Deleted {len(m)} messages."
                ),
                delete_after=3
            )
        else:
            m = await ctx.channel.purge(limit=amount)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"<:nano_check:484247886461403144> Deleted {amount} messages."
                ),
                delete_after=3
            )
        _logging = await self.bot.get_logging_channel(ctx.guild)
        if _logging:
            amount = len(m)
            embed = discord.Embed(
                color=discord.Color.blurple(),
                timestamp=datetime.utcnow(),
                description=f"{ctx.channel.mention}"
            )
            embed.set_author(
                name="Chat was purged",
                icon_url=ctx.author.avatar_url_as(static_format="png")
            )
            embed.add_field(
                name="Total messages deleted",
                value=f"{amount}"
            )
            if user:
                embed.add_field(
                    name="Affected user",
                    value=f"{user}"
                )
            embed.add_field(
                name="Responsible Moderator",
                value=f"{ctx.author}"
            )
            await _logging.send(embed=embed)
        await asyncio.sleep(2)
        self.bot.is_purging[ctx.channel.id] = False

    # Warning related commands

    @commands.group(
        description="Warn a user for a certain thing.",
        brief="Warn a user",
        invoke_without_command=True
    )
    @commands.has_permissions(manage_guild=True)
    async def warn(self, ctx, user: discord.Member, *, reason=None):
        warns = await self.bot.db.fetchval("SELECT warns FROM warnings WHERE userid=$1 AND guildid=$2;",
                                           user.id, ctx.guild.id)
        if warns is None:
            warns = []
            await self.bot.db.execute("INSERT INTO warnings VALUES ($1, $2, $3);", ctx.guild.id, user.id, [reason])
        else:
            await self.bot.db.execute("UPDATE warnings SET warns=$1 WHERE userid=$2 AND guildid=$3;",
                                      warns+[reason], user.id, ctx.guild.id)
        try:
            await user.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"<:nano_exclamation:483063871360466945> You were warning in **{ctx.guild}**\n"
                                f"Reason: **{reason or 'No reason specified'}**\n"
                                f"Moderator: **{ctx.author}**\n"
                                f"Total warnings: **{len(warns)+1}**"
                )
            )
            dm = True
        except discord.Forbidden:
            dm = False
        embed = discord.Embed(
            color=discord.Color.blurple(),
            description=f"<:nano_exclamation:483063871360466945> {user} has been warned.",
        )
        if not dm:
            embed.set_footer(text="!! I could not DM the user. The warn was recorded anyway. !!")
        await ctx.send(embed=embed, delete_after=10)
        channel = await self.bot.get_logging_channel(ctx.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{user}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="User was warned.",
            icon_url=user.avatar_url_as(static_format="png")
        )
        embed.add_field(
            name="Responsible Moderator",
            value=f"{ctx.author}"
        )
        embed.add_field(
            name="Reason",
            value=f"{reason or 'None provided.'}"
        )
        embed.set_footer(text=f"DMed? {dm}")
        await channel.send(embed=embed)

    @warn.command(
        description="View warns for a specific user, or yourself.",
        brief="View warnings for a user."
    )
    async def list(self, ctx, *, user: discord.Member=None):
        if not user or user == ctx.author:
            embed = discord.Embed(
                color=discord.Color.blurple(),
                title=f"{ctx.author}"
            )
            warns = await self.bot.db.fetchval("SELECT warns FROM warnings WHERE userid=$1 AND guildid=$2;",
                                               ctx.author.id, ctx.guild.id)
            embed.set_author(
                name="User warnings",
                icon_url=ctx.author.avatar_url_as(static_format="png")
            )
            if warns:
                embed.add_field(
                    name=f"Total warnings: {len(warns)}",
                    value="- "+"\n- ".join(warns)
                )
            else:
                embed.add_field(
                    name="All warnings: 0",
                    value="No warnings for this guild."
                )
            await ctx.send(embed=embed)
            return
        if not ctx.author.guild_permissions.manage_messages:
            assert False, "Invalid permissions."
        warns = await self.bot.db.fetchval("SELECT warns FROM warnings WHERE userid=$1 AND guildid=$2;",
                                           user.id, ctx.guild.id)
        embed = discord.Embed(
            title=f"{user}",
            color=discord.Color.blurple(),
        )
        embed.set_author(
            name="User warnings",
            icon_url=user.avatar_url_as(static_format="png")
        )
        if warns:
            embed.add_field(
                name=f"All warnings: {len(warns)}",
                value="- "+"\n- ".join(warns)
            )
        else:
            embed.add_field(
                name="All warnings: 0",
                value="No warnings for this guild."
            )
        await ctx.send(embed=embed)

    @warn.command(
        description="Clear a specific warning from a user.",
        brief="Clear a warning."
    )
    @commands.has_permissions(manage_messages=True)
    async def clear(self, ctx, user: discord.Member, *, warn=None):
        warns = await self.bot.db.fetchval("SELECT warns FROM warnings WHERE userid=$1 AND guildid=$2;",
                                           user.id, ctx.guild.id)
        assert warns is not None, "User has no warnings."
        assert len(warns) > 0, "User has no warnings."
        if not warn:
            rem = warns.pop(0)
            await self.bot.db.execute("UPDATE warnings SET warns=$1 WHERE userid=$2 AND guildid=$3;",
                                      warns, user.id, ctx.guild.id)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="<:nano_check:484247886461403144> Warning removed."
                ),
                delete_after=5
            )
        else:
            assert warn in warns, "No warning found.\nNote: When removing a specific warning,\nmake sure it is typed" \
                                  " exactly the same."
            warns.remove(warn)
            await self.bot.db.execute("UPDATE warnings SET warns=$1 WHERE userid=$2 AND guildid=$3;",
                                      warns, user.id, ctx.guild.id)
            rem = warn
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description="<:nano_check:484247886461403144> Warning removed."
                ),
                delete_after=5
            )
        channel = await self.bot.get_logging_channel(ctx.guild)
        if not channel:
            return
        embed = discord.Embed(
            title=f"{ctx.author}",
            color=discord.Color.blurple(),
            description=f"**Warn**\n{rem}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="A warning was cleared",
            icon_url=ctx.author.avatar_url_as(static_format="png")
        )
        await channel.send(embed=embed)

    @warn.command(
        description="Remove all warnings of a specified user.",
        brief="Remove all warnings."
    )
    @commands.has_permissions(manage_messages=True)
    async def clearall(self, ctx, *, user: discord.Member):
        warns = await self.bot.db.fetchval("SELECT warns FROM warnings WHERE userid=$1 AND guildid=$2;",
                                           user.id, ctx.guild.id)
        assert warns is not None, f"{user} has no warnings."
        await self.bot.db.execute("UPDATE warnings SET warns=NULL WHERE userid=$1 AND guildid=$2;",
                                  user.id, ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> Removed all warnings for {user}"
            ),
            delete_after=5
        )
        channel = await self.bot.get_logging_channel(ctx.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{ctx.author}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="Users warnings were cleared",
            icon_url=ctx.author.avatar_url_as(static_format="png")
        )
        embed.add_field(
            name="Total warnings removed",
            value=f"{len(warns)}"
        )
        await channel.send(embed=embed)

    # Member removal

    @commands.command(
        description="Kick a member from the guild, with optional reasoning.",
        brief="Kick a member from the guild."
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(self, ctx, user: discord.Member, *, reason="No reason specified."):
        assert self.bot.higher_role(ctx.author, user), "Invalid Permissions."
        try:
            await user.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    timestamp=datetime.utcnow(),
                    description=f"""You were kicked from **{ctx.guild}**
Responsible Moderator: **{ctx.author}**
Reason: ```{reason}```,
"""
                )
            )
            dm = True
        except discord.Forbidden:
            dm = False
        await user.kick(reason=reason)
        await ctx.send(
            delete_after=5,
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> {user} was kicked."
            )
        )
        channel = await self.bot.get_logging_channel(ctx.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{user}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="User was kicked.",
            icon_url=user.avatar_url_as(static_format="png")
        )
        embed.add_field(
            name="Responsible Moderator",
            value=f"{ctx.author}",
            inline=False
        )
        embed.add_field(
            name="Reason",
            value=f"```\n{reason}\n```",
            inline=False
        )
        embed.set_footer(
            text=f"DMed user? {dm}"
        )
        await channel.send(embed=embed)

    @commands.command(
        description="Ban a member from the guild, with optional reasoning.",
        brief="Ban a mamber from the guild."
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(self, ctx, user: discord.Member, *, reason="No reason specified."):
        assert self.bot.higher_role(ctx.author, user), "Invalid permissions."
        try:
            await user.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"""You were banned from **{ctx.guild}**
Responsible Moderator: **{ctx.author}**
Reason: ```\n{reason}\n```""",
                    timestamp=datetime.utcnow()
                )
            )
            dm = True
        except discord.Forbidden:
            dm = False
        await user.ban(reason=reason, delete_message_days=7)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> {user} was banned."
            ),
            delete_after=5
        )
        channel = await self.bot.get_logging_channel(ctx.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{user}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="User was banned",
            icon_url=user.avatar_url_as(static_format="png")
        )
        embed.add_field(
            name="Responsible Moderator",
            value=f"{ctx.author}",
            inline=False
        )
        embed.add_field(
            name="Reason",
            value=f"```\n{reason}\n```"
        )
        embed.set_footer(
            text=f"DMed user? {dm}"
        )
        await channel.send(embed=embed)

    @commands.command(
        description="Kick a user from the guild, and delete their messages. Reason optional.",
        brief="Kick a user and delete their messages."
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def softban(self, ctx, user: discord.Member, *, reason="No reason specified."):
        assert self.bot.higher_role(ctx.author, user), "Invalid permissions."
        try:
            await user.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    timestamp=datetime.utcnow(),
                    description=f"""You were kicked from **{ctx.guild}**
Responsible Moderator: **{ctx.author}**
Reason: ```\n{reason}\n```"""
                )
            )
            dm = True
        except discord.Forbidden:
            dm = False
        await user.ban(reason=reason, delete_message_days=7)
        await user.unban()
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> {user} was kicked."
            ),
            delete_after=5
        )
        channel = await self.bot.get_logging_channel(ctx.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{user}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="User was kicked",
            icon_url=user.avatar_url_as(static_format="png")
        )
        embed.set_footer(
            text=f"DMed user? {dm}"
        )
        await channel.send(embed=embed)

    @commands.command(
        description="Ban a specific user id from this server. This works even if the user isn't in the server.",
        brief="Hackily back a user."
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def hackban(self, ctx, useridid: int):
        obj = discord.Object(id=useridid)
        try:
            await ctx.guild.ban(obj)
        except discord.NotFound:
            assert False, "ID given was not a valid User ID."
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description="<:nano_check:484247886461403144> Success."
            )
        )

    @commands.command()
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def massban(self, ctx, *members: discord.Member):
        success = []
        fail = {}
        for mem in members:
            if self.bot.higher_role(ctx.author, mem):
                try:
                    await ctx.guild.ban(mem, reason=f"Mass ban by {ctx.author}")
                    success.append(mem)
                except Exception as e:
                    fail.setdefault(mem, f"{type(e).__name__)}: {e}")
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> Banned {len(success)}"
            ).add_field(
                name=f"Failed to ban {len(fail.keys())}",
                value="\n".join([f"- {m}\n> {r}" for m, r in fail.items()])
            ),
            delete_after=4
        )

    # Member muting / unmuting commands
    # NOTE: timers wont be available until
    # i get a dedicated vps

    @commands.command(
        description="Mute a member from typing in chat and speaking in voice channels.",
        brief="Mute a member."
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def mute(self, ctx, user: discord.Member, *, reason="No reason specified."):
        assert self.bot.higher_role(ctx.author, user), "Invalid permissions."
        role = await self.bot.get_muted_role(ctx.guild)
        assert role is not None, "Guild has no muted role specified."
        assert role not in user.roles, "User is already muted."
        await user.add_roles(role)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> {user} was muted."
            ),
            delete_after=5
        )
        channel = await self.bot.get_logging_channel(ctx.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{user}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="Member was muted",
            icon_url=user.avatar_url_as(static_format="png")
        )
        embed.add_field(
            name="Responsible Moderator",
            value=f"{ctx.author}",
            inline=False
        )
        embed.add_field(
            name="Reason",
            value=f"```\n{reason}\n```"
        )
        await channel.send(embed=embed)

    @commands.command(
        description="Unmute a user, allowing them to type in chat and speak in voice.",
        brief="Unmute a user."
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def unmute(self, ctx, *, user: discord.Member):
        assert self.bot.higher_role(ctx.author, user), "Invalid Permissions."
        role = await self.bot.get_muted_role(ctx.guild)
        assert role is not None, "Guild does not have a muted role."
        assert role in user.roles, "User is not muted."
        await user.remove_roles(role)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> {user} was unmuted."
            ),
            delete_after=5
        )
        channel = await self.bot.get_logging_channel(ctx.guild)
        if not channel:
            return
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{user}",
            timestamp=datetime.utcnow()
        )
        embed.set_author(
            name="User was unmuted",
            icon_url=user.avatar_url_as(format="png")
        )
        embed.add_field(
            name="Responsible Moderator",
            value=f"{ctx.author}"
        )
        await channel.send(embed=embed)

    # emoji management
    @commands.command(
        description="Upload a custom emoticon to the server. Both you and the bot requires Manage Emojis permissions.",
        brief="Upload a custom emote to the server.",
        aliases=['emojiadd', 'emoteadd', 'addemote']
    )
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_emojis=True)
    async def addemoji(self, ctx, name, url=None):
        assert url is not None or len(ctx.message.attachments) > 0, "You must give either a link or an attachment."
        assert discord.utils.get(ctx.guild.emojis, name=name) is None, "An emoji by this name already exists."
        if url is None:
            attach = ctx.message.attachments[0]
            assert attach.height is not None, "Attachment is not an image."
            async with ctx.typing():
                await attach.save(f"tmp/{ctx.guild.id}_{ctx.message.id}.png")
                with open(f"tmp/{ctx.guild.id}_{ctx.message.id}.png", "rb") as f:
                    try:
                        emote = await ctx.guild.create_custom_emoji(name=name, image=f.read())
                    except discord.HTTPException:
                        assert False, "Failed to upload. Note that you cannot have spaces in the emoji name."
                await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"{emote} was successfully created."
                    )
                )
        else:
            try:
                async with ctx.typing():
                    async with self.bot.session.get(url) as resp:
                        assert resp.status == 200, "An unknown error has occured."
                        data = await resp.read()
                        try:
                            emote = await ctx.guild.create_custom_emoji(name=name, image=data)
                        except discord.HTTPException:
                            assert False, "Failed to upload. Note that you cannot have spaces in the emoji name."
                        await ctx.send(
                            embed=discord.Embed(
                                color=discord.Color.blurple(),
                                description=f"{emote} was successfully created."
                            )
                        )
            except InvalidURL:
                assert False, "Invalid url entered."

    @commands.command(
        description="Delete a custom emote from the server. This is particularly useful for mobile users.",
        brief="Delete a custom emote.",
        aliases=['emojidelete', 'deleteemote', 'emotedelete']
    )
    @commands.has_permissions(manage_emojis=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def deleteemoji(self, ctx, name):
        emote = discord.utils.get(ctx.guild.emojis, name=name)
        assert emote is not None, "An emote by that name was not found."
        await emote.delete()
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description="<:nano_check:484247886461403144> Success."
            )
        )


def setup(bot):
    bot.add_cog(Mods(bot))
