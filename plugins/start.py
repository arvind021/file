import asyncio
from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from config import Config
from database.db import add_user, get_user_count, get_file, get_batch, is_banned
from helpers import decode_id


# ════════════════════════════════════════════════════════════════════════════
# FORCE JOIN
# ════════════════════════════════════════════════════════════════════════════

async def force_join_check(client: Client, message: Message) -> bool:
    if not Config.FORCE_SUB:
        return True
    try:
        member = await client.get_chat_member(Config.FORCE_SUB, message.from_user.id)
        if member.status in ("left", "kicked", "banned"):
            raise Exception("not joined")
        return True
    except Exception:
        ch = Config.FORCE_SUB.lstrip("@")
        await message.reply(
            "⚠️ **Access Denied!**\n\n"
            "You must join our official channel to use this bot.\n\n"
            "👇 Join below then click **✅ I've Joined**",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("📢 Join Channel", url=f"https://t.me/{ch}")],
                [InlineKeyboardButton("✅ I've Joined", callback_data="check_join")]
            ])
        )
        return False


@Client.on_callback_query(filters.regex("^check_join$"))
async def check_join_cb(client: Client, query: CallbackQuery):
    if not Config.FORCE_SUB:
        return await query.answer("✅ You can use the bot!", show_alert=True)
    try:
        member = await client.get_chat_member(Config.FORCE_SUB, query.from_user.id)
        if member.status in ("left", "kicked", "banned"):
            raise Exception
        await query.answer("✅ Verified! Send /start again.", show_alert=True)
        await query.message.delete()
    except Exception:
        await query.answer("❌ You haven't joined yet!", show_alert=True)


# ════════════════════════════════════════════════════════════════════════════
# KEYBOARDS
# ════════════════════════════════════════════════════════════════════════════

def start_kb():
    ch = Config.UPDATES_CHANNEL.lstrip("@") if Config.UPDATES_CHANNEL else "telegram"
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("❓ HELP",  callback_data="help_menu"),
            InlineKeyboardButton("ℹ️ ABOUT", callback_data="about_bot"),
        ],
        [InlineKeyboardButton("🤖 CREATE MY OWN CLONE", callback_data="clone_info")],
        [InlineKeyboardButton("📢 UPDATE CHANNEL ↗", url=f"https://t.me/{ch}")],
    ])

BACK_KB = InlineKeyboardMarkup([
    [InlineKeyboardButton("◀️ BACK", callback_data="back_start")]
])

HELP_TEXT = """
❓ **Help Menu**

I am a permanent file store bot. Store files from your channel and share via a link!

📚 **Commands:**
➜ /start — Check I am alive
➜ /genlink — Store a single file *(mods only)*
➜ /batch — Channel range → batch link *(mods only)*
➜ /custom\_batch — Forward messages → batch link *(mods only)*
➜ /special\_link — Editable multi-message link *(mods only)*
➜ /universal\_link — Clone-accessible link *(mods only)*
➜ /shortener — Shorten any link *(mods only)*
➜ /settings — Settings panel
➜ /addstory — Add story channel
➜ /stories — View story channels

🛡 **Mod/Owner Only:**
➜ /broadcast — Message all users
➜ /ban — Ban a user
➜ /unban — Unban a user
➜ /stats — Total users
"""

ABOUT_TEXT = """
ℹ️ **About Me**

🤖 **Bot:** File Store Bot
⚙️ **Framework:** Pyrogram v2
🗄 **Database:** MongoDB
🔗 **Link System:** Base64 deep links
🔒 **Access:** Force join + Ban system

I store your Telegram files permanently and give you shareable links that never expire!
"""

CLONE_TEXT = """
🤖 **Create Your Own Clone**

**Steps:**
1️⃣ Get API ID & Hash → [my.telegram.org](https://my.telegram.org)
2️⃣ Create bot → @BotFather
3️⃣ MongoDB Atlas free cluster → [mongodb.com](https://mongodb.com)
4️⃣ Create private storage channel → add bot as admin
5️⃣ Fill `.env` file → run `python bot.py`

📦 Ask owner for source code!
"""


# ════════════════════════════════════════════════════════════════════════════
# /start
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("start") & filters.private)
async def start_cmd(client: Client, message: Message):
    user = message.from_user
    await add_user(user.id, user.first_name)

    # Ban check
    if await is_banned(user.id):
        return await message.reply("🚫 You are banned from using this bot.")

    # Force join check
    if not await force_join_check(client, message):
        return

    # Deep link payload
    args = message.command
    if len(args) > 1:
        payload = args[1]
        try:
            decoded = decode_id(payload)
        except Exception:
            return await message.reply("❌ Invalid or expired link.")

        if decoded.startswith("file_"):
            data = await get_file(decoded[5:])
            if not data:
                return await message.reply("❌ File not found or deleted.")
            return await _deliver_file(client, message, data)

        elif decoded.startswith("batch_"):
            data = await get_batch(decoded[6:])
            if not data:
                return await message.reply("❌ Batch not found or deleted.")
            return await _deliver_batch(client, message, data)

    # Normal welcome
    await message.reply(
        f"Hello {user.mention} ✨\n\n"
        "I am a **permanent file store bot** and users can access "
        "stored messages by using a shareable link given by me.\n\n"
        "_To know more click help button_ 👇",
        reply_markup=start_kb()
    )


# ════════════════════════════════════════════════════════════════════════════
# CALLBACKS
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex("^help_menu$"))
async def help_cb(client: Client, query: CallbackQuery):
    await query.answer()
    await query.message.edit(HELP_TEXT, reply_markup=BACK_KB, disable_web_page_preview=True)


@Client.on_callback_query(filters.regex("^about_bot$"))
async def about_cb(client: Client, query: CallbackQuery):
    await query.answer()
    await query.message.edit(ABOUT_TEXT, reply_markup=BACK_KB)


@Client.on_callback_query(filters.regex("^clone_info$"))
async def clone_cb(client: Client, query: CallbackQuery):
    await query.answer()
    await query.message.edit(CLONE_TEXT, reply_markup=BACK_KB, disable_web_page_preview=False)


@Client.on_callback_query(filters.regex("^back_start$"))
async def back_start_cb(client: Client, query: CallbackQuery):
    await query.answer()
    user = query.from_user
    await query.message.edit(
        f"Hello {user.mention} ✨\n\n"
        "I am a **permanent file store bot** and users can access "
        "stored messages by using a shareable link given by me.\n\n"
        "_To know more click help button_ 👇",
        reply_markup=start_kb()
    )


@Client.on_callback_query(filters.regex("^stats$"))
async def stats_cb(client: Client, query: CallbackQuery):
    await query.answer()
    total = await get_user_count()
    await query.message.edit(
        f"📊 **Bot Stats**\n\n👤 Total Users: `{total}`",
        reply_markup=BACK_KB
    )


# ════════════════════════════════════════════════════════════════════════════
# DELIVERY HELPERS
# ════════════════════════════════════════════════════════════════════════════

async def _deliver_file(client: Client, message: Message, data: dict):
    try:
        msg = await client.get_messages(data["channel_id"], data["msg_id"])
        sent = await msg.copy(message.chat.id)
        # Auto delete if configured
        if Config.FILE_AUTO_DELETE > 0:
            await asyncio.sleep(Config.FILE_AUTO_DELETE)
            await sent.delete()
    except Exception as e:
        await message.reply(f"❌ Could not fetch file: `{e}`")


async def _deliver_batch(client: Client, message: Message, data: dict):
    notice = await message.reply("📦 Sending files, please wait...")
    count, total = 0, len(data["msg_ids"])
    for mid in data["msg_ids"]:
        try:
            msg = await client.get_messages(data["channel_id"], mid)
            await msg.copy(message.chat.id)
            count += 1
            await asyncio.sleep(0.4)
        except Exception:
            pass
    await notice.edit(f"✅ Done! Sent `{count}` / `{total}` files.")
