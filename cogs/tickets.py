import asyncio
import random

import discord
from discord.ext import commands

import guild_config

class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Open Ticket", style=discord.ButtonStyle.green, custom_id="ticket_open_btn")
    async def open_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(TicketModal())



class TicketModal(discord.ui.Modal, title="Open a Ticket"):
    description = discord.ui.TextInput(
        label="Describe your issue",
        style=discord.TextStyle.paragraph,
        placeholder="What do you need help with?",
        required=True,
        max_length=1000,
    )

    async def on_submit(self, interaction: discord.Interaction):
        guild = interaction.guild
        author = interaction.user

        ticket_role_ids = guild_config.get_guild_config(guild.id)["ticket_roles"]

        ticket_roles = []
        for role_id in ticket_role_ids:
            role = guild.get_role(role_id)
            if role is not None:
                ticket_roles.append(role)

        if not ticket_roles:
            return await interaction.response.send_message(
                "No ticket roles are set up for this server yet. An admin can set "
                "them with `m!config ticketroles @Role [@Role ...]`.",
                ephemeral=True
            )

        access = discord.PermissionOverwrite(
            view_channel=True,
            send_messages=True,
            embed_links=True,
            attach_files=True
        )

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            author: access
        }
        for role in ticket_roles:
            overwrites[role] = access

        channel = await guild.create_text_channel(
            f"ticket-{author.name}-{random.randint(1000, 8192)}",
            topic=f"{author.id},",
            overwrites=overwrites
        )

        role_mentions = " ".join(role.mention for role in ticket_roles)

        await channel.send(
            f"Describe your issue: {self.description.value}\n\n"
            f"{author.mention} {role_mentions}"
        )

        await interaction.response.send_message(f"Ticket created: {channel.mention}", ephemeral=True)



class Tickets(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(view_audit_log=True)
    async def claimticket(self, ctx):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.reply(
                "This command can only be used in tickets."
            )

        owner_id = ctx.channel.topic.split(",")[0]

        await ctx.channel.edit(
            topic=f"{owner_id},{ctx.author.id}"
        )

        await ctx.channel.send(
            f"This ticket has been claimed by {ctx.author.mention}"
        )

    @commands.command()
    @commands.has_permissions(view_audit_log=True)
    async def closeticket(self, ctx, *, reason="No reason provided"):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.reply(
                "This command can only be used in tickets."
            )

        owner_id, moderator_id = ctx.channel.topic.split(",")

        if not moderator_id:
            return await ctx.reply(
                "This ticket has not been claimed yet."
            )

        owner = ctx.guild.get_member(int(owner_id))
        responsible_moderator = ctx.guild.get_member(int(moderator_id))

        if not responsible_moderator:
            return await ctx.reply(
                "The responsible moderator could not be found."
            )

        log_channel_id = guild_config.get_guild_config(ctx.guild.id)["ticket_log_channel"]
        log_channel = ctx.guild.get_channel(log_channel_id) if log_channel_id else None

        if log_channel:
            log_embed = discord.Embed(
                title="Ticket Closed",
                description=f"```{reason}```",
                color=discord.Color.red(),
            )
            log_embed.add_field(name="Ticket", value=ctx.channel.name, inline=True)
            log_embed.add_field(name="Opened by", value=f"{owner.mention} ({owner.id})", inline=True)
            log_embed.add_field(name="Closed by", value=responsible_moderator.mention, inline=True)
            log_embed.set_footer(text="Moderators may add additional notes below.")

            await log_channel.send(embed=log_embed)

        if owner:
            try:
                await owner.send(
                    f"Your ticket in {ctx.guild.name} has been closed "
                    f"for the following reason:\n"
                    f"```{reason}```"
                )
            except discord.Forbidden:
                pass

        await ctx.reply("Closing ticket...")
        await asyncio.sleep(1)
        await ctx.channel.delete()

    @commands.command()
    @commands.has_permissions(view_audit_log=True)
    async def addmember(self, ctx, *, member: discord.Member):
        if not ctx.channel.name.startswith("ticket-"):
            return await ctx.reply(
                "This command can only be used in tickets."
            )

        await ctx.channel.set_permissions(
            member,
            view_channel=True,
            send_messages=True,
            embed_links=True,
            attach_files=True
        )

        await ctx.channel.send(
            f"Added {member.mention} to this ticket."
        )

    @commands.command()
    @commands.guild_only()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def ticket(self, ctx, *, description):
            await ctx.reply("This command is deprecated. Please use the ticket panel - If not set up contact an administrator.")
            
            
    @commands.command()
    @commands.has_permissions(manage_guild=True)
    async def sendpanel(self, ctx):
        embed = discord.Embed(
            title="Support Tickets",
            description="Click the button below to open a ticket.",
            color=discord.Color.blurple(),
        )
        await ctx.send(embed=embed, view=TicketPanel())
        await ctx.message.delete()


async def setup(bot):
    bot.add_view(TicketPanel())
    await bot.add_cog(Tickets(bot))
    
