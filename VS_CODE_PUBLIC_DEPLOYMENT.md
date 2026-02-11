# Deploying CARL via VS Code - PUBLIC GitHub (Updated)

## Important Update
Streamlit Community Cloud now requires **PUBLIC** GitHub repositories for free hosting. Private repos require Streamlit Teams ($42/month).

For beta testing, we'll use a **public repo** with a beta notice on the app.

---

## Prerequisites

- VS Code installed
- Git installed  
- GitHub account

---

## Part 1: Setup in VS Code

### Step 1: Create Your Project Folder

1. **Create a new folder** on your computer:
   - Name it: `carl-deployment`
   - Location: Anywhere you like (Desktop, Documents, etc.)

2. **Download the 4 required files** and put them in this folder:
   - `streamlit_carl.py`
   - `enhanced_calculator.py`
   - `chimney_calculator.py`
   - `requirements_carl.txt`

3. **CRITICAL: Rename the requirements file**
   ```
   requirements_carl.txt  →  requirements.txt
   ```
   Must be named exactly `requirements.txt`!

Your folder should now look like:
```
carl-deployment/
├── streamlit_carl.py
├── enhanced_calculator.py
├── chimney_calculator.py
└── requirements.txt
```

---

### Step 2: Open Folder in VS Code

1. Open VS Code
2. Click **File** → **Open Folder**
3. Navigate to and select `carl-deployment`
4. Click **Select Folder**

You should now see your 4 files in the VS Code Explorer panel on the left.

---

### Step 3: Open Integrated Terminal

1. In VS Code, click **Terminal** → **New Terminal**
   - Or press `` Ctrl + ` `` (that's the backtick key)

2. Terminal opens at the bottom of VS Code

3. Verify you're in the right folder:
   ```bash
   pwd
   # Should show: /path/to/carl-deployment
   ```

---

## Part 2: Initialize Git Repository

### Step 4: Initialize Git

In the VS Code terminal, type:

```bash
git init
```

You should see: `Initialized empty Git repository`

---

### Step 5: Configure Git (First Time Only)

If you haven't used Git before on this computer:

```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

Replace with your actual name and email.

---

### Step 6: Stage Files

**Option A: Using Terminal**
```bash
git add .
```

**Option B: Using VS Code GUI**
1. Click the **Source Control** icon (3rd icon on left sidebar)
2. You'll see 4 files under "Changes"
3. Click the **+** button next to "Changes" (stages all files)

---

### Step 7: Commit Files

**Option A: Using Terminal**
```bash
git commit -m "Initial CARL deployment - v1.0 Beta"
```

**Option B: Using VS Code GUI**
1. In Source Control panel
2. Type message: `Initial CARL deployment - v1.0 Beta`
3. Click the **✓ Commit** button

---

## Part 3: Create GitHub Repository

### Step 8: Create PUBLIC Repo on GitHub

1. Go to: **https://github.com/new**

2. Fill in:
   - **Repository name:** `carl-chimney-calculator`
   - **Description:** "CARL - Chimney Analysis and Reasoning Layer (Beta)"
   - **Visibility:** ✅ **Public** (Required for free Streamlit hosting)
   - **DO NOT** check "Initialize with README"
   - **DO NOT** add .gitignore or license

3. Click **Create repository**

4. **Keep this page open** - you'll need the commands!

---

## Part 4: Connect VS Code to GitHub

### Step 9: Link Local Repo to GitHub

GitHub will show you commands. In VS Code terminal, run:

```bash
git remote add origin https://github.com/YOUR-USERNAME/carl-chimney-calculator.git
git branch -M main
git push -u origin main
```

**Replace `YOUR-USERNAME`** with your actual GitHub username!

**If prompted for credentials:**
- Username: Your GitHub username
- Password: Use a **Personal Access Token** (not your password)

---

### Step 10: Create Personal Access Token (If Needed)

If you don't have a token:

1. Go to: https://github.com/settings/tokens
2. Click **Generate new token** → **Generate new token (classic)**
3. Note: `CARL deployment`
4. Expiration: `90 days`
5. Scopes: Check ✅ **repo** (all repo permissions)
6. Click **Generate token**
7. **COPY THE TOKEN** immediately!
8. Use this as your password when pushing

---

### Step 11: Verify Upload

1. Refresh your GitHub repository page
2. You should see your 4 files!
3. Your repo is now **public** (anyone can see the code)

---

## Part 5: Deploy to Streamlit Cloud

### Step 12: Go to Streamlit Cloud

1. Open: **https://share.streamlit.io/**
2. Click **Sign in**
3. Click **Continue with GitHub**
4. Authorize Streamlit

---

### Step 13: Create New App

1. Click **New app** button

2. Fill in the form:

   **Repository:**
   - Select: `YOUR-USERNAME/carl-chimney-calculator`

   **Branch:**
   - Select: `main`

   **Main file path:**
   - Type: `streamlit_carl.py`

   **App URL** (optional):
   - Leave default or customize

3. Click **Deploy!**

---

### Step 14: Wait for Deployment

- Status shows "Deploying..." 
- Takes 2-3 minutes
- Watch the logs scroll
- When done: Status shows "Running" ✅

---

### Step 15: Your App is Live!

Your app URL:
```
https://YOUR-USERNAME-carl-chimney-calculator.streamlit.app
```

🎉 **Your app is now publicly accessible!**

---

## Part 6: Share with Beta Testers

### Step 16: Send Link to Testers

Email your testers:

```
Subject: CARL Beta Testing - Now Available

Hi team,

CARL (Chimney Analysis and Reasoning Layer) is now live for beta testing!

🔗 URL: https://your-username-carl-chimney-calculator.streamlit.app

Instructions:
1. Click the link
2. Start analyzing venting systems
3. Test with your real projects
4. Send me feedback on any issues or suggestions

Note: This is a beta version under active development. 
For production use, contact US Draft Co. at 817-393-4029.

Please keep this link within our team for now.

Thanks!
```

---

## Part 7: Making Updates

### Step 17: Update Code

When you want to make changes:

1. **Edit files** in VS Code

2. **Save files** (Ctrl+S)

3. **Commit and push:**

   **Via Terminal:**
   ```bash
   git add .
   git commit -m "Fixed calculation bug"
   git push
   ```

   **Via VS Code GUI:**
   - Source Control panel
   - Stage changes (+)
   - Enter commit message
   - Click Commit
   - Click **Sync Changes** button

4. **Streamlit auto-updates** in ~2 minutes!

---

## Controlling Access (Since It's Public)

Since the repo and app must be public for free hosting, here are ways to limit access:

### Option 1: Obscure URL (Simple)
- Don't publicize the URL
- Only share with beta testers via email
- Most people won't find it randomly

### Option 2: Beta Notice (Included)
- App shows: "🧪 BETA VERSION - Contact US Draft Co. for production use"
- This discourages random users

### Option 3: Add Usage Tracking
Add this to track who's using it:

```python
# At top of streamlit_carl.py
import datetime

# After st.title()
if 'session_start' not in st.session_state:
    st.session_state.session_start = datetime.datetime.now()
    # Optional: Log to file or send to your email
```

### Option 4: Rate Limiting (Advanced)
Add limits on calculations per IP:

```python
# Limit to 10 calculations per session
if 'calc_count' not in st.session_state:
    st.session_state.calc_count = 0

if st.session_state.calc_count >= 10:
    st.error("Session limit reached. Please refresh to continue.")
    st.stop()
```

### Option 5: Upgrade to Streamlit Teams
- **Cost:** $42/month
- **Benefits:** Private repos, authentication, custom domain
- **Link:** https://streamlit.io/cloud

---

## Important Notes About Public Repos

### ✅ What's Public:
- Source code (formulas, calculations)
- App functionality
- Documentation

### ⚠️ Keep These Private:
- Don't commit API keys
- Don't commit passwords
- Don't commit customer data
- Don't commit proprietary algorithms (if any)

### 🔒 Your Code is Safe Because:
- Formulas are based on public ASHRAE standards
- US Draft Co. products are publicly documented
- The value is in the expertise, not the code
- Many successful companies have open-source tools

---

## Troubleshooting

### Problem: "Repository must be public"

**Solution:** This is correct! Streamlit Community Cloud requires public repos.
- Either make repo public
- Or upgrade to Streamlit Teams ($42/mo)

---

### Problem: "git: command not found"

**Solution:** Install Git
- Download: https://git-scm.com/downloads
- Install
- Restart VS Code
- Try again

---

### Problem: "ModuleNotFoundError"

**Solution:** Check `requirements.txt`
- Must be named exactly `requirements.txt`
- Must contain: `streamlit>=1.28.0`
- In root folder with other files

---

### Problem: App shows errors

**Solution:** View logs
1. Streamlit Cloud → Your app
2. Click **⋮** → **Logs**
3. See error details
4. Fix in VS Code
5. Commit and push

---

## Quick Reference

### Git Commands
```bash
# Check status
git status

# Stage all changes
git add .

# Commit with message
git commit -m "Your message"

# Push to GitHub
git push

# Pull latest changes
git pull
```

### VS Code Shortcuts
```
Ctrl + `          Open terminal
Ctrl + Shift + P  Command palette
Ctrl + S          Save file
Ctrl + Shift + G  Source control panel
```

---

## Deployment Checklist

- [ ] Created `carl-deployment` folder
- [ ] Downloaded 4 files
- [ ] Renamed `requirements_carl.txt` → `requirements.txt`
- [ ] Opened folder in VS Code
- [ ] Opened integrated terminal
- [ ] Ran `git init`
- [ ] Configured Git (name/email)
- [ ] Staged files (`git add .`)
- [ ] Committed files
- [ ] Created **PUBLIC** GitHub repo
- [ ] Pushed to GitHub
- [ ] Went to share.streamlit.io
- [ ] Deployed app
- [ ] Verified app works
- [ ] Shared URL with beta testers

---

## Alternative: Private Hosting Options

If you need true privacy:

### Option A: Streamlit Teams
- **Cost:** $42/month
- **Features:** Private repos, SSO, custom domain
- **Link:** https://streamlit.io/cloud

### Option B: Self-Host with Docker
- **Cost:** $5-20/month (VPS)
- **Complexity:** Medium
- **Privacy:** Complete
- Files included in your package

### Option C: Internal Network Only
- Run on company server
- Only accessible from company network
- Free but requires IT setup

---

## Success! 🎉

Your CARL app is now:
- ✅ Deployed to Streamlit Cloud
- ✅ Publicly accessible
- ✅ Auto-updates from GitHub
- ✅ Free hosting
- ✅ HTTPS included
- ✅ Professional URL
- ✅ Ready for beta testing

---

## Next Steps

1. **Test thoroughly** yourself first
2. **Share URL** with select beta testers
3. **Collect feedback** 
4. **Make improvements** in VS Code
5. **Commit and push** updates
6. **Repeat** until production-ready

---

## Need Help?

**Streamlit Docs:** https://docs.streamlit.io  
**Git Guide:** https://git-scm.com/doc  
**VS Code Docs:** https://code.visualstudio.com/docs  
**Community:** https://discuss.streamlit.io

---

**You're all set! Deploy away! 🚀**
