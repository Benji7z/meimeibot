"""Shared command checks that depend on per-guild config."""

from discord.ext import commands

import guild_config


def has_staff_role():
    """Allows anyone with one of the guild's configured staff roles.

    Replaces the old hardcoded MODERATOR_ROLE_ID/ADMIN_ROLE_ID checks so
    this works the same way in any server, once that server has set
    staff roles with `m!config staffroles`.
    """

    async def predicate(ctx):
        if ctx.guild is None:
            return False

        staff_role_ids = guild_config.get_guild_config(ctx.guild.id)["staff_roles"]
        member_role_ids = {role.id for role in ctx.author.roles}

        if member_role_ids.isdisjoint(staff_role_ids):
            raise commands.MissingAnyRole(staff_role_ids)

        return True

    return commands.check(predicate)

def has_config_role(role):
    """Allows anyone with one of the guild's configured roles under `role`.

    `role` is the config key, e.g. "ai_role", pointing to a list of
    role IDs in the guild's config.
    """

    async def predicate(ctx):
        if ctx.guild is None:
            return False

        role_ids = guild_config.get_guild_config(ctx.guild.id)[role]
        member_role_ids = {r.id for r in ctx.author.roles}

        if member_role_ids.isdisjoint(role_ids):
            raise commands.MissingAnyRole(role_ids)
        return True

    return commands.check(predicate)
        
        