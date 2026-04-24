from pyrogram import Client, filters
from pyrogram.types import Message
from database.db import add_story, get_all_stories, remove_story
from helpers import is_mod

USAGE = (
    "📖 **Usage:**\n"
    "`/addstory <name> | <channel_username_or_link>`\n\n"
    "**OR** reply to a message with name + URL and send `/addstory`\n\n"
    "**Example:**\n"
    "`/addstory shadow | https://t.me/soul_shadow_07`\n"
    "`/addstory anime | @animechannel`"
)


# ════════════════════════════════════════════════════════════════════════════
# /addstory
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("addstory") & filters.private)
async def addstory_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")

    text = None

    # Case 1: /addstory name | channel
    if len(message.command) > 1:
        text = message.text.split(" ", 1)[1].strip()

    # Case 2: reply to a message with name | channel
    elif message.reply_to_message and message.reply_to_message.text:
        text = message.reply_to_message.text.strip()

    if not text:
        return await message.reply(USAGE)

    if "|" not in text:
        return await message.reply(f"❌ Missing `|` separator.\n\n{USAGE}")

    parts = text.split("|", 1)
    name    = parts[0].strip()
    channel = parts[1].strip()

    if not name or not channel:
        return await message.reply(f"❌ Name or channel is empty.\n\n{USAGE}")

    await add_story(name, channel)
    await message.reply(
        f"✅ **Story channel added!**\n\n"
        f"📌 Name: `{name}`\n"
        f"📢 Channel: `{channel}`"
    )


# ════════════════════════════════════════════════════════════════════════════
# /stories
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("stories") & filters.private)
async def stories_cmd(client: Client, message: Message):
    cursor = await get_all_stories()
    stories = await cursor.to_list(length=200)

    if not stories:
        return await message.reply(
            "📭 No story channels configured yet.\n\n"
            "Use /addstory to add one."
        )

    lines = [f"📖 **Configured Story Channels ({len(stories)}):**\n"]
    for i, s in enumerate(stories, 1):
        lines.append(f"`{i}.` **{s['name']}** — {s['channel']}")

    await message.reply("\n".join(lines), disable_web_page_preview=True)


# ════════════════════════════════════════════════════════════════════════════
# /removestory
# ════════════════════════════════════════════════════════════════════════════

@Client.on_message(filters.command("removestory") & filters.private)
async def removestory_cmd(client: Client, message: Message):
    if not is_mod(message.from_user.id):
        return await message.reply("🚫 Moderators only.")

    args = message.command
    if len(args) < 2:
        return await message.reply("Usage: `/removestory <story_name>`")

    name = " ".join(args[1:]).strip()
    await remove_story(name)
    await message.reply(f"✅ Story `{name}` removed.")
