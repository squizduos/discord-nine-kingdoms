# -*-coding:utf-8-*-
import environ
import random

from config import AppConfig

import discord
from discord.ext import commands
from discord import app_commands


class RollCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cfg = environ.to_config(AppConfig)

    # @commands.command()
    # async def sync(self, ctx) -> None:
    #     ctx.bot.tree.copy_global_to(guild=ctx.guild)
    #     fmt = await ctx.bot.tree.sync(guild=ctx.guild)
    #     await ctx.send(f"Synced {len(fmt)} commands.")

    @app_commands.command(name="roll", description="Бросаем кубики")
    @app_commands.describe(
        dices='Количество кубиков',
        complexity='Заявленная сложность',
        auto_success='Автоуспехи'
    )
    async def roll(self, interaction: discord.Interaction, dices: int, complexity: int = 6, auto_success: int = 0):
        results = sorted([random.randint(1, 10) for i in range(dices)], reverse=True)
        success = sum([1 for element in results if element >= complexity])
        message = f"`{' '.join([f'[{i}]' for i in results])}`\n"
        if success == 0:
            message += f"😱 ** КРИТИЧЕСКИЙ ПРОВАЛ! ** 😱"
        elif success == dices:
            message += f"🔥 **КРИТИЧЕСКИЙ УСПЕХ НА {(dices + auto_success)} КУБАХ!! ** 🔥"
        else:
            message += f"{success} из {dices} по {complexity} сложности"
            if auto_success > 0:
                message += f", плюс {auto_success} автоуспехов => {success + auto_success} успехов"
        await interaction.response.send_message(message, ephemeral=True)


def setup(bot):
    bot.add_cog(RollCog(bot))
