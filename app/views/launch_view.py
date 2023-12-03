import discord

from .player_view import PlayerView


class LaunchView(discord.ui.View):
    def __init__(self, *, timeout=180, bot=None):
        self.bot = bot
        super().__init__(timeout=timeout)

    def caption(self):
        return "Бот готов к запуску музыки!\nОбратите внимание, управлять музыкой может только администратор сервера."

    @discord.ui.button(label="Запустить музыку (только админ)", style=discord.ButtonStyle.green)
    async def green_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.guild_permissions.administrator:
            player_view = PlayerView(
                bot=self.bot, music_folder=self.bot.cfg.files_dir, words=self.bot.cfg.words.split(",")
            )
            await interaction.response.send_message(content=player_view.caption(), view=player_view, ephemeral=True)
        else:
            await interaction.response.send_message(content=f"У вас нет прав для администрирования музыки!")
