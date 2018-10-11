from discord.ext import commands
import discord
import json


"""
persona fuse <name> [game]
persona learnset <name> [game]
persona info <name> [game]
"""


class FES:
    def __init__(self):
        with open("cogs/persona/fes/persona.json", "rb") as f:
            self.personae = json.loads(f.read())
        with open("cogs/persona/fes/specialfuse.json", "rb") as f:
            self.special_fuse = json.loads(f.read())

    def embedify_record(self, record):
        content = f"""Base level: **{record.get("level")}**
Arcana: **The {record.get("arcana").capitalize()}**
Special: **{record.get("special") or False}**
Summon Price: **${self.get_price(record)}**"""
        embed = discord.Embed(
            color=discord.Color.red(),
            title=record.get("name"),
            description=content
        )
        return embed

    def get_persona(self, name):
        for value in self.personae:
            ret = value.get("name")
            if ret == name:
                return value
        raise ValueError("Persona by that name was not found.")

    def get_price(self, *data):
        total = 0
        for item in data:
            level = item.get("level")
            total += (27 * level * level) + (126 * level) + 2147
        return total

    def get_special_recipe(self, name):
        personae = self.get_persona(name)
        assert personae.get("special"), "Personae doesn't have a special recipe."
        for recipe in self.special_fuse:
            if recipe.get("result") == name:
                pass

    def retrieve_recipe(self, name):
        # TODO Calculate the recipe for the persona via https://arantius.com/misc/persona-3-fes-fusion-calculator/app.js
        data = self.get_persona(name)
        if data.get("special"):
            pass
        else:
            pass


class Persona:
    def __init__(self):
        self.valid = ("p3", "persona 3", "persona3", "p3fes", "persona3fes", "persona 3 fes", "p4",
                      "persona4", "persona 4", "p5", "persona5", "persona 5", "p3p", "persona3portable",
                      "persona 3 portable")
        self.fes = FES()

    @staticmethod
    def personathree(arg):
        return arg in ("p3", "persona3", "persona 3", "p3fes", "persona3fes", "persona 3 fes")

    @staticmethod
    def personaportable(arg):
        return arg in ("p3p", "persona3portable", "persona 3 portable")

    @staticmethod
    def personafour(arg):
        return arg in ("p4", "persona4", "persona 4")

    @staticmethod
    def personafive(arg):
        return arg in ("p5", "persona5", "persona 5")

    def persona_convert(self, arg):
        if self.personathree(arg):
            return arg
        if self.personaportable(arg):
            return arg
        if self.personafour(arg):
            return arg
        if self.personafive(arg):
            return arg
        raise ValueError("Invalid game.")

    @commands.group(
        name="persona",
        usage="persona [subcommand] [...]",
        description='The base command for all Persona-related commands.',
        brief="Base Persona command.",
        invoke_without_comman=True
    )
    async def _persona_base(self, ctx):
        cmds = """`persona fuse <name> [game]`: Gets the top 3 fusion recipes for that Persona.
`persona learnset <name> [game]`: Gets the learnset for the Persona.
`persona info <name> [game]`: Gets detailed information about the Persona.
        """
        await ctx.send(
            embed=discord.Embed(
                color=discord.Color.red(),
                description=f"Valid subcommands:\n\n{cmds}"
            )
        )

    @_persona_base.command(
        name="fuse",
        usage="persona fuse <name> [game]",
        description="Gets the top 3 fusion recipes for a Persona.",
        brief="View fusing recipes for a Persona."
    )
    async def _persona_fuse(self, ctx):
        pass


def setup(bot):
    bot.add_cog(Persona())

