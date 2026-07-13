import hashlib

def generate_lyrics_hash(lyrics: str) -> str:
    normalized = lyrics.strip().lower()
    normalized = " ".join(normalized.split())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def generate_lyrics_preview(lyrics: str, word_limit: int = 15) -> str:
    words = lyrics.strip().split()
    preview = " ".join(words[:word_limit])
    if len(words) > word_limit:
        preview += "..."
    return preview
