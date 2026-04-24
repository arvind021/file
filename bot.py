import logging
from pyrogram import Client
from config import Config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class Bot(Client):
    def __init__(self):
        super().__init__(
            name="FileStoreBot",
            api_id=Config.API_ID,
            api_hash=Config.API_HASH,
            bot_token=Config.BOT_TOKEN,
            plugins={"root": "plugins"},
            workers=50
        )

    async def start(self):
        await super().start()
        me = await self.get_me()
        logger.info(f"✅ Bot @{me.username} started!")
        if Config.LOG_CHANNEL:
            try:
                await self.send_message(
                    Config.LOG_CHANNEL,
                    f"✅ **Bot Started!**\n🤖 @{me.username}"
                )
            except Exception:
                pass

    async def stop(self, *args):
        await super().stop()
        logger.info("🛑 Bot stopped.")


app = Bot()

if __name__ == "__main__":
    app.run()
