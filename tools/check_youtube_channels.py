import sys
from pathlib import Path
sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "studio"))
sys.path.insert(0, str(ROOT))

import requests
from youtube_manager import load_youtube_config, get_fresh_access_token

cfg = load_youtube_config()
channels = cfg.get('channels', [])
print(f"Total channels configured: {len(channels)}")

videos_to_check = ['WjI_iHaz-r8', 'rsEkzztZeRc', 'wzJMSuOFg7w']

for ch in channels:
    ch_id = ch['id']
    ch_name = ch.get('name', ch_id).strip()
    print(f"\n--- Checking Channel: {ch_name} ({ch_id}) ---")
    try:
        token = get_fresh_access_token(ch_id)
        # Fetch uploaded videos for this channel
        r = requests.get(
            f"https://www.googleapis.com/youtube/v3/channels?part=snippet,contentDetails&mine=true",
            headers={"Authorization": f"Bearer {token}"}
        )
        ch_items = r.json().get("items", [])
        if ch_items:
            uploads_playlist = ch_items[0]["contentDetails"]["relatedPlaylists"]["uploads"]
            r_uploads = requests.get(
                f"https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&playlistId={uploads_playlist}&maxResults=5",
                headers={"Authorization": f"Bearer {token}"}
            )
            up_items = r_uploads.json().get("items", [])
            print(f"Latest {len(up_items)} uploads on this channel:")
            for item in up_items:
                vid = item["snippet"]["resourceId"]["videoId"]
                title = item["snippet"]["title"]
                desc = item["snippet"].get("description", "")
                print(f"  * Video ID: {vid}")
                print(f"    Title: {title}")
                print(f"    Desc preview: {desc[:60]}...")
        else:
            print("  Could not fetch channel uploads playlist.")

        # Also check specific unlisted video IDs
        for target_vid in videos_to_check:
            r_vid = requests.get(
                f"https://www.googleapis.com/youtube/v3/videos?part=snippet,status,contentDetails&id={target_vid}",
                headers={"Authorization": f"Bearer {token}"}
            )
            v_items = r_vid.json().get("items", [])
            if v_items:
                snip = v_items[0]["snippet"]
                stat = v_items[0]["status"]
                print(f"  -> MATCH TARGET VIDEO {target_vid}:")
                print(f"     Title: {snip.get('title')}")
                print(f"     Description (first 100 chars): {snip.get('description', '')[:100]}")
                print(f"     Tags: {len(snip.get('tags', []))} tags")
                print(f"     Privacy: {stat.get('privacyStatus')}")
    except Exception as e:
        print(f"  Error on channel {ch_name}: {e}")
