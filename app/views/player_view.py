# -*-coding:utf-8-*-

import math
import os

import discord
from typing import List, Optional

from buttons.filter_button import FilterPlaylistButton
from buttons.play_button import PlayButton


class PlayerView(discord.ui.View):
    def __init__(
        self, *, timeout=60 * 60 * 24, bot=None, music_folder: str = "files", words: Optional[List[str]] = None
    ):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.page = 0
        self.filter = ""
        self.current = "#NA"
        self.volume = 1
        self.music_folder = music_folder
        self.words = words if words else list()

        self.render_filter_buttons()

        self.buttons_list = list()

        self.refresh()

    def caption(self):
        return f"""
Сейчас воспроизводится: `{self.current}`
Громкость: `{self.volume:.0%}`
Фильтр: `{self.filter if self.filter else "Отсутствует"}`
Страница: `{self.page + 1} из {math.ceil(len(self.files_list) / self.__page_size__())}`
            """

    def __page_size__(self):
        return 20 - (len(self.words) + 1)

    def __get_music_files__(self, music_folder: Optional[str] = None):
        current_music_folder = music_folder if music_folder else self.music_folder
        files_list = sorted(os.listdir(os.path.join(os.path.abspath(os.curdir), current_music_folder)))
        music_extensions = [".mp3", ".m4a", ".flac", ".ogg"]
        return [f for f in files_list if any(f.endswith(extension) for extension in music_extensions)]

    def __get_files_list__(self, filter_str: str = ""):
        return [
            element for element in self.__get_music_files__() if filter_str.lower() in element.lower() or not filter_str
        ]

    def __refresh_button_list__(self):
        buttons_list = []
        self.files_list = self.__get_files_list__(self.filter)
        for file_name in self.files_list[self.page * self.__page_size__() : (self.page + 1) * self.__page_size__()]:
            title = "".join(file_name.split(".")[:-1])
            play_button = PlayButton(title=title, filename=file_name, bot=self.bot, player_view=self)
            buttons_list.append(play_button)
        return buttons_list

    def render_filter_buttons(self):
        for word in self.words:
            fitler_button = FilterPlaylistButton(title=word, filter=word, player_view=self)
            self.add_item(fitler_button)
        no_filter_button = FilterPlaylistButton(title="Все", filter="", player_view=self)
        self.add_item(no_filter_button)

    def refresh(self):
        buttons_list = self.__refresh_button_list__()
        for item in self.buttons_list:
            self.remove_item(item)
        self.buttons_list = buttons_list
        for item in self.buttons_list:
            self.add_item(item)

    async def show(self, interaction: discord.Interaction):
        await interaction.response.edit_message(content=self.caption(), view=self)

    @discord.ui.button(label="◀️", style=discord.ButtonStyle.green, row=0)
    async def list_back_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page -= 1
        self.refresh()
        await self.show(interaction)

    @discord.ui.button(label="🔈", style=discord.ButtonStyle.green, row=0)
    async def volume_down(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.volume = max(self.volume - 0.2, 0)
        if self.bot.ctx.voice_client.source is not None:
            self.bot.ctx.voice_client.source.volume = self.volume
        self.refresh()
        await self.show(interaction)

    @discord.ui.button(label="⏹", style=discord.ButtonStyle.green, row=0)
    async def stop_music(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.bot.ctx.voice_client.is_playing():
            self.bot.ctx.voice_client.pause()

        self.bot.is_playing = False
        self.current = "#NA"

        self.refresh()

        await self.show(interaction)

    @discord.ui.button(label="🔊", style=discord.ButtonStyle.green, row=0)
    async def volume_up(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.volume = min(self.volume + 0.2, 1)
        if self.bot.ctx.voice_client.source is not None:
            self.bot.ctx.voice_client.source.volume = self.volume
        self.refresh()
        await self.show(interaction)

    @discord.ui.button(label="▶️", style=discord.ButtonStyle.green, row=0)
    async def list_forward_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.page += 1
        self.refresh()
        await self.show(interaction)
