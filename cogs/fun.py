import random
import discord
import edge_tts

from datetime import timedelta
from discord.ext import commands

from data.questions import questions
from checks import has_staff_role


class HeresyView(discord.ui.View):

    def __init__(self, answer):
        super().__init__(timeout=None)
        self.answer = answer
        self.guessed_users = set()
        self.message = None

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True

        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass

    async def answer_question(self, interaction, correct):
        if interaction.user.id in self.guessed_users:
            return await interaction.response.send_message(
                "You already guessed!",
                ephemeral=True
            )

        self.guessed_users.add(interaction.user.id)

        if self.answer == correct:
            await interaction.response.send_message(
                f"{interaction.user.mention} gave the correct answer! ✅"
            )
        else:
            await interaction.response.send_message(
                f"{interaction.user.mention} GOT THE QUESTION WRONG ❌"
            )
            await interaction.user.timeout(timedelta(minutes=1))

    @discord.ui.button(label="Heresy", style=discord.ButtonStyle.danger)
    async def heresy(self, interaction, button):
        await self.answer_question(interaction, "heresy")

    @discord.ui.button(label="Not heresy", style=discord.ButtonStyle.success)
    async def not_heresy(self, interaction, button):
        await self.answer_question(interaction, "not_heresy")

    @discord.ui.button(
        label="Another question",
        style=discord.ButtonStyle.primary
    )
    async def another_question(self, interaction, button):
        question, answer = random.choice(questions)

        embed = discord.Embed(
            title="Heresy or not",
            description=question,
            color=discord.Color.blurple()
        )

        await interaction.response.send_message(
            embed=embed,
            view=HeresyView(answer)
        )


class GiveawayView(discord.ui.View):

    def __init__(self, cog, guild_id):
        super().__init__(timeout=None)
        self.cog = cog
        self.guild_id = guild_id
        self.message = None

    @discord.ui.button(
        label="Sign Up",
        style=discord.ButtonStyle.primary
    )
    async def signup(self, interaction, button):

        if interaction.user.bot:
            return await interaction.response.send_message(
                "Bots cannot participate!",
                ephemeral=True
            )

        if self.guild_id in self.cog.giveaway_closed:
            return await interaction.response.send_message(
                "This giveaway is closed!",
                ephemeral=True
            )

        # Make sure a signup set actually exists for this guild,
        # and that it's the same object stored on the cog (not a
        # throwaway default that never gets saved).
        signups = self.cog.giveaway_signups.setdefault(
            self.guild_id, set()
        )

        if interaction.user.id in signups:
            return await interaction.response.send_message(
                "You're already signed up!",
                ephemeral=True
            )

        signups.add(interaction.user.id)

        await interaction.response.send_message(
            "You've successfully signed up!",
            ephemeral=True
        )


class Fun(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

        # Giveaway data, separated by server
        self.giveaway_signups = {}
        self.giveaway_winners = {}
        self.giveaway_closed = set()
        self.giveaway_views = {}

    # =========================
    # 8BALL
    # =========================

    @commands.command(name="8ball")
    @commands.cooldown(1, 60, commands.BucketType.user)
    async def eightball(self, ctx, *, question):

        answers = [
            "Yes.", "No.", "Probably.", "Probably not.",
            "Definitely.", "Definitely not.",
            "It is certain.", "Very unlikely."
        ]

        embed = discord.Embed(
            title=question,
            description=random.choice(answers),
            color=discord.Color.blurple()
        )

        await ctx.reply(embed=embed)

    # =========================
    # OTHER COMMANDS
    # =========================

    @commands.command()
    async def whatappamiusing(self, ctx):
        await ctx.reply("You're using discord.")

    @commands.command()
    async def heresyornot(self, ctx):

        question, answer = random.choice(questions)

        embed = discord.Embed(
            title="Heresy or not",
            description=question,
            color=discord.Color.blurple()
        )

        await ctx.reply(
            embed=embed,
            view=HeresyView(answer)
        )

    # =========================
    # VOICE
    # =========================

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def join(self, ctx):

        await ctx.message.delete()

        if ctx.author.voice and ctx.author.voice.channel:
            channel = ctx.author.voice.channel

            if ctx.voice_client is None:
                await channel.connect()
            else:
                await ctx.voice_client.move_to(channel)
        else:
            await ctx.send("You are not in a voice channel!")

    @commands.command()
    @commands.has_permissions(administrator=True)
    async def leave(self, ctx):

        await ctx.message.delete()

        if ctx.voice_client:
            await ctx.voice_client.disconnect()

    @commands.command()
    async def say(self, ctx, *, text):

        await ctx.message.delete()

        if not ctx.voice_client:
            return await ctx.send("I'm not in a voice channel.")

        try:
            communicate = edge_tts.Communicate(
                text,
                "en-US-AriaNeural"
            )

            await communicate.save("/tmp/speech.mp3")

            source = discord.FFmpegPCMAudio("/tmp/speech.mp3")
            ctx.voice_client.play(source)

        except Exception as e:
            print(f"VOICE ERROR: {type(e).__name__}: {e}")
            await ctx.send(f"Voice error: `{type(e).__name__}: {e}`")

    # =========================
    # GIVEAWAY
    # =========================

    @commands.command()
    @has_staff_role()
    @commands.guild_only()
    async def gw(self, ctx, *, prize):

        guild_id = ctx.guild.id

        # Reset giveaway data
        self.giveaway_signups[guild_id] = set()
        self.giveaway_winners[guild_id] = []
        self.giveaway_closed.discard(guild_id)

        embed = discord.Embed(
            title="Giveaway",
            description=f"## Prize: {prize}\nClick the button below to participate!",
            color=discord.Color.blurple()
        )

        view = GiveawayView(self, guild_id)

        message = await ctx.send(
            embed=embed,
            view=view
        )

        # Remember the message so gwdraw/gwredraw can disable the
        # button later. This was missing before, which is why
        # gwdraw always failed with "Could not find giveaway message!".
        view.message = message
        self.giveaway_views[guild_id] = view

    # =========================
    # DRAW WINNER
    # =========================

    @commands.command()
    @has_staff_role()
    @commands.guild_only()
    async def gwdraw(self, ctx):

        guild_id = ctx.guild.id

        if guild_id not in self.giveaway_signups:
            return await ctx.send("No active giveaway!")

        if guild_id in self.giveaway_closed:
            return await ctx.send("This giveaway has already been drawn!")

        self.giveaway_closed.add(guild_id)

        # Disable signup button
        view = self.giveaway_views.get(guild_id)

        if view:
            for item in view.children:
                item.disabled = True

            message = getattr(view, "message", None)

            # Retrieve the original giveaway message
            if message is not None:
                try:
                    await message.edit(view=view)
                except discord.HTTPException:
                    pass

        members = [
            ctx.guild.get_member(uid)
            for uid in self.giveaway_signups[guild_id]
        ]

        members = [
            m for m in members
            if m and not m.bot
        ]

        if not members:
            return await ctx.send("Nobody signed up!")

        winner = random.choice(members)
        self.giveaway_winners[guild_id].append(winner.id)

        embed = discord.Embed(
            title="Giveaway Winner",
            description=f"{winner.mention} has won the giveaway!",
            color=discord.Color.blurple()
        )

        await ctx.send(winner.mention, embed=embed)

    # =========================
    # REDRAW
    # =========================

    @commands.command()
    @has_staff_role()
    @commands.guild_only()
    async def gwredraw(self, ctx):

        guild_id = ctx.guild.id

        if guild_id not in self.giveaway_signups:
            return await ctx.send("No active giveaway!")

        if guild_id not in self.giveaway_closed:
            return await ctx.send("Draw the first winner before redrawing!")

        previous_winners = self.giveaway_winners.get(
            guild_id, []
        )

        members = [
            ctx.guild.get_member(uid)
            for uid in self.giveaway_signups[guild_id]
            if uid not in previous_winners
        ]

        members = [
            m for m in members
            if m and not m.bot
        ]

        if not members:
            return await ctx.send("Nobody left to redraw!")

        winner = random.choice(members)
        self.giveaway_winners[guild_id].append(winner.id)

        embed = discord.Embed(
            title="Giveaway Re-draw",
            description=f"{winner.mention} has won the re-draw!",
            color=discord.Color.blurple()
        )

        await ctx.send(winner.mention, embed=embed)


async def setup(bot):
    await bot.add_cog(Fun(bot))