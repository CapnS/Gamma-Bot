import discord
from discord.ext import commands
from .utils.paginator import Paginator


class CommandConverter(commands.Converter):
    async def convert(self, ctx, arg):
        cmd = ctx.bot.get_command(arg)
        if cmd:
            return cmd
        raise commands.ConversionError(self, ValueError(f"No command named '{arg}'."))


class Help:
    def __init__(self, bot):
        self.bot = bot
        self.paginator = Paginator(self.bot)

    @commands.command(
        name="help",
        brief="The help command.",
        description="What to say? This will show the help for all commands.",
        usage="help [command]"
    )
    async def _help_command(self, ctx, command: CommandConverter=None):
        pass


def setup(bot):
    bot.remove_command('help')
    bot.add_cog(Help(bot))
