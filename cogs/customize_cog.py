# cogs/customize_cog.py
import discord
from discord import app_commands
from discord.ext import commands
from ui.customization_modal import CustomizationModal

class CustomizeCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    customize_group = app_commands.Group(name="customize", description="Customize alerts per account.")

    @customize_group.command(name="set", description="Customize notification for a specific tracked user.")
    @app_commands.describe(username="The username to customize (must be tracked in this channel).")
    async def set_modal(self, interaction: discord.Interaction, username: str):
        settings = self.bot.db_manager.get_account_settings(username.lower(), interaction.channel_id)
        
        if not settings and "role_id" not in (settings or {}): 

            tracked = self.bot.db_manager.get_accounts_for_channel(interaction.channel_id)
            if username.lower() not in tracked:
                await interaction.response.send_message(f"❌ `{username}` is not tracked in this channel. Use `/add` first.", ephemeral=True)
                return
            settings = {}

        modal = CustomizationModal(username.lower(), interaction.channel_id, settings)
        await interaction.response.send_modal(modal)

    @customize_group.command(name="placeholders", description="Show variables you can use.")
    async def placeholders(self, interaction: discord.Interaction):
        embed = discord.Embed(title="Available Placeholders", color=discord.Color.green())
        embed.add_field(name="{user}", value="Username", inline=True)
        embed.add_field(name="{caption}", value="Post Caption", inline=True)
        embed.add_field(name="{url}", value="Post Link", inline=True)
        embed.add_field(name="{likes}", value="Like Count", inline=True)
        embed.add_field(name="{date}", value="Date (KST)", inline=True)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(CustomizeCog(bot))