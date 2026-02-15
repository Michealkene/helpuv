# 🚀 Quick Start Guide

## Step 1: Install Dependencies (One Time)

```bash
cd C:\Users\Administrator\automation-bots
npm install
```

This will install Playwright and download browsers (~300MB).

## Step 2: Set Up Your First Account Profile

Pick one of your accounts (e.g., `marcuschen231@gmail.com`) and run:

```bash
node setup-profile.js marcuschen231@gmail.com
```

**What happens:**
1. Browser opens with 4 tabs (Google, Twitter, TikTok, Reddit)
2. Sign in to each platform in the tabs
3. Close the browser when done
4. All your sessions are saved!

**Important:** You only need to do this **once per account**, not once per platform.

## Step 3: Test Your Bots

### Twitter
```bash
node twitter-bot.js marcuschen231@gmail.com "My first automated tweet!"
```

### TikTok
```bash
node tiktok-bot.js marcuschen231@gmail.com C:\path\to\video.mp4 "Cool video #fyp"
```

### YouTube
```bash
node youtube-bot.js marcuschen231@gmail.com C:\path\to\video.mp4 "Video Title" "Description"
```

### Reddit
```bash
node reddit-bot.js marcuschen231@gmail.com funny "Check this out" "My reddit post content"
```

## Step 4: Set Up More Accounts (Optional)

```bash
node setup-profile.js second-account@gmail.com
node setup-profile.js third-account@gmail.com
```

## 🎯 What You Get

- **One login per account** (not per platform)
- **Persistent sessions** (no re-login needed)
- **Multiple accounts** (as many as you want)
- **All platforms in one system** (Twitter, TikTok, YouTube, Reddit)

## 🔄 Daily Usage

After setup, just run the bots:

```bash
# Morning tweets
node twitter-bot.js account1@gmail.com "Good morning!"
node twitter-bot.js account2@gmail.com "Starting the day right"

# Upload TikToks
node tiktok-bot.js account1@gmail.com video1.mp4 "Video 1"
node tiktok-bot.js account2@gmail.com video2.mp4 "Video 2"
```

No login prompts. No session expired errors. Just works.

## 📋 Pro Tips

1. **Backup your profiles** - Copy `C:\Users\Administrator\browser-profiles` to backup your sessions
2. **Test first** - Try with one account before adding more
3. **Review before posting** - Bots stop before final post by default (safety feature)
4. **Enable auto-post** - Edit bot files and uncomment the post button click
5. **Schedule runs** - Use Windows Task Scheduler to run bots automatically

## ❓ Need Help?

- **Profile not found?** Run `setup-profile.js` for that email
- **Not logged in?** Session expired, run `setup-profile.js` again
- **Want to add more platforms?** Copy a bot file and modify for your platform

---

Ready to automate? Start with Step 1! 🚀
