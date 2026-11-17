"""Per-server configuration.

Each guild gets its own entry in a small JSON file next to this module,
so one bot process can serve multiple Discord servers with different
ticket roles, staff roles, and log channels. Set through the `m!config`
command (see cogs/config.py).
"""

import json
import os

import config

_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "guild_config.json")

_DEFAULTS = {
    "ticket_roles": [],
    "staff_roles": [],
    "ticket_log_channel": None,
    "muted_role": [],
    "member_role": [],
    "log_channel": None,
    "ai_role": [],
}


def _load():
    if not os.path.exists(_PATH):
        return {}

    with open(_PATH) as f:
        return json.load(f)


def _save(data):
    with open(_PATH, "w") as f:
        json.dump(data, f, indent=2)


def seed_defaults():
    """
    THIS FUNCTION IS NOT NEEDED ANYMORE BUT IF I REMOVE IT THE ENTIRE CODE BREAKS
    """
    data = _load()
    key = str(config.GUILD_ID)

    if key in data:
        return

    data[key] = {
        "ticket_roles": [config.MODERATOR_ROLE_ID, config.ADMIN_ROLE_ID],
        "staff_roles": [config.MODERATOR_ROLE_ID, config.ADMIN_ROLE_ID],
        "ticket_log_channel": config.TICKET_LOGS_CHANNEL_ID,
    }
    _save(data)


def get_guild_config(guild_id):
    data = _load()

    guild_data = dict(_DEFAULTS)
    guild_data.update(data.get(str(guild_id), {}))
    return guild_data


def _update(guild_id, **changes):
    data = _load()
    key = str(guild_id)

    guild_data = dict(_DEFAULTS)
    guild_data.update(data.get(key, {}))
    guild_data.update(changes)

    data[key] = guild_data
    _save(data)
    
def get_configured_roles(guild, key):
    role_ids = get_guild_config(guild.id)[key]
    roles = []
    for rid in role_ids:
        role = guild.get_role(rid)
        if role:
            roles.append(role)
    return roles


def set_ticket_roles(guild_id, role_ids):
    _update(guild_id, ticket_roles=list(role_ids))


def set_staff_roles(guild_id, role_ids):
    _update(guild_id, staff_roles=list(role_ids))


def set_ticket_log_channel(guild_id, channel_id):
    _update(guild_id, ticket_log_channel=channel_id)
    
def set_log_channel(guild_id, channel_id):
    _update(guild_id, log_channel=channel_id)

def set_muted_role(guild_id, role_ids):
    _update(guild_id, muted_role=list(role_ids))
    
def set_member_role(guild_id, role_ids):
    _update(guild_id, member_role=list(role_ids))

def set_ai_role(guild_id, role_ids):
    _update(guild_id, ai_role=list(role_ids))
    