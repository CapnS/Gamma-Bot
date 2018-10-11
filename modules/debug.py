from discord.ext import commands
import discord

class Debug:
    def __init__(self, bot):
        self.bot = bot
        self.validators = [455289384187592704]
    
    async def __local_check(self, ctx):
        return ctx.author.id in self.validators
    
    def __unload(self):
        self.bot.unload_extension("jishaku")
    
    @commands.command(
        name="gbl",
        aliases=["globalblacklist", "gblacklist"],
        description="Globally blacklist someone from using my commands. They cannont use any of my commands, regardless of which server they are in.",
        brief="Globally blacklist someone.",
    )
    async def _global_blacklist(self, ctx, *, member: discord.Member):
        if member.id not in self.bot.global_blacklist:
            self.bot.global_blacklist.append(member.id)
            await ctx.send(f"Blacklisted **{member}**.")
        else:
            self.bot.global_blacklist.remove(member.id)
            await ctx.send(f"Unblacklisted **{member}**.")
        await self.bot.flush_database()
    
    @commands.command(
        name="vgbl",
        aliases=['viewglobalblacklist', 'viewgblacklist'],
        description="View the currently active global blacklist.",
        brief="View the currently active global blacklist.",
    )
    async def _view_global_blacklist(self, ctx):
        try:
            await ctx.send("**Here is everyone that is blacklisted.**{}".format("".join([f"\n- **{self.bot.get_user(m)}**" for m in self.bot.global_blacklist]) or "None"))
        except discord.HTTPException:
            try:
                for mems in [self.bot.global_blacklist[x:x+5] for x in range(0, len(self.bot.global_blacklist), 20)]:
                    await ctx.send("- {}".format([f"\n- **{m}**" for m in mems]))
            except discord.Forbidden:
                return await ctx.send("Too long, and I cannot dm you.")
            await ctx.send("Too long, lemme DM you.")
    
    @commands.command(
        name="exit",
        aliases=['close','die'],
        description="Close the bot, disconnect and destroy the script.",
        brief="Exit the bot.",
    )
    async def _exit(self, ctx):
        await ctx.send("k")
        await self.bot.flush_database()
        await self.bot.logout()
        
def setup(bot):
    bot.load_extension("jishaku")
    bot.add_cog(Debug(bot))