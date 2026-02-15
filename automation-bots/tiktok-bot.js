/**
 * TikTok Bot
 * Uploads videos using a pre-authenticated profile
 * Usage: node tiktok-bot.js <email> <video_path> <caption>
 */

const ProfileManager = require('./profile-manager');
const path = require('path');
const fs = require('fs');

async function uploadTikTok(accountEmail, videoPath, caption) {
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

  console.log(`🎵 TikTok Bot - ${accountEmail}`);
  console.log(`📹 Video: ${path.basename(videoPath)}`);
  console.log(`📝 Caption: "${caption}"\n`);

  const { context, page } = await profileManager.launchBrowser(accountEmail);

  try {
    // Navigate to TikTok upload page
    await page.goto('https://www.tiktok.com/upload', { waitUntil: 'networkidle' });
    
    // Check if logged in
    if (page.url().includes('/login')) {
      console.log('❌ Not logged in! Run setup-profile.js first.');
      await context.close();
      process.exit(1);
    }

    console.log('✅ Logged in successfully');

    // Wait for upload button
    await page.waitForSelector('input[type="file"]', { timeout: 10000 });

    // Upload video file
    const fileInput = await page.locator('input[type="file"]').first();
    await fileInput.setInputFiles(path.resolve(videoPath));
    
    console.log('📤 Uploading video...');
    
    // Wait for upload to process
    await page.waitForTimeout(5000);

    // Add caption
    const captionBox = await page.locator('[placeholder*="caption"]').first();
    if (await captionBox.count() > 0) {
      await captionBox.fill(caption);
      console.log('✅ Caption added');
    }

    await page.waitForTimeout(2000);

    // Click post button (uncomment when ready to actually post)
    // await page.click('button:has-text("Post")');
    
    console.log('⚠️  Video uploaded and ready to post');
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
const videoPath = process.argv[3];
const caption = process.argv.slice(4).join(' ') || 'Check this out! 🎵';

if (!accountEmail || !videoPath) {
  console.log('Usage: node tiktok-bot.js <email> <video_path> <caption>');
  console.log('Example: node tiktok-bot.js john@gmail.com video.mp4 "My awesome video"');
  process.exit(1);
}

uploadTikTok(accountEmail, videoPath, caption);
