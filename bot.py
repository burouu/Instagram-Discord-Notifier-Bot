import os
import logging
import asyncio
import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone
import random 

from deep_translator import GoogleTranslator
from instagrapi.types import Media

import config
from core.database_manager import DatabaseManager
from core.instagram_checker import InstagramChecker

load_dotenv()
os.makedirs(os.path.dirname(config.DATABASE_PATH), exist_ok=True)
os.makedirs(os.path.dirname(config.LOG_FILE_PATH), exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s',
                    handlers=[
                        logging.FileHandler(config.LOG_FILE_PATH, encoding='utf-8'),
                        logging.StreamHandler()
                    ])

class InstagramNotifierBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix="!", intents=discord.Intents.default())
        self.guild_id = config.DISCORD_GUILD_ID
        self.db_manager = DatabaseManager(config.DATABASE_PATH)
        self.instagram_checker = InstagramChecker(config.INSTAGRAM_USERNAME)

    async def setup_hook(self):
        await self.load_extension("cogs.management_cog")
        await self.load_extension("cogs.customize_cog")
        self.tree.copy_global_to(guild=discord.Object(id=self.guild_id)) 
        await self.tree.sync(guild=discord.Object(id=self.guild_id)) 
        logging.info("Slash commands synced.") 

    async def on_ready(self):
        logging.info(f'Logged in as {self.user}')
        instagram_check_loop.start()

    def format_with_placeholders(self, text: str, media: Media, caption_override: str = None) -> str:
        if not text: return None
        
        kst = timezone(timedelta(hours=9))
        post_time_kst = media.taken_at.astimezone(kst)
        final_caption = caption_override if caption_override is not None else (media.caption_text or "")
        
        replacements = {
            "{user}": media.user.username, 
            "{user_fullname}": media.user.full_name, 
            "{user_avatar}": str(media.user.profile_pic_url), 
            "{url}": f"https://www.instagram.com/p/{media.code}/", 
            "{caption}": final_caption,
            "{likes}": f"{media.like_count:,}", 
            "{comments}": f"{media.comment_count:,}", 
            "{date}": post_time_kst.strftime('%d/%m/%Y'), 
            "{time}": post_time_kst.strftime('%H:%M KST')
        }
        for placeholder, value in replacements.items(): 
            text = text.replace(placeholder, str(value))
        return text

    def create_default_image_embed(self, media: Media, caption_override: str = None) -> discord.Embed:
        post_url = f"https://www.instagram.com/p/{media.code}/"
        display_caption = caption_override if caption_override is not None else media.caption_text
        
        title = (display_caption[:253] + '...') if display_caption and len(display_caption) > 256 else display_caption or f"New Post from {media.user.username}"
        description = f"❤️ {media.like_count:,}  💬 {media.comment_count:,}"
        
        kst = timezone(timedelta(hours=9))
        post_time_kst = media.taken_at.astimezone(kst)
        
        embed = discord.Embed(title=title, url=post_url, description=description, color=discord.Color.dark_magenta())
        embed.set_author(name=media.user.username, icon_url=str(media.user.profile_pic_url))
        
        image_url = str(media.thumbnail_url) if media.thumbnail_url else None
        if not image_url and media.resources:
             image_url = str(media.resources[0].thumbnail_url)
        
        if image_url: embed.set_image(url=image_url)
        embed.set_footer(text=f"Posted on {post_time_kst.strftime('%d %B %Y at %H:%M KST')}")
        return embed

    async def send_notification(self, channel: discord.TextChannel, media: Media):
        if media.media_type == 2 and media.product_type == 'clips':
            kkinsta_url = f"https://www.kkinstagram.com/p/{media.code}/"
            settings = self.db_manager.get_account_settings(media.user.username, channel.id)
            if not settings: settings = {}
            role_mention = f"<@&{settings['role_id']}> " if settings.get("role_id") else ""
            await channel.send(f"{role_mention}**{media.user.username}** new reels!\n{kkinsta_url}")
            return

        translated_text = ""
        if media.caption_text:
            try:
                translated_text = await asyncio.to_thread(
                    GoogleTranslator(source='auto', target='en').translate, 
                    media.caption_text
                )
            except Exception:
                translated_text = media.caption_text 

        all_embeds = []
        settings = self.db_manager.get_account_settings(media.user.username, channel.id)
        if not settings: settings = {}
        
        role_mention = f"<@&{settings['role_id']}> " if settings.get("role_id") else ""
        content_text = None
        has_custom_embed = any(v is not None for k, v in settings.items() if k.startswith('embed_'))
        
        if settings.get("message_content"):
            content_text = self.format_with_placeholders(settings.get("message_content"), media, translated_text)
        
        if content_text: content_text = f"{role_mention}{content_text}"
        elif role_mention: content_text = role_mention

        main_embed = None
        if has_custom_embed:
            color_hex = settings.get("embed_color")
            color = discord.Color.blue() if not color_hex else discord.Color(int(color_hex[1:], 16))
            main_embed = discord.Embed(color=color)
            
            title = self.format_with_placeholders(settings.get("embed_title"), media, translated_text)
            if title: main_embed.title = title
            
            desc = self.format_with_placeholders(settings.get("embed_description"), media, translated_text)
            if desc: main_embed.description = desc

            footer = self.format_with_placeholders(settings.get("embed_footer_text"), media, translated_text)
            if footer: main_embed.set_footer(text=footer)

            img = str(media.thumbnail_url or (media.resources[0].thumbnail_url if media.resources else ""))
            main_embed.set_image(url=img)
        else:
            main_embed = self.create_default_image_embed(media, translated_text)

        if main_embed: all_embeds.append(main_embed)

        if media.media_type == 8 and media.resources:
            for node in media.resources[1:]: 
                sub_embed = discord.Embed(url=f"https://www.instagram.com/p/{media.code}/")
                sub_embed.set_image(url=str(node.thumbnail_url or node.video_url)) 
                if main_embed and main_embed.color: sub_embed.color = main_embed.color
                all_embeds.append(sub_embed)

        chunks = [all_embeds[i:i + 10] for i in range(0, len(all_embeds), 10)]
        
        if not chunks and content_text:
             await channel.send(content=content_text)
        
        for i, chunk in enumerate(chunks):
            msg = content_text if i == 0 else None
            await channel.send(content=msg, embeds=chunk)

bot = InstagramNotifierBot()

@tasks.loop(seconds=config.CHECK_INTERVAL_SECONDS)
async def instagram_check_loop():
    logging.info("Starting check cycle...")
    unique_usernames = bot.db_manager.get_unique_tracked_usernames()
    if not unique_usernames: return

    for raw_username in unique_usernames:
        username = raw_username.lstrip('@')
        try:
            new_medias = await asyncio.to_thread(bot.instagram_checker.get_new_posts, username, 10)

            new_medias.sort(key=lambda x: x.taken_at, reverse=True)

            for media in new_medias:
            
                if bot.db_manager.is_media_sent(media.code): continue

                now_utc = datetime.now(timezone.utc)
                post_time = media.taken_at.astimezone(timezone.utc)
                
                time_diff = (now_utc - post_time).total_seconds()
                
                if time_diff > 86400: 
                    logging.info(f"Skipping OLD media (Silent Save): {media.code} | Age: {time_diff/3600:.1f}h")
                    bot.db_manager.mark_media_as_sent(media.code)
                    continue

                logging.info(f"New media found: {media.code}")
                target_channels = bot.db_manager.get_channels_for_username(raw_username)
                
                for ch_id in target_channels:
                    channel = bot.get_channel(ch_id)
                    if channel: await bot.send_notification(channel, media)
                
                bot.db_manager.mark_media_as_sent(media.code)
                await asyncio.sleep(random.uniform(5, 10))

        except Exception as e:
            logging.error(f"Check failed for {username}: {e}")
            await asyncio.sleep(5)

    logging.info("Cycle finished.")

@instagram_check_loop.before_loop
async def before_check():
    await bot.wait_until_ready()

if __name__ == "__main__":
    bot.run(os.getenv("DISCORD_BOT_TOKEN"))