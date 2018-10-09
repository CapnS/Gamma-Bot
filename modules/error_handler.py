from discord.ext import commands
import discord
from utils import errors
import traceback


class ErrorHandler:
    def __init__(self, bot):
        self.bot = bot
        self.error_channel = 496492187270512670
        self.ignored_errors = commands.CommandNotFound, commands.NotOwner  # ignored error classes
        
    async def on_ready(self):
        self.error_channel = self.bot.get_channel(self.error_channel)
        
    async def on_command_error(self, ctx, exc):
        exc = getattr(exc, "original", exc)
        if any(isinstance(exc, e) for e in self.ignored_errors):
            return
        await ctx.error(str(exc))
        
    async def on_error(self, event, *args, **kwargs):
        await self.error_channel.send(f"Error in **__{event}__**:\n```py\n{traceback.format_exc()}\n```")
        traceback.print_exc()
        print(args)
        print(kwargs)
        
def setup(bot):
    bot.add_cog(ErrorHandler(bot))