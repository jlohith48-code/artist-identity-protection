"""
youtube_ingest.py
"""
import os
import re
import argparse
from datetime import datetime, timezone
from dataclasses import dataclass
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()

SUBSCRIBER_THRESHOLD = 10_000
CHANNEL_AGE_YEARS = 2
MAX_VIDEOS_PER_CHANNEL = 300

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

CREDIT_PATTERNS = [
    r"lyrics?\s*(?:by\s*)?[:\-]\s*(.+)",
    r"lyricist\s*[:\-]\s*(.+)",
    r"written\s+by\s*[:\-]?\s*(.+)",
    r"penned\s+by\s*[:\-]?\s*(.+)",
    r"music\s*(?:by\s*)?[:\-]\s*(.+)",
    r"composed\s+by\s*[:\-]?\s*(.+)",
    r"singers?\s*[:\-]\s*(.+)",
    r"sung\s+by\s*[:\-]?\s*(.+)",
]

@dataclass
class ChannelInfo:
    channel_id: str
    title: str
    subscriber_count: int
    published_at: datetime
    is_topic_channel: bool
    is_verified: bool

@dataclass
class ExtractedCredit:
    role: str
    credited_name: str
    raw_match: str
    tag: str = None
    matched_artist: str = None
    match_type: str = None

@dataclass
class EvidenceRecord:
    video_id: str
    video_url: str
    video_title: str
    channel_id: str
    confidence: str
    evidence_type: str
    status: str
    credits: list

def compute_status(credits):
    if any(c.match_type == "exact" for c in credits):
        return "auto_confirmed"
    return "pending_review"

@dataclass
class ArtistEntry:
    name: str
    aliases: list = None
    def all_names(self):
        return [self.name] + (self.aliases or [])

def get_youtube_client():
    if not YOUTUBE_API_KEY:
        raise RuntimeError("YOUTUBE_API_KEY not set. Add it to your .env file in backend/.")
    return build("youtube", "v3", developerKey=YOUTUBE_API_KEY)

def resolve_channel_id(youtube, channel_input):
    channel_input = channel_input.strip()
    if channel_input.startswith("UC") and " " not in channel_input and "/" not in channel_input:
        return channel_input
    handle = channel_input
    if "youtube.com" in handle:
        handle = handle.rstrip("/").split("/")[-1]
    handle = handle.lstrip("@")
    resp = youtube.channels().list(part="id", forHandle=handle).execute()
    items = resp.get("items", [])
    if not items:
        search_resp = youtube.search().list(part="snippet", q=channel_input, type="channel", maxResults=1).execute()
        search_items = search_resp.get("items", [])
        if not search_items:
            raise ValueError(f"Could not resolve channel: {channel_input}")
        return search_items[0]["snippet"]["channelId"]
    return items[0]["id"]

def get_channel_info(youtube, channel_id):
    resp = youtube.channels().list(part="snippet,statistics", id=channel_id).execute()
    items = resp.get("items", [])
    if not items:
        raise ValueError(f"Channel not found: {channel_id}")
    item = items[0]
    title = item["snippet"]["title"]
    published_at = datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z", "+00:00"))
    subscriber_count = int(item["statistics"].get("subscriberCount", 0))
    is_topic_channel = title.strip().endswith("- Topic")
    return ChannelInfo(channel_id=channel_id, title=title, subscriber_count=subscriber_count,
                        published_at=published_at, is_topic_channel=is_topic_channel, is_verified=False)

def score_confidence(channel):
    if channel.is_topic_channel:
        return "high"
    age_years = (datetime.now(timezone.utc) - channel.published_at).days / 365.25
    if channel.subscriber_count >= SUBSCRIBER_THRESHOLD and age_years >= CHANNEL_AGE_YEARS:
        return "medium"
    return "low"

def get_channel_videos(youtube, channel_id, max_results=MAX_VIDEOS_PER_CHANNEL):
    ch_resp = youtube.channels().list(part="contentDetails", id=channel_id).execute()
    uploads_playlist_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    videos = []
    next_page_token = None
    while len(videos) < max_results:
        pl_resp = youtube.playlistItems().list(part="snippet", playlistId=uploads_playlist_id,
                                                 maxResults=min(50, max_results - len(videos)),
                                                 pageToken=next_page_token).execute()
        for item in pl_resp.get("items", []):
            snippet = item["snippet"]
            videos.append({"video_id": snippet["resourceId"]["videoId"], "title": snippet["title"],
                            "description": snippet.get("description", "")})
        next_page_token = pl_resp.get("nextPageToken")
        if not next_page_token:
            break
    return videos

def extract_credits(description):
    credits_found = []
    for line in description.split("\n"):
        line = line.strip()
        if not line:
            continue
        for pattern in CREDIT_PATTERNS:
            match = re.search(pattern, line, re.IGNORECASE)
            if not match:
                continue
            raw_value = match.group(1).strip()
            tags = re.findall(r"\(([^)]+)\)", raw_value)
            cleaned = re.sub(r"\([^)]*\)", "", raw_value).strip()
            cleaned = re.split(r"\s{2,}|#|\||\u2022|--+", cleaned)[0].strip()
            cleaned = cleaned.rstrip(".,;:-").strip()
            if not cleaned or len(cleaned) >= 60:
                continue
            if not re.match(r"^[A-Za-z .]+$", cleaned):
                continue
            credits_found.append(ExtractedCredit(role=_role_label(pattern), credited_name=cleaned,
                                                   raw_match=match.group(0).strip(), tag=tags[0] if tags else None))
    return credits_found

def _role_label(pattern):
    if "lyric" in pattern:
        return "lyrics"
    if "written" in pattern or "penned" in pattern:
        return "writer"
    if "music" in pattern or "composed" in pattern:
        return "music"
    if "sing" in pattern:
        return "singer"
    return "credit"

def _normalize(s):
    return re.sub(r"[^a-z0-9]", "", s.lower())

def match_against_known_artists(credited_name, known_artists):
    norm_credited = _normalize(credited_name)
    if not norm_credited:
        return None, None
    for artist in known_artists:
        for candidate in artist.all_names():
            if _normalize(candidate) == norm_credited:
                return artist.name, "exact"
    for artist in known_artists:
        for candidate in artist.all_names():
            norm_candidate = _normalize(candidate)
            if len(norm_candidate) >= 4 and (norm_credited in norm_candidate or norm_candidate in norm_credited):
                return artist.name, "partial"
    return None, None

def find_raw_mentions(video_title, description, known_artists):
    haystack = _normalize(f"{video_title} {description}")
    found = []
    for artist in known_artists:
        for candidate in artist.all_names():
            norm_candidate = _normalize(candidate)
            if len(norm_candidate) >= 4 and norm_candidate in haystack:
                found.append(artist.name)
                break
    return list(dict.fromkeys(found))

def ingest_channel(channel_input, known_artists):
    youtube = get_youtube_client()
    channel_id = resolve_channel_id(youtube, channel_input)
    channel = get_channel_info(youtube, channel_id)
    confidence = score_confidence(channel)
    print(f"Channel: {channel.title}")
    print(f"  Subscribers: {channel.subscriber_count:,}")
    print(f"  Topic channel: {channel.is_topic_channel}")
    print(f"  Confidence tier: {confidence}")
    videos = get_channel_videos(youtube, channel_id)
    print(f"  Fetched {len(videos)} videos")
    evidence_records = []
    structured_count = 0
    mention_only_count = 0
    for video in videos:
        extracted = extract_credits(video["description"])
        matched_credits = []
        for credit in extracted:
            matched_name, match_type = match_against_known_artists(credit.credited_name, known_artists)
            if matched_name:
                credit.matched_artist = matched_name
                credit.match_type = match_type
                matched_credits.append(credit)
        if matched_credits:
            structured_count += 1
            evidence_records.append(EvidenceRecord(video_id=video["video_id"],
                video_url=f"https://www.youtube.com/watch?v={video['video_id']}",
                video_title=video["title"], channel_id=channel_id, confidence=confidence,
                evidence_type="structured_credit", status=compute_status(matched_credits), credits=matched_credits))
            continue
        mentions = find_raw_mentions(video["title"], video["description"], known_artists)
        if mentions:
            mention_only_count += 1
            fallback_credits = [ExtractedCredit(role="unknown", credited_name=name,
                raw_match="(name mentioned somewhere in title/description, no structured field found)",
                matched_artist=name, match_type="mention_only") for name in mentions]
            evidence_records.append(EvidenceRecord(video_id=video["video_id"],
                video_url=f"https://www.youtube.com/watch?v={video['video_id']}",
                video_title=video["title"], channel_id=channel_id, confidence=confidence,
                evidence_type="mention_only", status="pending_review", credits=fallback_credits))
    print(f"  Structured credit matches: {structured_count}")
    print(f"  Mention-only (needs review): {mention_only_count}")
    return evidence_records

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest YouTube ownership evidence.")
    parser.add_argument("--channel", required=True, help="Channel URL, @handle, or channel ID")
    parser.add_argument("--save-to-db", action="store_true", help="Write results into ownership_evidence table")
    args = parser.parse_args()

    KNOWN_ARTISTS = [
        ArtistEntry("Chethan Kumar", aliases=["Bharjari"]),
        ArtistEntry("Chandrabose"),
        ArtistEntry("Ramajogayya Sastry"),
        ArtistEntry("Vairamuthu"),
        ArtistEntry("Vivek Velmurugan"),
        ArtistEntry("Javed Akhtar"),
        ArtistEntry("Amitabh Bhattacharya"),
        ArtistEntry("Rafeeq Ahamed"),
        ArtistEntry("Vayalar Ramavarma"),
        ArtistEntry("Ed Sheeran"),
        ArtistEntry("Taylor Swift"),
    ]

    records = ingest_channel(args.channel, KNOWN_ARTISTS)
    structured = [r for r in records if r.evidence_type == "structured_credit"]
    mention_only = [r for r in records if r.evidence_type == "mention_only"]

    if structured:
        print("\n" + "=" * 60)
        print("STRUCTURED CREDIT MATCHES (strong evidence)")
        print("=" * 60)
        for rec in structured:
            print(f"\n{rec.video_title} ({rec.video_url}) - channel confidence: {rec.confidence}")
            for c in rec.credits:
                tag_info = f" [tag: {c.tag}]" if c.tag else ""
                print(f"   {c.role}: {c.credited_name}{tag_info} -> {c.matched_artist} [{c.match_type} match]  (raw: '{c.raw_match}')")

    if mention_only:
        print("\n" + "=" * 60)
        print("MENTION-ONLY (weak evidence - review manually before trusting)")
        print("=" * 60)
        for rec in mention_only:
            names = ", ".join(c.matched_artist for c in rec.credits)
            print(f"\n{rec.video_title} ({rec.video_url})")
            print(f"   mentions: {names}  - not tied to a specific credited role")

    if args.save_to_db:
        from db_writer import save_evidence_records
        print("\n" + "=" * 60)
        print("SAVING TO DATABASE...")
        print("=" * 60)
        summary = save_evidence_records(records)
        print(f"Inserted: {summary['inserted']} new evidence rows")
        print(f"Skipped (already existed): {summary['skipped_duplicates']}")
    else:
        print("\n(Run again with --save-to-db to write these results into the database.)")