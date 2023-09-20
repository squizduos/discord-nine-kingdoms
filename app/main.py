#-*-coding:utf-8-*-

import argparse
import asyncio
import json
import os
import logging
import traceback

import discord
from discord.ext import commands

import environ

from config import AppConfig

from music import MusicBot

import tracemalloc

tracemalloc.start()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(
    command_prefix=commands.when_mentioned_or(">", "!"),
    description='Plays local music file in voice channel',
    intents=intents
)



# initial_extensions = ['cogs.music']
# for extension in initial_extensions:
#     try:
#         bot.load_extension(extension)
#     except Exception as e:
#         print(f'Failed to load extension {extension}.', file=sys.stderr)
#         traceback.print_exc()

@bot.event
async def on_ready():
    print("Logged in as {0} ({0.id})".format(bot.user))
    print('------')

# @bot.event
# async def on_message(message):
#     # we do not want the bot to reply to itself
#     if message.author.id == self.user.id:
#         return
#
#     if message.content.startswith('!hello'):
#         await message.reply('Hello!', mention_author=True)


async def main(token):
    async with bot:
        await bot.add_cog(MusicBot(bot))
        await bot.start(token)


if __name__ == "__main__":
    print("Initializing...")
    discord.utils.setup_logging(level=logging.INFO, root=False)

    discord.opus.load_opus("/usr/lib/libopusenc.so.0")
    if not discord.opus.is_loaded():
        raise RuntimeError('Opus failed to load')

    cfg = environ.to_config(AppConfig)

    if cfg.token:
        asyncio.run(main(cfg.token))
    else:
        print("No token APP_TOKEN provided")
