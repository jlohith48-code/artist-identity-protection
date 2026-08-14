"""
debug_search.py — quick diagnostic: fetch many videos from a channel and
print any description that contains a given name, so we can see the ACTUAL
credit format this channel uses before tuning the real regex patterns.
"""

import os
import argparse
from googleapiclient.discovery import build
from dotenv import load_dotenv

load_dotenv()
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")


def get_client():
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
    if items:
        return items[0]["id"]
    search_resp = youtube.search().list(part="snippet", q=channel_input, type="channel", maxResults=1).execute()
    return search_resp["items"][0]["snippet"]["channelId"]


def fetch_all_videos(youtube, channel_id, max_results):
    ch_resp = youtube.channels().list(part="contentDetails", id=channel_id).execute()
    uploads_playlist_id = ch_resp["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    videos = []
    next_page_token = None
    while len(videos) < max_results:
        pl_resp = youtube.playlistItems().list(
            part="snippet",
            playlistId=uploads_playlist_id,
            maxResults=min(50, max_results - len(videos)),
            pageToken=next_page_token,
        ).execute()
        for item in pl_resp.get("items", []):
            snippet = item["snippet"]
            videos.append({
                "video_id": snippet["resourceId"]["videoId"],
                "title": snippet["title"],
                "description": snippet.get("description", ""),
            })
        next_page_token = pl_resp.get("nextPageToken")
        if not next_page_token:
            break
        print(f"  ...fetched {len(videos)} so far")
    return videos


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--channel", required=True)
    parser.add_argument("--name", required=True, help="Substring to search for, e.g. Chethan")
    parser.add_argument("--max", type=int, default=300, help="Max videos to scan")
    args = parser.parse_args()

    youtube = get_client()
    channel_id = resolve_channel_id(youtube, args.channel)
    print(f"Scanning up to {args.max} videos for channel {args.channel}...")
    videos = fetch_all_videos(youtube, channel_id, args.max)
    print(f"Total videos fetched: {len(videos)}")

    hits = [v for v in videos if args.name.lower() in v["description"].lower() or args.name.lower() in v["title"].lower()]
    print(f"\nVideos matching \"{args.name}\": {len(hits)}\n")

    for v in hits:
        print("=" * 60)
        print(f"TITLE: {v['title']}")
        print(f"URL: https://www.youtube.com/watch?v={v['video_id']}")
        print("DESCRIPTION:")
        print(v['description'][:500])
        print()

