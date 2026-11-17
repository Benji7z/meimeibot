import asyncio
import subprocess as sp

from discord.ext import commands
import discord
from datetime import datetime, timezone

from config import BENJI_ID, HERETIC_ROLE
from utils import get_video_title
from checks import has_staff_role


class Admin(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def msg(self, ctx, *, message):
        await ctx.message.delete()
        await ctx.send(message)
    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def vid(self, ctx, link):
        video_title = await get_video_title(link)

        await ctx.send(
            f"@everyone\n\n"
            f"Xiam posted a new video titled \"{video_title}\"\n\n"
            f"Don't forget to follow xiam or whatever I am supposed to say "
            f"at this point\n\n"
            f"{link}"
        )

        await ctx.message.delete()

    @commands.command()
    async def temp(self, ctx):
        output = sp.check_output(
            ["vcgencmd", "measure_temp"]
        ).decode()

        await ctx.send(f"```{output.strip()}```")

    @commands.command()
    async def shutdown(self, ctx):
        if ctx.author.id != BENJI_ID:
            return await ctx.reply(
                "```This incident will be reported to the sudoers file```"
            )

        await ctx.reply("Shutting down 192.168.0.115")
        await asyncio.sleep(1)

        sp.run(["sudo", "shutdown", "now"])

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def perms(self, ctx, member: discord.Member, selection: str = "all"):
        embed = discord.Embed(
            title=f"Permissions for {member}",
            color=discord.Color.blurple()
        )

        if selection == "all":
            perms_list = list(member.guild_permissions)
        elif selection == "True":
            perms_list = [(name, value) for name, value in member.guild_permissions if value]
        elif selection == "False":
            perms_list = [(name, value) for name, value in member.guild_permissions if not value]
        else:
            return await ctx.send("selection must be `all`, `True`, or `False`")

        embed.description = "\n".join(f"`{name}: {value}`" for name, value in perms_list)
        await ctx.send(embed=embed)

    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def hasperms(self, ctx, member: discord.Member, permission: str):
            if not hasattr(member.guild_permissions, permission):
                return await ctx.reply(f"Permission `{permission}` does not exist.")

            value = getattr(member.guild_permissions, permission)
            embed = discord.Embed(
                title=f"Permissions for {member}",
                color=discord.Color.blurple()
            )

            embed.description = f"`{permission}`: {value}"
            await ctx.send(embed=embed)
    @commands.command()
    @commands.guild_only()
    @has_staff_role()
    async def heresify(self, ctx, member: discord.Member = None):
        role = discord.utils.get(ctx.guild.roles, name=HERETIC_ROLE)
        if not member:
            return await ctx.reply("No member is provided.")
        await member.edit(nick=f"[Heretic] {member.nick or member.name}")
        await member.add_roles(role)
        


    @commands.command()
    @commands.guild_only()
    @has_staff_role()
    async def status(self, ctx, status: str):
        await ctx.message.delete()
        status = status.lower()

        if status == "online":
            ping="<@&1565369150602354770>"
            color = discord.Color.green()
            description = (
                f"🕒 <t:{int(datetime.now(timezone.utc).timestamp())}:F>\n\n"
                "✅ **Server is Online**\n"
                "The Minecraft server is online."
            )
        elif status == "offline":
            ping="No ping cause"
            color = discord.Color.red()
            description = (
                f"🕒 <t:{int(datetime.now(timezone.utc).timestamp())}:F>\n\n"
                "❌ **Server is Offline**\n"
                "The Minecraft server is currently offline."
            )
        else:
            await ctx.send("Usage: `!status <online|offline>`")
            return

        embed = discord.Embed(
            title="Server Status",
            description=description,
            color=color
        )

        await ctx.send(ping, embed=embed)

async def setup(bot):
    await bot.add_cog(Admin(bot))
