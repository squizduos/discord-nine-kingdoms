# -*-coding:utf-8-*-
import environ

from config import AppConfig

from discord.ext import commands

from views.launch_view import LaunchView


class MusicBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ctx = None
        self.is_playing = False

        self.cfg = environ.to_config(AppConfig)

    @commands.command()
    async def join(self, ctx):
        channel = ctx.guild.voice_channels[0]
        if ctx.voice_client is not None:
            return await ctx.voice_client.move_to(channel)

        self.ctx = ctx
        await channel.connect()

        launch_view = LaunchView(bot=self)
        await channel.send(launch_view.caption(), view=launch_view)

    @commands.command()
    async def quit(self, ctx):
        if self.ctx:
            if self.ctx.voice_client.is_playing():
                self.ctx.voice_client.stop()

        await ctx.voice_client.disconnect()


def setup(bot):
    bot.add_cog(MusicBot(bot))
