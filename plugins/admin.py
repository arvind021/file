import asyncio
import aiohttp
from pyrogram import Client, filters
from pyrogram.types import Message
from config import Config
from database.db import get_all_users, get_user_count, ban_user, unban_user
from helpers import is_mod


# ════════════════════════════════════════════════════════════════════════════
# /broadcast
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("broadcast") & filters.private)
async def broadcast_cmd(client: Client, message: Message):
    if message.from_user.id != Config.OWNER_ID:
        return await message.reply("🚫 Owner only command.")

    if not message.reply_to_message:
        return await message.reply("📨 **Reply to a message** to broadcast it.")

    prog = await message.reply("📡 Broadcasting...")
    success, fail = 0, 0

    async for user in await get_all_users():
        try:
            await message.reply_to_message.copy(user["user_id"])
            success += 1
        except Exception:
            fail += 1
        await asyncio.sleep(0.05)

    await prog.edit(
        f"✅ **Broadcast Complete!**\n\n"
        f"✅ Success: `{success}`\n"
        f"❌ Failed: `{fail}`\n"
        f"📊 Total: `{success + fail}`"
    )


# ════════════════════════════════════════════════════════════════════════════
# /ban
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("ban") & filters.private)
async def ban_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")

    args = message.command
    if len(args) < 2:
        return await message.reply(
            "Usage: `/ban <user_id>`\n"
            "Or reply to a user's message with `/ban`"
        )
    try:
        uid = int(args[1])
    except ValueError:
        return await message.reply("❌ Invalid user ID.")

    await ban_user(uid)
    await message.reply(f"🚫 User `{uid}` has been **banned**.")

    if Config.LOG_CHANNEL:
        await client.send_message(
            Config.LOG_CHANNEL,
            f"🚫 **User Banned**\nID: `{uid}`\nBy: {message.from_user.mention}"
        )


# ════════════════════════════════════════════════════════════════════════════
# /unban
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("unban") & filters.private)
async def unban_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")

    args = message.command
    if len(args) < 2:
        return await message.reply("Usage: `/unban <user_id>`")
    try:
        uid = int(args[1])
    except ValueError:
        return await message.reply("❌ Invalid user ID.")

    await unban_user(uid)
    await message.reply(f"✅ User `{uid}` has been **unbanned**.")

    if Config.LOG_CHANNEL:
        await client.send_message(
            Config.LOG_CHANNEL,
            f"✅ **User Unbanned**\nID: `{uid}`\nBy: {message.from_user.mention}"
        )


# ════════════════════════════════════════════════════════════════════════════
# /stats
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("stats") & filters.private)
async def stats_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")
    total = await get_user_count()
    await message.reply(
        f"📊 **Bot Stats**\n\n"
        f"👤 Total Users: `{total}`"
    )


# ════════════════════════════════════════════════════════════════════════════
# /shortener
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("shortener") & filters.private)
async def shortener_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")

    args = message.command
    if len(args) < 2:
        return await message.reply("Usage: `/shortener <url>`")

    url = args[1]

    if not Config.SHORT_API_KEY or not Config.SHORT_API_URL:
        return await message.reply(
            "⚠️ Link shortener API not configured.\n"
            "Set `SHORT_API_KEY` and `SHORT_API_URL` in your `.env` file."
        )

    try:
        api_url = f"{Config.SHORT_API_URL}?api={Config.SHORT_API_KEY}&url={url}"
        async with aiohttp.ClientSession() as session:
            async with session.get(api_url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                data = await resp.json()
                short = (
                    data.get("shortenedUrl")
                    or data.get("short_url")
                    or data.get("url")
                )
                if short:
                    await message.reply(
                        f"🔗 **Shortened Link:**\n`{short}`\n\n"
                        f"📎 Original: `{url}`"
                    )
                else:
                    await message.reply(f"❌ API returned: `{data}`")
    except asyncio.TimeoutError:
        await message.reply("❌ API request timed out.")
    except Exception as e:
        await message.reply(f"❌ Error: `{e}`")
