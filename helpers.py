import base64
from config import Config


def is_mod(user_id: int) -> bool:
    """Check if user is owner or moderator."""
    return user_id == Config.OWNER_ID or user_id in Config.MODERATORS


def encode_id(raw: str) -> str:
    """Base64 encode a string for use in deep links."""
    return base64.urlsafe_b64encode(raw.encode()).decode().rstrip("=")


def decode_id(enc: str) -> str:
    """Decode a base64 deep link payload."""
    pad = 4 - len(enc) % 4
    return base64.urlsafe_b64decode((enc + "=" * pad).encode()).decode()


def get_file_link(file_id: str) -> str:
    payload = encode_id(f"file_{file_id}")
    return f"https://t.me/{Config.BOT_USERNAME}?start={payload}"


def get_batch_link(batch_id: str) -> str:
    payload = encode_id(f"batch_{batch_id}")
    return f"https://t.me/{Config.BOT_USERNAME}?start={payload}"
