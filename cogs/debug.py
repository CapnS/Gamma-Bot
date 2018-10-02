from discord.ext import commands
from typing import Union
from contextlib import redirect_stdout
import discord
import traceback
import copy
import io
import logging


logger = logging.getLogger(__name__)


class Debug:
    def __init__(self, bot):
        self.bot = bot
        self._last_result = None
    
    async def __local_check(self, ctx):
        return await self.bot.is_owner(ctx.author)

    @staticmethod
    def cleanup_code(content):
        """Automatically removes code blocks from the code."""
        # remove ```py\n```
        if content.startswith('```') and content.endswith('```'):
            return '\n'.join(content.split('\n')[1:-1])
            # remove `foo`
        return content.strip('` \n')

    @commands.command(
        aliases=['gbl'],
        brief="Add someone to the global blacklist.",
        description="Globally blacklist / whitelist someone. "
                    "They will never be allowed to use any of my commands unless you whitelist them.",
        usage="gblacklist <user>"
    )
    async def gblacklist(self, ctx, *, user: discord.Member):
        if user.id not in self.bot.global_blacklist:
            self.bot.global_blacklist.append(user.id)
            d = "<:nano_check:484247886461403144> Globally blacklisted."
        else:
            self.bot.global_blacklist.remove(user.id)
            d = "<:nano_check:484247886461403144> Globally whitelisted."
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=d
            )
        )

    @commands.command(
        brief="View the current global blacklist.",
        description="View the current global blacklist.",
        usage="view_gblacklist",
        aliases=['vgbl']
    )
    async def view_gblacklist(self, ctx):
        data = self.bot.global_blacklist
        mems = [" - " + str(self.bot.get_user(m)) for m in data]
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                title="Global Blacklist",
                description="\n".join(mems)
            )
        )
    
    @commands.command(
        brief="Reboot the bot.",
        description="Reboot the bot.",
        usage="reboot"
    )
    async def reboot(self, ctx):
        await ctx.send("Restarting...")
        await self.bot.logout()

    @commands.command(
        aliases=["structured_query_language"],
        brief="Run an SQL query.",
        description="Run an SQL query.",
        usage="sql <query>"
    )
    async def sql(self, ctx, *, query: str):
        """Run some SQL."""
        # the imports are here because I imagine some people would want to use
        # this cog as a base for their other cog, and since this one is kinda
        # odd and unnecessary for most people, I will make it easy to remove
        # for those people.
        from .utils.formats import TabularData, Plural
        import time

        query = self.cleanup_code(query)

        is_multistatement = query.count(';') > 1
        if is_multistatement:
            # fetch does not support multiple statements
            strategy = self.bot.db.execute
        else:
            strategy = self.bot.db.fetch

        try:
            start = time.perf_counter()
            results = await strategy(query)
            dt = (time.perf_counter() - start) * 1000.0
        except Exception:
            return await ctx.send(f'```py\n{traceback.format_exc()}\n```')

        rows = len(results)
        if is_multistatement or rows == 0:
            return await ctx.send(f'`{dt:.2f}ms: {results}`')

        headers = list(results[0].keys())
        table = TabularData()
        table.set_columns(headers)
        table.add_rows(list(r.values()) for r in results)
        render = table.render()

        fmt = f'```\n{render}\n```\n*Returned {Plural(row=rows)} in {dt:.2f}ms*'
        if len(fmt) > 2000:
            fp = io.BytesIO(fmt.encode('utf-8'))
            await ctx.send('Too many results...', file=discord.File(fp, 'results.txt'))
        else:
            await ctx.send(fmt)
    
    @commands.command(
        brief="Run a command as another user.",
        description="Run a command as another user.",
        usage="runas <user> <command>"
    )
    async def runas(self, ctx, who: Union[discord.Member, discord.User], *, command: str):
        msg = copy.copy(ctx.message)
        msg.author = who
        msg.content = ctx.prefix + command
        new_ctx = await self.bot.get_context(msg)
        await self.bot.invoke(new_ctx)

    def cleanup_filter(self, message):
        return message.author == message.guild.me

    @commands.command(
        brief="Cleanup the bots messages.",
        usage="cleanup [amount]",
        description="Cleanup the bots messages."
    )
    async def cleanup(self, ctx, amount: int=50):
        c = 0
        async for message in ctx.history(limit=amount).filter(self.cleanup_filter):
            await message.delete()
            c += 1
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> Cleaned {c} messages."
            ),
            delete_after=5
        )

    @commands.command(
        brief="Pull the git repo and reboot.",
        usage="update"
    )
    async def update(self, ctx):
        await ctx.invoke(self.bot.get_command("jsk git"), code="pull")
        await ctx.send("```prolog\nRestarting...\n```")
        await self.bot.logout()
    
    def cleanup_response(self, resp):
        return resp.strip("RESPONSE[]").split(",")
    
    @commands.command(
        brief="View all bot statistics.",
        usage="global_statistics"
    )
    async def global_statistics(self, ctx):
        data = await self.bot.get_data(ctx, "REQUEST[latency,usage_memory,usage_cpu,shards,guilds]")
        embed = discord.Embed(color=discord.Color.blurple(), title="Global Statistic Usage", description="Response Time | Memory Usage | CPU Usage | Shard Count | Guild Count")
        com = ["Tau", "Lambda", "Gamma", "Omicron", "Sigma", "Zeta"]
        for name, response in data.items():
            com.remove(name)
            embed.add_field(name=name,value=" | ".join(f for f in self.cleanup_response(response)), inline=False)
        for value in com:
            embed.add_field(name=value, value="No response...", inline=False)
        await ctx.send(embed=embed)

def setup(bot):
    bot.add_cog(Debug(bot))
