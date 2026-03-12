# 🎬 Social Media Video Automation Pipeline

Automated video processing and social media publishing pipeline. Fetches videos from Dropbox, upscales them, removes watermarks, and publishes to multiple social media platforms.

## 🚀 Features

- **GitHub Actions Automation**: Runs 3 times a day automatically
- **Dropbox Integration**: Automatically fetch videos from your Dropbox folder
- **Smart Processing**: Only processes new videos, skips already processed ones
- **Video Processing**:
  - Upscale to 1080x1920 (vertical format for Reels/Shorts/TikTok)
  - Watermark removal (bottom-right corner)
  - Keeps original audio
- **Multi-Platform Upload**:
  - Instagram Reels & Stories
  - Facebook Reels & Stories
  - Threads
  - YouTube Shorts

## 🔄 Automation Workflow

```
GitHub Actions (3x daily)
        ↓
Check Dropbox /luzara ross
        ↓
New video found?
   ├─ YES → Download → Process → Upload → Mark as published
   └─ NO  → Exit (nothing to do)
```

## 📋 Prerequisites

1. **Python 3.8+**
2. **FFmpeg** installed and in PATH
3. **Dropbox App** with API access
4. **Social Media API Credentials** (Instagram, Facebook, YouTube, etc.)

## 🔧 Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Install FFmpeg

**Windows:**
```bash
# Using winget
winget install FFmpeg

# Or download from https://ffmpeg.org/download.html
```

**Linux:**
```bash
sudo apt install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

### 3. Configure Dropbox (ONE TIME SETUP FOR AUTOMATION)

**Step A: Create Dropbox App**
1. Go to [Dropbox App Console](https://www.dropbox.com/developers/apps)
2. Click "Create app"
3. Choose:
   - **Scoped access** (not API generation)
   - **Full Dropbox** access
4. Name your app and create it

**Step B: Get App Key and Secret**
1. In your app settings, find:
   - **App key** (copy to `.env` as `DROPBOX_APP_KEY`)
   - **App secret** (copy to `.env` as `DROPBOX_APP_SECRET`)

**Step C: Generate Refresh Token (NEVER EXPIRES)**
1. Run the token generator:
   ```bash
   py generate_dropbox_token.py
   ```
2. Open the URL it gives you
3. Authorize the app
4. Copy the authorization code
5. Paste it back in the terminal
6. Copy the `DROPBOX_REFRESH_TOKEN` it gives you
7. Add to `.env`:
   ```env
   DROPBOX_APP_KEY=your_app_key
   DROPBOX_APP_SECRET=your_app_secret
   DROPBOX_REFRESH_TOKEN=the_refresh_token_you_just_got
   DROPBOX_ACCESS_TOKEN=the_access_token_you_just_got
   DROPBOX_FOLDER=/luzara ross
   ```

**That's it! The refresh token never expires, so your automation will run forever.**

### 4. Set Up GitHub Actions (For Cloud Automation)

**Step A: Push code to GitHub**
```bash
git add .
git commit -m "Setup video automation"
git push
```

**Step B: Add GitHub Secrets**
1. Go to your GitHub repository
2. Click **Settings** → **Secrets and variables** → **Actions**
3. Click **New repository secret**
4. Add all secrets from `.github/SECRETS_SETUP.md`

**Required secrets:**
- `DROPBOX_APP_KEY`
- `DROPBOX_APP_SECRET`
- `DROPBOX_REFRESH_TOKEN`
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_ACCOUNT_ID`
- `FACEBOOK_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`
- `THREADS_ACCESS_TOKEN`
- `THREADS_USER_ID`
- `POLLINATIONS_API_KEY`

**Step C: Workflow runs automatically**
- Runs 3 times a day (8:00 AM, 4:00 PM, 12:00 AM UTC)
- You can also trigger manually from **Actions** tab

### 5. Configure Social Media Credentials

Edit the `.env` file with your API credentials:

```env
# Instagram
INSTAGRAM_ACCESS_TOKEN=
INSTAGRAM_ACCOUNT_ID=

# Facebook
FACEBOOK_ACCESS_TOKEN=
FACEBOOK_PAGE_ID=

# YouTube
YT_CLIENT_ID=
YT_CLIENT_SECRET=
YT_REFRESH_TOKEN=

# Threads
THREADS_ACCESS_TOKEN=
THREADS_USER_ID=

# AI Caption Generation
POLLINATIONS_API_KEY=
AI_MODEL=openai
```

## 📁 Folder Structure

```
.
├── Videos/                 # Input folder (videos from Dropbox)
├── Processed_Videos/       # Processed videos (upscaled, watermark removed)
├── Published_Videos/       # Already published videos
├── dropbox_fetch.py        # Dropbox integration
├── process_videos.py       # Video processing (upscale + delogo)
├── daily_publisher.py      # Social media uploader
├── auto_pipeline.py        # Main automation script
├── .env                    # Environment variables (API keys)
└── requirements.txt        # Python dependencies
```

## 🎯 Usage

### GitHub Actions (Automated - Recommended)

Once set up, the workflow runs automatically **3 times a day**:
- **8:00 AM UTC**
- **4:00 PM UTC**
- **12:00 AM UTC**

**Workflow:**
1. Add video to Dropbox `/luzara ross` folder
2. GitHub Actions will automatically:
   - Download the video
   - Process it (upscale + watermark removal)
   - Upload to all social media platforms
   - Mark as published

### Manual Local Run

Run the complete pipeline (Dropbox → Process → Upload):

```bash
python auto_pipeline.py
```

### Individual Steps

**Fetch from Dropbox only:**
```bash
python dropbox_fetch.py
```

**Process videos only:**
```bash
python process_videos.py
```

**Publish to social media only:**
```bash
python daily_publisher.py
```

**Upload specific video to Facebook:**
```bash
python upload_facebook_only.py path/to/video.mp4
```

## ⚙️ Customization

### Watermark Position

Edit `process_videos.py` to adjust watermark removal area:

```python
# Adjust these values based on your watermark size/position
w_delogo = int(180 * (width / 720))  # Width of watermark area
h_delogo = int(80 * (height / 1280))  # Height of watermark area
```

### Output Resolution

Change the upscale resolution in `process_videos.py`:

```python
# Current: 1080x1920 (vertical format)
vf_filter = f"...scale=1080:1920:flags=spline..."
```

### Delete from Dropbox After Download

Set `delete_after_download=True` in `auto_pipeline.py`:

```python
downloaded = fetch_videos_from_dropbox(delete_after_download=True)
```

## 🔄 GitHub + Dropbox Workflow

1. **Push code to GitHub** (no videos in repo)
2. **Add videos to Dropbox** `/videos_to_process` folder
3. **Run pipeline** on your server/machine:
   ```bash
   python auto_pipeline.py
   ```
4. Videos are automatically:
   - Downloaded from Dropbox
   - Processed (upscaled + watermark removed)
   - Uploaded to all social media platforms
   - Moved to `Published_Videos/` folder

## 🛠️ Troubleshooting

### FFmpeg not found
Ensure FFmpeg is installed and in your system PATH.

### Dropbox connection error
Verify your `DROPBOX_ACCESS_TOKEN` is valid and hasn't expired.

### Upload failures
Check that all API tokens in `.env` are valid and haven't expired.

### Watermark not removed correctly
Adjust the watermark position/size parameters in `process_videos.py`.

## 📝 Notes

- Videos are kept in the `Videos/` folder after processing (not deleted from Dropbox by default)
- Already processed videos are tracked in `published_videos.json`
- Original audio is preserved (no music addition)
- Processing can take several minutes per video depending on length and quality

## 🚨 Important

- Keep your `.env` file private (add to `.gitignore`)
- Never commit API tokens to GitHub
- Test with a single video before running bulk operations
