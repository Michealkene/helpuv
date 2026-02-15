/**
 * Twitter/X Bot
 * Posts tweets using a pre-authenticated profile
 * Usage: node twitter-bot.js <email> <tweet_text>
 */

const ProfileManager = require('./profile-manager');

async function postTweet(accountEmail, tweetText) {
  const profileManager = new ProfileManager();
  
  if (!profileManager.profileExists(accountEmail)) {
    console.log(`❌ Profile not found: ${accountEmail}`);
    console.log('💡 Run: node setup-profile.js ' + accountEmail);
    process.exit(1);
  }

  console.log(`🐦 Twitter Bot - ${accountEmail}`);
  console.log(`📝 Tweet: "${tweetText}"\n`);

  const { context, page } = await profileManager.launchBrowser(accountEmail);

  try {
    // Navigate to Twitter
    await page.goto('https://twitter.com/home', { waitUntil: 'networkidle' });
    
    // Check if logged in
    if (page.url().includes('/login')) {
      console.log('❌ Not logged in! Run setup-profile.js first.');
      await context.close();
      process.exit(1);
    }

    console.log('✅ Logged in successfully');

    // Click tweet button
    await page.click('[data-testid="tweetButtonInline"]', { timeout: 5000 });
    await page.waitForTimeout(1000);

    // Type tweet
    const tweetBox = await page.locator('[data-testid="tweetTextarea_0"]');
    await tweetBox.fill(tweetText);
    await page.waitForTimeout(500);

    // Click post button
    await page.click('[data-testid="tweetButton"]');
    
    console.log('✅ Tweet posted successfully!');
    await page.waitForTimeout(3000);

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
const tweetText = process.argv.slice(3).join(' ');

if (!accountEmail || !tweetText) {
  console.log('Usage: node twitter-bot.js <email> <tweet_text>');
  console.log('Example: node twitter-bot.js john@gmail.com "Hello world!"');
  process.exit(1);
}

postTweet(accountEmail, tweetText);
