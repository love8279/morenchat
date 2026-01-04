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

# --- CONFIGURATION ---
TOKEN = "EyJhbGciOiJIUzM4NCIsInR5cCI6IkpXVCJ9.eyJpZCI6MTI4NzE5MzEyLCJvcmdJZCI6NzYzMzIwLCJ0eXBlIjoxLCJtb2JpbGUiOiI5MTgyNzkwNDk1NjgiLCJuYW1lIjoiTG92ZWt1c2giLCJlbWFpbCI6ImVhM2U0NjNkOWM5NjQ0YzJiZGE1ZDFiNWNkZjE5NTkzQGdtYWlsLmNvbSIsImlzRmlyc3RMb2dpbiI6dHJ1ZSwiZGVmYXVsdExhbmd1YWdlIjoiRU4iLCJjb3VudHJ5Q29kZSI6IklOIiwiaXNJbnRlcm5hdGlvbmFsIjowLCJpc0RpeSI6dHJ1ZSwibG9naW5WaWEiOiJPdHAiLCJmaW5nZXJwcmludElkIjoiODQ3MTU0MjAzMzYyNDMwN2IwMzUyOTZiZThhOWIxMDIiLCJpYXQiOjE3Njc0OTk0MTQsImV4cCI6MTc2ODEwNDIxNH0.ia_YuAJaftl74ZQQT9cqi4fYyMhUsOwgHoJ7Vt1SQjRiMIUQFXOjCz2iu7nwLcY_"
ORG_CODE = "UIEVJH"

def get_duration(filename):
    try:
        result = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                 "format=duration", "-of",
                                 "default=noprint_wrappers=1:nokey=1", filename],
            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        return float(result.stdout)
    except:
        return 0

def fetch_drm_key(video_url):
    """DRM Protected videos ke liye KID:KEY fetch karna"""
    try:
        if "/drm/" not in video_url:
            return None
        # URL se videoId nikalna
        video_id = video_url.split("/drm/")[1].split("/")[0]
        api_url = f"https://api.classplusapp.com/v2/videos/get-video-details?videoId={video_id}"
        headers = {"X-Access-Token": TOKEN, "Org-Code": ORG_CODE, "User-Agent": "Mobile-Android"}
        
        response = requests.get(api_url, headers=headers, timeout=10).json()
        if response.get('status') == 'success':
            return response.get('data', {}).get('key')
    except Exception:
        pass
    return None

async def download_handler(client, m, video_url, name):
    reply = await m.reply_text(f"🔎 **Analyzing:** `{name}`")
    
    clean_name = re.sub(r'[\\/*?:"<>|]', "", name)
    output_file = f"{clean_name}.mp4"
    
    # 1. DRM Check
    is_drm = "/drm/" in video_url
    drm_key = None
    
    if is_drm:
        await reply.edit("🔐 **DRM Protected!** Fetching Decryption Key...")
        drm_key = fetch_drm_key(video_url)
        if not drm_key:
            await reply.edit("❌ **Error:** DRM Key nahi mil payi. Link expired ya token invalid hai.")
            return

    # 2. Build yt-dlp Command
    if is_drm:
        # DRM Decryption Command
        cmd = (
            f'yt-dlp --allow-unplayable-formats --fixup warn '
            f'--add-header "X-Access-Token:{TOKEN}" '
            f'--add-header "Org-Code:{ORG_CODE}" '
            f'--decryption-key "{drm_key}" '
            f'-o "{output_file}" "{video_url}"'
        )
    else:
        # Normal Download (Nursing Batch)
        cmd = (
            f'yt-dlp -f "bestvideo[height<=720]+bestaudio/best" '
            f'--no-check-certificate --merge-output-format mp4 '
            f'-o "{output_file}" "{video_url}"'
        )

    await reply.edit(f"📥 **Downloading:** `{name}`")
    
    try:
        subprocess.run(cmd, shell=True)
        
        if os.path.exists(output_file) and os.path.getsize(output_file) > 1000:
            dur = int(get_duration(output_file))
            await reply.edit(f"📤 **Uploading:** `{name}`")
            
            await client.send_video(
                chat_id=m.chat.id,
                video=output_file,
                caption=f"✅ **{name}**",
                duration=dur,
                supports_streaming=True,
                progress=progress_bar,
                progress_args=(reply, time.time())
            )
            os.remove(output_file)
            await reply.delete()
        else:
            await reply.edit("❌ **Failed:** File download nahi hui. (Possible Expiry or Block)")
            
    except Exception as e:
        await reply.edit(f"⚠️ **Error:** {str(e)}")

# Note: Purane bot handlers yahan call honge
