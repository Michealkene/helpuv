/**
 * YouTube Bot
 * Uploads videos using a pre-authenticated profile
 * Usage: node youtube-bot.js <email> <video_path> <title> <description>
 */

const ProfileManager = require('./profile-manager');
const path = require('path');
const fs = require('fs');

async function uploadYouTube(accountEmail, videoPath, title, description) {
  const profileManager = new ProfileManager();
  
  if (!profileManager.profileExists(accountEmail)) {
    console.log(`❌ Profile not found: ${accountEmail}`);
    console.log('💡 Run: node setup-profile.js ' + accountEmail);
    process.exit(1);
  }

  if (!fs.existsSync(videoPath)) {
    console.log(`❌ Video not found: ${videoPath}`);
    process.exit(1);
  }

  console.log(`📺 YouTube Bot - ${accountEmail}`);
  console.log(`📹 Video: ${path.basename(videoPath)}`);
  console.log(`📝 Title: "${title}"`);
  console.log(`📄 Description: "${description}"\n`);

  const { context, page } = await profileManager.launchBrowser(accountEmail);

  try {
    // Navigate to YouTube Studio upload
    await page.goto('https://studio.youtube.com', { waitUntil: 'networkidle' });
    
    // Check if logged in
    if (page.url().includes('accounts.google.com')) {
      console.log('❌ Not logged in! Run setup-profile.js first.');
      await context.close();
      process.exit(1);
    }

    console.log('✅ Logged in successfully');

    // Click upload button
    await page.click('ytcp-button#upload-icon', { timeout: 10000 });
    await page.waitForTimeout(1000);

    // Upload file
    const fileInput = await page.locator('input[type="file"]');
    await fileInput.setInputFiles(path.resolve(videoPath));
    
    console.log('📤 Uploading video...');
    await page.waitForTimeout(5000);

    // Add title
    const titleInput = await page.locator('[aria-label*="title"]').first();
    if (await titleInput.count() > 0) {
      await titleInput.fill(title);
      console.log('✅ Title added');
    }

    // Add description
    const descInput = await page.locator('[aria-label*="description"]').first();
    if (await descInput.count() > 0) {
      await descInput.fill(description);
      console.log('✅ Description added');
    }

    await page.waitForTimeout(2000);

    // Set to "Not made for kids" (usually required)
    try {
      await page.click('[name="VIDEO_MADE_FOR_KIDS_NOT_MFK"]', { timeout: 3000 });
    } catch (e) {
      console.log('⚠️  Could not set "Not for kids" option');
    }

    await page.waitForTimeout(2000);

    // Click next through steps (uncomment to auto-publish)
    // await page.click('button:has-text("Next")');
    // await page.waitForTimeout(1000);
    // await page.click('button:has-text("Next")');
    // await page.waitForTimeout(1000);
    // await page.click('button:has-text("Next")');
    // await page.waitForTimeout(1000);
    // await page.click('button:has-text("Publish")');

    console.log('⚠️  Video uploaded and ready to publish');
    console.log('💡 Bot stopped before publishing - remove comments to auto-publish');
    console.log('🖱️  You can review and publish manually');

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
const videoPath = process.argv[3];
const title = process.argv[4] || 'My Video';
const description = process.argv.slice(5).join(' ') || 'Check out my video!';

if (!accountEmail || !videoPath) {
  console.log('Usage: node youtube-bot.js <email> <video_path> <title> <description>');
  console.log('Example: node youtube-bot.js john@gmail.com video.mp4 "My Title" "My description"');
  process.exit(1);
}

uploadYouTube(accountEmail, videoPath, title, description);
