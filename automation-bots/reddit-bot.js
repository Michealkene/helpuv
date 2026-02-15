/**
 * Reddit Bot
 * Posts to subreddits using a pre-authenticated profile
 * Usage: node reddit-bot.js <email> <subreddit> <title> <text>
 */

const ProfileManager = require('./profile-manager');

async function postReddit(accountEmail, subreddit, title, text) {
  const profileManager = new ProfileManager();
  
  if (!profileManager.profileExists(accountEmail)) {
    console.log(`❌ Profile not found: ${accountEmail}`);
    console.log('💡 Run: node setup-profile.js ' + accountEmail);
    process.exit(1);
  }

  console.log(`🤖 Reddit Bot - ${accountEmail}`);
  console.log(`📋 Subreddit: r/${subreddit}`);
  console.log(`📝 Title: "${title}"`);
  console.log(`📄 Text: "${text}"\n`);

  const { context, page } = await profileManager.launchBrowser(accountEmail);

  try {
    // Navigate to subreddit
    const url = `https://www.reddit.com/r/${subreddit}/submit`;
    await page.goto(url, { waitUntil: 'networkidle' });
    
    // Check if logged in
    if (page.url().includes('/login')) {
      console.log('❌ Not logged in! Run setup-profile.js first.');
      await context.close();
      process.exit(1);
    }

    console.log('✅ Logged in successfully');
    await page.waitForTimeout(2000);

    // Click on text post tab if available
    try {
      await page.click('[data-name="Text"]', { timeout: 3000 });
      await page.waitForTimeout(500);
    } catch (e) {
      // Already on text post tab or different UI
    }

    // Fill title
    const titleInput = await page.locator('[placeholder*="Title"]').first();
    await titleInput.fill(title);
    console.log('✅ Title added');
    await page.waitForTimeout(500);

    // Fill text content
    const textBox = await page.locator('[placeholder*="Text"]').first();
    await textBox.fill(text);
    console.log('✅ Text added');
    await page.waitForTimeout(1000);

    // Click post button (uncomment to auto-post)
    // await page.click('button:has-text("Post")');
    
    console.log('⚠️  Post ready to submit');
    console.log('💡 Bot stopped before posting - remove comment to auto-post');
    console.log('🖱️  You can review and post manually');

    // Keep browser open for manual review
    await page.waitForTimeout(30000);

    await context.close();
    console.log('✅ Done!');

  } catch (error) {
    console.error('❌ Error:', error.message);
    await context.close();
    process.exit(1);
  }
}

// CLI usage
const accountEmail = process.argv[2];
const subreddit = process.argv[3];
const title = process.argv[4];
const text = process.argv.slice(5).join(' ');

if (!accountEmail || !subreddit || !title) {
  console.log('Usage: node reddit-bot.js <email> <subreddit> <title> <text>');
  console.log('Example: node reddit-bot.js john@gmail.com AskReddit "What\'s your story?" "Tell me..."');
  process.exit(1);
}

postReddit(accountEmail, subreddit, title, text);
