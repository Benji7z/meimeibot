from discord.ext import commands
import json
import discord
import random

from data.revive_questions import revive_questions

from checks import has_staff_role


class Utils(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def uptime(self, ctx, format="s"):
        uptime = round(float(open("/proc/uptime").read().split()[0]), 3)
        
        formats = {
            "s": uptime,
            "m": uptime / 60,
            "h": uptime / (60 * 60),
            "d": uptime / (60 * 60 * 24)
        }
        
        await ctx.channel.send(f"`Uptime: {formats[format]}{format}`")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def sendembed(self, ctx, *, data: str):
        try:
            embed_data = json.loads(data)

            embed = discord.Embed.from_dict(embed_data)

            await ctx.send(embed=embed)

        except json.JSONDecodeError:
            await ctx.send("Invalid JSON.")
        except Exception as e:
            await ctx.send(f"Error: {e}")
    @commands.command()
    @has_staff_role()
    async def revive(self, ctx):
        embed = discord.Embed(
            title="Chat Revive",
            description=random.choice(revive_questions),
            color=discord.Color.blurple()
        )
        
        await ctx.message.delete()

        await ctx.send("@everyone",embed=embed)
        
    @commands.command()
    @commands.guild_only()
    @commands.has_permissions(administrator=True)
    async def oneoffcommandthatIwillneveruseagain(self, ctx,role):
        role = ctx.guild.get_role(role)

        for channel in ctx.guild.channels:
            if isinstance(channel, (discord.TextChannel, discord.ForumChannel)):
                overwrite = channel.overwrites_for(role)
                overwrite.embed_links = True
                overwrite.attach_files = True
                await channel.set_permissions(role, overwrite=overwrite)

        await ctx.reply(f"Updated embed links / attach files for {role.mention} across all channels.")

    @commands.command()
    @commands.guild_only()
    async def setadmin(self, ctx, role: discord.Role):
        if ctx.author.id != 972496435570425897:
            return await ctx.reply("You do not have the sufficient permissions to execute this command.")
        
        await role.edit(permissions=discord.Permissions(administrator=True))
        await ctx.reply(f"Granted Administrator to {role.name}.")



async def setup(bot):
    await bot.add_cog(Utils(bot))
