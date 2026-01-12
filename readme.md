# 🤖 Discord Bot - Instagram Notifier for Discord

This is a Discord bot developed in **Python 3.12** focused on monitoring Instagram profiles (specifically for the band QWER) and sending real-time notifications to specific channels.

The project utilizes Instagram's Private API (via `instagrapi`) to simulate an Android device, allowing access to data not available through the official public API.

## 🚀 Current Features

* **Hybrid Monitoring:** Checks both the **Main Feed** and the **Reels Tab** simultaneously (ensuring exclusive Reels videos are not missed).
* **Media Type Detector:**
    * **Photos/Carousels:** Sends a rich Embed with customizable colors and image previews.
    * **Reels:** Sends a `kkinstagram.com` link (fix to enable native video playback within Discord) and bypasses the static Embed.
* **Auto-Translation:** Attempts to translate captions (e.g., Korean -> English) using `deep-translator`.
* **KST Timezone:** Automatically converts post timestamps to Korea Standard Time (KST).
* **Database Management:**
    * SQLite database to manage which channels follow which profiles.
    * Individual configurations per channel (Embed colors, custom messages, role mentions).
* **Anti-Flood System:**
    * Ignores posts older than 24 hours during the first run to prevent chat spam.
    * Stores sent post IDs (`media.code`) in the local database.

## 🛠️ Tech Stack & Dependencies

* **Language:** Python 3.12+
* **Core:** `discord.py` (Discord API interaction)
* **Scraper:** `instagrapi` (Instagram Private API Wrapper)
* **Data:** `sqlite3` (Python native)
* **Utils:**
    * `deep-translator` (Google Translate API Wrapper)
    * `python-dotenv` (Environment variables management)
    * `pydantic` (Data validation - *See Patches section*)

## ⚠️ Mandatory Manual Patches (Monkey Patching)

The project runs on a modified version of the `instagrapi` library to fix validation errors (`ValidationError`) caused by recent Instagram API changes and `Pydantic` strictness.

**Modified File:** `.../site-packages/instagrapi/types.py`

The following changes were manually applied to make fields `Optional` and prevent crashes:

1. **`ImageCandidate`**:
   scans_profile: Optional[str] = None

2. **`ClipsMetadata`**:
   mashup_info: Optional[dict] = None

3. **`ClipsOriginalSoundInfo`**:
   audio_filter_infos: Optional[List[dict]] = []

**Note:** If you run `pip install --upgrade instagrapi`, these changes will be overwritten, and the bot will crash when encountering specific Reels.


📂 Project Structure

/
├── bot.py                  # Entry point. Manages the check loop and Discord sending.
├── config.py               # Global settings (Intervals, Paths).
├── requirements.txt        # Dependencies.
├── session_user.json       # Instagram session file (Cookies/Auth).
│
├── core/
│   ├── instagram_checker.py # Scraping Logic (Feed + Reels Merge).
│   └── database_manager.py  # SQLite CRUD operations.
│
├── cogs/
│   ├── management_cog.py    # Slash commands: /add, /remove, /list.
│   └── customize_cog.py     # Slash commands: /set_message, /set_color.
│
└── data/
    └── bot_database.db      # Database file (Auto-generated).

## 🐛 Known Issues & Challenges (Roadmap)

**1. IP Blocking (Error 429 - Too Many Requests)**
Symptom: Instagram detects requests coming from Datacenters (Oracle Cloud/AWS) and blocks the connection (HTTPSConnectionPool).

Status: Critical in cloud environments.

Current Workaround: Run the bot on Localhost (Personal PC) with a Residential IP or use rotating Residential Proxies.

**2. Pydantic Validation**
Symptom: Instagram frequently changes its response JSON structure, causing instagrapi to break with Field required or Input should be a valid dictionary errors.

Solution: Manual maintenance of the types.py file as new errors arise.

**3. Login Challenge (Checkpoint)**
Symptom: Instagram requests SMS/Email verification when detecting an IP change.

Solution: Generate the session file (session.json) locally and upload it to the server.


## 📝 How to Run (Local Dev)

1. Install dependencies: `pip install -r requirements.txt`

2. Configure Environment Variables: Create a .env file in the root directory:

DISCORD_BOT_TOKEN=your_token_here

3. Configure config.py.

4. Apply Patches: Edit the types.py file within the instagrapi library as described in the Patches section.

5. Start the bot:

python bot.py