# Migration Summary: Dropbox → Google Drive

## What Changed

### ✅ Completed Changes

| File | Change | Status |
|------|--------|--------|
| `requirements.txt` | Removed Dropbox, added Google Drive dependencies | ✅ Done |
| `google_drive_fetch.py` | **NEW** - Google Drive integration with recycling logic | ✅ Created |
| `auto_pipeline.py` | Updated to use Google Drive instead of Dropbox | ✅ Updated |
| `daily_publisher.py` | Added recycling logic + move to Published_Videos folder | ✅ Updated |
| `.env.example` | **NEW** - Google Drive credentials template | ✅ Created |
| `README.md` | Updated with Google Drive setup instructions | ✅ Updated |
| `GOOGLE_DRIVE_SETUP.md` | **NEW** - Detailed step-by-step setup guide | ✅ Created |

---

## Key Features Added

### 1. Smart Video Recycling with FAIR ROTATION ♻️
When all videos are published, the bot automatically recycles **in order**:
- **NOT** just repeating the same first video over and over
- Cycles through ALL videos fairly (video_1 → video_2 → video_3 → video_1...)
- Uses `published_videos.json` chronological order for rotation
- No gaps in your posting schedule
- Complete fairness: every video gets equal chance to be re-published

**Example:**
```
Run 1-3: Publish new videos (video_1, video_2, video_3)
Run 4:   All published! Recycle video_1 (oldest)
Run 5:   Recycle video_2
Run 6:   Recycle video_3
Run 7:   Cycle repeats - Recycle video_1
...and so on
```

### 2. Google Drive Integration
- **15GB free storage** (vs Dropbox's 2GB)
- **Service Account** authentication (no token expiration)
- **Faster downloads** with progress tracking
- **Better reliability** for automation

### 3. Published Videos Management
- Videos moved to `Published_Videos/` folder after publishing
- Complete history tracked in `published_videos.json`
- Recycled videos marked with `"recycled": true` flag

---

## Migration Steps

### 1. Download `published_videos.json` from GitHub (Important!)

Before making changes, download your publishing history:

```bash
# Option A: Download from GitHub UI
1. Go to your repository on GitHub
2. Click on `published_videos.json`
3. Click "Raw" button
4. Save as `published_videos.json` locally

# Option B: Use GitHub CLI
gh repo view --json published_videos.json
```

**Why?** This file contains your publishing history and prevents re-uploading the same videos.

### 2. Set Up Google Drive

Follow the complete guide: **[GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md)**

Quick summary:
1. Create Google Cloud Project
2. Enable Google Drive API
3. Create Service Account
4. Download JSON key file
5. Create Google Drive folder
6. Share folder with service account
7. Upload videos to Google Drive

### 3. Update GitHub Secrets

Go to: **Settings → Secrets and variables → Actions**

#### Add these new secrets:
| Secret | Example Value |
|--------|---------------|
| `GOOGLE_SERVICE_ACCOUNT_KEY` | `{ "type": "service_account", ... }` (entire JSON) |
| `GOOGLE_DRIVE_FOLDER_ID` | `1ABC123xyz456DEF` |

#### Keep these existing secrets:
- `FACEBOOK_APP_ID`
- `FACEBOOK_APP_SECRET`
- `FACEBOOK_ACCESS_TOKEN`
- `FACEBOOK_PAGE_ID`
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_ACCOUNT_ID`
- `THREADS_ACCESS_TOKEN`
- `THREADS_USER_ID`
- `POLLINATIONS_API_KEY`

#### Optional: Remove these (no longer needed):
- `DROPBOX_APP_KEY`
- `DROPBOX_APP_SECRET`
- `DROPBOX_REFRESH_TOKEN`

### 4. Upload `published_videos.json` to Repository

To maintain your publishing history:

```bash
# Copy the file to your repo root
cp /path/to/downloaded/published_videos.json .

# Commit and push
git add published_videos.json
git commit -m "Restore publishing history"
git push origin main
```

Or upload via GitHub UI:
1. Go to repository
2. Click **Add file** → **Upload files**
3. Drag `published_videos.json`
4. Commit changes

### 5. Test Locally (Optional but Recommended)

```bash
# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your credentials
# - GOOGLE_SERVICE_ACCOUNT_KEY
# - GOOGLE_DRIVE_FOLDER_ID

# Test Google Drive connection
python google_drive_fetch.py

# Test full pipeline
python auto_pipeline.py
```

### 6. Test GitHub Actions

1. Go to **Actions** tab
2. Click on the workflow
3. Click **Run workflow**
4. Monitor the logs for any errors

---

## File Structure After Migration

```
Reena Veloria/
├── .env.example              # NEW - Template for environment variables
├── .env                      # Local only (not committed)
├── credentials/
│   └── service_account.json  # Local only (not committed)
├── google_drive_fetch.py     # NEW - Google Drive integration
├── auto_pipeline.py          # UPDATED - Uses Google Drive
├── daily_publisher.py        # UPDATED - Recycling logic
├── process_videos.py         # No change
├── published_videos.json     # History (upload from backup)
├── Videos/                   # Downloaded videos (temporary)
├── Processed_Videos/         # Processed videos (temporary)
└── Published_Videos/         # Published videos (archive)
```

---

## Behavior Changes

### Before (Dropbox)
```
Dropbox → Download → Process → Publish → Done
❌ Stops when all videos are published
```

### After (Google Drive)
```
Google Drive → Download → Process → Publish → Archive
✅ Recycles from beginning when all videos are published
✅ Moves published videos to Published_Videos/
✅ Tracks recycling in published_videos.json
```

---

## Troubleshooting

### Issue: "No videos found"
- ✅ Verify `GOOGLE_DRIVE_FOLDER_ID` is correct
- ✅ Ensure service account has access to the folder
- ✅ Check that videos are uploaded

### Issue: "Permission denied"
- ✅ Re-share the folder with the service account email
- ✅ Verify the service account email is correct

### Issue: "Invalid JSON key"
- ✅ Ensure the JSON file is complete (not truncated)
- ✅ If pasting to GitHub Secrets, include all characters

### Issue: "Video already published"
- ✅ This is normal! The bot will recycle it
- ✅ Check `published_videos.json` for history

---

## Benefits of Migration

| Feature | Dropbox | Google Drive |
|---------|---------|--------------|
| Free Storage | 2GB | 15GB |
| Token Expiry | Yes (4 hours) | No (Service Account) |
| Download Speed | Medium | Fast |
| Reliability | Good | Excellent |
| YouTube Integration | No | Yes |
| API Rate Limits | Strict | Generous |

---

## Next Steps

1. ✅ Complete Google Drive setup
2. ✅ Update GitHub Secrets
3. ✅ Upload `published_videos.json` backup
4. ✅ Test the workflow
5. ✅ Monitor first automated run

---

## Need Help?

- **Setup Guide**: See [GOOGLE_DRIVE_SETUP.md](GOOGLE_DRIVE_SETUP.md)
- **Google Cloud Console**: https://console.cloud.google.com
- **GitHub Actions Logs**: Check the **Actions** tab for errors

---

**Migration complete!** 🎉 Your bot now runs on Google Drive with smart recycling.
