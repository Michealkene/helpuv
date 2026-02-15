/**
 * Browser Profile Manager
 * Manages persistent browser profiles for automation bots
 */

const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

class ProfileManager {
  constructor(profilesDir = 'C:\\Users\\Administrator\\browser-profiles') {
    this.profilesDir = profilesDir;
    
    // Ensure profiles directory exists
    if (!fs.existsSync(this.profilesDir)) {
      fs.mkdirSync(this.profilesDir, { recursive: true });
    }
  }

  /**
   * Get the path for a profile
   */
  getProfilePath(accountEmail) {
    const safeName = accountEmail.replace(/@/g, '_at_').replace(/\./g, '_');
    return path.join(this.profilesDir, safeName);
  }

  /**
   * Launch browser with persistent profile
   * @param {string} accountEmail - Email/identifier for the account
   * @param {object} options - Additional Playwright launch options
   */
  async launchBrowser(accountEmail, options = {}) {
    const profilePath = this.getProfilePath(accountEmail);
    
    // Create profile directory if it doesn't exist
    if (!fs.existsSync(profilePath)) {
      fs.mkdirSync(profilePath, { recursive: true });
    }

    console.log(`🌐 Launching browser with profile: ${accountEmail}`);
    console.log(`📁 Profile path: ${profilePath}`);

    const context = await chromium.launchPersistentContext(profilePath, {
      headless: false,
      viewport: { width: 1280, height: 720 },
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
      ...options
    });

    const page = context.pages()[0] || await context.newPage();
    
    return { context, page };
  }

  /**
   * Check if a profile exists
   */
  profileExists(accountEmail) {
    const profilePath = this.getProfilePath(accountEmail);
    return fs.existsSync(profilePath);
  }

  /**
   * List all profiles
   */
  listProfiles() {
    if (!fs.existsSync(this.profilesDir)) {
      return [];
    }
    
    return fs.readdirSync(this.profilesDir)
      .filter(name => fs.statSync(path.join(this.profilesDir, name)).isDirectory())
      .map(name => name.replace(/_at_/g, '@').replace(/_/g, '.'));
  }

  /**
   * Delete a profile
   */
  deleteProfile(accountEmail) {
    const profilePath = this.getProfilePath(accountEmail);
    if (fs.existsSync(profilePath)) {
      fs.rmSync(profilePath, { recursive: true, force: true });
      console.log(`🗑️  Deleted profile: ${accountEmail}`);
      return true;
    }
    return false;
  }
}

module.exports = ProfileManager;
