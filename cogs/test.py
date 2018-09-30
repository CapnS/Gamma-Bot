import custom_encoder
import discord
from discord.ext import commands
from .utils.argparser import ArgParser
import asyncio
import typing


class Test:
    def __init__(self, bot):
        self.bot = bot
        self.embed_sessions = []

    @staticmethod
    def _repl_embed_title(embed, data):
        assert len(data) <= 256, "Size too large."
        embed.title = data
        return embed

    @staticmethod
    def _repl_embed_description(embed, data):
        assert len(data) <= 2048, "Size too large."
        embed.description = data
        return embed

    @staticmethod
    def _repl_embed_title_url(embed, data):
        assert data.startswith("https://"), "Invalid link specified."
        embed.url = data
        return embed

    async def _repl_embed_author(self, embed, data):
        await ctx.send("`Note: to skip an option, type ❌.`")
        await ctx.send("Author name?")
        try:
            msg = await self.bot.wait_for("message", check=lambda m: m.author == ctx.author, timeout=15.0)
        except asyncio.TimeoutError:
            return embed
        author = msg.content if msg.content is not "❌" else None
        await ctx.send("Author link?")
        try:
            msg = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=15.0)
        except asyncio.TimeoutError:
            return embed
        url = msg.content if msg.content is not "❌" else None
        if url is not None:
            assert url.startswith("https://"), "Invalid url specified."
        await ctx.send("Author icon?")
        try:
            msg = await self.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=15.0)
        except asyncio.TimeoutError:
            return embed
        icon = msg.content if msg.content is not "❌" else None
        if icon is not None:
            assert icon.startswith("https://") and any([icon.endswith(f) for f in (".jpg", ".png", ".webp", ".gif")]), \
                "Invalid image url."
        embed.set_author(name=author, url=url, icon_url=icon)
        return embed

    @staticmethod
    def _repl_embed_color(embed, data):
        if isinstance(data, str) and data.isdigit():
            data = int(data)
        assert isinstance(data, int), "Must be an integer."
        embed.color = data
        return embed

    def _repl_embed_colour(self, embed, data):
        return self._repl_embed_color(embed, data)

    @staticmethod
    def _repl_embed_field_add(embed, data):
        pass

    @staticmethod
    def _repl_embed_thumbnail(embed, data):
        assert data.startswith("https://") and any([data.endswith(f) for f in (".jpg", ".png", ".webp", ".gif")]), \
            "Invalid image link sent."
        embed.set_thumbnail(url=data)
        return embed

    def _repl_embed_parse_arg(self, data, embed):
        split = data.split(" ")
        func = split[1].replace(" ", "_")
        data.remove(func)
        data = " ".join(func)
        if not hasattr(self, f"_repl_embed_{func}"):
            raise ValueError("<:thonk:493282307176923149>")
        f = getattr(self, f"_repl_embed_{func}")
        return f(embed, data)

    @commands.command(hidden=True)
    async def interactableembed(self, ctx):
        if ctx.author.id in self.embed_sessions:
            await ctx.send("A session is already running.")
            return
        await ctx.send("Alright. Type `[exit]` to cancel the session.")
        self.embed_sessions.append(ctx.author.id)
        custom_embed = discord.Embed()
        while True:
            try:
                msg = await ctx.bot.wait_for('message', check=lambda m: m.author == ctx.author, timeout=120.0)
            except asyncio.TimeoutError:
                await ctx.send("Timed out.")
                self.embed_sessions.remove(ctx.author.id)
                return  # return to cancel it completely
            if msg.content == "[exit]":
                self.embed_sessions.remove(ctx.author.id)
                return  # as above
            if msg.content == "finish":
                break  # break to send the embed
            try:
                custom_embed = self._repl_embed_parse_arg(msg, custom_embed)
            except ValueError as ve:
                await ctx.send(ve)
                continue  # skip and continue on
            except AssertionError as ae:
                await ctx.send(ae)
                continue  # anything else must be forced into the console.
        await ctx.send(embed=custom_embed)
        self.embed_sessions.remove(ctx.author.id)

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
    async def argparsetest(self, ctx, *, args=None):
        req = {"test": bool, "test2": int, "test3": str}
        args = ArgParser(flags=req, silent=True).parse(args)
        await ctx.send(args)

    @commands.command(hidden=True)
    async def nano(self, ctx, value, *, args=None):
        req = {"raw": bool}
        args = ArgParser(flags=req).parse(args)
        raw = args.get("raw")
        emote = discord.utils.get(self.bot.emojis, name=f"nano_{value}")
        if not emote:
            raise ValueError(f"Could not find nano emote 'nano_{value}'")
        await ctx.send("{}{}".format("\\" if raw else "", str(emote)))

    @commands.command(hidden=True)
    async def paginatortest(self, ctx):
        from .utils.paginator import Paginator
        paginator = Paginator(self.bot)
        for a in range(4):
            paginator.add_page(data=discord.Embed(color=discord.Color.blurple(), description=a, title='page ' + str(a)))
        await paginator.do_paginator(ctx)

    @commands.command(hidden=True)
    async def reactiontest(self, ctx):
        msg = await ctx.send("REACT")
        for a in range(5):
            try:
                reaction, user = await self.bot.wait_for(
                    'reaction_add',
                    check=lambda r, u: u == ctx.author and r.message == msg,
                    timeout=15.0
                )
                await ctx.send(f"```\n{reaction}\n```")
            except asyncio.TimeoutError:
                return

    @commands.command(hidden=True)
    async def uniontest(self, ctx, *what: typing.Union[discord.Member, discord.TextChannel]):
        for w in what:
            await ctx.send(f"is {type(w)} {w}")

    @commands.command(hidden=True)
    async def optionaltest(self, ctx, user: typing.Optional[discord.Member]=None,
                           channel: typing.Optional[discord.TextChannel]=None, *, rest=None):
        await ctx.send(f"User {user}")
        await ctx.send(f"Channel {channel}")
        await ctx.send(f"extra {rest}")

    @commands.command(hidden=True)
    async def greedytest(self, ctx, members: commands.Greedy[discord.Member], *, extra=None):
        m = "my fucking nan"  # pycharm keeps getting pissy at me
        await ctx.send(f"Members {' '.join(str(m) for m in members)}\nextra {extra}")

    @commands.command(hidden=True)
    async def test(self, ctx):
        await ctx.message.add_reaction("👌")


def setup(bot):
    bot.add_cog(Test(bot))
