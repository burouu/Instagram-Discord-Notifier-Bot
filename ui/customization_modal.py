# ui/customization_modal.py
import discord
from discord import ui
from typing import Optional, Dict, Any

class CustomizationModal(ui.Modal):
    def __init__(self, target_username: str, channel_id: int, current_settings: Optional[Dict[str, Any]]):
        self.target_username = target_username
        self.channel_id = channel_id
        super().__init__(title=f'Edit: {target_username}')
        
        self.current_settings = current_settings or {}

        self.message_content = ui.TextInput(
            label="Message Content (Above Embed)", 
            style=discord.TextStyle.short, 
            placeholder="e.g., {user} posted! or <@&12345>", 
            default=self.current_settings.get("message_content"), 
            required=False, max_length=500
        )
        self.add_item(self.message_content)

        self.embed_title = ui.TextInput(
            label="Embed Title", 
            style=discord.TextStyle.short, 
            placeholder="e.g., New Post!", 
            default=self.current_settings.get("embed_title"), 
            required=False, max_length=256
        )
        self.add_item(self.embed_title)

        self.embed_description = ui.TextInput(
            label="Embed Description", 
            style=discord.TextStyle.paragraph, 
            placeholder="e.g., {caption}", 
            default=self.current_settings.get("embed_description"), 
            required=False, max_length=2000
        )
        self.add_item(self.embed_description)

        self.embed_color = ui.TextInput(
            label="Embed Color (Hex)", 
            style=discord.TextStyle.short, 
            placeholder="#E1306C", 
            default=self.current_settings.get("embed_color"), 
            required=False, min_length=7, max_length=7
        )
        self.add_item(self.embed_color)

        self.embed_footer = ui.TextInput(
            label="Footer Text", 
            style=discord.TextStyle.short, 
            placeholder="{date}", 
            default=self.current_settings.get("embed_footer_text"), 
            required=False, max_length=200
        )
        self.add_item(self.embed_footer)

    async def on_submit(self, interaction: discord.Interaction):
        bot = interaction.client
        
        updates = {
            "message_content": self.message_content.value,
            "embed_title": self.embed_title.value,
            "embed_description": self.embed_description.value,
            "embed_color": self.embed_color.value,
            "embed_footer_text": self.embed_footer.value
        }

        for key, value in updates.items():
            final_val = value if value and value.strip() != "" else None
            bot.db_manager.update_account_setting(self.target_username, self.channel_id, key, final_val)

        await interaction.response.send_message(f"✅ Settings updated for **{self.target_username}**!", ephemeral=True)