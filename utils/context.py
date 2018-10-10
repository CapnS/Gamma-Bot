from discord.ext import commands
from utils import errors
import discord
import traceback


class SuperContext(commands.Context):
    async def error(self, message, *, exc=None):  # exc for logging fatal errors
        await self.send(embed=discord.Embed(color=discord.Color.red()).set_author(icon_url="https://cdn.discordapp.com/emojis/484247886494695436.png", name=message))
        if exc:
            await self.bot.log_exception(type(exc), exc, exc.__traceback__)
    
    async def info(self, message):
        await self.send(embed=discord.Embed(color=discord.Color.blue()).set_author(icon_url="https://cdn.discordapp.com/emojis/483063870706155540.png", name=message))

    async def add_reaction(self, reaction):
        await self.message.add_reaction(reaction)
    
    async def upload_emoji(self, name, *, image: discord.Attachment=None, url: str=None):
        if not image and not url:
            raise errors.MissingUpload()
        if url:
            try:
                async with self.bot.session.get(url) as resp:
                    if resp.status != 200:
                        raise errors.HTTPException(resp.status, resp.reason)
                    await self.guild.create_custom_emoji(name=name, image=await resp.read())
            except BaseException as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                raise errors.HTTPException(-1, "Something went wrong.")
        else:
            try:
                async with self.bot.session.get(image.url) as resp:
                    if resp.status != 200:
                        raise errors.HTTPException(resp.status, resp.reason)
                    await self.guild.create_custom_emoji(name=name, image=await resp.read())
            except BaseException as e:
                traceback.print_exception(type(e), e, e.__traceback__)
                raise errors.HTTPException(-1, "Something went wrong.")