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
            if self.is_playing:
                repeat_source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(file_path, options="-b:a 128k", executable=self.bot.cfg.ffmpeg_executable)
                )
                repeat_source.volume = self.bot.volume

                if self.bot.ctx.voice_client.is_playing():
                    self.bot.ctx.voice_client.pause()

                self.bot.ctx.voice_client.play(repeat_source, after=lambda e: repeat(file_path))
                self.bot.ctx.voice_client.is_playing()

        if self.bot.ctx.voice_client.is_playing():
            self.bot.ctx.voice_client.pause()

        self.is_playing = True
        repeat(target_file_path)

        self.bot.current = self.filename
        # self.ctx.voice_client.play(source, after=lambda e: repeat(source))
        # self.ctx.voice_client.is_playing()

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



# class MusicList(discord.ui.View):
#
#     def __init__(self, *, timeout=180):
#         super().__init__(timeout=timeout)
#         files_list = os.listdir("files/")
#         for f in files_list:
#             button = discord.ui.Button(style=discord.ButtonStyle.secondary, label=f)
#
#     @discord.ui.button(label="Запустить музыку (только админ)", style=discord.ButtonStyle.green)
#     async def gray_button(self, interaction:discord.Interaction, button: discord.ui.Button):
#         if interaction.user.guild_permissions.administrator:
#             await interaction.response.send_message(content=f"This is an edited button response!")
#         else:
#             await interaction.response.send_message(content=f"У вас нет прав для администрирования музыки!")


# class LaunchListButton(discord.ui.View):
#
#     def __init__(self, *, timeout=180):
#         super().__init__(timeout=timeout)
#
#     @discord.ui.button(label="Запустить музыку (только админ)", style=discord.ButtonStyle.green)
#     async def gray_button(self, interaction:discord.Interaction, button: discord.ui.Button):
#         if interaction.user.guild_permissions.administrator:
#             await interaction.response.send_message(content=f"This is an edited button response!")
#         else:
#             await interaction.response.send_message(content=f"У вас нет прав для администрирования музыки!")


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
            # print(file_name)
            # play_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label=file_name,
            #                                 custom_id=f"play_{file_name}")
            # play_button.file_name = file_name
            # play_button.callback = lambda button_interaction: self.play_song(button_interaction, file_name)
            # play_button.callback = None
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
            await interaction.response.edit_message(content=f"У вас нет прав для администрирования музыки!")


class MusicBot(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        # self.song_parent = db["files_dir"]
        # print("Music files will be loaded from {}.".format(self.song_parent))
        # self.song_database = db["songs"]
        # print("songs: ", end="")
        # for x in self.song_database:
        #     print(x["song_keys"][0], ", ", end="")
        # print("")
        # self.playlist = []
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

    async def change_volume(self, interaction: discord.Interaction):
        if interaction.data["custom_id"] == "volume_down":
            self.volume = max(self.volume - 0.2, 0)
        else:
            self.volume = min(self.volume + 0.2, 1)
        if self.ctx.voice_client.source is not None:
            self.ctx.voice_client.source.volume = self.volume

    async def stop(self, interaction: discord.Interaction):
        if self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()
            self.is_playing = False
        await interaction.response.edit_message(content=f"Сейчас ничего не воспроизводится.")

    async def play_song(self, interaction: discord.Interaction):
        print(interaction.data['custom_id'])
        target_file_name = interaction.data['custom_id'][5:]
        target_file_path = os.path.join(os.curdir, "../files", target_file_name)  # target_file_name

        def repeat(file_path):
            if self.is_playing:
                repeat_source = discord.PCMVolumeTransformer(
                    discord.FFmpegPCMAudio(file_path, options="-b:a 128k", executable=self.cfg.ffmpeg_executable)
                )
                repeat_source.volume = self.volume

                if self.ctx.voice_client.is_playing():
                    self.ctx.voice_client.stop()

                self.ctx.voice_client.play(repeat_source, after=lambda e: repeat(file_path))
                self.ctx.voice_client.is_playing()

        if self.ctx.voice_client.is_playing():
            self.ctx.voice_client.stop()

        self.is_playing = True
        repeat(target_file_path)
        # self.ctx.voice_client.play(source, after=lambda e: repeat(source))
        # self.ctx.voice_client.is_playing()

        print("Now playing: {}".format(target_file_path))
        await interaction.response.edit_message(content=f"Воспроизводится {target_file_path}")

    async def show_files_list(self, interaction: discord.Interaction):
        if not interaction:  # interaction.user.guild_permissions.administrator
            await interaction.response.send_message(content=f"У вас нет прав для запуска музыки!", ephemeral=True)
        else:
            page = 0
            edited = False
            if "custom_id" in interaction.data and interaction.data["custom_id"].startswith("page_"):
                page = int(interaction.data["custom_id"].replace("page_", ""))
                edited = True

            music_view = discord.ui.View()
            files_list = os.listdir("../files/")

            list_back_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="◀️",
                custom_id=f"page_{page - 1}",
                row=0
            )
            if page == 0:
                list_back_button.disabled = True
            list_back_button.callback = self.show_files_list

            volume_down_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="⤵️",
                custom_id=f"volume_down",
                row=0
            )
            volume_down_button.callback = self.change_volume

            stop_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="⏹",
                custom_id=f"stop",
                row=0
            )
            stop_button.callback = self.stop

            volume_up_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="⤴️",
                custom_id=f"volume_up",
                row=0
            )
            volume_up_button.callback = self.change_volume

            list_forward_button = discord.ui.Button(
                style=discord.ButtonStyle.primary,
                label="▶️",
                custom_id=f"page_{page + 1}",
                row=0
            )
            if len(files_list) < (page + 1) * 20:
                list_forward_button.disabled = True
            list_forward_button.callback = self.show_files_list

            music_view.add_item(list_back_button)
            music_view.add_item(volume_down_button)
            music_view.add_item(stop_button)
            music_view.add_item(volume_up_button)
            music_view.add_item(list_forward_button)

            for file_name in files_list[page * 20:(page + 1) * 20]:
                play_button = discord.ui.Button(style=discord.ButtonStyle.secondary, label=file_name,
                                                custom_id=f"play_{file_name}")
                play_button.file_name = file_name
                # play_button.callback = lambda button_interaction: self.play_song(button_interaction, file_name)
                play_button.callback = self.play_song
                music_view.add_item(play_button)

            if edited:
                await interaction.response.edit_message(view=music_view)
            else:
                await interaction.response.send_message(content=f"Сейчас ничего не воспроизводится.", view=music_view,
                                                        ephemeral=True)

    @commands.command()
    async def join(self, ctx):
        channel = ctx.guild.voice_channels[0]
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        self.ctx = ctx
        await channel.connect()

        # async def button_callback(interaction):
        #     await interaction.response.edit_message(content='Button clicked!', view=None)
        #
        # button = Button(custom_id='button1', label='WOW button!', style=discord.ButtonStyle.green)
        # button.callback = button_callback

        # launchListView = discord.ui.View()
        # launchListButton = discord.ui.Button(label="Запустить музыку (только админ)", style=discord.ButtonStyle.green)
        # launchListButton.callback = lambda interaction: self.show_files_list(interaction)
        # launchListView.add_item(launchListButton)

        launch_button_view = LaunchButtonView(bot=self)
        await channel.send(
            'Бот готов к запуску музыки!\nОбратите внимание, управлять музыкой может только администратор сервера.',
            view=launch_button_view)

    @commands.command()
    async def quit(self, ctx):
        if self.ctx:
            if self.ctx.voice_client.is_playing():
                self.ctx.voice_client.stop()

        # ctx.voice_client.stop()
        await ctx.voice_client.disconnect()

    # def parse(self, query):
    #     play_args = self.parser.parse_args(query.split(" "))
    #     target_songs = []
    #     # process args!
    #     if "artist" in play_args and play_args.artist is not None:
    #         print("Query artists: ", end="")
    #         print(play_args.artist)
    #         for artist in play_args.artist:
    #             artist_clean = artist.lower().replace(" ", "")  # sanitize
    #             tmp = [x for x in self.song_database if artist_clean in x["artist_keys"]]
    #             target_songs = [*target_songs, *tmp]
    #     if "album" in play_args and play_args.album is not None:
    #         print("Query album: ", end="")
    #         print(play_args.album)
    #         for album in play_args.album:
    #             album_clean = album.lower().replace(" ", "")
    #             tmp = [x for x in self.song_database if album_clean in x["album_keys"]]
    #             target_songs = [*target_songs, *tmp]
    #     if "song" in play_args and play_args.song is not None:
    #         query_songs = [x.replace("\"", "").replace("\'", "") for x in  play_args.song]
    #         print("Query songs: ", end="")
    #         print(query_songs)
    #         if len(target_songs) != 0: # filter!
    #             target_songs_new = []
    #             for song in query_songs:
    #                 song_clean = song.lower().replace(" ", "")
    #                 tmp = [x for x in target_songs if song_clean in x["song_keys"]]
    #                 target_songs_new = [*target_songs_new, *tmp]
    #             target_songs = target_songs_new
    #         else:
    #             for song in query_songs:
    #                 song_clean = song.lower().replace(" ", "")
    #                 tmp = [x for x in self.song_database if song_clean in x["song_keys"]]
    #                 target_songs = [*target_songs, *tmp]

    #     return target_songs

    # @commands.command()
    # async def add(self, ctx, *, query):
    #     self.ctx = ctx

    #     target_songs = self.parse(query)
    #     self.playlist = [*self.playlist, *target_songs]

    # @commands.command()
    # async def play(self, ctx, *, query):
    #     self.ctx = ctx
    #     print("Incoming query: ", query)

    #     target_songs = self.parse(query)

    #     self.playlist = [*self.playlist, *target_songs]
    #     print("Current playlist: ", end="")
    #     for x in self.playlist:
    #         print("    {} by {}".format(x["song_keys"][0], x["artist_keys"][0]))

    #     if ctx.voice_client.is_playing():
    #         ctx.voice_client.stop()
    #     else:
    #         await self.play_song(None)

    # async def play_song(self, error):
    #     if error is not None:
    #         print("Error: {}".format(e))
    #         return
    #     print("Checking playlist...")
    #     if len(self.playlist) == 0:
    #         await self.ctx.send("Playlist empty")
    #         self.is_playing = False
    #         return

    #     print("looking for the file")
    #     target_file_path = os.path.join(self.song_parent, self.playlist[0]["filename"])
    #     target_song = self.playlist[0]["song_keys"][0]
    #     target_artist = self.playlist[0]["artist_keys"][0]
    #     del self.playlist[0]

    #     await self.ensure_voice(self.ctx)

    #     source = discord.PCMVolumeTransformer(
    #         discord.FFmpegPCMAudio(target_file_path, options="-b:a 128k")
    #     )
    #     source.volume = self.volume
    #     await self.ctx.send("Now playing: {} by {}".format(target_song, target_artist))
    #     self.current = "{} by {}".format(target_song, target_artist)
    #     self.ctx.voice_client.play(
    #         source,
    #         after=self.dispatch_play_song
    #     )
    #     print("Now playing: {} by {}".format(target_song, target_artist))

    # def dispatch_play_song(self, e):
    #     print("dispatch!")
    #     if e is not None:
    #         print("Error: ", end="")
    #         print(e)
    #         return

    #     # asyncio.run(self.play_song(None), self.bot.loop)
    #     coro = self.play_song(None)
    #     fut = asyncio.run_coroutine_threadsafe(coro, self.bot.loop)
    #     try:
    #         print("fut.result")
    #         fut.result()
    #     except:
    #         pass

    #     return

    # @commands.command()
    # async def pause(self, ctx):
    #     if ctx.voice_client.is_playing():
    #         ctx.voice_client.pause()

    # @commands.command()
    # async def resume(self, ctx):
    #     if ctx.voice_client.is_paused():
    #         ctx.voice_client.resume()

    # @commands.command()
    # async def skip(self, ctx, *, how_many=0):
    #     m_del = int(how_many)
    #     m_del = m_del if m_del <= len(self.playlist) else len(self.playlist)
    #     for _ in range(m_del):
    #         del self.playlist[0]
    #     # await self.play_song(None)
    #     ctx.voice_client.stop()

    # @commands.command()
    # async def show(self, ctx):
    #     to_show = [
    #         "Now playing: " + self.current,
    #         "Songs in playlist: "
    #     ]
    #     if len(self.playlist) == 0:
    #         to_show[-1] = "Playlist empty"
    #     for i, song in enumerate(self.playlist):
    #         to_add = "{0:02d}. ".format(i) + song["song_keys"][0] + " by " + song["artist_keys"][0]
    #         to_show.append(to_add)

    #     await ctx.send("\n".join(to_show))

    # @commands.command()
    # async def quit(self, ctx):
    #     self.playlist = []

    #     ctx.voice_client.stop()

    #     await ctx.voice_client.disconnect()

    # @commands.command()
    # async def q(self, ctx):
    #     await self.quit(ctx)

    # @commands.command()
    # async def volume(self, ctx, volume: int):
    #     if ctx.voice_client is None:
    #         return await ctx.send("Not connected to a voice channel.")

    #     self.volume = volume / 100
    #     if ctx.voice_client.source is not None:
    #         ctx.voice_client.source.volume = self.volume
    #     await ctx.send("Changed volume to {}%".format(volume))

    # @play.before_invoke
    # async def ensure_voice(self, ctx):
    #     if ctx.voice_client is None:
    #         if ctx.author.voice:
    #             await ctx.author.voice.channel.connect()
    #         else:
    #             await ctx.send("You are not connected to a voice channel.")
    #             raise commands.CommandError("Author not connected to a voice channel.")
    #     elif ctx.voice_client.is_playing():
    #         pass

    # # @commands.command()
    # @discord.app_commands.command(name="hello")
    # async def hello(self, interaction: discord.Interaction, member: discord.Member):
    #     """Says hello"""
    #     await interaction.response.send_message(f'Hello!', ephemeral=True)


def setup(bot):
    bot.add_cog(MusicBot(bot))
