import discord
from discord.ext import commands

import asyncio
import re

from config import EXEMPT_ROLE, DEBATER_ROLE
from checks import has_staff_role
import guild_config

from data.tags import tags

async def schedule_unmute(member, muted_roles, member_roles, seconds):
    await asyncio.sleep(seconds)
    await member.remove_roles(*muted_roles)
    if member_roles:
        await member.add_roles(*member_roles)

_DURATION_RE = re.compile(r"^(\d+)([smhd])$")
_UNITS = {"s": 1, "m": 60, "h": 3600, "d": 86400}

def parse_duration(text):
    match = _DURATION_RE.match(text.strip().lower())
    if not match:
        return None

    amount, unit = match.groups()
    return int(amount) * _UNITS[unit]



class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def block(self, ctx, *, member: discord.Member):
        
        role = discord.utils.get(ctx.guild.roles, name=EXEMPT_ROLE)
        
        if role is None:
            return await ctx.send(f"Role '{EXEMPT_ROLE}' not found.")
        
        await member.add_roles(role)

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def unblock(self, ctx, *, member: discord.Member):
        
        role = discord.utils.get(ctx.guild.roles, name=EXEMPT_ROLE)
        
        if role is None:
            return await ctx.send(f"Role '{EXEMPT_ROLE}' not found.")
        
        await member.remove_roles(role)
        
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def startdebate(self, ctx, debater_1: discord.Member, debater_2: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name=DEBATER_ROLE)
        if role is None:
            await ctx.send(f"Role '{DEBATER_ROLE}' not found.")
            return

        await debater_1.add_roles(role)
        await debater_2.add_roles(role)
        await ctx.send(f"{debater_1.mention} and {debater_2.mention} are now debating.")
    @commands.command()
    @commands.has_permissions(administrator=True)
    async def stopdebate(self, ctx, debater_1: discord.Member, debater_2: discord.Member):
        role = discord.utils.get(ctx.guild.roles, name=DEBATER_ROLE)
        if role is None:
            await ctx.send(f"Role '{DEBATER_ROLE}' not found.")
            return

        await debater_1.remove_roles(role)
        await debater_2.remove_roles(role)
        await ctx.send(f"The debate has been stopped.")
    
    @commands.command()
    @has_staff_role()
    async def tag(self, ctx, tag):
        tag_data = tags.get(tag)
        
        if tag_data is None:
            return await ctx.reply("That tag doesn't exist.")
        
        embed =  discord.Embed(
            title=tag_data["title"],
            description=tag_data["description"],
            color=discord.Color.blurple()
        )
        
        if ctx.message.reference:
            await ctx.channel.send(embed=embed, reference=ctx.message.reference)
        else:
            await ctx.send(embed=embed)
    @commands.command()
    @has_staff_role()
    async def add_role(self, ctx, member: discord.Member = None, *, role_name: str = None):
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            return await ctx.reply("Couldn't find specified role.")
            

        if role in member.roles:
            return await ctx.reply("Member already has that role.")
            
        
        await member.add_roles(role)

    @commands.command()
    @has_staff_role()
    async def remove_role(self, ctx, member: discord.Member = None, *, role_name: str = None):
        role = discord.utils.get(ctx.guild.roles, name=role_name)
        if role is None:
            return await ctx.reply("Couldn't find specified role.")
        
        if role not in member.roles:
            return await ctx.reply("Member does not have that role.")

        await member.remove_roles(role)
        
    @commands.command(aliases=["timeout", "to"])
    @has_staff_role()
    async def mute(self, ctx, member: discord.Member, duration: str, *, reason="No reason provided"):
        try:
            seconds = parse_duration(duration)
            if seconds is None:
                embed = discord.Embed(
                    title="Mute failed",
                    description="Invalid duration.\nformat: m!mute @User 1h reason",
                    color=discord.Color.blurple()
                )
                return await ctx.reply(embed=embed)

            roles = guild_config.get_configured_roles(ctx.guild, "muted_role")
            if not roles:
                return await ctx.reply("Muted role not set - use `m!config mutedrole @Role` to set the muted role.")

            member_roles = guild_config.get_configured_roles(ctx.guild, "member_role")

            for role in member_roles:
                if role in member.roles:
                    await member.remove_roles(role)

            await member.add_roles(*roles, reason=reason)
            embed = discord.Embed(
                title="Mute successful",
                description=f"Moderator: {ctx.author.mention}\nUser: {member.mention}\nReason: {reason}\nDuration: {seconds}",
                color=discord.Color.blurple()
            )

            log_channel_id = guild_config.get_guild_config(ctx.guild.id)["log_channel"]
            log_channel = ctx.guild.get_channel(log_channel_id) if log_channel_id else None
            if log_channel:
                await log_channel.send(embed=embed)
            await ctx.channel.send(embed=embed)

            self.bot.loop.create_task(schedule_unmute(member, roles, member_roles, seconds))

        except discord.Forbidden:
            await ctx.reply(f"⚠️ I don't have permission to modify roles on {member.mention}. Check my role position and permissions.")
        except discord.HTTPException as e:
            await ctx.reply(f"⚠️ Discord API error while muting {member.mention}: `{e}`")
        except KeyError as e:
            await ctx.reply(f"⚠️ Missing config key {e} — check your guild config setup (e.g. `log_channel`).")
        except Exception as e:
            await ctx.reply(f"⚠️ Unexpected error while running mute: `{type(e).__name__}: {e}`")
            raise  # re-raise so it still shows up in your logs/console
    @commands.command()
    @has_staff_role()
    async def unmute(self, ctx, member: discord.Member, *, reason="No reason provided"):
        muted_roles = guild_config.get_configured_roles(ctx.guild, "muted_role")
        member_roles = guild_config.get_configured_roles(ctx.guild, "member_role")

        roles_to_remove = [r for r in muted_roles if r in member.roles]
        if roles_to_remove:
            await member.remove_roles(*roles_to_remove, reason=reason)

        roles_to_add = [r for r in member_roles if r not in member.roles]
        if roles_to_add:
            await member.add_roles(*roles_to_add, reason=reason)

        embed = discord.Embed(
            title="Unmute successful",
            description = f"Moderator: {ctx.author.mention}\nUser: {member.mention}\nReason: {reason}\n",
            color=discord.Color.blurple()
        )
        
        log_channel_id = guild_config.get_guild_config(ctx.guild.id)["log_channel"]
        log_channel = ctx.guild.get_channel(log_channel_id) if log_channel_id else None
        
        await log_channel.send(embed=embed)
        await ctx.send(embed=embed)
async def setup(bot):
    await bot.add_cog(Moderation(bot))
