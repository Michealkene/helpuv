/**
 * List all browser profiles
 * Usage: node list-profiles.js
 */

const ProfileManager = require('./profile-manager');

const profileManager = new ProfileManager();
const profiles = profileManager.listProfiles();

console.log('📋 Browser Profiles\n');

if (profiles.length === 0) {
  console.log('No profiles found.');
  console.log('\n💡 Create your first profile:');
  console.log('   node setup-profile.js your-email@gmail.com');
} else {
  profiles.forEach((profile, index) => {
    console.log(`${index + 1}. ${profile}`);
    const path = profileManager.getProfilePath(profile);
    console.log(`   📁 ${path}\n`);
  });
  
  console.log(`Total: ${profiles.length} profile(s)`);
}
