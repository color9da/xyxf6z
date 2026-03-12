# ✅ GitHub Actions Robustness Checklist

## Pre-Deployment Checklist

### 1. Required GitHub Secrets (11 secrets)

**Dropbox (Required):**
- [ ] `DROPBOX_APP_KEY` = `cbhvns42d7eokwc`
- [ ] `DROPBOX_APP_SECRET` = `3jhfft733nq6dch`
- [ ] `DROPBOX_REFRESH_TOKEN` = `Uf0ci92sJVQAAAAAAAAAAXYS6AszCv8NmHNqlIPFwYTBOUcEH7jr9YvGya4JEn1H`
- [ ] `DROPBOX_ACCESS_TOKEN` = (copy from .env)

**Instagram (Required):**
- [ ] `INSTAGRAM_ACCESS_TOKEN` = (copy from .env)
- [ ] `INSTAGRAM_ACCOUNT_ID` = `26555057914080162`

**Facebook (Required):**
- [ ] `FACEBOOK_ACCESS_TOKEN` = (copy from .env)
- [ ] `FACEBOOK_PAGE_ID` = `1001822213016889`

**Threads (Required):**
- [ ] `THREADS_ACCESS_TOKEN` = (copy from .env)
- [ ] `THREADS_USER_ID` = `26063839556615988`

**AI Caption (Required):**
- [ ] `POLLINATIONS_API_KEY` = (copy from .env)

**YouTube (Optional):**
- [ ] `YT_CLIENT_ID` = (copy from .env)
- [ ] `YT_CLIENT_SECRET` = (copy from .env)
- [ ] `YT_REFRESH_TOKEN` = (copy from .env)

---

### 2. Files in Repository

**Core Files (Must Have):**
- [ ] `.env` (keep private, add to .gitignore)
- [ ] `auto_pipeline.py`
- [ ] `daily_publisher.py`
- [ ] `dropbox_fetch.py`
- [ ] `process_videos.py`
- [ ] `requirements.txt`
- [ ] `published_videos.json`
- [ ] `.github/workflows/auto_publish.yml`

**Upload Modules (Must Have):**
- [ ] `upload/upload_instagram.py`
- [ ] `upload/upload_facebook.py`
- [ ] `upload/upload_threads.py`
- [ ] `upload/upload_to_youtube.py`

**Documentation:**
- [ ] `README.md`
- [ ] `WORKFLOW.md`
- [ ] `DEPLOYMENT.md`

---

### 3. GitHub Actions Configuration

**Workflow Settings:**
- [ ] Runs on `ubuntu-latest`
- [ ] Python 3.11
- [ ] FFmpeg installed
- [ ] Timeout: 30 minutes
- [ ] Pip caching enabled

**Schedule:**
- [ ] 8:00 AM UTC
- [ ] 4:00 PM UTC
- [ ] 12:00 AM UTC

**Error Handling:**
- [ ] Checks for missing secrets
- [ ] Graceful failure on no videos
- [ ] Proper exit codes

---

### 4. Dropbox Setup

- [ ] App created at https://www.dropbox.com/developers/apps
- [ ] Full Dropbox access granted
- [ ] Refresh token generated (never expires)
- [ ] Folder `/luzara ross` exists in Dropbox
- [ ] Test video added to Dropbox folder

---

### 5. Testing Before Deployment

**Local Test:**
```bash
# Test Dropbox connection
py dropbox_fetch.py

# Test video processing
py process_videos.py Videos/your-test-video.mp4

# Test full pipeline
py auto_pipeline.py
```

**GitHub Actions Test:**
1. Push to GitHub
2. Go to Actions tab
3. Click "Auto Publish Videos"
4. Click "Run workflow"
5. Watch for errors in logs

---

## Robustness Features Implemented

### ✅ Error Handling

1. **Missing Secrets Detection**
   - Workflow checks all required secrets before running
   - Fails fast with clear error message

2. **Graceful "No Videos" Exit**
   - If no new videos in Dropbox, exits cleanly
   - No error, just informational message

3. **Timeout Protection**
   - 30-minute timeout prevents hanging
   - Failed runs don't block future runs

4. **Dependency Caching**
   - Pip cache speeds up subsequent runs
   - Reduces failure points from network issues

### ✅ FFmpeg Handling

- Installed via apt-get (reliable)
- Available in PATH for all steps
- Standard Ubuntu installation

### ✅ Git Operations

- Only commits `published_videos.json` (small file)
- Doesn't commit large video files
- Graceful handling if no changes

### ✅ Logging

- Clear console output
- Step-by-step progress
- Success/failure indicators

---

## Common Failure Points & Solutions

### ❌ "Missing secrets" Error

**Solution:** Add all required secrets to GitHub repository settings

### ❌ "No videos found"

**Not an error!** This is normal when Dropbox folder is empty or all videos processed.

### ❌ FFmpeg not found

**Solution:** Already handled in workflow - installs automatically

### ❌ Dependency installation fails

**Solution:** 
- Pip cache enabled
- Requirements.txt pinned to stable versions
- Network retry built into pip

### ❌ Upload fails for one platform

**Solution:** 
- Other platforms continue uploading
- Failure logged
- Video marked as partially published

### ❌ Token expired

**Solution:** 
- Dropbox refresh token never expires
- Other tokens: monitor and update when needed

---

## Monitoring

### Check Workflow Status

1. Go to GitHub repository
2. Click **Actions** tab
3. View recent runs
4. Click on any run for details

### Success Indicators

- ✅ Green checkmark
- ✅ "Pipeline completed successfully"
- ✅ All platforms show "true" in published_videos.json

### Failure Indicators

- ❌ Red X mark
- ❌ Error in logs
- ❌ Missing output files

---

## Maintenance

### Regular Tasks

- [ ] Check workflow runs weekly
- [ ] Monitor API token expiration (except Dropbox)
- [ ] Review published_videos.json for consistency
- [ ] Clean up old videos from Processed_Videos/

### Token Renewal

**Dropbox:** Never expires (refresh token)
**Instagram:** Check every 60 days
**Facebook:** Check every 60 days
**Threads:** Check every 60 days
**YouTube:** Check every 7 days (if used)

---

## Support

If workflow fails:

1. Check Actions logs for error message
2. Verify all secrets are present
3. Test locally with `py auto_pipeline.py`
4. Check Dropbox folder has videos
5. Review published_videos.json for already-processed videos

---

**Everything is configured for robust, failure-resistant automation!** 🎉
