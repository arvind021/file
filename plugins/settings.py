from pyrogram import Client, filters
from pyrogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from database.db import get_settings, update_setting

# Tracks users waiting to input setting values
_pending: dict = {}   # uid -> "caption" | "button" | "clone"


# ════════════════════════════════════════════════════════════════════════════
# KEYBOARD
# ════════════════════════════════════════════════════════════════════════════

def settings_kb():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 MY CLONE BOT",    callback_data="set_clone")],
        [InlineKeyboardButton("💾 GOOGLE BACKUP",   callback_data="set_backup")],
        [InlineKeyboardButton("🔗 LINK SHORTENER",  callback_data="set_shortener")],
        [InlineKeyboardButton("✏️ CUSTOM CAPTION",  callback_data="set_caption")],
        [InlineKeyboardButton("✨ CUSTOM BUTTON",   callback_data="set_button")],
        [InlineKeyboardButton("🔒 PROTECT CONTENT", callback_data="set_protect")],
        [InlineKeyboardButton("◀️ BACK",            callback_data="back_start")],
    ])


# ════════════════════════════════════════════════════════════════════════════
# /settings command
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("settings") & filters.private)
async def settings_cmd(client: Client, message: Message):
    await message.reply(
        "⚙️ **Settings**\n\n_Customize your settings as your need_",
        reply_markup=settings_kb()
    )


@Client.on_callback_query(filters.regex("^settings$"))
async def settings_cb(client: Client, query: CallbackQuery):
    await query.answer()
    await query.message.edit(
        "⚙️ **Settings**\n\n_Customize your settings as your need_",
        reply_markup=settings_kb()
    )


# ════════════════════════════════════════════════════════════════════════════
# PROTECT CONTENT toggle
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex("^set_protect$"))
async def protect_cb(client: Client, query: CallbackQuery):
    uid = query.from_user.id
    s = await get_settings(uid)
    new_val = not s.get("protect_content", False)
    await update_setting(uid, "protect_content", new_val)
    status = "✅ Enabled" if new_val else "❌ Disabled"
    await query.answer(f"Protect Content: {status}", show_alert=True)


# ════════════════════════════════════════════════════════════════════════════
# LINK SHORTENER toggle
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex("^set_shortener$"))
async def shortener_toggle_cb(client: Client, query: CallbackQuery):
    uid = query.from_user.id
    s = await get_settings(uid)
    new_val = not s.get("link_shortener", False)
    await update_setting(uid, "link_shortener", new_val)
    status = "✅ Enabled" if new_val else "❌ Disabled"
    await query.answer(f"Link Shortener: {status}", show_alert=True)


# ════════════════════════════════════════════════════════════════════════════
# CUSTOM CAPTION
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex("^set_caption$"))
async def caption_cb(client: Client, query: CallbackQuery):
    await query.answer()
    _pending[query.from_user.id] = "caption"
    await query.message.reply(
        "✏️ Send your **custom caption** now.\n\n"
        "Variables you can use: `{file_name}` `{file_size}`\n\n"
        "Send /cancel to abort."
    )


# ════════════════════════════════════════════════════════════════════════════
# CUSTOM BUTTON
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex("^set_button$"))
async def button_cb(client: Client, query: CallbackQuery):
    await query.answer()
    _pending[query.from_user.id] = "button"
    await query.message.reply(
        "✨ Send your **custom button** in this format:\n\n"
        "`Button Text | https://yourlink.com`\n\n"
        "Multiple buttons → separate with new lines.\n"
        "Send /cancel to abort."
    )


# ════════════════════════════════════════════════════════════════════════════
# CLONE BOT TOKEN
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex("^set_clone$"))
async def clone_token_cb(client: Client, query: CallbackQuery):
    await query.answer()
    _pending[query.from_user.id] = "clone"
    await query.message.reply(
        "🤖 Send your **Clone Bot Token** (from @BotFather).\n\n"
        "Send /cancel to abort."
    )


# ════════════════════════════════════════════════════════════════════════════
# GOOGLE BACKUP (placeholder)
# ════════════════════════════════════════════════════════════════════════════

@Client.on_callback_query(filters.regex("^set_backup$"))
async def backup_cb(client: Client, query: CallbackQuery):
    await query.answer("🚧 Google Backup — Coming Soon!", show_alert=True)


# ════════════════════════════════════════════════════════════════════════════
# INPUT HANDLER for setting values
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(
    filters.private
    & ~filters.command([])
    & filters.create(lambda _, __, m: bool(m.from_user and m.from_user.id in _pending))
)
async def settings_input(client: Client, message: Message):
    uid = message.from_user.id
    action = _pending.pop(uid, None)

    if action == "caption":
        await update_setting(uid, "custom_caption", message.text)
        await message.reply("✅ Custom caption saved!")

    elif action == "button":
        lines = (message.text or "").strip().split("\n")
        buttons = []
        for line in lines:
            parts = line.split("|", 1)
            if len(parts) == 2:
                text = parts[0].strip()
                url  = parts[1].strip()
                if text and url:
                    buttons.append({"text": text, "url": url})
        if buttons:
            await update_setting(uid, "custom_button", buttons)
            await message.reply(f"✅ `{len(buttons)}` button(s) saved!")
        else:
            await message.reply("❌ Invalid format. Use:\n`Button Text | https://url.com`")

    elif action == "clone":
        token = (message.text or "").strip()
        await update_setting(uid, "clone_bot", token)
        await message.reply("✅ Clone bot token saved!")
