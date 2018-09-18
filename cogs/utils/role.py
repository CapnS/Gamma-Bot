import discord


def get_top_colored_role(roles: list) -> discord.Role:
    """
    Returns the first role of a list of roles

    :param roles: list of roles:
    :returns discord.Role:
    """
    n_roles = [r for r in roles if r.color.value > 0]
    return n_roles[1]
