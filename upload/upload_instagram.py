"""
Instagram Reels Upload - Using tmpfiles.org for Public URL
Uploads video to tmpfiles.org, then uses URL for Instagram API
"""

import os
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def upload_to_instagram(video_path, caption, is_story=False):
    """
    Upload video to Instagram via temporary public URL.
    Can be a Reel or a Story.
    
    Uses Instagram Graph API endpoints (NOT Facebook endpoints).
    """
    media_type = 'STORIES' if is_story else 'REELS'

    print("\n" + "=" * 60)
    print(f"📸 INSTAGRAM {media_type} UPLOAD STARTING")
    print("=" * 60)

    # Get Instagram credentials
    access_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')
    user_id = os.getenv('INSTAGRAM_ACCOUNT_ID')

    # Debug info (masked)
    def mask(s): return f"{s[:10]}...{s[-4:]}" if s and len(s) > 10 else ("PLACEHOLDER" if s == "***" else "MISSING")
    print(f"[instagram] User ID Provided: {user_id}")
    print(f"[instagram] Access Token: {mask(access_token)}")

    if not access_token:
        raise ValueError("❌ INSTAGRAM_ACCESS_TOKEN not set")
    
    if not user_id:
        raise ValueError("❌ INSTAGRAM_ACCOUNT_ID not set")

    # Validate token using Facebook Graph API (works with both EA and IG tokens)
    print("[instagram] 🔍 Validating access token via Facebook Graph API...")
    
    try:
        test_resp = requests.get(
            f"https://graph.facebook.com/v21.0/me",
            params={
                "fields": "id,name",
                "access_token": access_token
            },
            timeout=10
        )
        
        if test_resp.status_code == 200:
            test_data = test_resp.json()
            print(f"[instagram] ✅ Token is VALID (Facebook user: {test_data.get('name', 'N/A')})")
            
            # Resolve Instagram Business Account ID from connected Facebook Page
            print("[instagram] 🔍 Resolving Instagram Business Account...")
            accounts_resp = requests.get(
                f"https://graph.facebook.com/v21.0/me/accounts",
                params={
                    "fields": "id,name,instagram_business_account{id,username}",
                    "access_token": access_token
                },
                timeout=10
            )
            
            if accounts_resp.status_code == 200:
                accounts_data = accounts_resp.json().get('data', [])
                found = False
                for page in accounts_data:
                    ig_account = page.get('instagram_business_account')
                    if ig_account:
                        ig_id = ig_account.get('id')
                        ig_username = ig_account.get('username', 'N/A')
                        print(f"[instagram] ✅ Found Instagram Business Account: @{ig_username} (ID: {ig_id})")
                        if str(ig_id) != str(user_id):
                            print(f"[instagram] ⚠️  Account ID mismatch! Updating from {user_id} → {ig_id}")
                            user_id = ig_id
                        found = True
                        break
                
                if not found:
                    print(f"[instagram] ❌ No Instagram Business Account linked to any Facebook Page!")
                    print(f"[instagram] ⚠️  Make sure your Instagram is a Business/Creator account")
                    print(f"[instagram] ⚠️  and linked to your Facebook Page in Settings.")
                    raise Exception("No Instagram Business Account linked to Facebook Page")
            else:
                print(f"[instagram] ⚠️  Could not list pages: {accounts_resp.text[:200]}")
                print(f"[instagram] ⚠️  Proceeding with configured account ID: {user_id}")
        else:
            error_data = test_resp.json() if test_resp.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Invalid token')
            error_code = error_data.get('error', {}).get('code', 'Unknown')
            
            print(f"[instagram] ❌ Token INVALID!")
            print(f"[instagram] Error Code: {error_code}")
            print(f"[instagram] Error: {error_msg}")
            print(f"[instagram] ⚠️  SKIPPING Instagram upload")
            raise Exception(f"Instagram token invalid (Code {error_code}): {error_msg}")
            
    except requests.exceptions.RequestException as e:
        print(f"[instagram] ❌ Network error validating token: {e}")
        raise Exception(f"Instagram connection failed: {e}")
    
    print(f"[instagram] ✅ Instagram credentials validated successfully")
    
    # Check video file
    video_path_obj = Path(video_path)
    if not video_path_obj.exists():
        error_msg = f"❌ Video file not found: {video_path}"
        print(f"[instagram] {error_msg}")
        raise FileNotFoundError(error_msg)
    
    file_size_mb = video_path_obj.stat().st_size / (1024 * 1024)
    print(f"[instagram] ✅ Video file found: {video_path}")
    print(f"[instagram] Video size: {file_size_mb:.2f} MB")
    
    # Limit caption
    caption_limited = caption[:2200] if len(caption) > 2200 else caption
    print(f"[instagram] Caption length: {len(caption_limited)} characters")
    
    try:
        # Step 1: Upload to tmpfiles.org to get public URL
        print(f"[instagram] 📤 Step 1: Uploading to temporary hosting...")
        
        with open(video_path_obj, 'rb') as video_file:
            files = {'file': ('video.mp4', video_file, 'video/mp4')}
            temp_response = requests.post(
                'https://tmpfiles.org/api/v1/upload',
                files=files,
                timeout=180
            )
        
        if temp_response.status_code != 200:
            error_msg = f"Failed to upload to temporary hosting: {temp_response.status_code}"
            print(f"[instagram] ❌ {error_msg}")
            print(f"[instagram] Response: {temp_response.text[:200]}")
            raise Exception(error_msg)
        
        temp_data = temp_response.json()
        if temp_data.get('status') != 'success':
            error_msg = f"Temporary hosting failed: {temp_data}"
            print(f"[instagram] ❌ {error_msg}")
            raise Exception(error_msg)
        
        # tmpfiles.org returns URL in format: https://tmpfiles.org/12345
        # We need direct download link: https://tmpfiles.org/dl/12345
        temp_url = temp_data.get('data', {}).get('url', '')
        video_url = temp_url.replace('tmpfiles.org/', 'tmpfiles.org/dl/')
        
        print(f"[instagram] ✅ Temporary URL created: {video_url}")
        
        if not user_id or user_id == 'None' or user_id == '***':
             # Note: logic for '***' added to handle placeholders in logs
             pass

        # Step 2: Create Instagram container with video URL
        print(f"[instagram] 📦 Step 2: Creating Instagram {media_type} container...")
        
        # v21.0 or v18.0? The "new" one used v21.0
        container_url = f"https://graph.instagram.com/v21.0/{user_id}/media"
        container_params = {
            'media_type': media_type,
            'video_url': video_url,
            'access_token': access_token
        }
        
        if not is_story:
            container_params['caption'] = caption_limited
            container_params['share_to_feed'] = 'false'  # Post to Reels tab ONLY, not main grid
            container_params['thumb_offset'] = '5000' # Set thumbnail to 5 seconds in to avoid dark start
        
        container_response = requests.post(container_url, params=container_params, timeout=60)
        
        if container_response.status_code != 200:
            error_data = container_response.json() if container_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[instagram] ❌ Container creation failed: {error_msg}")
            print(f"[instagram] Full response: {container_response.text[:500]}")
            
            # Fallback to graph.facebook.com if graph.instagram.com fails
            print(f"[instagram] 🔄 Retrying with Facebook Graph API endpoint...")
            container_url = f"https://graph.facebook.com/v21.0/{user_id}/media"
            container_response = requests.post(container_url, params=container_params, timeout=60)
            
            if container_response.status_code != 200:
                error_data = container_response.json() if container_response.text else {}
                error_msg = error_data.get('error', {}).get('message', 'Unknown error')
                raise Exception(f"Instagram Container Error: {error_msg}")
        
        container_id = container_response.json().get('id')
        print(f"[instagram] ✅ Container created: {container_id}")
        
        # Step 3: Wait for processing
        print(f"[instagram] ⏳ Step 3: Waiting for video processing...")
        max_wait = 180 # Increased wait time
        waited = 0
        
        while waited < max_wait:
            # Check status on the same endpoint used for creation
            status_url = f"https://graph.instagram.com/v21.0/{container_id}"
            status_params = {
                'fields': 'status_code',
                'access_token': access_token
            }
            
            status_response = requests.get(status_url, params=status_params, timeout=30)
            
            # Fallback if status check fails on instagram.com
            if status_response.status_code != 200:
                status_url = f"https://graph.facebook.com/v21.0/{container_id}"
                status_response = requests.get(status_url, params=status_params, timeout=30)

            status_data = status_response.json()
            status_code = status_data.get('status_code', 'UNKNOWN')
            
            print(f"[instagram] Status: {status_code} (waited {waited}s)")
            
            if status_code == 'FINISHED':
                print(f"[instagram] ✅ Video processing complete!")
                break
            elif status_code == 'ERROR':
                error_msg = status_data.get('error_message', 'Video processing failed')
                print(f"[instagram] ❌ {error_msg}")
                raise Exception(error_msg)
            
            time.sleep(10)
            waited += 10
        
        if waited >= max_wait:
            error_msg = "Video processing timed out"
            print(f"[instagram] ❌ {error_msg}")
            raise Exception(error_msg)
        
        # Step 4: Publish
        print(f"[instagram] 📤 Step 4: Publishing to Instagram... (Adding 5s buffer)")
        time.sleep(5) # Small buffer because IG sometimes says FINISHED before it's actually ready
        
        publish_url = f"https://graph.instagram.com/v21.0/{user_id}/media_publish"
        publish_params = {
            'creation_id': container_id,
            'access_token': access_token
        }
        
        # Robust Retry Logic for Publishing
        max_publish_retries = 3
        publish_response = None
        
        for attempt in range(max_publish_retries):
            publish_response = requests.post(publish_url, params=publish_params, timeout=60)
            
            if publish_response.status_code == 200:
                break
            else:
                print(f"[instagram] ⚠️ Publish attempt {attempt+1} failed. Retrying...")
                time.sleep(10)
                
            # Fallback to facebook.com if instagram.com consistently fails
            if attempt == max_publish_retries - 1:
                publish_url = f"https://graph.facebook.com/v21.0/{user_id}/media_publish"
                publish_response = requests.post(publish_url, params=publish_params, timeout=60)

        if not publish_response or publish_response.status_code != 200:
            error_data = publish_response.json() if publish_response and publish_response.text else {}
            error_msg = error_data.get('error', {}).get('message', 'Unknown error')
            print(f"[instagram] ❌ Publish failed after retries: {error_msg}")
            raise Exception(f"Instagram Publish Error: {error_msg}")
        
        media_id = publish_response.json().get('id')
        
        print(f"[instagram] ✅ SUCCESS! Video published to Instagram!")
        print(f"[instagram] Media ID: {media_id}")
        print(f"[instagram] Check your Instagram profile to see the post!")
        print("=" * 60)
        
        return {
            'id': media_id,
            'platform': 'instagram',
            'status': 'success'
        }
        
    except Exception as e:
        print(f"[instagram] ❌ ERROR!")
        print(f"[instagram] {str(e)}")
        print("=" * 60)
        raise

if __name__ == '__main__':
    video_file = Path('ielts_short.mp4')
    if video_file.exists():
        try:
            result = upload_to_instagram(str(video_file), "IELTS Band 9 Upgrade! #IELTS #English")
            print(f"\n✅ Success! Result: {result}")
        except Exception as e:
            print(f"\n❌ Failed: {e}")
    else:
        print(f"❌ Video not found: {video_file}")
