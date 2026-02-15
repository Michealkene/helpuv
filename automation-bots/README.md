# Social Media Automation Bots

Multi-platform automation system using persistent browser profiles. Sign in once, use everywhere.

## 🎯 Features

✅ **One-time login** - Sign in once per account, not per platform  
✅ **Persistent sessions** - All your logins saved in browser profiles  
✅ **Multi-platform** - Twitter, TikTok, YouTube, Reddit  
✅ **Multi-account** - Manage multiple accounts easily  
✅ **No API keys needed** - Uses real browser automation

## 📦 Installation

```bash
cd C:\Users\Administrator\automation-bots
npm install
```

## 🚀 Quick Start

### 1. Set Up Your First Profile

```bash
node setup-profile.js your-email@gmail.com
```

This will:
- Open a browser with your new profile
- Open tabs for Twitter, TikTok, Reddit, etc.
- Let you sign in to all platforms
- Save all sessions when you close the browser

**Do this once per account.**

### 2. Use Your Bots

#### Twitter Bot
```bash
node twitter-bot.js your-email@gmail.com "Hello Twitter!"
```

#### TikTok Bot
```bash
node tiktok-bot.js your-email@gmail.com video.mp4 "Cool video! #fyp"
```

#### YouTube Bot
```bash
node youtube-bot.js your-email@gmail.com video.mp4 "My Video Title" "Description here"
```

#### Reddit Bot
```bash
node reddit-bot.js your-email@gmail.com AskReddit "What's your story?" "Tell me..."
```

## 📁 File Structure

```
automation-bots/
├── profile-manager.js      # Core profile system
├── setup-profile.js         # Profile setup script
├── twitter-bot.js           # Twitter automation
├── tiktok-bot.js           # TikTok automation
├── youtube-bot.js          # YouTube automation
├── reddit-bot.js           # Reddit automation
└── README.md               # This file

browser-profiles/
├── your-email_at_gmail_com/  # Account 1 profile
├── other_at_email_com/       # Account 2 profile
└── ...                       # More profiles
```

## 🔧 Managing Profiles

### List All Profiles
```bash
node -e "const PM = require('./profile-manager'); new PM().listProfiles().forEach(p => console.log(p))"
```

### Check If Profile Exists
```bash
node -e "const PM = require('./profile-manager'); console.log(new PM().profileExists('your-email@gmail.com'))"
```

### Delete a Profile
```bash
node -e "const PM = require('./profile-manager'); new PM().deleteProfile('your-email@gmail.com')"
```

## 🎭 Multiple Accounts

Set up different profiles for different accounts:

```bash
node setup-profile.js account1@gmail.com
node setup-profile.js account2@gmail.com
node setup-profile.js account3@gmail.com
```

Then use them:

```bash
node twitter-bot.js account1@gmail.com "Post from account 1"
node twitter-bot.js account2@gmail.com "Post from account 2"
```

## ⚙️ Customizing Bots

All bots follow the same pattern:
1. Load profile with ProfileManager
2. Navigate to platform
3. Perform action
4. Close browser

Edit the bot files to:
- Add delays (change `waitForTimeout` values)
- Auto-post (uncomment post button clicks)
- Add more features (hashtags, scheduling, etc.)

## 🔒 Safety Features

- Bots stop before final "Post" action by default
- You can review posts before they go live
- Sessions are stored locally (not in cloud)
- Each account has isolated profile

## 🐛 Troubleshooting

### "Profile not found"
Run `setup-profile.js` first for that email.

### "Not logged in"
Your session expired. Run `setup-profile.js` again.

### Browser won't close
Press Ctrl+C in terminal or close browser manually.

### Selector not found
Platform UI changed. Update the selectors in bot files.

## 💡 Tips

- Keep browser profiles backed up
- Test with one account first
- Review posts before enabling auto-post
- Add delays to avoid rate limits
- Use different profiles for different niches

## 📝 Next Steps

1. Set up your profiles (one per account)
2. Test each bot manually
3. Uncomment auto-post code when ready
4. Build a scheduler to run bots automatically
5. Add more platforms (Instagram, Facebook, etc.)

---

**Built with Playwright + Persistent Contexts**
