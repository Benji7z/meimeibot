import threading
import re

import discord
from discord.ext import commands

import config
import state
import guild_config
from utils import isBlocked, temperature_monitor



class Core(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.add_check(self.block_role)

    def block_role(self, ctx):
        return not isBlocked(ctx.author)

    # ---------------- Error handling ----------------

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):

        if isBlocked(ctx.author):
            return

        if isinstance(error, commands.CommandNotFound):
            await ctx.reply("I don't know that command.")
            return

        if isinstance(error, commands.MissingPermissions):
            await ctx.reply(
                "You don't have the required permissions to run the command."
            )
            return

        if isinstance(error, commands.MissingAnyRole):
            return await ctx.reply("You're missing the required role(s) to use this command.")

        if isinstance(error, commands.CheckFailure):
            return
        
        if isinstance(error, commands.MissingRequiredArgument):
            return await ctx.reply("You're missing a required argument.")
        

        if isinstance(error, commands.BadArgument):
            return await ctx.reply(f"Bad argument: {error}")

        if isinstance(error, commands.CommandOnCooldown):
            await ctx.reply(
                f"You're currently on cooldown try again after {error.retry_after:.1f}s."
            )
            return

        raise error

    # ---------------- Events ----------------

    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel):
        if channel.name.lower().startswith("ticket"):
            return

        roles = guild_config.get_configured_roles(channel.guild, "muted_role")

        if not roles:
            return

        for role in roles:
            if isinstance(channel, discord.TextChannel):
                await channel.set_permissions(
                    role,
                    send_messages=False,
                    add_reactions=False,
                    create_public_threads=False,
                    create_private_threads=False,
                    send_messages_in_threads=False,
                    attach_files=False,
                    embed_links=False,
                )
            elif isinstance(channel, discord.VoiceChannel):
                await channel.set_permissions(
                    role,
                    speak=False,
                    request_to_speak=False,
                    connect=False,
                )


    @commands.Cog.listener()
    async def on_member_join(self, member):
        await state.general_chat.send(
            f"Welcome {member.mention}! "
            f"You can get additional roles in {state.roles_channel.mention} "
            f"Please read the rules in {state.rules_channel.mention} "
            f"And if you have an issue create a ticket!"
        )

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if isBlocked(message.author):
            return

        if any(user.id == config.DEPRECATED_XIAM_ID for user in message.mentions):
            await message.reply(
                f"This account is deprecated. Use {state.xiam.mention}"
            )
            
        if message.content.startswith(("M!", "/M!", "/m!", "/m", "/M")):
            await message.reply("`m!` is the correct prefix.")
            
    @commands.Cog.listener()
    async def on_guild_role_update(self, before, after):
        if not before.permissions.administrator and after.permissions.administrator:
            permissions = after.permissions
            permissions.administrator = False
            await after.edit(reason="Automatic raid detection: role granted admin permissions.",permissions=permissions)
        
    @commands.Cog.listener()
    async def on_ready(self):
        state.guild = self.bot.get_guild(config.GUILD_ID)

        if state.guild is None:
            print("Guild not found.")
            return

        state.general_chat = self.bot.get_channel(config.GENERAL_CHAT_ID)
        state.roles_channel = self.bot.get_channel(config.ROLES_CHANNEL_ID)
        state.rules_channel = self.bot.get_channel(config.RULES_CHANNEL_ID)

        guild_config.seed_defaults()

        try:
            state.xiam = await self.bot.fetch_user(config.XIAM_ID)
        except discord.NotFound:
            state.xiam = None

        print(f"Logged in as {self.bot.user}")

        if not state.thread_started:
            threading.Thread(
                target=temperature_monitor,
                daemon=True
            ).start()

            state.thread_started = True


async def setup(bot):
    await bot.add_cog(Core(bot))