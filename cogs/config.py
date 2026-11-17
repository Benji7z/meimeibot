import discord
from discord.ext import commands

import guild_config


class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="config", invoke_without_command=True)
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def config_(self, ctx):
        await ctx.send(
            "Usage:\n"
            "`m!config ticketroles @Role [@Role ...]` - roles pinged and added to new tickets\n"
            "`m!config staffroles @Role [@Role ...]` - roles allowed to use staff commands "
            "(tag, add_role, remove_role, revive, heresify)\n"
            "`m!config ticketlog #channel` - where closed-ticket summaries are sent\n"
            "`m!config mutedrole @Role [@Role ...]` - roles that cannot talk outside of ticket channels\n"
            "`m!config memberrole @Role [@Role ...]` - default member role (WILL NOT BE ADDED ON JOIN)\n"
            "`m!config airole @Role [@Role ...]` - rooles allowed to use the ai command\n"
            "`m!config show` - view the current configuration"
        )

    @config_.command(name="ticketroles")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def ticketroles(self, ctx, *roles: discord.Role):
        if not roles:
            return await ctx.reply(
                "Mention at least one role, e.g. `m!config ticketroles @Moderator @Admin`."
            )

        guild_config.set_ticket_roles(ctx.guild.id, [role.id for role in roles])

        mentions = ", ".join(role.mention for role in roles)
        await ctx.reply(f"New tickets will now ping and be visible to: {mentions}")

    @config_.command(name="staffroles")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def staffroles(self, ctx, *roles: discord.Role):
        if not roles:
            return await ctx.reply(
                "Mention at least one role, e.g. `m!config staffroles @Moderator @Admin`."
            )

        guild_config.set_staff_roles(ctx.guild.id, [role.id for role in roles])

        mentions = ", ".join(role.mention for role in roles)
        await ctx.reply(
            f"Staff commands (tag, add_role, remove_role, revive, heresify) "
            f"are now available to: {mentions}"
        )

    @config_.command(name="ticketlog")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def ticketlog(self, ctx, channel: discord.TextChannel):
        guild_config.set_ticket_log_channel(ctx.guild.id, channel.id)
        await ctx.reply(f"Closed tickets will now be logged in {channel.mention}")
        
    @config_.command(name="mutedrole")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def mutedrole(self, ctx, *roles: discord.Role):
        if not roles:
            return await ctx.reply(
                "Mention at least one role, e.g. `m!config mutedrole @MutedRole`."
            )

        guild_config.set_muted_role(ctx.guild.id, [role.id for role in roles])

        mentions = ", ".join(role.mention for role in roles)
        await ctx.reply(f"Muted role(s) set to: {mentions}")
        
    @config_.command(name="memberrole")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def memberrole(self, ctx, *roles: discord.Role):
        if not roles:
            return await ctx.reply(
                "Mention at least one role, e.g. `m!config memberrole @MemberRole`."
            )
        guild_config.set_member_role(ctx.guild.id, [role.id for role in roles])

        mentions = ", ".join(role.mention for role in roles)
        await ctx.reply(f"Member role(s) set to: {mentions}")
        
    @config_.command(name="logchannel")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def logchannel(self, ctx, channel: discord.TextChannel):
        guild_config.set_log_channel(ctx.guild.id, channel.id)
        await ctx.reply(f"Logs will now be logged in {channel.mention}")
    
    @config_.command(name="airole")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def airole(self, ctx, *roles: discord.Role):
        if not roles:
            return await ctx.reply(
                "Mention at least one role, e.g. `m!config AiRole @AiRole"
            )
        guild_config.set_ai_role(ctx.guild.id, [role.id for role in roles])
        
        mentions = ", ".join(role.mention for role in roles)
        await ctx.reply(f"AI role(s) set to: {mentions}")

    @config_.command(name="show")
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def show(self, ctx):
        cfg = guild_config.get_guild_config(ctx.guild.id)

        def role_list(role_ids):
            return ", ".join(f"<@&{rid}>" for rid in role_ids) if role_ids else "*not set*"

        embed = discord.Embed(
            title=f"Configuration for {ctx.guild.name}",
            color=discord.Color.blurple()
        )
        embed.add_field(name="Ticket roles", value=role_list(cfg["ticket_roles"]), inline=False)
        embed.add_field(name="Staff roles", value=role_list(cfg["staff_roles"]), inline=False)
        embed.add_field(
            name="Ticket log channel",
            value=f"<#{cfg['ticket_log_channel']}>" if cfg["ticket_log_channel"] else "*not set*",
            inline=False,
        )
        embed.add_field(
            name="Log Channel",
            value=f"<#{cfg['log_channel']}>" if cfg["log_channel"] else "*not set*",
            inline=False
        )
        embed.add_field(name="Muted role(s)", value=role_list(cfg["muted_role"]), inline=False)
        embed.add_field(name="Member role(s)", value=role_list(cfg["member_role"]), inline=False)
        embed.add_field(name="AI role(s)", value=role_list(cfg["ai_role"]), inline=False)

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Config(bot))
