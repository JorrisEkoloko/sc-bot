# Google Sheets OAuth Setup Guide

## Step 1: Use Your Existing Google Cloud Project ✅

You already have a project set up:

- **Project name**: sc-bot-1
- **Project ID**: sc-bot-1
- **Project number**: 420070245462

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Select project **sc-bot-1** from the dropdown

## Step 2: Enable Google Sheets API

1. In your project, go to **APIs & Services** > **Library**
2. Search for "Google Sheets API"
3. Click **Enable**

## Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure OAuth consent screen:

   - User Type: **External** (or Internal if you have Google Workspace)
   - App name: **Crypto Intelligence**
   - User support email: **jorisecko@gmail.com**
   - Developer contact: **jorisecko@gmail.com**
   - Scopes: Add `https://www.googleapis.com/auth/spreadsheets`
   - Test users: Add **jorisecko@gmail.com**
   - Click **Save and Continue**

4. Back to Create OAuth client ID:

   - Application type: **Desktop app**
   - Name: **Crypto Intelligence Desktop**
   - Click **Create**

5. Download the JSON file
6. Save it as `credentials/oauth_credentials.json`

## Step 4: Create Credentials Directory

```bash
mkdir credentials
# Move your downloaded JSON file to credentials/oauth_credentials.json
```

## Step 5: First Run (OAuth Flow)

When you run the system for the first time:

```bash
python scripts/historical_scraper.py --limit 10
```

1. A browser window will open automatically
2. Sign in with **jorisecko@gmail.com**
3. Grant permissions to access Google Sheets
4. The token will be saved to `credentials/token.json`
5. Future runs will use the saved token (no browser needed)

## Step 6: Verify Setup

After OAuth flow completes, verify:

```bash
# Check that token was created
ls credentials/

# Should see:
# - oauth_credentials.json
# - token.json
```

## Current Configuration

Your `.env` is configured with:

```
GOOGLE_SHEETS_ENABLED=true
GOOGLE_AUTH_METHOD=oauth
GOOGLE_OAUTH_CREDENTIALS_FILE=credentials/oauth_credentials.json
GOOGLE_TOKEN_FILE=credentials/token.json
GOOGLE_SPREADSHEET_NAME=Crypto Intelligence Data
GOOGLE_SHARE_EMAIL=jorisecko@gmail.com
```

## What Happens on First Run

1. System checks for `credentials/token.json`
2. If not found, starts OAuth flow (browser opens)
3. You authenticate with Google
4. Token is saved for future use
5. Spreadsheet "Crypto Intelligence Data" is created (if doesn't exist)
6. Spreadsheet is shared with jorisecko@gmail.com
7. 4 sheets are created: Messages, Token Prices, Performance, Historical
8. Data starts flowing to Google Sheets!

## Troubleshooting

### "credentials/oauth_credentials.json not found"

- Download OAuth credentials from Google Cloud Console
- Save to `credentials/oauth_credentials.json`

### "Access blocked: This app's request is invalid"

- Make sure you added jorisecko@gmail.com as a test user in OAuth consent screen

### "Token has been expired or revoked"

- Delete `credentials/token.json`
- Run again to re-authenticate

### Browser doesn't open

- Check firewall settings
- Try running from a machine with a browser
- Use service account authentication instead (different setup)

## Next Steps

1. Download OAuth credentials JSON from Google Cloud Console
2. Save to `credentials/oauth_credentials.json`
3. Run: `python scripts/historical_scraper.py --limit 10`
4. Complete OAuth flow in browser
5. Check Google Drive for "Crypto Intelligence Data" spreadsheet!
