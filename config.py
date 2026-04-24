import os


class Config:
    # ── Bot Credentials ──────────────────────────────────────────────────────
    BOT_TOKEN        = os.environ.get("BOT_TOKEN", "")
    API_ID           = int(os.environ.get("API_ID", 0))
    API_HASH         = os.environ.get("API_HASH", "")
    BOT_USERNAME     = os.environ.get("BOT_USERNAME", "")   # without @

    # ── MongoDB ──────────────────────────────────────────────────────────────
    MONGO_URI        = os.environ.get("MONGO_URI", "")
    DB_NAME          = os.environ.get("DB_NAME", "FileStoreBot")

    # ── Owner & Mods ─────────────────────────────────────────────────────────
    OWNER_ID         = int(os.environ.get("OWNER_ID", 0))
    MODERATORS       = (
        list(map(int, os.environ.get("MODERATORS", "").split()))
        if os.environ.get("MODERATORS") else []
    )

    # ── Channels ─────────────────────────────────────────────────────────────
    STORAGE_CHANNEL  = int(os.environ.get("STORAGE_CHANNEL", 0))  # bot must be admin here
    LOG_CHANNEL      = int(os.environ.get("LOG_CHANNEL", 0))

    # Force join — "@yourchannel"  |  leave empty "" to disable
    FORCE_SUB        = os.environ.get("FORCE_SUB", "")

    # Shown on UPDATE CHANNEL button in /start
    UPDATES_CHANNEL  = os.environ.get("UPDATES_CHANNEL", "")

    # ── Misc ─────────────────────────────────────────────────────────────────
    FILE_AUTO_DELETE = int(os.environ.get("FILE_AUTO_DELETE", 0))  # seconds; 0 = off
    SHORT_API_KEY    = os.environ.get("SHORT_API_KEY", "")
    SHORT_API_URL    = os.environ.get("SHORT_API_URL", "")
