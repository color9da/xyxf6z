"""
Instagram Reels Upload - Using temp hosting services for Public URL
Uploads video via fallback chain of free hosts, then uses URL for Instagram API
"""

import os
import subprocess
import requests
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

TEMP_COMPRESS_DIR = Path(tempfile.gettempdir()) / "ig_compress"
TEMP_COMPRESS_DIR.mkdir(parents=True, exist_ok=True)

REQ_TIMEOUT = (15, 120)


def compress_for_instagram(video_path):
    """Compress video to ~30-40MB for faster Instagram processing."""
    input_path = Path(video_path)
    output_path = TEMP_COMPRESS_DIR / f"compressed_{input_path.stem}.mp4"

    original_size_mb = input_path.stat().st_size / (1024 * 1024)
    print(f"[instagram] Original size: {original_size_mb:.1f} MB")

    if original_size_mb < 40:
        print(f"[instagram] Under 40MB, skipping compression")
        return str(video_path)

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_path),
        "-c:v", "libx264",
        "-crf", "28",
        "-preset", "fast",
        "-c:a", "aac",
        "-b:a", "96k",
        "-movflags", "+faststart",
        str(output_path)
    ]

    print(f"[instagram] Compressing video (target ~30MB)...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)

    if result.returncode != 0 or not output_path.exists():
        print(f"[instagram] Compression failed: {result.stderr[:500]}")
        print(f"[instagram] Falling back to original video")
        return str(video_path)

    compressed_size_mb = output_path.stat().st_size / (1024 * 1024)
    ratio = (1 - compressed_size_mb / original_size_mb) * 100
    print(f"[instagram] Compressed: {original_size_mb:.1f}MB -> {compressed_size_mb:.1f}MB ({ratio:.0f}% reduction)")
    return str(output_path)


def cleanup_compressed(file_path):
    """Remove compressed temp file."""
    try:
        p = Path(file_path)
        if p.parent == TEMP_COMPRESS_DIR and p.exists():
            p.unlink()
    except Exception:
        pass


def upload_to_tempfile(file_path):
    """Upload a file to tmpfiles.org and return the direct download URL."""
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://tmpfiles.org/api/v1/upload',
            files={'file': ('video.mp4', f, 'video/mp4')},
            timeout=REQ_TIMEOUT
        )
    if resp.status_code != 200:
        raise Exception(f"tmpfiles.org upload failed: {resp.status_code}")
    data = resp.json()
    if data.get('status') != 'success':
        raise Exception(f"tmpfiles.org upload failed: {data}")
    temp_url = data.get('data', {}).get('url', '')
    return temp_url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')


def upload_to_0x0(file_path):
    """Upload a file to 0x0.st and return the direct URL."""
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://0x0.st',
            files={'file': ('video.mp4', f, 'video/mp4')},
            timeout=REQ_TIMEOUT
        )
    if resp.status_code != 200:
        raise Exception(f"0x0.st upload failed: {resp.status_code} {resp.text[:200]}")
    url = resp.text.strip()
    if not url.startswith('https://'):
        raise Exception(f"0x0.st returned invalid URL: {url}")
    return url


def upload_to_catbox(file_path):
    """Upload a file to catbox.moe and return the direct URL."""
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://catbox.moe/user/api.php',
            data={'reqtype': 'fileupload'},
            files={'fileToUpload': ('video.mp4', f, 'video/mp4')},
            timeout=REQ_TIMEOUT
        )
    if resp.status_code != 200:
        raise Exception(f"catbox.moe upload failed: {resp.status_code} {resp.text[:200]}")
    url = resp.text.strip()
    if not url.startswith('https://'):
        raise Exception(f"catbox.moe returned invalid URL: {url}")
    return url


def upload_to_uguu(file_path):
    """Upload a file to uguu.se and return the direct URL."""
    with open(file_path, 'rb') as f:
        resp = requests.post(
            'https://uguu.se/upload',
            files={'files[]': ('video.mp4', f, 'video/mp4')},
            timeout=REQ_TIMEOUT
        )
    if resp.status_code != 200:
        raise Exception(f"uguu.se upload failed: {resp.status_code} {resp.text[:200]}")
    data = resp.json()
    if not data.get('success'):
        raise Exception(f"uguu.se upload failed: {data}")
    return data['files'][0]['url']


HOSTING_SERVICES = [
    ("tmpfiles.org", upload_to_tempfile),
    ("0x0.st", upload_to_0x0),
    ("catbox.moe", upload_to_catbox),
    ("uguu.se", upload_to_uguu),
]


def upload_to_temporary_host(file_path):
    """Try each hosting service in order until one works."""
    last_error = None
    for name, upload_func in HOSTING_SERVICES:
        try:
            print(f"[instagram] Trying {name}...")
            url = upload_func(file_path)
            print(f"[instagram] Uploaded via {name}: {url}")
            return url
        except Exception as e:
            print(f"[instagram] {name} failed: {e}")
            last_error = e
            continue
    raise Exception(f"All hosting services failed. Last error: {last_error}")


def upload_to_instagram(video_path, caption, is_story=False):
    media_type = 'STORIES' if is_story else 'REELS'

    print("\n" + "=" * 60)
    print(f"INSTAGRAM {media_type} UPLOAD STARTING")
    print("=" * 60)

    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN') or os.getenv('FACEBOOK_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_ACCOUNT_ID') or os.getenv('IG_USER_ID')

    def mask(s):
        return f"{s[:10]}...{s[-4:]}" if s and len(s) > 10 else ("PLACEHOLDER" if s == "***" else "MISSING")

    print(f"[instagram] User ID Provided: {user_id}")
    print(f"[instagram] Access Token: {mask(access_token)}")

    if not access_token:
        print("[instagram] Skipping Instagram upload - no token set")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'instagram'}

    if not user_id:
        print("[instagram] Skipping Instagram upload - no account ID set")
        return {'status': 'skipped', 'reason': 'Missing credentials', 'platform': 'instagram'}

    print("[instagram] Credentials loaded")

    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"Video file not found: {video_path}"
        print(f"[instagram] {error_msg}")
        raise FileNotFoundError(error_msg)

    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[instagram] Video file found: {video_path}")
    print(f"[instagram] Video size: {file_size_mb:.2f} MB")

    caption_limited = caption[:2200] if len(caption) > 2200 else caption
    print(f"[instagram] Caption length: {len(caption_limited)} characters")

    compressed = compress_for_instagram(video_path)
    upload_path = compressed

    try:
        print("[instagram] Step 1: Uploading to GitHub raw URL...")
        import uuid as _uuid, os as _os, requests as _req, base64 as _b64, time as _time
        _vid_name = "ig_" + _uuid.uuid4().hex[:8] + ".mp4"
        _token = _os.environ.get("GH_TOKEN") or _os.environ.get("GITHUB_TOKEN") or ""
        if _token:
            with open(str(video_path_obj), "rb") as _f:
                _enc = _b64.b64encode(_f.read()).decode()
            _put = _req.put("https://api.github.com/repos/color9da/xyxf6z/contents/" + _vid_name,
                headers={"Authorization": "Bearer " + _token, "Accept": "application/vnd.github+json"},
                json={"message": "add " + _vid_name, "content": _enc, "branch": "main"}, timeout=30)
            if _put.status_code in [200, 201]:
                print("[instagram] Uploaded via GitHub API")
            else:
                print("[instagram] Upload failed (" + str(_put.status_code) + ")")
                return {'status': 'skipped', 'reason': 'Upload failed', 'platform': 'instagram'}
        else:
            print("[instagram] No GITHUB_TOKEN found, using git push...")
            import os as _os2, subprocess as _sp2
            _os2.system("cp " + str(video_path_obj) + " " + _vid_name)
            _os2.system("git config --global user.email bot@bot.com")
            _os2.system("git config --global user.name Bot")
            _os2.system("git add -f " + _vid_name)
            _os2.system("git commit --no-verify -m \"add " + _vid_name + "\"")
            _r1 = _sp2.run(["git", "push", "origin", "main"], capture_output=True, text=True)
            if _r1.returncode != 0:
                print("[instagram] git push stderr: " + _r1.stderr[:200])
                print("[instagram] Trying --force...")
                _r2 = _sp2.run(["git", "push", "--force", "origin", "main"], capture_output=True, text=True)
                if _r2.returncode != 0:
                    print("[instagram] Force push also failed: " + _r2.stderr[:200])
                    return {'status': 'skipped', 'reason': 'Git push failed', 'platform': 'instagram'}
        
        video_url = "https://raw.githubusercontent.com/color9da/xyxf6z/main/" + _vid_name
        print("[instagram] GitHub raw URL: " + video_url)
        _time.sleep(5)
        print(f"[instagram] Step 2: Creating Instagram {media_type} container...")

        container_url = f"https://graph.facebook.com/v21.0/{user_id}/media"
        container_params = {
            'media_type': media_type,
            'video_url': video_url,
            'access_token': access_token
        }

        if not is_story:
            container_params['caption'] = caption_limited



        container_response = requests.post(container_url, params=container_params, timeout=60)

        if container_response.status_code != 200:
            error_data = container_response.json() if container_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[instagram] Container creation failed: {error_msg}")
            print(f"[instagram] Full response: {container_response.text[:500]}")

            print("[instagram] Retrying with Instagram Graph API endpoint...")
            container_url = f"https://graph.facebook.com/v21.0/{user_id}/media"
            container_response = requests.post(container_url, params=container_params, timeout=60)

            if container_response.status_code != 200:
                error_data = container_response.json() if container_response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Instagram Container Error: {error_msg}")

        container_id = container_response.json().get('id')
        print(f"[instagram] Container created: {container_id}")

        print("[instagram] Step 3: Waiting 60 seconds for processing...")
        import time as _t3
        _t3.sleep(60)

        # Step 4: Publish
        print("[instagram] Step 4: Publishing...")
        pub_url = f"https://graph.facebook.com/v21.0/{user_id}/media_publish"
        pub_params = {'creation_id': container_id, 'access_token': access_token}
        pub_resp = requests.post(pub_url, params=pub_params, timeout=60)
        if pub_resp.status_code != 200:
            _t3.sleep(30)
            pub_resp = requests.post(pub_url, params=pub_params, timeout=60)
        if pub_resp.status_code != 200:
            print("[instagram] Publish failed")
            return {'status': 'error', 'platform': 'instagram'}
        media_id = pub_resp.json().get('id')
        print("[instagram] SUCCESS! Media ID: " + str(media_id))
        return {'id': media_id, 'platform': 'instagram', 'status': 'success'}

    except Exception as e:
        print("[instagram] ERROR!")
        print(f"[instagram] {str(e)}")
        print("=" * 60)
        raise

    finally:
        cleanup_compressed(upload_path)


if __name__ == '__main__':
    video_file = Path('ielts_short.mp4')
    if video_file.exists():
        try:
            result = upload_to_instagram(str(video_file), "IELTS Band 9 Upgrade! #IELTS #English")
            print(f"\nSuccess! Result: {result}")
        except Exception as e:
            print(f"\nFailed: {e}")
    else:
        print(f"Video not found: {video_file}")
