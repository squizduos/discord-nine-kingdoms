# -*-coding:utf-8-*-

import argparse
import asyncio
import json
import os
import environ

from config import AppConfig

import discord
from discord.ext import commands
# from discord_components import DiscordComponents, Button, ButtonStyle
from typing import List, Optional

ffmpeg_options = {
    'options': '-vn'
}


class PlayButton(discord.ui.Button['Music']):
    def __init__(self, title: str, filename: str, bot):
        super().__init__(style=discord.ButtonStyle.secondary, label=title)
        self.filename = filename
        self.bot = bot

    async def callback(self, interaction: discord.Interaction):
        target_file_path = os.path.join(os.curdir, "../files", self.filename)
        print("Now playing: {}".format(target_file_path))

        def repeat(file_path):
            if self.bot.is_playing:
                repeat_source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(file_path, options="-b:a 128k -stream_loop -1", executable=self.bot.cfg.ffmpeg_executable)
                )
                repeat_source.volume = self.bot.volume

                if self.bot.ctx.voice_client.is_playing():
                    self.bot.ctx.voice_client.pause()

                self.bot.ctx.voice_client.play(
                    repeat_source, # after=lambda e: repeat(file_path)
                )
                # self.bot.ctx.voice_client.is_playing()

        if self.bot.ctx.voice_client.is_playing():
            self.bot.ctx.voice_client.pause()

        self.bot.is_playing = True

        repeat(target_file_path)

        self.bot.current = self.filename

        await interaction.response.edit_message(content=self.bot.caption())


class FilterPlaylistButton(discord.ui.Button['Music']):
    def __init__(self, title: str, filter: str, player_view):
        super().__init__(style=discord.ButtonStyle.danger, label=title)
        self.filter = filter
        self.player_view = player_view

    async def callback(self, interaction: discord.Interaction):
        self.player_view.filter = self.filter
        self.player_view.refresh()
        await self.player_view.show(interaction)


class PlayerView(discord.ui.View):
    def __init__(self, *, timeout=180, bot=None, music_folder: str = "files", words: Optional[List[str]] = None):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.page = 0
        self.filter = ""
        self.files_list = self.__get_music_files__(music_folder)
        self.words = words if words else list()

        for word in self.words:
            fitler_button = FilterPlaylistButton(title=word, filter=word, player_view=self)
            self.add_item(fitler_button)
        no_filter_button = FilterPlaylistButton(title="Все", filter="", player_view=self)
        self.add_item(no_filter_button)

        self.buttons_list = list()

        self.refresh()

    def __page_size__(self):
        return 20 - (len(self.words) + 1)


    def __get_music_files__(self, music_folder: str = ""):
        files_list = sorted(os.listdir(os.path.join(os.path.abspath(os.curdir), music_folder)))
        music_extensions = [".mp3", ".m4a", ".flac", ".ogg"]
        return [f for f in files_list if any(f.endswith(extension) for extension in music_extensions)]

    def __refresh_button_list__(self):
        buttons_list = []
        files_list = [element for element in self.files_list if self.filter.lower() in element.lower() or not self.filter]
        for file_name in files_list[self.page * self.__page_size__():(self.page + 1) * self.__page_size__()]:
            title = "".join(file_name.split(".")[:-1])

            play_button = PlayButton(title=title, filename=file_name, bot=self.bot)
            buttons_list.append(play_button)
        return buttons_list

    def refresh(self, interaction: Optional = None):
        buttons_list = self.__refresh_button_list__()
        for item in self.buttons_list:
            self.remove_item(item)
        self.buttons_list = buttons_list
        for item in self.buttons_list:
            self.add_item(item)

    async def show(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=self.bot.caption(), view=self)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.green, row=0)
    async def list_back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self.refresh()
        await self.show(interaction)

    @discord.ui.button(label="🔈", style=discord.ButtonStyle.green, row=0)
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.volume = max(self.bot.volume - 0.2, 0)
        if self.bot.ctx.voice_client.source is not None:
            self.bot.ctx.voice_client.source.volume = self.bot.volume
        self.refresh()
        await self.show(interaction)

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.green, row=0)
    async def stop_music(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.bot.ctx.voice_client.is_playing():
            self.bot.ctx.voice_client.pause()

        self.bot.is_playing = False
        self.bot.current = "#NA"

        self.refresh()

        await self.show(interaction)

    @discord.ui.button(label="🔊", style=discord.ButtonStyle.green, row=0)
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.bot.volume = min(self.bot.volume + 0.2, 1)
        if self.bot.ctx.voice_client.source is not None:
            self.bot.ctx.voice_client.source.volume = self.bot.volume
        self.refresh()
        await self.show(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.green, row=0)
    async def list_forward_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self.refresh()
        await self.show(interaction)


class LaunchButtonView(discord.ui.View):

    def __init__(self, *, timeout=180, bot=None):
        self.bot = bot
        super().__init__(timeout=timeout)

    @discord.ui.button(label="Запустить музыку (только админ)", style=discord.ButtonStyle.green)
    async def green_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.administrator:
            player_view = PlayerView(
                bot=self.bot,
                music_folder=self.bot.cfg.files_dir,
                words=self.bot.cfg.words.split(",")
            )
            await interaction.response.send_message(content=self.bot.caption(), view=player_view, ephemeral=True)
        else:
            await interaction.response.send_message(content=f"У вас нет прав для администрирования музыки!")


class MusicBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.current = "#NA"
        self.ctx = None
        self.volume = 1
        self.is_playing = False

        self.cfg = environ.to_config(AppConfig)

    def caption(self):
        return f"""
Сейчас воспроизводится: `{self.current}`
Громкость: `{self.volume:.0%}`
        """

    @commands.command()
    async def join(self, ctx):
        channel = ctx.guild.voice_channels[0]
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        self.ctx = ctx
        await channel.connect()

        launch_button_view = LaunchButtonView(bot=self)
        await channel.send(
            'Бот готов к запуску музыки!\nОбратите внимание, управлять музыкой может только администратор сервера.',
            view=launch_button_view
        )

    @commands.command()
    async def quit(self, ctx):
        if self.ctx:
            if self.ctx.voice_client.is_playing():
                self.ctx.voice_client.stop()

        # ctx.voice_client.stop()
        await ctx.voice_client.disconnect()



def setup(bot):
    bot.add_cog(MusicBot(bot))
