import discord
from discord.ext import commands
from .utils.paginator import Paginator


class CommandConverter(commands.Converter):
    async def convert(self, ctx, arg):
        cmd = ctx.bot.get_command(arg)
        if cmd:
            return cmd
        raise commands.BadArgument(f"Command '{arg}' not found.")


class Help:
    def __init__(self, bot):
        self.bot = bot

    @commands.command(
        name="help",
        brief="The help command.",
        description="What to say? This will show the help for all commands.",
        usage="help [command]"
    )
    async def _help_command(self, ctx, command: CommandConverter=None):
        if not command:
            pass
        else:
            embed=discord.Embed(
                color=discord.Color.blurple(),
                title=command.name+" [subcommand] [...]",
                description=command.description
            )
            if isinstance(command, commands.Group):
                for cmd in command.commands:
                    embed.add_field(
                        name=cmd.usage,
                        value=cmd.description,
                        inline=False
                    )
                await ctx.send(embed=embed)
            else:
                pass


def setup(bot):
    bot.remove_command('help')
    bot.add_cog(Help(bot))
