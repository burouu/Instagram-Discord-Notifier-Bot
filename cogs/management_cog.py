import discord
from discord import app_commands
from discord.ext import commands
import logging
import asyncio

class ManagementCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="add", description="Add an Instagram account to track.")
    @app_commands.describe(
        username="The @username of the Instagram account.", 
        channel="The channel for notifications.",
        role="Optional: Role to mention when this user posts."
    )
    @app_commands.default_permissions(administrator=True)
    async def add(self, interaction: discord.Interaction, username: str, channel: discord.TextChannel = None, role: discord.Role = None):
        target_channel = channel or interaction.channel
        
        if username.startswith('@'):
            username = username[1:]
        
        role_id = role.id if role else None
        
        success = self.bot.db_manager.add_account(username.lower(), target_channel.id, role_id)
        
        if success:
            msg = f"✅ Tracking `{username}` in {target_channel.mention}."
            if role:
                msg += f" Mentioning: {role.mention}"
            await interaction.response.send_message(msg, ephemeral=True)
        else:
            await interaction.response.send_message(
                f"⚠️ Account `{username}` is already being tracked in {target_channel.mention}.",
                ephemeral=True
            )

    @app_commands.command(name="remove", description="Remove a tracked Instagram account.")
    async def remove(self, interaction: discord.Interaction, username: str, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel
        if username.startswith('@'): username = username[1:]
        
        success = self.bot.db_manager.remove_account(username.lower(), target_channel.id)
        if success:
            await interaction.response.send_message(f"🗑️ Stopped tracking `{username}` in {target_channel.mention}.", ephemeral=True)
        else:
            await interaction.response.send_message(f"❌ `{username}` is not tracked in {target_channel.mention}.", ephemeral=True)

    @app_commands.command(name="list", description="List all tracked Instagram accounts.")
    async def list(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel
        accounts = self.bot.db_manager.get_accounts_for_channel(target_channel.id)
        if not accounts:
            await interaction.response.send_message(f"ℹ️ No accounts tracked in {target_channel.mention}.", ephemeral=True)
            return
        
        desc = []
        for acc in accounts:
            settings = self.bot.db_manager.get_account_settings(acc, target_channel.id)
            role_mention = f"<@&{settings['role_id']}>" if settings and settings.get('role_id') else "No Role"
            desc.append(f"- **{acc}** ({role_mention})")

        embed = discord.Embed(
            title=f"📸 Accounts in #{target_channel.name}",
            description="\n".join(desc),
            color=discord.Color.blue()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="fetch", description="Force fetch the latest post for a user.")
    async def fetch(self, interaction: discord.Interaction, username: str, channel: discord.TextChannel = None):
        target_channel = channel or interaction.channel
        if username.startswith('@'): username = username[1:]

        await interaction.response.defer(ephemeral=True)

        try:
            medias = await asyncio.to_thread(
                self.bot.instagram_checker.get_new_posts, 
                username, 
                1
            )
            
            if not medias:
                await interaction.followup.send(f"❌ Could not retrieve posts for `{username}`. Check logs.", ephemeral=True)
                return

            latest_media = medias[0]
            
            await self.bot.send_notification(target_channel, latest_media)
            
            await interaction.followup.send(f"✅ Fetched latest post for `{username}`.", ephemeral=True)

        except Exception as e:
            logging.error(f"Manual fetch failed: {e}")
            await interaction.followup.send(f"❌ Error fetching post: {e}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(ManagementCog(bot))