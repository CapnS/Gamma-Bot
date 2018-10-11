import discord
from discord.ext import commands


class RoleGroup:
    def __init__(self, *, name: str, role_requirement: discord.Role=None, level_requirement: int=None):
        self.name = name
        self.req = role_requirement, level_requirement  # level wont be implemented for a while


class Role:
    def __init__(self, *, role: discord.Role, guild: discord.Guild, group: RoleGroup=None):
        self.role = role
        self.guild = guild
        self.group = group
