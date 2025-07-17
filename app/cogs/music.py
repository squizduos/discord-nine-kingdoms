# -*-coding:utf-8-*-
import environ
import random
import subprocess

from config import AppConfig

import discord
from discord.ext import commands
from discord import app_commands
from discord.ext import listening

from views.launch_view import LaunchView


class MusicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bot.repeat_source = None
        self.ctx = None
        self.is_playing = False

        self.cfg = environ.to_config(AppConfig)

        self.repeat_source = None

        self.process_pool = listening.AudioProcessPool(1)

    @app_commands.command(name="start", description="Включает музыкального бота в первый доступный голосовой канал")
    async def join(self, interaction: discord.Interaction):
        ctx = await self.bot.get_context(interaction)
        channel = ctx.guild.voice_channels[0]
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        self.ctx = ctx
        await channel.connect(cls=listening.VoiceClient)

        async def on_listen_finish(sink: listening.AudioFileSink, exc=None, channel=None):
            await sink.convert_files(stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        ctx.voice_client.listen(
            listening.AudioFileSink(listening.MP3AudioFile, "./records"),
            self.process_pool,
            channel=interaction.channel,
            after=on_listen_finish
        )

        launch_view = LaunchView(bot=self)
        await channel.send(launch_view.caption(), view=launch_view)
        await interaction.response.send_message(f"Бот подсоединён к голосовому каналу {channel.mention}", ephemeral=True)

    @app_commands.command(name="stop", description="Выключает музыкального бота")
    async def quit(self,  interaction: discord.Interaction):
        ctx = await self.bot.get_context(interaction)
        if self.ctx:
            if self.ctx.voice_client.is_playing():
                self.ctx.voice_client.stop()

        if self.bot.repeat_source:
            self.bot.repeat_source.cleanup()

        ctx.voice_client.stop_listening()
        await ctx.voice_client.disconnect()
        await interaction.response.send_message(f"Бот отсоединён от голосового канала", ephemeral=True)



    # @commands.command()
    # async def sync(self, ctx) -> None:
    #     ctx.bot.tree.copy_global_to(guild=ctx.guild)
    #     fmt = await ctx.bot.tree.sync(guild=ctx.guild)
    #     await ctx.send(f"Synced {len(fmt)} commands.")


def setup(bot):
    bot.add_cog(MusicCog(bot))
