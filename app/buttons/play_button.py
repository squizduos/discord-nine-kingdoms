import os

import discord

import config


class PlayButton(discord.ui.Button["Music"]):
    def __init__(self, title: str, filename: str, bot, player_view):
        super().__init__(style=discord.ButtonStyle.secondary, label=title)
        self.filename = filename
        self.bot = bot
        self.player_view = player_view

    async def callback(self, interaction: discord.Interaction):
        target_file_path = os.path.join(os.curdir, self.bot.cfg.files_dir, self.filename)
        print("Now playing: {}".format(target_file_path))

        if self.bot.ctx.voice_client.is_playing():
            self.bot.ctx.voice_client.pause()

        self.player_view.is_playing = True

        repeat_source = discord.PCMVolumeTransformer(
            discord.FFmpegPCMAudio(target_file_path, executable=self.bot.cfg.ffmpeg_executable, **config.FFMPEG_OPTS)
        )
        repeat_source.volume = self.player_view.volume

        if self.bot.ctx.voice_client.is_playing():
            self.bot.ctx.voice_client.pause()

        self.bot.ctx.voice_client.play(repeat_source)
        self.bot.ctx.voice_client.is_playing()

        self.player_view.current = self.filename

        await interaction.response.edit_message(content=self.player_view.caption())
