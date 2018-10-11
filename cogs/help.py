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
            paginator = Paginator(self.bot)
            cmds = list(self.bot.commands)
            ret = {}
            for cog in self.bot.cogs.values():
                ret.setdefault(cog.__class__.__name__, discord.Embed(
                    color=discord.Color.blurple(),
                    title=f"{cog.__class__.__name__} Commands",
                    description=cog.__doc__
                ))
            for command in cmds:
                try:
                    if not await command.can_run(ctx):
                        continue
                except commands.MissingPermissions:
                    continue
                except commands.NotOwner:
                    continue
                ret[command.cog_name].add_field(
                    name=command.usage,
                    value=command.description or command.brief,
                    inline=False
                )
            for page in ret.values():
                if len(page.fields) > 0:
                    paginator.add_page(data=page)
            await paginator.do_paginator(ctx)
        else:
            if command.hidden:
                raise commands.CommandNotFound(f"No command named {command.name}")
            if isinstance(command, commands.Group):
                embed = discord.Embed(
                    color=discord.Color.blurple(),
                    title=command.name + " [subcommand] [...]",
                    description=command.description or command.brief
                )
                for cmd in command.commands:
                    embed.add_field(
                        name=cmd.usage,
                        value=cmd.description or cmd.brief,
                        inline=False
                    )
                await ctx.send(embed=embed)
            else:
                embed = discord.Embed(
                    color=discord.Color.blurple()
                )
                embed.add_field(
                    name=command.usage,
                    value=command.description or command.brief,
                    inline=False
                )
                await ctx.send(embed=embed)


def setup(bot):
    bot.remove_command('help')
    bot.add_cog(Help(bot))
