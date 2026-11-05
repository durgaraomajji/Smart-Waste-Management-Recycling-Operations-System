from urllib.parse import urlparse

ALLOWED_IMAGE_EXT = (".jpg", ".jpeg", ".png", ".webp")


def is_valid_photo_url(url: str) -> bool:
    """Photo evidence is stored as a reference URL (no binary upload). Only http(s) image URLs are accepted."""
    parsed = urlparse(url)
    return parsed.scheme in ("http", "https") and parsed.path.lower().endswith(ALLOWED_IMAGE_EXT)
