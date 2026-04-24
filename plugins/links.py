import asyncio
from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from config import Config
from database.db import save_file, save_batch
from helpers import is_mod, get_file_link, get_batch_link

# Active sessions per user_id
# Value: "genlink" | {"type": "custom_batch"|"special_link"|"universal_link", "msgs": []}
_sessions: dict = {}


# ════════════════════════════════════════════════════════════════════════════
# UTILS
# ════════════════════════════════════════════════════════════════════════════

def _link_btn(link: str):
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔗 Open Link", url=link)]
    ])


# ════════════════════════════════════════════════════════════════════════════
# /genlink — Single message/file
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("genlink") & filters.private)
async def genlink_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")
    _sessions[message.from_user.id] = "genlink"
    await message.reply(
        "📨 **Forward the message/file** you want to store.\n\n"
        "Send /cancel to abort."
    )


# ════════════════════════════════════════════════════════════════════════════
# /batch — Channel range
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("batch") & filters.private)
async def batch_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")
    _sessions[message.from_user.id] = "batch_await"
    await message.reply(
        "📦 **Batch Link Generator**\n\n"
        "Send in this format:\n"
        "`@channel_username start_id end_id`\n\n"
        "Example: `@mychannel 100 200`\n\n"
        "Max 500 messages per batch."
    )


# ════════════════════════════════════════════════════════════════════════════
# /custom_batch — Forward manually
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("custom_batch") & filters.private)
async def custom_batch_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")
    _sessions[message.from_user.id] = {"type": "custom_batch", "msgs": []}
    await message.reply(
        "📨 **Custom Batch Mode**\n\n"
        "Forward messages one by one.\n"
        "Send /done when finished.\n"
        "Send /cancel to abort."
    )


# ════════════════════════════════════════════════════════════════════════════
# /special_link — Editable batch
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("special_link") & filters.private)
async def special_link_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")
    _sessions[message.from_user.id] = {"type": "special_link", "msgs": []}
    await message.reply(
        "✨ **Special Link Mode** (Editable)\n\n"
        "Forward messages one by one.\n"
        "Send /done when finished.\n"
        "Send /cancel to abort."
    )


# ════════════════════════════════════════════════════════════════════════════
# /universal_link — All clones accessible
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("universal_link") & filters.private)
async def universal_link_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")
    _sessions[message.from_user.id] = {"type": "universal_link", "msgs": []}
    await message.reply(
        "🌐 **Universal Link Mode**\n\n"
        "Forward messages one by one.\n"
        "Link will work on all bot clones.\n"
        "Send /done when finished.\n"
        "Send /cancel to abort."
    )


# ════════════════════════════════════════════════════════════════════════════
# /cancel — End any session
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("cancel") & filters.private)
async def cancel_cmd(client: Client, message: Message):
    uid = message.from_user.id
    if uid in _sessions:
        del _sessions[uid]
        await message.reply("❌ Session cancelled.")
    else:
        await message.reply("No active session.")


# ════════════════════════════════════════════════════════════════════════════
# /done — Finish collecting messages
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("done") & filters.private)
async def done_cmd(client: Client, message: Message):
    uid = message.from_user.id
    session = _sessions.get(uid)

    if not isinstance(session, dict):
        return await message.reply("No active collection session. Use /custom_batch, /special_link, or /universal_link first.")

    msgs = session.get("msgs", [])
    stype = session.get("type", "custom_batch")

    if not msgs:
        del _sessions[uid]
        return await message.reply("❌ No messages were added.")

    editable  = (stype == "special_link")
    universal = (stype == "universal_link")

    bid = await save_batch(msgs, Config.STORAGE_CHANNEL, editable=editable, universal=universal)
    link = get_batch_link(bid)
    del _sessions[uid]

    label = {
        "custom_batch":  "Custom Batch",
        "special_link":  "Special Link (Editable)",
        "universal_link": "Universal Link"
    }.get(stype, "Batch")

    await message.reply(
        f"✅ **{label} Created!**\n\n"
        f"📝 Messages: `{len(msgs)}`\n\n"
        f"🔗 **Link:** `{link}`",
        reply_markup=_link_btn(link)
    )


# ════════════════════════════════════════════════════════════════════════════
# MESSAGE HANDLER — Catch forwarded/sent messages during active sessions
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(
    filters.private
    & ~filters.command([
        "start", "genlink", "batch", "custom_batch", "special_link",
        "universal_link", "cancel", "done", "settings", "broadcast",
        "ban", "unban", "stats", "shortener", "addstory", "stories",
        "removestory"
    ])
    & filters.create(lambda _, __, m: bool(m.from_user and m.from_user.id in _sessions))
)
async def session_handler(client: Client, message: Message):
    uid = message.from_user.id
    session = _sessions.get(uid)

    # ── genlink ──────────────────────────────────────────────────────────────
    if session == "genlink":
        try:
            copied = await message.copy(Config.STORAGE_CHANNEL)
            fid = await save_file(copied.id, Config.STORAGE_CHANNEL)
            link = get_file_link(fid)
            del _sessions[uid]
            await message.reply(
                f"✅ **File Stored!**\n\n🔗 **Link:** `{link}`",
                reply_markup=_link_btn(link)
            )
        except Exception as e:
            await message.reply(f"❌ Error: `{e}`")

    # ── batch_await ───────────────────────────────────────────────────────────
    elif session == "batch_await":
        parts = (message.text or "").strip().split()
        if len(parts) != 3:
            return await message.reply("❌ Format: `@channel start_id end_id`")

        channel, start_id, end_id = parts[0], int(parts[1]), int(parts[2])
        if start_id > end_id:
            return await message.reply("❌ Start ID must be less than End ID.")
        if (end_id - start_id) > 499:
            return await message.reply("❌ Max 500 messages per batch.")

        prog = await message.reply(f"⏳ Copying messages {start_id} → {end_id} ...")
        copied_ids, errors = [], 0

        for mid in range(start_id, end_id + 1):
            try:
                msg = await client.get_messages(channel, mid)
                if msg and not msg.empty:
                    c = await msg.copy(Config.STORAGE_CHANNEL)
                    copied_ids.append(c.id)
                    await asyncio.sleep(0.3)
            except Exception:
                errors += 1

        if not copied_ids:
            del _sessions[uid]
            return await prog.edit("❌ No messages could be copied.")

        bid = await save_batch(copied_ids, Config.STORAGE_CHANNEL)
        link = get_batch_link(bid)
        del _sessions[uid]

        await prog.edit(
            f"✅ **Batch Created!**\n\n"
            f"📝 Copied: `{len(copied_ids)}`\n"
            f"❌ Errors: `{errors}`\n\n"
            f"🔗 **Link:** `{link}`",
            reply_markup=_link_btn(link)
        )

    # ── custom_batch / special_link / universal_link ──────────────────────────
    elif isinstance(session, dict) and session.get("type") in ("custom_batch", "special_link", "universal_link"):
        try:
            copied = await message.copy(Config.STORAGE_CHANNEL)
            _sessions[uid]["msgs"].append(copied.id)
            count = len(_sessions[uid]["msgs"])
            await message.reply(
                f"✅ Added! Total: `{count}` messages.\n"
                f"Send more or /done to finish."
            )
        except Exception as e:
            await message.reply(f"❌ Error: `{e}`")
