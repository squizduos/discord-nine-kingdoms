# -*-coding:utf-8-*-

import asyncio
import logging
import platform

import discord
from discord.ext import commands

import environ

from config import AppConfig

from cogs.music import MusicCog
from cogs.roll import RollCog

import tracemalloc

tracemalloc.start()

import os
import sys

sys.path.append(os.getcwd())


intents = discord.Intents.default()
intents.message_content = True


bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(">", "!"),
    description="Plays local music file in voice channel",
    intents=intents,
)


@bot.event
async def on_ready():
    logging.info("Logged in as {0} ({0.id})".format(bot.user))
    logging.info("------")


@bot.command(name="sync")
async def sync(ctx):
    ctx.bot.tree.copy_global_to(guild=ctx.guild)
    synced = await bot.tree.sync(guild=ctx.guild)
    print(f"Synced {len(synced)} command(s).")


async def main(token):
    async with bot:
        await bot.add_cog(MusicCog(bot))
        await bot.add_cog(RollCog(bot))
        await bot.start(token)
        print("123")


if __name__ == "__main__":
    cfg = environ.to_config(AppConfig)

    logging_level = logging.DEBUG if cfg.debug else logging.INFO
    discord.utils.setup_logging(level=logging_level, root=False)

    if platform.system() == "Linux":
        discord.opus.load_opus("/usr/lib/libopusenc.so.0")
        if not discord.opus.is_loaded():
            raise RuntimeError("Opus failed to load")

    if cfg.token:
        asyncio.run(main(cfg.token))
    else:
        print("No token APP_TOKEN provided")
