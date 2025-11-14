# Quick OAuth Setup - Direct Links

## Step-by-Step with Direct Links

### 1. Create/Select Google Cloud Project

🔗 **https://console.cloud.google.com/projectcreate**

- Project name: `Crypto Intelligence`
- Click **CREATE**

### 2. Enable Google Sheets API

🔗 **https://console.cloud.google.com/apis/library/sheets.googleapis.com**

- Click **ENABLE**
- Wait for it to enable (~10 seconds)

### 3. Configure OAuth Consent Screen

🔗 **https://console.cloud.google.com/apis/credentials/consent**

- User Type: **External** → Click **CREATE**
- App information:
  - App name: `Crypto Intelligence`
  - User support email: `jorisecko@gmail.com`
- Developer contact: `jorisecko@gmail.com`
- Click **SAVE AND CONTINUE**

- Scopes: Click **ADD OR REMOVE SCOPES**

  - Search: `spreadsheets`
  - Check: `https://www.googleapis.com/auth/spreadsheets`
  - Click **UPDATE** → **SAVE AND CONTINUE**

- Test users: Click **+ ADD USERS**

  - Enter: `jorisecko@gmail.com`
  - Click **ADD** → **SAVE AND CONTINUE**

- Click **BACK TO DASHBOARD**

### 4. Create OAuth Client ID

🔗 **https://console.cloud.google.com/apis/credentials**

- Click **+ CREATE CREDENTIALS** → **OAuth client ID**
- Application type: **Desktop app**
- Name: `Crypto Intelligence Desktop`
- Click **CREATE**

### 5. Download Credentials

- Click **DOWNLOAD JSON** (download icon)
- Save the file

### 6. Setup Credentials

**Option A: Use Setup Script**

```bash
python setup_google_oauth.py
```

Then paste the JSON content or place the file manually.

**Option B: Manual**

```bash
# Save the downloaded file as:
credentials/oauth_credentials.json
```

### 7. Test It!

```bash
python scripts/historical_scraper.py --limit 10
```

- Browser opens automatically
- Sign in with `jorisecko@gmail.com`
- Click **Allow**
- Done! Spreadsheet created and shared with you!

## Troubleshooting

### "Access blocked: This app's request is invalid"

- Make sure you added `jorisecko@gmail.com` as a test user in Step 3

### "The OAuth client was not found"

- Make sure you selected the correct project in Google Cloud Console

### "API has not been used in project"

- Go back to Step 2 and enable Google Sheets API

### "redirect_uri_mismatch"

- Make sure you selected **Desktop app** (not Web application)

## What Happens Next

1. First run: Browser opens for OAuth
2. You authenticate once
3. Token saved to `credentials/token.json`
4. Spreadsheet "Crypto Intelligence Data" created
5. Shared with jorisecko@gmail.com
6. Future runs: No browser needed!

## Current Configuration

Your system is configured to:

- ✅ Use OAuth authentication
- ✅ Create spreadsheet named "Crypto Intelligence Data"
- ✅ Share with jorisecko@gmail.com
- ✅ Create 4 sheets: Messages, Token Prices, Performance, Historical
- ✅ Write data to all sheets automatically

Ready to go! 🚀
