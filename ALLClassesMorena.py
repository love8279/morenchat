import os
import re
import time
import asyncio
import requests
import subprocess
from math import ceil
from pyrogram import Client, filters
from pyrogram.types import Message
from utils import progress_bar

# --- CONFIGURATION (Aapka Naya Token) ---
TOKEN = "EyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTI4NzE5MzEyLCJvcmdJZCI6NzYzMzIwLCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTgyNzkwNDk1NjgiLCJuYW1lIjoiTG92ZWt1c2giLCJlbWFpbCI6ImVhM2U0NjNkOWM5NjQ0YzJiZGE1ZDFiNWNkZjE5NTkzQGdtYWlsLmNvbSIsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjoiRU4iLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpc0RpeSI6dHJ1ZSwibG9naW5WaWEiOiJPdHAiLCJmaW5nZXJwcmludElkIjoiODQ3MTU0MjAzMzYyNDMwN2IwMzUyOTZiZThhOWIxMDIiLCJpYXQiOjE3Njc0OTk0MTQsImV4cCI6MTc2ODEwNDIxNH0.ia_YuAJaftl74ZQQT9cqi4fYyMhUsOwgHoJ7Vt1SQjRiMIUQFXOjCz2iu7nwLcY_"
ORG_CODE = "UIEVJH"

def get_duration(filename):
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        return float(result.stdout)
    except:
        return 0

def get_mps_and_keys(video_url):
    """
    Agar link m3u8 hai toh direct return karega, 
    agar videoId hai toh API se fetch karega.
    """
    if "master.m3u8" in video_url or ".m3u8" in video_url:
        return video_url, None
    
    video_id = video_url
    if "videoId=" in str(video_url):
        video_id = video_url.split("videoId=")[-1].split("&")[0]

    api_url = f"https://api.classplusapp.com/v2/videos/get-video-details?videoId={video_id}"
    headers = {
        "X-Access-Token": TOKEN,
        "Org-Code": ORG_CODE,
        "User-Agent": "Mobile-Android"
    }

    try:
        response = requests.get(api_url, headers=headers, timeout=15)
        if response.status_code == 200:
            data = response.json().get('data', {})
            return data.get('url'), data.get('key')
    except:
        pass
    return None, None

# --- Main Download & Split Logic ---
async def download_and_process(client, m, video_url, name):
    reply = await m.reply_text(f"🚀 **Starting:** `{name}`")
    
    # 1. Fetch Details
    mpd_url, keys = get_mps_and_keys(video_url)
    if not mpd_url:
        mpd_url = video_url # Fallback if API fails but URL is direct
    
    clean_name = re.sub(r'[\\/*?:"<>|]', "", name)
    filename = f"{clean_name}.mp4"

    # 2. Download with Headers
    # Isse "moov atom not found" error kam aayega
    cmd = (
        f'yt-dlp -f "bestvideo[height<=720]+bestaudio/best" '
        f'--add-header "User-Agent:Mobile-Android" '
        f'--add-header "X-Access-Token:{TOKEN}" '
        f'--no-check-certificate --merge-output-format mp4 '
        f'--fixup force -o "{filename}" "{mpd_url}"'
    )
    
    await reply.edit(f"📥 **Downloading...**\n`{name}`")
    process = subprocess.run(cmd, shell=True)

    if not os.path.exists(filename) or os.path.getsize(filename) == 0:
        await reply.edit("❌ **Download Failed!**\nLink expire ho gaya hai ya block hai.")
        return

    # 3. Handle Large Files (Splitting)
    size_mb = os.path.getsize(filename) / (1024 * 1024)
    if size_mb > 2000:
        await reply.edit("✂️ **File too large, splitting into parts...**")
        # Yahan aapka purana split_large_video function call ho sakta hai
        # Abhi ke liye hum simple upload kar rahe hain
    
    # 4. Final Upload
    dur = int(get_duration(filename))
    await reply.edit(f"📤 **Uploading...**\n`{name}`")
    
    try:
        await client.send_video(
            chat_id=m.chat.id,
            video=filename,
            caption=f"✅ **{name}**",
            duration=dur,
            supports_streaming=True,
            progress=progress_bar,
            progress_args=(reply, time.time())
        )
    except Exception as e:
        await reply.edit(f"❌ **Upload Error:** {str(e)}")
    
    if os.path.exists(filename):
        os.remove(filename)
    await reply.delete()

# --- Baki Bot Handlers Yahan Aayenge ---
