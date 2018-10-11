import traceback
import discord
import asyncio


"""
NOTICE:

Each function here MUST return an embed.
"""


class Paginator:
    def __init__(self, bot):
        self.pages = []  # list of embeds
        self.active = None
        if bot.official:
            self.reactions = {
                ":nano_left:492831102189436969": self.previous_page,
                ":nano_right:492831102864588801": self.next_page,
                ":nano_cross:484247886494695436": self.cancel,
                ":nano_question:483063870706155540": self.info,
                ":nano_clip:483070124262293534": self.jump
            }
        else:
            self.reactions = {
                "⬅": self.previous_page,
                "➡": self.next_page,
                "❌": self.cancel,
                "❓": self.info,
                "📎": self.jump
            }

    def add_page(self, *, data: discord.Embed):
        self.pages.append(data)

    async def do_paginator(self, ctx):
        paginator = await self.prepare_paginator(ctx)
        cont = True
        while cont:
            try:
                reaction, user = await ctx.bot.wait_for('reaction_add',
                                                        check=lambda r, u: u == ctx.author,
                                                        timeout=60.0
                                 )
            except asyncio.TimeoutError:
                break
            cont = await self.parse_reaction(await ctx.bot.get_context(paginator), ctx, str(reaction))

    async def prepare_paginator(self, ctx):
        msg = await ctx.send(embed=self.pages[0])
        for reaction in self.reactions.keys():
            await msg.add_reaction(reaction)
        self.active = self.pages[0]
        return msg

    async def parse_reaction(self, bot_ctx, user_ctx, reaction):
        if bot_ctx.bot.official:
            reaction = str(reaction).strip("<>")
        try:
            func = self.reactions.get(reaction)
        except Exception as e:
            traceback.print_exception(type(e), e, e.__traceback__)
            return
        try:
            value = func()  # if the command doesnt need an argument
        except:  # if the command does, this only applies to `jump` which requires a page number/name
            try:
                msg = await bot_ctx.send("What page do you want to go to?")
                data = await bot_ctx.bot.wait_for('message', check=lambda m: m.author == user_ctx.author, timeout=15.0)
                value = func(data.content)
                await msg.delete()
                try:
                    await data.delete()
                except discord.Forbidden:
                    pass
            except asyncio.TimeoutError:
                return
        if value is True:
            await bot_ctx.message.delete()
            return
        try:  # otherwise, the value can only be an embed
            await bot_ctx.message.remove_reaction(reaction, user_ctx.author)
        except discord.Forbidden:
            pass
        await bot_ctx.message.edit(embed=value)
        return True

    def try_get_page(self, page):
        if page.isdigit():
            try:
                return self.pages[int(page)-1]
            except IndexError:
                return
        for p in self.pages:
            if p.title.startswith(page):
                return p
        return

    @property
    def page_count(self):
        return len(self.pages)

    @property
    def current_page_number(self):
        try:
            return self.pages.index(self.active)
        except ValueError as e:  # shouldnt happen supposedly
            traceback.print_exception(type(e), e, e.__traceback__)
            return

    @property
    def current_page(self):
        return self.active

    def next_page(self):
        """Switch to the next page, or do nothing if there are no more pages."""
        data = self.pages[min(self.pages.index(self.current_page)+1, self.page_count-1)]
        self.active = data
        return data

    def previous_page(self):
        """Go back a page, or do nothing if you are at the start."""
        data = self.pages[max(self.pages.index(self.current_page)-1, 0)]
        self.active = data
        return data

    @staticmethod
    def cancel():
        """Exit the paginator."""
        return True

    def info(self):
        """View help on how to use the paginator."""
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title="Paginator information",
            description="Heres how to use Xua's completely customized and interacble Paginator!\n\n" +
                        "\n".join([f"<{emote}>: {resp.__doc__}" for emote, resp in self.reactions.items()])
        ).set_footer(text=f"You were on page \"{self.active.title}\" (#{self.pages.index(self.active)+1})")
        return embed

    def jump(self, page):
        """Jump to a specific page"""
        page = self.try_get_page(page)
        if not page:
            raise ValueError("No page found.")
        self.active = page
        return page
