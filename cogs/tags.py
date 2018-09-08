from discord.ext import commands
from datetime import datetime
from SimplePaginator import SimplePaginator
import discord


class Tags:
    def __init__(self, bot):
        self.bot = bot

    async def get_tag(self, ctx, tag):
        tags = await self.bot.db.fetch("SELECT * "
                                       "FROM tags "
                                       "WHERE guildid=$1 AND name % $2"
                                       "ORDER BY similarity(name, $2) DESC "
                                       "LIMIT 4;", ctx.guild.id, tag)
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
    async def tag(self, ctx, *, tag):
        tag = await self.get_tag(ctx, tag)
        await self.bot.db.execute("UPDATE tags SET uses=uses+1 WHERE name=$1 AND guildid=$2;", tag, ctx.guild.id)
        await ctx.send(tag['response'])

    @tag.command(
        dewscription="Create a new tag for anyone on the server to enjoy.",
        brief="Create a new tag."
    )
    async def create(self, ctx, name, *, response):
        tag = await self.bot.db.fetchval("SELECT response FROM tags WHERE name=$1 AND guildid=$2;", name, ctx.guild.id)
        assert tag is None, "Tag by that name already exists."
        assert not name.lower().startswith(('all', 'create', 'delete', 'edit', 'list', 'info')), "Tag starts with" \
                                                                                                "a keyword."
        query = "INSERT INTO tags VALUES ($1, $2, $3, $4, 0, $5);"
        await self.bot.db.execute(query, ctx.guild.id, ctx.author.id, name, response, datetime.utcnow())
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> Tag **{name}** was created."
            )
        )

    @tag.command(
        description="Edit an existing tag. You must own the tag in order to edit it.",
        brief="Edit an existing tag."
    )
    async def edit(self, ctx, name, *, response):
        owner = await self.bot.db.fetchval("SELECT ownerid FROM tags WHERE name=$1 AND guildid=$2;", name, ctx.guild.id)
        assert owner is not None, "Tag by that name does not exist."
        assert ctx.guild.get_member(owner) is ctx.author, "You do not own this tag."
        await self.bot.db.execute("UPDATE tags SET response=$1 WHERE name=$2 AND guildid=$3;", response, name,
                                  ctx.guild.id)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> Tag **{name}** was edited."
            )
        )

    @tag.command(
        description="Remove an existing tag. You must own the tag in order to delete it.",
        brief="Delete an existing tag."
    )
    async def delete(self, ctx, *, name):
        owner = await self.bot.db.fetchval("SELECT ownerid FROM tags WHERE name=$1 AND guildid=$2;", name, ctx.guild.id)
        assert owner is not None, "tag by that name does not exist."
        assert ctx.guild.get_member(owner) is ctx.author, "You do not own this tag."
        await self.bot.db.execute("DELETE FROM tags WHERE guildid=$1 AND name=$1;", ctx.guild.id, name)
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.blurple(),
                description=f"<:nano_check:484247886461403144> Tag **{name}** was deleted."
            )
        )

    @tag.command(
        description="View all tags of the current guild.",
        brief="View all tags."
    )
    async def all(self, ctx):
        tags = await self.bot.db.fetch("SELECT * FROM tags WHERE guildid=$1 ORDER BY uses DESC;", ctx.guild.id)
        assert not tags, "There are no tags for this guild."
        l = [f"{_+1}. {tags[_]['name']}" for _ in range(len(tags))]
        await SimplePaginator(entries=l, colour=0x7289da, title=f"{ctx.guild} tags", length=20).paginate(ctx)

    @tag.command(
        description="View all of your tags, or all of someone elses tags.",
        brief="View your tags."
    )
    async def list(self, ctx, *, user: discord.Member=None):
        user = user or ctx.author
        tags = await self.bot.db.fetch("SELECT * FROM tags WHERE guildid=$1 AND ownerid=$2 ORDER BY uses DESC;",
                                       ctx.guild.id, user.id)
        print(tags)
        assert tags is not None, f"{user} has no tags."
        l = [f"{_+1}. {tags[_]['name']}" for _ in range(len(tags))]
        await SimplePaginator(entries=l, colour=0x7289da, title=f"Tags for {user}", length=20).paginate(ctx)

    @tag.command(
        description="View information about a certain tag.",
        brief="View tag information."
    )
    async def info(self, ctx, *, tag):
        tag = await self.get_tag(ctx, tag)
        embed = discord.Embed(
            color=discord.Color.blurple(),
            title=f"{tag['name']}",
            timestamp=tag['created']
        )
        user = ctx.guild.get_member(tag['ownerid'])
        embed.set_author(
            name=ctx.author,
            icon_url=ctx.author.avatar_url_as(static_format="png")
        )
        embed.add_field(
            name="Owner",
            value=f"{user.mention} {user}" if user else "Unknown"
        )
        embed.add_field(
            name="Uses",
            value=f"{tag['uses']}"
        )
        embed.set_footer(text="Created")
        await ctx.send(embed=embed)


def setup(bot):
    bot.add_cog(Tags(bot))
