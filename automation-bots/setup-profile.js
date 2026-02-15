/**
 * Profile Setup Script
 * Run this to set up a new account profile
 * Usage: node setup-profile.js <email>
 */

const ProfileManager = require('./profile-manager');
const readline = require('readline');

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

function question(prompt) {
  return new Promise(resolve => rl.question(prompt, resolve));
}

async function setupProfile() {
  const profileManager = new ProfileManager();
  
  console.log('🔧 Browser Profile Setup');
  console.log('========================\n');

  // Get account email
  const email = process.argv[2] || await question('Enter account email/username: ');
  
  if (!email) {
    console.log('❌ Email is required');
    process.exit(1);
  }

  console.log(`\n📧 Setting up profile for: ${email}`);
  console.log('\n📋 Instructions:');
  console.log('1. Browser will open with your new profile');
  console.log('2. Sign in to all your platforms:');
  console.log('   - Google (for YouTube)');
  console.log('   - Twitter/X');
  console.log('   - TikTok');
  console.log('   - Reddit');
  console.log('   - Instagram');
  console.log('   - Facebook');
  console.log('   - Any other platforms you use');
  console.log('3. When done, close the browser');
  console.log('4. Your sessions will be saved automatically\n');

  await question('Press Enter to launch browser...');

  const { context, page } = await profileManager.launchBrowser(email);

  // Open helpful pages in tabs
  await page.goto('https://www.google.com');
  await context.newPage().then(p => p.goto('https://twitter.com/login'));
  await context.newPage().then(p => p.goto('https://www.tiktok.com/login'));
  await context.newPage().then(p => p.goto('https://www.reddit.com/login'));

  console.log('\n✅ Browser launched!');
  console.log('📝 Sign in to all your accounts...');
  console.log('⏳ Waiting for you to finish (press Ctrl+C when done or just close the browser)\n');

  // Wait for user to close browser
  await new Promise(resolve => {
    context.on('close', () => {
      console.log('\n✅ Profile saved!');
      console.log(`📁 Location: ${profileManager.getProfilePath(email)}`);
      console.log('\n🎉 Setup complete! Your bots can now use this profile.');
      resolve();
      rl.close();
    });
  });
}

setupProfile().catch(error => {
  console.error('❌ Error:', error.message);
  rl.close();
  process.exit(1);
});
