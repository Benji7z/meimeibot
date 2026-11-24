import asyncio
import os

from dotenv import load_dotenv

import discord
from discord.ext import commands

#from config import TOKEN_PATH === OUTDATED

load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")


intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=["m!","."], intents=intents)


async def load_cogs():
    for filename in os.listdir("./cogs"):
        if filename.endswith(".py"):
            await bot.load_extension(f"cogs.{filename[:-3]}")


async def main():
    async with bot:
        await load_cogs()
        
        await bot.start(BOT_TOKEN)


asyncio.run(main())
