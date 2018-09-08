from discord.ext import commands
from datetime import datetime
import discord


class Tags:
    def __init__(self, bot):
        self.bot = bot

    async def get_tag(self, ctx, tag):
        tags = await self.bot.db.fetch("SELECT * "
                                       "FROM tags "
                                       "WHERE guildid=$1 AND name % $2"
                                       "ORDER BY similarirty(name, $2) DESC "
                                       "LIMT 4;", ctx.guild.id, tag)
        if not tags:
            assert False, "Tag not found."
        if tags[0]['name'] == tag:
            return tags[0]
        else:
            assert False, "Tag not found. Did you mean\n"+"\n".join([tag['name'] for tag in tags])

    @commands.group(
        description="Base command for all tag related commands, also view existing tags.",
        brief="Base tag command.",
        invoke_without_command=True
    )
    async def tag(self, ctx, *, tag=None):
        tag = await self.get_tag(ctx, tag)
        await ctx.send(tag['response'])

    @tag.command(
        dewscription="Create a new tag for anyone on the server to enjoy.",
        brief="Create a new tag."
    )
    async def create(self, ctx, name, *, response):
        tag = await self.bot.db.fetchval("SELECT response FROM tags WHER name=$1 AND guildid=$2;", name, ctx.guild.id)
        assert tag is None, "Tag by that name already exists."
        query = """
        INSERT INTO tags
        VALUES ($1, $2, $3, $4, 0, $5);
                """
        await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, name, response, datetime.utcnow())


def setup(bot):
    bot.add_cog(Tags(bot))
