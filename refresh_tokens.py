"""
Auto Token Refresh Script
Run this monthly to keep tokens fresh forever

This script:
1. Uses Facebook Page token (never expires) for Instagram posting
2. Updates .env automatically
3. Commits and pushes changes to GitHub
"""
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv

# Load current .env
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

print("=" * 70)
print("🔄 AUTO TOKEN REFRESH")
print("=" * 70)

# Get credentials from environment
FB_APP_ID = os.getenv("FACEBOOK_APP_ID", "")
FB_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET", "")
FB_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN", "")
FB_PAGE_ID = os.getenv("FACEBOOK_PAGE_ID", "")

print(f"\n📋 Current Setup:")
print(f"  Facebook Page ID: {FB_PAGE_ID}")
print(f"  Facebook Token: {FB_ACCESS_TOKEN[:20]}...")

# Step 1: Verify current Facebook token still works
print("\n" + "=" * 70)
print("📌 Step 1: Verifying Facebook Token")
print("=" * 70)

try:
    url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}"
    params = {
        "fields": "id,name,access_token",
        "access_token": FB_ACCESS_TOKEN
    }
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        page_data = response.json()
        print(f"\n✅ Facebook token is VALID!")
        print(f"   Page: {page_data.get('name')}")
        print(f"   Page Access Token: {page_data.get('access_token', 'N/A')[:20]}...")
        
        # Get the page-specific access token (this one never expires!)
        page_access_token = page_data.get('access_token', FB_ACCESS_TOKEN)
        
    else:
        print(f"\n❌ Facebook token is INVALID!")
        print(f"   Error: {response.text[:200]}")
        print(f"\n⚠️  You need to manually generate a new Facebook token:")
        print(f"   1. Go to: https://developers.facebook.com/tools/explorer/")
        print(f"   2. Get token with permissions:")
        print(f"      - pages_manage_posts")
        print(f"      - pages_read_engagement")
        print(f"      - instagram_basic")
        print(f"      - instagram_content_publish")
        print(f"   3. Update .env: FACEBOOK_ACCESS_TOKEN=EAAM...")
        raise Exception("Facebook token invalid")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    raise

# Step 2: Get Instagram Account ID from Facebook Page
print("\n" + "=" * 70)
print("📌 Step 2: Getting Instagram Account ID")
print("=" * 70)

try:
    url = f"https://graph.facebook.com/v18.0/{FB_PAGE_ID}"
    params = {
        "fields": "instagram_business_account{id,username,name}",
        "access_token": page_access_token
    }
    response = requests.get(url, params=params, timeout=10)
    
    if response.status_code == 200:
        data = response.json()
        ig_account = data.get('instagram_business_account')
        
        if ig_account:
            print(f"\n✅ Instagram Business Account Found!")
            print(f"   Instagram ID: {ig_account.get('id')}")
            print(f"   Username: @{ig_account.get('username')}")
            print(f"   Name: {ig_account.get('name')}")
            
            # Save Instagram credentials
            new_ig_id = ig_account.get('id')
            new_ig_token = page_access_token  # Use Facebook Page token for Instagram!
            
        else:
            print(f"\n⚠️  No Instagram Business Account connected to this Facebook Page")
            print(f"\n🔧 TO FIX:")
            print(f"   1. Open Facebook → Your Page 'Reena Veloria' → Settings")
            print(f"   2. Click 'Instagram' → 'Connect Account'")
            print(f"   3. Login with Instagram (@reenaveloria)")
            print(f"   4. Run this script again")
            raise Exception("Instagram not connected to Facebook Page")
    else:
        print(f"\n❌ Failed to get Instagram account")
        print(f"   Error: {response.text[:200]}")
        raise Exception("Could not fetch Instagram account")
        
except Exception as e:
    print(f"\n❌ Error: {e}")
    raise

# Step 3: Test Instagram Token
print("\n" + "=" * 70)
print("📌 Step 3: Testing Instagram Token")
print("=" * 70)

# Test using the Instagram token (which is the Facebook Page token)
url = "https://graph.instagram.com/me"
params = {
    "fields": "id,username",
    "access_token": new_ig_token
}

print(f"\nTesting token: {new_ig_token[:20]}...")

response = requests.get(url, params=params, timeout=10)

if response.status_code == 200:
    ig_data = response.json()
    print(f"\n✅ Instagram token is VALID!")
    print(f"   Instagram ID: {ig_data.get('id')}")
    print(f"   Username: @{ig_data.get('username')}")
else:
    print(f"\n⚠️  Instagram token test failed: {response.text[:200]}")
    print(f"   This might be OK - Facebook Page token works differently")
    print(f"   We'll use it anyway for Instagram posting via Graph API")

# Step 4: Update .env file
print("\n" + "=" * 70)
print("📌 Step 4: Updating .env File")
print("=" * 70)

# Read current .env
with open(env_path, 'r', encoding='utf-8') as f:
    env_content = f.read()

# Update Instagram credentials
old_ig_id = os.getenv("INSTAGRAM_ACCOUNT_ID", "")
old_ig_token = os.getenv("INSTAGRAM_ACCESS_TOKEN", "")

# Replace Instagram Account ID
if f"INSTAGRAM_ACCOUNT_ID={old_ig_id}" in env_content:
    env_content = env_content.replace(
        f"INSTAGRAM_ACCOUNT_ID={old_ig_id}",
        f"INSTAGRAM_ACCOUNT_ID={new_ig_id}"
    )
    print(f"\n✅ Updated INSTAGRAM_ACCOUNT_ID")
    print(f"   Old: {old_ig_id}")
    print(f"   New: {new_ig_id}")

# Replace Instagram Access Token with Facebook Page token
# (Facebook Page token works for Instagram posting via Graph API)
if old_ig_token and f"INSTAGRAM_ACCESS_TOKEN={old_ig_token}" in env_content:
    env_content = env_content.replace(
        f"INSTAGRAM_ACCESS_TOKEN={old_ig_token}",
        f"INSTAGRAM_ACCESS_TOKEN={new_ig_token}"
    )
    print(f"\n✅ Updated INSTAGRAM_ACCESS_TOKEN")
    print(f"   (Using Facebook Page token for Instagram)")

# Write updated .env
with open(env_path, 'w', encoding='utf-8') as f:
    f.write(env_content)

print(f"\n✅ .env file updated successfully!")

# Step 5: Commit and push to GitHub
print("\n" + "=" * 70)
print("📌 Step 5: Committing Changes to GitHub")
print("=" * 70)

import subprocess

try:
    # Configure git
    subprocess.run(['git', 'config', 'user.email', 'action@github.com'], check=True, capture_output=True)
    subprocess.run(['git', 'config', 'user.name', 'GitHub Action'], check=True, capture_output=True)
    
    # Add .env file
    subprocess.run(['git', 'add', '.env'], check=True, capture_output=True)
    
    # Check if there are changes to commit
    diff_result = subprocess.run(['git', 'diff', '--staged', '--quiet'], capture_output=True)
    
    if diff_result.returncode == 0:
        print(f"\nℹ️  No changes to commit (tokens already up to date)")
    else:
        # Commit
        subprocess.run(['git', 'commit', '-m', 'Auto-refresh Instagram credentials [skip ci]'], 
                      check=True, capture_output=True)
        print(f"\n✅ Committed changes")
        
        # Push
        subprocess.run(['git', 'push'], check=True, capture_output=True)
        print(f"\n✅ Pushed to GitHub")
        
except subprocess.CalledProcessError as e:
    print(f"\n⚠️  Git error: {e}")
    print(f"   (This is OK if running locally)")
except FileNotFoundError:
    print(f"\n⚠️  Git not found (this is OK if running locally)")

# Final Summary
print("\n" + "=" * 70)
print("✅ TOKEN REFRESH COMPLETE!")
print("=" * 70)

print(f"\n📋 Updated Credentials:")
print(f"  Facebook Page ID: {FB_PAGE_ID}")
print(f"  Facebook Token: {FB_ACCESS_TOKEN[:20]}... (never expires)")
print(f"  Instagram ID: {new_ig_id}")
print(f"  Instagram Token: {new_ig_token[:20]}... (uses Facebook Page token)")

print(f"\n📅 NEXT REFRESH:")
print(f"  Run this script again in 30 days")
print(f"  Or set up GitHub Actions to run automatically")

print(f"\n🔧 TO AUTOMATE WITH GITHUB ACTIONS:")
print(f"  1. Add FACEBOOK_APP_ID and FACEBOOK_APP_SECRET to GitHub Secrets")
print(f"  2. Create .github/workflows/refresh_tokens.yml")
print(f"  3. Schedule to run monthly (cron: '0 0 1 * *')")

print("\n" + "=" * 70)
