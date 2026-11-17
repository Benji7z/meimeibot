import discord
from discord.ext import commands

import asyncio

from google import genai
from google.genai import errors, types

from config import GEMINI_API_KEY_PATH


import os
from dotenv import load_dotenv


from pathlib import Path

from checks import has_config_role

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

FOLLOWERS_OF_CHRIST_GUILD_ID = 1515437759903301633


class AI(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.cooldown(1, 10, commands.BucketType.user)
    @has_config_role("ai_role")
    async def ai(self, ctx, *, question):
        client = genai.Client(api_key=GEMINI_API_KEY)

        with open(
            "/home/benjisrpi/Documents/FoC/src/meimeibot/data/AI_Instructions.txt",
            "r",
            encoding="utf-8",
        ) as f:
            instructions = f.read()

        if ctx.guild.id == FOLLOWERS_OF_CHRIST_GUILD_ID:
            roles_line = f"- Roles: {', '.join(role.name for role in ctx.author.roles)}            "
        else:
            roles_line = ""

        user_info = f"""
            User information:
            - Username: {ctx.author}
            - User ID: {ctx.author.id}
            - Display name: {ctx.author.display_name}
            - Server: {ctx.guild.name}
            - Server ID: {ctx.guild.id}
            {roles_line}
            - Is server administrator: {ctx.author.guild_permissions.administrator}
            """

        try:
            response = await asyncio.to_thread(
                client.models.generate_content,
                model="gemini-3.5-flash-lite",
                contents=f"{user_info}\n\nUser Question: {question}",
                config=types.GenerateContentConfig(
                    system_instruction=instructions,
                ),
            )

            if not response.text:
                candidate = response.candidates[0] if response.candidates else None
                finish_reason = candidate.finish_reason if candidate else None
                safety_ratings = candidate.safety_ratings if candidate else None
                prompt_feedback = getattr(response, "prompt_feedback", None)

                print(f"[AI] Empty response in guild {ctx.guild.id} ({ctx.guild.name})")
                print(f"[AI] finish_reason: {finish_reason}")
                print(f"[AI] safety_ratings: {safety_ratings}")
                print(f"[AI] prompt_feedback: {prompt_feedback}")

                if prompt_feedback and prompt_feedback.block_reason:
                    await ctx.reply(
                        f"Myself refused to even look at that one (reason: {prompt_feedback.block_reason.name}). "
                        "Try rephrasing, or it might be something in your roles/question it doesn't like."
                    )
                    return

            await ctx.reply(response.text or "I'm just not gonna give you a response, okay?")

        except errors.APIError as e:
            await ctx.reply(f"Gemini API error: {e}")

        except Exception as e:
            print(f"Unexpected error: {type(e).__name__}: {e}")
            await ctx.reply("Something went wrong while contacting Myself.")


async def setup(bot):
    await bot.add_cog(AI(bot))