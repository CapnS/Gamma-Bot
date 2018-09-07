from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from datetime import datetime
import random
import discord

class Economy:
    def __init__(self, bot):
        self.bot = bot
        self.wheel = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
                      1.1, 1.2, 1.3, 1.4, 1.5, 1.6, 1.7, 1.8, 1.9, 2.0]
    
    async def __before_invoke(self, ctx):
        data = await self.bot.db.fetchrow("SELECT * FROM economy WHERE userid=$1;", ctx.author.id)
        if not data:
            await self.bot.db.execute("INSERT INTO economy VALUES ($1, 1000);",ctx.author.id)

    @commands.command(
        aliases=["$", "bal"],
        description="View yours, or another members balance.",
        brief="View a members balance."
    )
    async def balance(self, ctx, *, member: discord.Member=None):
        member = member or ctx.author
        bal = await self.bot.db.fetchval("SELECT balance FROM economy WHERE userid=$1", member.id)
        assert bal is not None, f"{member} does not have an account!"
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_cash:484224928342605835> **{member}** has **${bal}**"
            )
        )
    
    @commands.command(
        description="Claim your daily reward!",
        brief="Claim your daily reward!"
    )
    @commands.cooldown(1, 86400, BucketType.user)
    async def daily(self, ctx):
        utc = datetime.utcnow()
        n = datetime(utc.year, utc.month, utc.day)
        seed = (ctx.author.id-n.timestamp())/1234567890
        random.seed(seed)
        rng = random.randint(500, 1500)
        await self.bot.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", rng, ctx.author.id)
        embed = discord.Embed(
            color=discord.Color.blurple(),
            description=f"<:nano_cash:484224928342605835> You gained **${rng}**"
        )
        embed.set_footer(text=f"Seed: {round(seed)}")
        await ctx.send(embed=embed)

    @commands.command(
        description="Test your luck against RNG itself!",
        brief="Try your luck!"
    )
    async def bet(self, ctx, number: int, amount: int):
        # Range setup (if you bet within this range, you win)
        utc = datetime.utcnow()
        n = datetime(utc.year, utc.month, utc.day)
        seed = n.timestamp()
        random.seed(seed)
        b_range = random.randint(0, 100)

        # do some checks
        bal = await self.bot.db.fetchval('SELECT balance FROM economy WHERE userid=$1;',ctx.author.id)
        assert bal is not None, "You don't have an account!"
        assert amount < bal, "You don't have enough money for that!"
        assert 0 < number < 101, "A number between 1-100 is required."
        
        # do the rng
        nbal = bal - amount
        random.seed(ctx.author.id/utc.timestamp())
        rng = random.randint(1,100)
        
        debug = f"{max(0,rng-b_range)} < {number} < {min(100,rng+b_range)}"

        # finish up
        if max(0,rng-b_range) < number < min(100,rng+b_range):
            n_amount = round(amount * max(round((b_range*-1)%10,2),1.5))
            """
            print(b_range)
            print(b_range*-1)
            print((b_range*-1)%10)
            print(round((b_range*-1)%10,2))
            print(min(round((b_range*-1)%10,2),1.5))
            print(max(round((b_range*-1)%10,2),1.5))
            print(amount*min(round((b_range*-1)%10,2),1.5))
            print(f"{round(amount * min(round((b_range*-1)%10,2),1.5))}")
            """
            n_bal = nbal + amount

            await self.bot.db.execute("UPDATE economy SET balance=$1 WHERE userid=$2;",n_bal,ctx.author.id)

            embed = discord.Embed(color=discord.Color.blurple(),
            description=f"<:nano_check:484247886461403144> You won **${n_amount}**!")
            embed.set_footer(text=debug)
            await ctx.send(embed=embed)
        else:
            await self.bot.db.execute("UPDATE economy SET balance=$1 WHERE userid=$2;", nbal, ctx.author.id)
            embed = discord.Embed(color=discord.Color.blurple(),
            description=f"<:nano_cross:484247886494695436> You lost **${amount}**.")
            embed.set_footer(text=debug)
            await ctx.send(embed=embed)
    
    @commands.command(
        description="View todays betting range.",
        brief="View todays betting range.",
        name="range"
    )
    async def bet_range(self, ctx):
        utc = datetime.utcnow()
        n = datetime(utc.year,utc.month,utc.day)
        seed = n.timestamp()
        random.seed(seed)
        b_range = random.randint(0,100)
        await ctx.send(embed=discord.Embed(color=discord.Color.blurple(),
        description=f"<:nano_info:483063870655823873> Today's range is **{b_range}**."))


def setup(bot):
    bot.add_cog(Economy(bot))
