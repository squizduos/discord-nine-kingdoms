# -*-coding:utf-8-*-

import asyncio
import logging
import platform

import discord
from discord.ext import commands

import environ

from config import AppConfig

from music import MusicBot

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


async def main(token):
    async with bot:
        await bot.add_cog(MusicBot(bot))
        await bot.start(token)


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
