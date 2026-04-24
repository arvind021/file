import time
import random
import string
from motor.motor_asyncio import AsyncIOMotorClient
from config import Config

# ── Client & DB ──────────────────────────────────────────────────────────────
_client      = AsyncIOMotorClient(Config.MONGO_URI)
db           = _client[Config.DB_NAME]

users_col    = db["users"]
files_col    = db["files"]
batches_col  = db["batches"]
settings_col = db["settings"]
stories_col  = db["stories"]


# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════

def _rand_id(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_letters + string.digits, k=n))


# ════════════════════════════════════════════════════════════════════════════
# USERS
# ════════════════════════════════════════════════════════════════════════════

async def add_user(user_id: int, name: str):
    if not await users_col.find_one({"user_id": user_id}):
        await users_col.insert_one({
            "user_id": user_id,
            "name": name,
            "banned": False,
            "joined": time.time()
        })


async def get_all_users():
    return users_col.find({})


async def get_user_count() -> int:
    return await users_col.count_documents({})


async def ban_user(user_id: int):
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"banned": True}},
        upsert=True
    )


async def unban_user(user_id: int):
    await users_col.update_one(
        {"user_id": user_id},
        {"$set": {"banned": False}}
    )


async def is_banned(user_id: int) -> bool:
    u = await users_col.find_one({"user_id": user_id})
    return u.get("banned", False) if u else False


# ════════════════════════════════════════════════════════════════════════════
# FILE LINKS  (single message)
# ════════════════════════════════════════════════════════════════════════════

async def save_file(msg_id: int, channel_id: int) -> str:
    fid = _rand_id(8)
    await files_col.insert_one({
        "file_id":    fid,
        "msg_id":     msg_id,
        "channel_id": channel_id,
        "created":    time.time()
    })
    return fid


async def get_file(file_id: str) -> dict | None:
    return await files_col.find_one({"file_id": file_id})


async def delete_file(file_id: str):
    await files_col.delete_one({"file_id": file_id})


# ════════════════════════════════════════════════════════════════════════════
# BATCH LINKS  (multiple messages)
# ════════════════════════════════════════════════════════════════════════════

async def save_batch(
    msg_ids: list,
    channel_id: int,
    editable: bool = False,
    universal: bool = False
) -> str:
    bid = _rand_id(10)
    await batches_col.insert_one({
        "batch_id":   bid,
        "msg_ids":    msg_ids,
        "channel_id": channel_id,
        "editable":   editable,
        "universal":  universal,
        "created":    time.time()
    })
    return bid


async def get_batch(batch_id: str) -> dict | None:
    return await batches_col.find_one({"batch_id": batch_id})


async def update_batch_msgs(batch_id: str, msg_ids: list):
    await batches_col.update_one(
        {"batch_id": batch_id},
        {"$set": {"msg_ids": msg_ids}}
    )


async def delete_batch(batch_id: str):
    await batches_col.delete_one({"batch_id": batch_id})


# ════════════════════════════════════════════════════════════════════════════
# SETTINGS  (per user)
# ════════════════════════════════════════════════════════════════════════════

_default_settings = {
    "protect_content": False,
    "custom_caption":  None,
    "custom_button":   None,
    "link_shortener":  False,
    "google_backup":   False,
    "clone_bot":       None,
}


async def get_settings(user_id: int) -> dict:
    s = await settings_col.find_one({"user_id": user_id})
    if not s:
        return dict(_default_settings)
    return {**_default_settings, **s}


async def update_setting(user_id: int, key: str, value):
    await settings_col.update_one(
        {"user_id": user_id},
        {"$set": {key: value}},
        upsert=True
    )


# ════════════════════════════════════════════════════════════════════════════
# STORIES
# ════════════════════════════════════════════════════════════════════════════

async def add_story(name: str, channel: str):
    await stories_col.update_one(
        {"name": name.lower()},
        {"$set": {"name": name.lower(), "channel": channel}},
        upsert=True
    )


async def get_all_stories():
    return stories_col.find({})


async def remove_story(name: str):
    await stories_col.delete_one({"name": name.lower()})
