# Shared runtime state, populated in on_ready (cogs/core.py).
# Imported by other cogs so they can read/write the same values.

guild = None

general_chat = None
roles_channel = None
rules_channel = None

xiam = None

thread_started = False
