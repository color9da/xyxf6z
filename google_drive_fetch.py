"""
Google Drive Integration Module
Fetch videos from a specific Google Drive folder for processing.
Uses Google Drive API v3 with service account credentials.
"""
import os
import json
import sys
import tempfile
from pathlib import Path
from dotenv import load_dotenv
from googleapiclient.http import MediaIoBaseDownload

if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

load_dotenv()

# Google Drive credentials
GOOGLE_DRIVE_FOLDER_ID = os.getenv("GOOGLE_DRIVE_FOLDER_ID")
GOOGLE_SERVICE_ACCOUNT_KEY = os.getenv("GOOGLE_SERVICE_ACCOUNT_KEY")  # Path to JSON key file
LOCAL_INPUT_DIR = os.getenv("LOCAL_INPUT_DIR", "Videos")

PUBLISHED_LOG = "published_videos.json"


def get_published_videos():
    """Get list of already published video names."""
    if os.path.exists(PUBLISHED_LOG):
        with open(PUBLISHED_LOG, 'r', encoding='utf-8') as f:
            try:
                data = json.load(f)
                # Extract video names from the log
                return [item.get('video_name', '') for item in data]
            except json.JSONDecodeError:
                return []
    return []


def get_drive_service():
    """Initialize and return Google Drive API client."""
    try:
        from google.oauth2 import service_account
        from googleapiclient.discovery import build

        SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

        if not GOOGLE_SERVICE_ACCOUNT_KEY:
            raise ValueError("GOOGLE_SERVICE_ACCOUNT_KEY not set")

        # Check if it's a file path or JSON content
        if os.path.exists(GOOGLE_SERVICE_ACCOUNT_KEY):
            # It's a file path
            creds = service_account.Credentials.from_service_account_file(
                GOOGLE_SERVICE_ACCOUNT_KEY, scopes=SCOPES)
            service = build('drive', 'v3', credentials=creds)
            print("Google Drive initialized with Service Account file")
            return service
        elif GOOGLE_SERVICE_ACCOUNT_KEY.strip().startswith('{'):
            # It's JSON content - write to temp file
            temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
            temp_file.write(GOOGLE_SERVICE_ACCOUNT_KEY)
            temp_file.close()

            creds = service_account.Credentials.from_service_account_file(
                temp_file.name, scopes=SCOPES)
            service = build('drive', 'v3', credentials=creds)
            print("Google Drive initialized with Service Account JSON")

            # Clean up temp file after credentials are loaded
            os.unlink(temp_file.name)
            return service
        else:
            raise ValueError("Google Service Account key is invalid")

    except ImportError as e:
        print(f"Installing required Google Drive libraries...")
        import subprocess
        subprocess.check_call([sys.executable, "-m", "pip", "install", "google-auth", "google-auth-oauthlib", "google-auth-httplib2", "google-api-python-client"])
        return get_drive_service()
    except Exception as e:
        print(f"Error initializing Google Drive: {e}")
        return None


def list_drive_videos(service):
    """List all video files in the Google Drive folder."""
    if not service:
        return []

    try:
        # Query files in the folder with video MIME types
        query = f"'{GOOGLE_DRIVE_FOLDER_ID}' in parents and trashed=false"
        video_mime_types = [
            "video/mp4",
            "video/quicktime",
            "video/x-msvideo",
            "video/x-matroska"
        ]

        videos = []
        for mime_type in video_mime_types:
            query_with_mime = f"{query} and mimeType contains '{mime_type}'"
            results = service.files().list(
                q=query_with_mime,
                fields="files(id, name, size, mimeType)",
                spaces='drive'
            ).execute()

            videos.extend(results.get('files', []))

        # Sort by name for consistent ordering
        videos.sort(key=lambda x: x.get('name', ''))
        return videos
    except Exception as e:
        print(f"Google Drive API error: {e}")
        return []


def download_video(service, file_info, local_path):
    """Download a video from Google Drive to local storage."""
    try:
        request = service.files().get_media(fileId=file_info['id'])

        with open(local_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while done is False:
                status, done = downloader.next_chunk()
                print(f"  Download progress: {int(status.progress() * 100)}%")

        print(f"Downloaded: {file_info['name']}")
        return True
    except Exception as e:
        print(f"Failed to download {file_info['name']}: {e}")
        return False


def fetch_one_video_from_drive():
    """
    Fetch ONE video from Google Drive for processing.
    Checks published_videos.json to skip already processed videos.
    If ALL videos are published, recycles from the beginning.

    Returns:
        Path to downloaded video or None
    """
    # Ensure local input directory exists
    Path(LOCAL_INPUT_DIR).mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("FETCHING VIDEO FROM GOOGLE DRIVE")
    print("=" * 60)

    # Get list of already published videos
    published = get_published_videos()
    print(f"Already published: {len(published)} video(s)")
    if published:
        for vid in published[:3]:  # Show first 3
            print(f"  - {vid}")
        if len(published) > 3:
            print(f"  ... and {len(published) - 3} more")

    if not GOOGLE_DRIVE_FOLDER_ID:
        print("Error: GOOGLE_DRIVE_FOLDER_ID not set in .env")
        return None

    service = get_drive_service()
    if not service:
        return None

    videos = list_drive_videos(service)

    if not videos:
        print("No videos found in Google Drive folder.")
        return None

    print(f"\nFound {len(videos)} video(s) in Google Drive.")

    # Track if we tried and failed to download any video
    download_attempts = 0
    download_failures = 0
    all_are_published = True
    published_videos_list = []

    # Find first video NOT in published list
    for video_info in videos:
        video_name = video_info['name']

        # Check if already published
        if video_name in published:
            print(f"Skipping {video_name} - already published")
            # Track all published videos for fair rotation
            published_videos_list.append(video_info)
            continue

        # Found an unpublished video
        all_are_published = False

        # Download this video
        download_attempts += 1
        local_path = os.path.join(LOCAL_INPUT_DIR, video_name)
        if download_video(service, video_info, local_path):
            print(f"\n✅ Selected: {video_name}")
            return local_path
        else:
            download_failures += 1
            print(f"⚠️  Download failed, trying next video...")

    # If we tried to download videos but all failed
    if download_attempts > 0 and download_failures == download_attempts:
        print(f"\n❌ Failed to download all {download_attempts} video(s). Check permissions.")
        return None

    # All videos are published - recycle using FAIR ROTATION
    if all_are_published and published_videos_list:
        print("\n⚠️  All videos have been published. Recycling with fair rotation...")

        # Build a mapping of video name -> last published timestamp
        # We want to find the video that was published LEAST recently (oldest)
        video_last_published = {}
        for entry in published:
            video_name = entry.get('video_name', '')
            if video_name:
                # Get the timestamp from metadata if available
                timestamp = entry.get('metadata', {}).get('published_at', '')
                # Store/update with the latest timestamp for this video
                video_last_published[video_name] = timestamp

        # Find unique video names from Drive folder
        drive_video_names = set(v['name'] for v in published_videos_list)

        # Find the video with the oldest (or missing) timestamp
        # Videos without timestamps are prioritized, then oldest first
        video_to_recycle_name = None
        oldest_timestamp = None

        for video_name in drive_video_names:
            if video_name not in video_last_published:
                # This video has no timestamp - prioritize it
                video_to_recycle_name = video_name
                break
            else:
                ts = video_last_published[video_name]
                if oldest_timestamp is None or ts < oldest_timestamp:
                    oldest_timestamp = ts
                    video_to_recycle_name = video_name

        # Fallback to first video if nothing found
        if not video_to_recycle_name:
            video_to_recycle_name = published_videos_list[0]['name']

        # Find the video info object
        video_to_recycle = None
        for vid_info in published_videos_list:
            if vid_info['name'] == video_to_recycle_name:
                video_to_recycle = vid_info
                break

        video_name = video_to_recycle['name']
        print(f"🔄 Re-publishing (fair rotation): {video_name}")

        local_path = os.path.join(LOCAL_INPUT_DIR, video_name)
        if download_video(service, video_to_recycle, local_path):
            print(f"\n✅ Selected (recycled): {video_name}")
            return local_path
        else:
            print(f"\n❌ Failed to download recycled video.")
            return None

    return None


if __name__ == "__main__":
    # Test the Google Drive connection
    fetch_one_video_from_drive()
