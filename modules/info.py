from discord.ext import commands
from utils import checks, info
from datetime import datetime


class Information:
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command()
    @checks.not_blacklisted()
    async def stats(self, ctx):
        """ View quick statistics about the bot. """
        await ctx.send(f"""I have been running since {info.time_diff(datetime.utcnow(), self.bot.launch)}
{self.bot.process.memory_full_info().uss//(1024**2) or self.bot.process.memory_info().rss//(1024**2)}MB ram
{self.bot.process.cpu_percent()}% CPU usage
{round(self.bot.latency*1000)} ms websocket latency.""")

    @commands.command()
    @checks.not_blacklisted()
    async def ping(self, ctx):
        """ Check my (websocket) latency to Discord:tm: """
        await ctx.send(":ping_pong: **{round(self.bot.latency*1000)}**ms")
        
    @commands.command()
    @checks.not_blacklisted()
    async def pong(self, ctx):
        """ Try your luck and see if you can beat the snowflake! """
        msg = await ctx.send("Ping")
        if msg.created_at >= ctx.message.created_at:
            await msg.delete()

def setup(bot): 
    bot.add_cog(Information(bot))