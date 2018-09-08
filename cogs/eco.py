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
    async def bet(self, ctx, amount: int):
        bal = await self.bot.db.fetchval("SELECT balance FROM economy WHERE userid=$1;", ctx.author.id)
        assert bal >= amount, "You don't have enougb money for that!"
        rng = random.randint(1, 101)
        total = int(((rng / 25) / 2.5) * amount)
        if total < amount:
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:nano_minus:483063870672601114> You lost **${total}**",
                    color=discord.Color.blurple()
                )
            )
            await self.bot.db.execute("UPDATE economy SET balance=balance-$1 WHERE userid=$2;", total, ctx.author.id)
        else:
            await ctx.send(
                embed=discord.Embed(
                    description=f"<:nano_plus:483063870827528232> You won **${total}**",
                    color=discord.Color.blurple()
                )
            )
            await self.bot.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", total, ctx.author.id)

    @commands.command(
        description="Try your luck and double your bet!",
        brief="Double or nothing.",
        aliases=['doubleornothing', '50', '50/50']
    )
    async def don(self, ctx, amount: int):
        bal = await self.bot.db.fetchval("SELECT balance FROM economy WHERE userid=$1;", ctx.author.id)
        assert bal is not None, "You don't have any money!"
        assert bal >= amount, "You don't have enough money!"
        yes = random.choice([True, False])
        if yes:
            await self.bot.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", amount, ctx.author.id)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"<:nano_plus:483063870827528232> You won **${amount}**!"
                )
            )
        else:
            await self.bot.db.execute("UPDATE economy SET balance=balance-$1 WHERE userid=$2;", amount, ctx.author.id)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"<:nano_minus:483063870672601114> You lost **${amount}**."
                )
            )

    @commands.command(
        description="View the leaderboard, whether its global or local.",
        brief="View the leaderboard.",
        aliases=['lb']
    )
    async def leaderboard(self, ctx, mode="local"):
        mode = mode.lower()
        assert mode == 'local' or mode == 'global', "Invalid leaderboard type."
        users = await self.bot.db.fetch("SELECT * FROM economy ORDER BY balance DESC;")
        if mode == 'local':
            mems = {users[u]['userid']: users[u]['balance'] for u in range(min(len(users), 10))
                    if ctx.guild.get_member(users[u]['userid']) is not None}
        else:
            mems = {users[u]['userid']: users[u]['balance'] for u in range(min(len(users), 10))
                    if self.bot.get_user(users[u]['userid'] is not None)}
        await ctx.send(
            embed=discord.Embed(
                title=f"{ctx.guild} Leaderboard" if mode == 'local' else "Global Leaderboard",
                color=discord.Color.blurple(),
                description="\n".join([f"{a+1}. {self.bot.get_user(b)}: ${c}" for a, b, c in zip(range(len(mems)),
                                                                                                 mems.keys(),
                                                                                                 mems.values())])
            )
        )

    @commands.command(
        description="Try to rob a person. The more money, the more likely you are to succeed.\nNOTE! If you fail, they"
                    "will be alerted!",
        brief="Try to rob another member.",
        aliases=['rob']
    )
    async def steal(self, ctx, amount: int, user: discord.Member):
        pass

    @commands.command(
        description="Give some money to a user.",
        brief="Give some money to a user.",
        aliases=['give']
    )
    async def transfer(self, ctx, user: discord.Member, amount: int):
        balance = await self.bot.db.fetchval("SELECT balance FROM economy WHERE userid=$1;", ctx.author.id)
        bal = await self.bot.db.fetchvak("SELECT balance FROM economy WHERE userid=$1;", user.id)
        assert balance is not None, "You don't have any money!"
        assert bal is not NOne, f"{user} doesn't have an account!'"
        assert balance >= amount, "You don't have enough money!"
        await self.bot.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", amount, user.id)
        await self.bot.db.execute("UPDATE economy SET balance=balance-$1 WHERE userid=$2;", amount, user.id)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> Transferred **${amount}** to {user}."
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def baladjust(self, ctx, amount: int, user: discord.Member=None):
        await self.bot.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", amount, user.id)
        await ctx.send("\U0001f44c")


def setup(bot):
    bot.add_cog(Economy(bot))
