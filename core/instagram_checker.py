import logging
import os
from instagrapi import Client
from instagrapi.exceptions import LoginRequired
import config

class InstagramChecker:
    def __init__(self, username: str):
        self.username = username
        self.cl = Client()
        self.cl.delay_range = [2, 5]
        
        session_file = f"session_{username}.json"
        
        if os.path.exists(session_file):
            try:
                self.cl.load_settings(session_file)
            except Exception as e:
                logging.warning(f"Could not load session: {e}")
        
        self._login()

    def _login(self):
        try:
            self.cl.get_timeline_feed()
            logging.info(f"Session valid for {self.username}.")
        except (LoginRequired, Exception):
            logging.info("Logging in with password...")
            try:
                self.cl.login(self.username, config.INSTAGRAM_PASSWORD)
                self.cl.dump_settings(f"session_{self.username}.json")
                logging.info("Login successful.")
            except Exception as e:
                logging.critical(f"Login failed: {e}")
                raise e

    def get_user_id(self, username: str):
        try:
            return self.cl.user_info_by_username_v1(username).pk
        except Exception as e:
            logging.error(f"Failed to get User ID for {username}: {e}")
            return None

    def get_new_posts(self, username: str, amount=10):
        user_id = self.get_user_id(username)
        if not user_id:
            return []
            
        try:

            medias = self.cl.user_medias_v1(user_id, amount=amount)
            
            clips = self.cl.user_clips_v1(user_id, amount=amount)
            
            combined_medias = {media.code: media for media in medias + clips}
            
            return list(combined_medias.values())

        except Exception as e:
            logging.error(f"Error fetching media for {username}: {e}")
            return []