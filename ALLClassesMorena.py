import os
import re
import time
import subprocess
import requests
import asyncio
from math import ceil
from pyrogram import Client, filters
from pyrogram.types import Message
from utils import progress_bar

# --- CONFIGURATION ---
TOKEN = "EyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTI4NzE5MzEyLCJvcmdJZCI6NzYzMzIwLCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTgyNzkwNDk1NjgiLCJuYW1lIjoiTG92ZWt1c2giLCJlbWFpbCI6ImVhM2U0NjNkOWM5NjQ0YzJiZGE1ZDFiNWNkZjE5NTkzQGdtYWlsLmNvbSIsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjoiRU4iLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpc0RpeSI6dHJ1ZSwibG9naW5WaWEiOiJPdHAiLCJmaW5nZXJwcmludElkIjoiODQ3MTU0MjAzMzYyNDMwN2IwMzUyOTZiZThhOWIxMDIiLCJpYXQiOjE3Njc0OTk0MTQsImV4cCI6MTc2ODEwNDIxNH0.ia_YuAJaftl74ZQQT9cqi4fYyMhUsOwgHoJ7Vt1SQjRiMIUQFXOjCz2iu7nwLcY_"
ORG_CODE = "UIEVJH"

def get_duration(filename):
    result = subprocess.run(["ffprobe", "-v", "-error", "-show_entries",
                             "format=duration", "-of",
                             "default=noprint_wrappers=1:nokey=1", filename],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT)
    return float(result.stdout)

def get_mps_and_keys(video_id):
    """
    Official Classplus API se MPD URL aur Keys fetch karne ke liye.
    """
    # Agar video_id mein poora URL hai toh ID nikalne ki koshish karein
    if "videoId=" in str(video_id):
        video_id = video_id.split("videoId=")[-1].split("&")[0]

    api_url = f"https://api.classplusapp.com/v2/videos/get-video-details?videoId={video_id}"
    
    headers = {
        "X-Access-Token": TOKEN,
        "Org-Code": ORG_CODE,
        "User-Agent": "Mobile-Android",
        "Accept": "application/json"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        if response.status_code == 200:
            res_data = response.json()
            if res_data.get('status') == 'success':
                data = res_data.get('data', {})
                mpd = data.get('url')
                keys = data.get('key') # DRM key agar response mein hai
                return mpd, keys
            else:
                print(f"API Error Message: {res_data.get('message')}")
        else:
            print(f"Server Error: Status {response.status_code}")
    except Exception as e:
        print(f"Request Exception: {e}")
    
    return None, None

async def download_video(client, m, video_id, name):
    reply = await m.reply_text(f"🔎 Fetching details for: `{name}`")
    
    mpd_url, keys = get_mps_and_keys(video_id)
    
    if not mpd_url:
        await reply.edit("❌ Error: API se details nahi mil payi. Token check karein.")
        return

    await reply.edit(f"📥 Downloading: `{name}`\n\nQuality: 720p")
    
    output_filename = f"{name}.mp4"
    
    # yt-dlp command (Headers ke sath taki block na ho)
    cmd = (
        f'yt-dlp -f "bv[height<=720]+ba/b" '
        f'--add-header "User-Agent:Mobile-Android" '
        f'--add-header "X-Access-Token:{TOKEN}" '
        f'--allow-unplayable-format --no-check-certificate '
        f'-o "{output_filename}" "{mpd_url}"'
    )

    try:
        # Note: Agar keys ki zaroorat ho toh mp4decrypt yahan add karna hoga
        process = subprocess.run(cmd, shell=True)
        
        if os.path.exists(output_filename):
            dur = int(get_duration(output_filename))
            await reply.edit(f"📤 Uploading: `{name}`")
            await client.send_video(
                chat_id=m.chat.id,
                video=output_filename,
                caption=f"✅ **{name}**",
                duration=dur,
                supports_streaming=True,
                progress=progress_bar,
                progress_args=(reply, time.time())
            )
            os.remove(output_filename)
            await reply.delete()
        else:
            await reply.edit("❌ Download failed. MPD protected ho sakta hai.")
    except Exception as e:
        await reply.edit(f"❌ Error: {str(e)}")

# --- Bot Handlers (Example) ---
# Yahan aap apne purane Pyrogram filters laga sakte hain jo 'download_video' ko call karein.
