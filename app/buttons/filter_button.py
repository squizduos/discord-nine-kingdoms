import discord


class FilterPlaylistButton(discord.ui.Button["Music"]):
    def __init__(self, title: str, filter: str, player_view):
        super().__init__(style=discord.ButtonStyle.danger, label=title)
        self.filter = filter
        self.page = 0
        self.player_view = player_view

    async def callback(self, interaction: discord.Interaction):
        self.player_view.filter = self.filter
        self.player_view.page = 0
        self.player_view.refresh()
        await self.player_view.show(interaction)
