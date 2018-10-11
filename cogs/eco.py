from discord.ext import commands
from discord.ext.commands.cooldowns import BucketType
from datetime import datetime
import random
import discord
import logging
import asyncio

logger = logging.getLogger(__name__)


class Balance:
    def __init__(self, db):
        self.db = db

    async def get(self, user: discord.Member):
        return await self.db.fetchval("SELECT balance FROM economy WHERE userid=$1;", user.id)

    @staticmethod
    def to_str(amount: int):
        amount = str(amount)
        amount = amount[::-1]
        spl = [amount[i:i + 3][::-1] for i in range(0, len(amount), 3)]
        return "$"+",".join(spl[::-1])

    async def get_loan(self, user: discord.Member):
        return await self.db.fetchval("SELECT require FROM loans WHERE userid=$1;", user.id)

    @staticmethod
    async def get_rate():
        random.seed(datetime.utcnow().timestamp)
        return random.randint(1, 100)

    async def new_loan(self, user: discord.Member, amount: int):
        rate = await self.get_rate() / 100
        total = amount + (amount*rate)
        await self.db.execute("INSERT INTO loans VALUES ($1, $2);", user.id, int(total))
        await self.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", amount, user.id)
        return total

    async def clear_loan(self, user: discord.Member):
        await self.db.execute("DELETE FROM loans WHERE userid=$1;", user.id)


class Economy:
    def __init__(self, bot):
        self.bot = bot
        self.wheel = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9,
                      1.2, 1.4, 1.5, 1.6, 1.8, 1.9, 2.0]
        self.dictionary = {}
        self.bal = Balance(bot.db)
    
    async def __before_invoke(self, ctx):
        data = await self.bal.get(ctx.author)
        if data is None:
            await self.bot.db.execute("INSERT INTO economy VALUES ($1, 1000);", ctx.author.id)
        loan = await self.bal.get_loan(ctx.author)
        if loan is not None:
            if data > loan:
                n = self.bal.to_str(loan)
                await self.bot.db.execute("UPDATE economy SET balance=balance-$1 WHERE userid=$2;", loan, ctx.author.id)
                await self.bot.db.execute("DELETE FROM loans WHERE userid=$1;", ctx.author.id)
                await ctx.send(
                    embed=discord.Embed(
                        color=discord.Color.blurple(),
                        description=f"<:nano_info:483063870655823873> {ctx.author}, your loan of **{n}** was "
                                    f"automatically repaid."
                    )
                )

    @commands.command(
        aliases=["$", "bal"],
        description="View yours, or another members balance.",
        brief="View a members balance.",
        usage="bal [user]"
    )
    async def balance(self, ctx, *, member: discord.Member=None):
        member = member or ctx.author
        bal = await self.bal.get(member)
        assert bal is not None, f"{member} does not have an account!"
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_cash:484224928342605835> **{member}** has **{self.bal.to_str(bal)}**"
            )
        )
    
    @commands.command(
        description="Claim your daily reward!",
        brief="Claim your daily reward!",
        usage="daily"
    )
    @commands.cooldown(1, 86400, BucketType.user)
    async def daily(self, ctx):
        bal = await self.bal.get(ctx.author)
        assert bal is not None
        utc = datetime.utcnow()
        n = datetime(utc.year, utc.month, utc.day)
        seed = (ctx.author.id-n.timestamp())/1234567890
        random.seed(seed)
        low = random.randint(1, 5000)
        high = random.randint(5001, 20000)
        if low < high:
            rng = random.randint(low, high)
        else:
            rng = random.randint(high, low)
        rng = int(rng)
        await self.bot.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", rng, ctx.author.id)
        embed = discord.Embed(
            color=discord.Color.blurple(),
            description=f"<:nano_cash:484224928342605835> You gained **{self.bal.to_str(rng)}**"
        )
        embed.set_footer(text=f"Seed: {round(seed)}")
        await ctx.send(embed=embed)

    @commands.command(
        description="Test your luck against RNG itself!",
        brief="Try your luck!",
        usage="bet <amount>"
    )
    @commands.cooldown(4, 30, BucketType.user)
    async def bet(self, ctx, amount: int):
        bal = await self.bal.get(ctx.author)
        assert bal is not None
        assert bal >= amount, "You don't have enough money."
        await self.bot.db.execute("UPDATE economy SET balance=balance-$1 WHERE userid=$2;", amount, ctx.author.id)
        n_bal = bal - amount
        wheel = random.choice(self.wheel)
        total = int(amount*wheel)
        nbal = n_bal + total
        if total < amount:
            success = "<:nano_cross:484247886494695436> You lost **{}**."
        else:
            success = "<:nano_check:484247886461403144> You won **{}**!"
        await self.bot.db.execute("UPDATE economy SET balance=$1 WHERE userid=$2;", nbal, ctx.author.id)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=success.format(self.bal.to_str(nbal-bal) if total > amount
                                           else self.bal.to_str((nbal-bal)*-1))
            )
        )

    @commands.command(
        description="Try your luck and double your bet!",
        brief="Double or nothing.",
        aliases=['doubleornothing', '50', '50/50'],
        usage="don <amount>"
    )
    async def don(self, ctx, amount: int):
        bal = await self.bal.get(ctx.author)
        assert bal is not None, "You don't have any money!"
        assert bal >= amount, "You don't have enough money!"
        yes = random.choice([True, False])
        if yes:
            await self.bot.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", amount, ctx.author.id)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"<:nano_plus:483063870827528232> You won **{self.bal.to_str(amount)}**!"
                )
            )
        else:
            await self.bot.db.execute("UPDATE economy SET balance=balance-$1 WHERE userid=$2;", amount, ctx.author.id)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"<:nano_minus:483063870672601114> You lost **{self.bal.to_str(amount)}**."
                )
            )

    @commands.command(
        description="View the leaderboard, whether its global or local. The parameter \"mode\" can be either \"local\""
                    " or \"global\". Defaults to \"local\".",
        brief="View the leaderboard.",
        aliases=['lb'],
        usage="lb [mode]"
    )
    async def leaderboard(self, ctx, mode="local"):
        mode = mode.lower()
        assert mode == 'local' or mode == 'global', "Invalid leaderboard type."
        users = await self.bot.db.fetch("SELECT * FROM economy ORDER BY balance DESC, userid ASC;")
        if mode == 'local':
            mems = {users[u]['userid']: users[u]['balance'] for u in range(len(users))
                    if ctx.guild.get_member(users[u]['userid']) is not None}
            print(f"Local members length {len(mems)}")
        else:
            mems = {users[u]['userid']: users[u]['balance'] for u in range(len(users))
                    if self.bot.get_user(users[u]['userid']) is not None}
            print(f"Global members length {len(mems)}")
        mems = dict(list(mems.items())[:10])
        await ctx.send(
            embed=discord.Embed(
                title=f"{ctx.guild} Leaderboard" if mode == 'local' else "Global Leaderboard",
                color=discord.Color.blurple(),
                description="\n".join([f"{a+1}. {self.bot.get_user(b)}: {self.bal.to_str(c)}"
                                       for a, b, c in zip(range(len(mems)), mems.keys(), mems.values())])
            )
        )

    @commands.command(
        description="Try to rob a person. The more money, the more likely you are to succeed.\nNOTE! If you fail, they"
                    "will be alerted!",
        brief="Try to rob another member.",
        aliases=['rob'],
        usage="steal <amount> <user>"
    )
    async def steal(self, ctx, amount: int, user: discord.Member):
        pass

    @commands.command(
        description="Give some money to a user.",
        brief="Give some money to a user.",
        aliases=['give'],
        usage="give <user> <amount>"
    )
    async def transfer(self, ctx, user: discord.Member, amount: int):
        balance = await self.bal.get(ctx.author)
        bal = await self.bal.get(user)
        assert balance is not None, "You don't have any money!"
        assert bal is not None, f"{user} doesn't have an account!'"
        assert balance >= amount, "You don't have enough money!"
        await self.bot.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", amount, user.id)
        await self.bot.db.execute("UPDATE economy SET balance=balance-$1 WHERE userid=$2;", amount, ctx.author.id)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> Transferred **${self.bal.to_str(amount)}** to {user}."
            )
        )

    @commands.command(hidden=True)
    @commands.is_owner()
    async def baladjust(self, ctx, amount: int, user: discord.Member=None):
        await self.bot.db.execute("UPDATE economy SET balance=balance+$1 WHERE userid=$2;", amount, user.id)
        await ctx.send("\U0001f44c")

    @commands.command(
        description="Hello. I am Mr. L. Shark. you can request a loan for me, however depending on how I feel, you may"
                    "need to pay a certain amount of interest in return. You cannot loan more than $10k",
        brief="Request a loan from Mr. L. Shark.",
        usage="loan <amount>"
    )
    async def loan(self, ctx, amount: int):
        assert amount <= 10000, "I can't give more than $10,000!"
        interest = await self.bal.get_loan(ctx.author)
        assert interest is None, "You already have a loan waiting."
        rate = await self.bal.get_rate()
        m = await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f'<:nano_info:483063870655823873> Todays rate is {rate}%. Do you want to continue?'
                            f'\nReact with <:nano_check:484247886461403144> to confirm.'
            )
        )
        await m.add_reaction(':nano_check:484247886461403144')
        try:
            await self.bot.wait_for('reaction_add', timeout=15.0, check=lambda r, u: u == ctx.author and
                                    str(r) == '<:nano_check:484247886461403144>')
        except asyncio.TimeoutError:
            pass
        else:
            n = await self.bal.new_loan(ctx.author, amount)
            await ctx.send(
                embed=discord.Embed(
                    color=discord.Color.blurple(),
                    description=f"<:nano_check:484247886461403144> Done. You gained **{amount}** and now have a loan of"
                                f" **{n}** waiting for you."
                ).set_footer(text='Note: run the "loaninfo" command to view information about loans.')
            )
        finally:
            await m.delete()

    @commands.command(
        description="View detailed information about loans, how they work, the interest rates etc.",
        brief="View information about loans.",
        usage="loaninfo"
    )
    async def loaninfo(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Economy(bot))
