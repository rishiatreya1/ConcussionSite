# Gmail OAuth Setup Instructions

This guide will help you set up Gmail OAuth authentication for sending referral emails from ConcussionSite.

## Prerequisites

- **A Google account** (any Gmail account works - personal or work)
- **Access to Google Cloud Console** (free tier is sufficient)
- **5-10 minutes** to complete setup

## Step 1: Create Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. **Sign in** with your Google account (the same one you want to use for sending emails)
3. Click "Select a project" → "New Project"
4. Name it "ConcussionSite" (or your preferred name)
5. Click "Create"
6. Wait for the project to be created, then select it from the project dropdown

## Step 2: Enable Gmail API

1. In your project, go to "APIs & Services" → "Library"
2. Search for "Gmail API"
3. Click on "Gmail API"
4. Click "Enable"

## Step 3: Configure OAuth Consent Screen

**Important:** You must do this BEFORE creating credentials.

1. Go to "APIs & Services" → "OAuth consent screen"
2. Select **"External"** (unless you have Google Workspace)
3. Click "Create"
4. Fill in the form:
   - **App name:** `ConcussionSite`
   - **User support email:** Your email address
   - **Developer contact:** Your email address
   - Click "Save and Continue"
5. **Scopes:** Click "Add or Remove Scopes"
   - Search for `gmail.send`
   - Check the box for `https://www.googleapis.com/auth/gmail.send`
   - Click "Update" then "Save and Continue"
6. **Test users:** 
   - Click "Add Users"
   - Add **your own email address** (the one you'll use to send emails)
   - Click "Add" then "Save and Continue"
7. Click "Back to Dashboard"

## Step 4: Create OAuth Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. **Application type:** Select "Desktop app"
4. **Name:** `ConcussionSite Desktop Client`
5. Click "Create"
6. **IMPORTANT:** A popup will appear with your credentials
   - Click "Download JSON" button
   - **Save this file** - you'll need it in the next step

## Step 5: Place Credentials File

1. **Rename** the downloaded JSON file to exactly `credentials.json` (case-sensitive)
2. **Move** it to the `email_service/` directory in your project:
   ```
   ConcussionSite/
   └── email_service/
       └── credentials.json  ← Place it here
   ```
3. **Verify** the file is in the correct location:
   ```bash
   ls email_service/credentials.json
   ```
   You should see the file listed.

## Step 6: First-Time Authentication

When you run the application and try to send an email for the first time:

1. **A browser window will automatically open**
2. **Sign in** with the same Google account you used in Step 3 (the test user email)
3. You'll see a warning: "Google hasn't verified this app"
   - Click "Advanced" → "Go to ConcussionSite (unsafe)"
   - This is normal for unverified apps in testing mode
4. **Grant permissions** - Click "Allow" to let the app send emails
5. **Success!** The token will be saved to `email_service/token.json` automatically
6. You won't need to do this again unless you delete the token file

**Note:** The browser might close automatically after authentication. This is normal.

## Step 7: Verify Setup

You can verify your setup is working by running this Python command:

```python
from email_service.email_service import check_oauth_setup
is_setup, message = check_oauth_setup()
print(f"Setup: {is_setup}")
print(f"Message: {message}")
```

**Expected output:**
- If credentials file is missing: `Setup: False, Message: "Credentials file not found..."`
- If credentials found but no token: `Setup: False, Message: "Credentials file found, but no token..."`
- If everything is ready: `Setup: True, Message: "OAuth token found. Setup appears complete."`

**Or test by running the full application** - when you try to send an email, it will prompt for authentication if needed.

## Troubleshooting

### "Credentials file not found"
- **Check the file location:** `email_service/credentials.json` (relative to project root)
- **Check the file name:** Must be exactly `credentials.json` (case-sensitive, no spaces)
- **Check you downloaded it:** Make sure you clicked "Download JSON" in Step 4

### "Access blocked: This app's request is invalid"
- **You must add yourself as a test user** in Step 3 (OAuth consent screen → Test users)
- Make sure you're signing in with the same email you added as a test user
- For production use, you'll need to verify your app with Google (not needed for testing)

### "Token expired" or "Invalid token"
- **Delete the token file:** `rm email_service/token.json`
- **Re-authenticate:** Run the app again and go through the browser authentication
- The token should refresh automatically, but sometimes you need to re-authenticate

### "Insufficient permissions" or "Scope not granted"
- **Check Gmail API is enabled** in Step 2
- **Check OAuth scope** includes `https://www.googleapis.com/auth/gmail.send` in Step 3
- **Re-authenticate** after adding scopes (delete token.json and try again)

### Browser doesn't open for authentication
- Make sure you're running the app locally (not on a remote server)
- Check your firewall isn't blocking local connections
- Try manually opening: `http://localhost:8080` (or the port shown in terminal)

## Security Notes

- **Never commit `credentials.json` or `token.json` to git**
- These files are already in `.gitignore`
- Keep your credentials secure
- For production, use environment variables or secure secret management

## Production Deployment

For production use:
1. Complete OAuth consent screen verification
2. Use service account or OAuth 2.0 with proper scopes
3. Store credentials securely (not in code)
4. Implement proper error handling and logging

