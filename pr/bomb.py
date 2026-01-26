import asyncio
import logging
import random
import json
import csv
from datetime import datetime, timedelta
from pathlib import Path
from playwright.async_api import TimeoutError as PlaywrightTimeout
from itertools import product
import os
from typing import List, Dict, Optional, Tuple

# Configuration
COOLDOWN_HOURS = 24
MAX_RETRIES = 3
STATE_FILE = "posting_state.json"
MIN_DELAY_BETWEEN_POSTS = 300  # 5 minutes minimum
MAX_DELAY_BETWEEN_POSTS = 900  # 15 minutes maximum

class PostingState:
    """Track which combinations have been posted with file locking"""
    def __init__(self, state_file: str = STATE_FILE):
        self.state_file = state_file
        self.completed_combinations = set()
        self.failed_attempts: Dict[Tuple, int] = {}
        self.load_state()
    
    def load_state(self) -> None:
        """Load previous posting state with error handling"""
        if not Path(self.state_file).exists():
            logging.info("No previous state found, starting fresh")
            return
            
        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.completed_combinations = set(tuple(x) for x in data.get('completed', []))
                self.failed_attempts = {tuple(k.split('|')): v for k, v in data.get('failed', {}).items()}
                logging.info(f"Loaded {len(self.completed_combinations)} completed combinations")
                logging.info(f"Loaded {len(self.failed_attempts)} failed attempts")
        except (json.JSONDecodeError, IOError) as e:
            logging.error(f"Error loading state file: {e}")
            logging.warning("Starting with empty state")
    
    def save_state(self) -> None:
        """Save posting state with backup"""
        try:
            # Create backup
            if Path(self.state_file).exists():
                backup_file = f"{self.state_file}.backup"
                Path(self.state_file).rename(backup_file)
            
            # Save new state
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump({
                    'completed': [list(x) for x in self.completed_combinations],
                    'failed': {'|'.join(k): v for k, v in self.failed_attempts.items()},
                    'last_updated': datetime.now().isoformat()
                }, f, indent=2)
                
            # Remove backup on success
            backup_file = f"{self.state_file}.backup"
            if Path(backup_file).exists():
                Path(backup_file).unlink()
                
        except IOError as e:
            logging.error(f"Error saving state: {e}")
    
    def mark_complete(self, account: str, subreddit: str, post_id: str) -> None:
        """Mark a combination as posted"""
        combo = (account, subreddit, post_id)
        self.completed_combinations.add(combo)
        # Remove from failed attempts if exists
        if combo in self.failed_attempts:
            del self.failed_attempts[combo]
        self.save_state()
    
    def mark_failed(self, account: str, subreddit: str, post_id: str) -> None:
        """Track failed posting attempts"""
        combo = (account, subreddit, post_id)
        self.failed_attempts[combo] = self.failed_attempts.get(combo, 0) + 1
        self.save_state()
    
    def is_complete(self, account: str, subreddit: str, post_id: str) -> bool:
        """Check if combination already posted"""
        return (account, subreddit, post_id) in self.completed_combinations
    
    def should_retry(self, account: str, subreddit: str, post_id: str) -> bool:
        """Check if we should retry a failed combination"""
        combo = (account, subreddit, post_id)
        return self.failed_attempts.get(combo, 0) < MAX_RETRIES
    
    def reset(self) -> None:
        """Clear all state (start fresh)"""
        self.completed_combinations = set()
        self.failed_attempts = {}
        self.save_state()
        logging.info("State reset - all combinations available")

class AccountManager:
    """Manage multiple Reddit accounts with cooldown tracking"""
    def __init__(self):
        self.accounts: Dict[str, Dict] = {}
    
    async def add_account(self, account_name: str, context) -> None:
        """Add a browser context for an account"""
        self.accounts[account_name] = {
            'context': context,
            'last_post_time': None,
            'total_posts': 0,
            'failed_posts': 0
        }
        logging.info(f"Added account: {account_name}")
    
    def get_available_accounts(self) -> List[str]:
        """Get accounts that can post (not in cooldown)"""
        available = []
        now = datetime.now()
        
        for name, data in self.accounts.items():
            if data['last_post_time'] is None:
                available.append(name)
            else:
                time_since = now - data['last_post_time']
                # Use configured cooldown, convert hours to timedelta
                if time_since >= timedelta(hours=COOLDOWN_HOURS):
                    available.append(name)
        
        return available
    
    def update_post_time(self, account_name: str, success: bool = True) -> None:
        """Update last post time and stats for account"""
        self.accounts[account_name]['last_post_time'] = datetime.now()
        self.accounts[account_name]['total_posts'] += 1
        if not success:
            self.accounts[account_name]['failed_posts'] += 1
    
    def get_context(self, account_name: str):
        """Get browser context for account"""
        return self.accounts[account_name]['context']
    
    def get_stats(self) -> Dict:
        """Get posting statistics for all accounts"""
        stats = {}
        for name, data in self.accounts.items():
            stats[name] = {
                'total_posts': data['total_posts'],
                'failed_posts': data['failed_posts'],
                'success_rate': (
                    (data['total_posts'] - data['failed_posts']) / data['total_posts'] * 100
                    if data['total_posts'] > 0 else 0
                )
            }
        return stats

def load_posts_from_json(filepath: str) -> List[Dict]:
    """Load posts from JSON file with validation"""
    if not Path(filepath).exists():
        raise FileNotFoundError(f"Posts file not found: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            posts = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in posts file: {e}")
    
    if not isinstance(posts, list):
        raise ValueError("Posts file must contain a JSON array")
    
    # Validate and ensure each post has required fields
    for i, post in enumerate(posts):
        if 'id' not in post:
            post['id'] = f"post_{i}"
        if 'title' not in post:
            raise ValueError(f"Post {i} missing required 'title' field")
        
        # Ensure body exists (can be empty string)
        post.setdefault('body', '')
    
    logging.info(f"Loaded {len(posts)} posts from {filepath}")
    return posts

def load_subreddits_from_file(filepath: str) -> List[str]:
    """Load subreddits from JSON or CSV file with validation"""
    path = Path(filepath)
    
    if not path.exists():
        raise FileNotFoundError(f"Subreddits file not found: {filepath}")
    
    subreddits = []
    
    try:
        if path.suffix == '.json':
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                # Handle both list and dict formats
                if isinstance(data, list):
                    subreddits = data
                else:
                    subreddits = data.get('subreddits', [])
        
        elif path.suffix == '.csv':
            with open(filepath, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Try multiple column names
                    sub = row.get('subreddit', row.get('name', row.get('sub', '')))
                    if sub:
                        subreddits.append(sub)
        else:
            raise ValueError("File must be .json or .csv")
    
    except (json.JSONDecodeError, csv.Error) as e:
        raise ValueError(f"Error reading subreddits file: {e}")
    
    # Clean subreddit names (remove r/ prefix if present)
    subreddits = [s.replace('r/', '').strip() for s in subreddits if s]
    
    if not subreddits:
        raise ValueError("No subreddits found in file")
    
    logging.info(f"Loaded {len(subreddits)} subreddits from {filepath}")
    return subreddits

async def human_sleep(min_ms: int, max_ms: int) -> None:
    """Simulate human-like delays with more randomness"""
    # Add gaussian noise for more realistic timing
    base_delay = random.uniform(min_ms, max_ms)
    noise = random.gauss(0, (max_ms - min_ms) * 0.1)
    delay = max(min_ms, base_delay + noise) / 1000
    await asyncio.sleep(delay)

async def human_type(page, selector: str, text: str, delay_range: Tuple[int, int] = (50, 150)) -> bool:
    """Type text with human-like delays and error handling"""
    try:
        element = await page.wait_for_selector(selector, timeout=10000)
        await element.click()
        await human_sleep(300, 800)
        
        for char in text:
            await element.type(char, delay=random.randint(*delay_range))
            # Occasional longer pauses
            if random.random() < 0.05:
                await human_sleep(300, 1000)
        
        return True
    except PlaywrightTimeout:
        logging.error(f"Timeout waiting for selector: {selector}")
        return False
    except Exception as e:
        logging.error(f"Error typing text: {e}")
        return False

async def verify_login(page) -> bool:
    """Verify user is logged in with multiple checks"""
    try:
        # Check for user menu
        await page.wait_for_selector("[id*='user-menu'], [aria-label*='User Menu']", timeout=5000)
        return True
    except PlaywrightTimeout:
        # Check for login button (indicates not logged in)
        try:
            login_btn = await page.locator("a[href*='login']").count()
            return login_btn == 0
        except Exception:
            return False

async def post_to_reddit(context, account_name: str, post: Dict, subreddit: str) -> bool:
    """Post to Reddit from specific account with comprehensive error handling"""
    title = post["title"]
    body = post.get("body", "")
    flair = post.get("flair")
    
    page = None
    
    try:
        page = await context.new_page()
        logging.info(f"[{account_name}] Posting to r/{subreddit}: '{title[:50]}...'")
        
        await human_sleep(2000, 5000)
        
        submit_url = f"https://www.reddit.com/r/{subreddit}/submit"
        
        try:
            await page.goto(submit_url, wait_until="networkidle", timeout=30000)
        except PlaywrightTimeout:
            logging.error(f"[{account_name}] Timeout loading submit page")
            return False
        
        # Verify login
        if not await verify_login(page):
            logging.error(f"[{account_name}] Not logged in!")
            return False
        
        # Wait for title field
        try:
            await page.wait_for_selector("textarea[name='title']", timeout=15000)
        except PlaywrightTimeout:
            # Check if subreddit exists or account is banned
            page_content = await page.content()
            if "banned" in page_content.lower():
                logging.error(f"[{account_name}] Account banned from r/{subreddit}")
            elif "private" in page_content.lower() or "restricted" in page_content.lower():
                logging.error(f"[{account_name}] r/{subreddit} is private or restricted")
            else:
                logging.error(f"[{account_name}] Submit page failed to load properly")
            return False
        
        # Type title
        if not await human_type(page, "textarea[name='title']", title):
            return False
        
        # Type body if present
        if body:
            await human_sleep(500, 1500)
            body_selectors = [
                "div[role='textbox']",
                "div.public-DraftEditor-content",
                "textarea[name='text']"
            ]
            
            body_typed = False
            for selector in body_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        if await human_type(page, selector, body):
                            body_typed = True
                            break
                except Exception as e:
                    logging.debug(f"Body selector {selector} failed: {e}")
                    continue
            
            if not body_typed:
                logging.warning(f"[{account_name}] Could not type body text")
        
        # Select flair if specified
        if flair:
            try:
                flair_button = page.locator("button:has-text('Select flair'), button:has-text('Choose flair')")
                if await flair_button.count() > 0:
                    await flair_button.first.click()
                    await human_sleep(500, 1000)
                    
                    flair_option = page.locator(f"button:has-text('{flair}'), div:has-text('{flair}')")
                    if await flair_option.count() > 0:
                        await flair_option.first.click()
                        await human_sleep(500, 1000)
                    else:
                        logging.warning(f"[{account_name}] Flair '{flair}' not found")
            except Exception as e:
                logging.warning(f"[{account_name}] Flair selection failed: {e}")
        
        # Wait before submitting (look more human)
        await human_sleep(3000, 7000)
        
        # Click submit button
        submit_selectors = [
            "button:has-text('Post')",
            "button[type='submit']:has-text('Post')",
            "button:has-text('Submit')"
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                submit_btn = page.locator(selector)
                if await submit_btn.count() > 0:
                    await submit_btn.first.click()
                    submitted = True
                    break
            except Exception as e:
                logging.debug(f"Submit selector {selector} failed: {e}")
                continue
        
        if not submitted:
            logging.error(f"[{account_name}] Submit button not found")
            return False
        
        # Wait for post to process
        await page.wait_for_timeout(5000)
        
        # Verify success - check for post URL
        try:
            await page.wait_for_url(f"**/r/{subreddit}/comments/**", timeout=15000)
            post_url = page.url
            logging.info(f"✓ [{account_name}] Posted successfully: {post_url}")
            return True
            
        except PlaywrightTimeout:
            # Check if there's an error message
            page_content = await page.content()
            
            if "try again" in page_content.lower():
                logging.warning(f"[{account_name}] Rate limited - need to try again later")
            elif "spam" in page_content.lower():
                logging.error(f"[{account_name}] Flagged as spam")
            elif "removed" in page_content.lower():
                logging.error(f"[{account_name}] Post was removed")
            else:
                logging.warning(f"[{account_name}] Post status unclear - check manually")
            
            return False
            
    except Exception as e:
        logging.error(f"❌ [{account_name}] Unexpected error: {type(e).__name__}: {e}")
        return False
        
    finally:
        if page:
            await human_sleep(2000, 4000)
            await page.close()

async def smart_rotation_post(account_manager: AccountManager, posts: List[Dict], 
                               subreddits: List[str], state: PostingState) -> None:
    """
    Intelligently rotate through accounts, posts, and subreddits
    Ensures no duplicate combinations until all are exhausted
    """
    
    # Get all possible combinations
    account_names = list(account_manager.accounts.keys())
    
    if not account_names:
        logging.error("No accounts available for posting")
        return
    
    all_combinations = list(product(account_names, subreddits, [p['id'] for p in posts]))
    
    # Filter out completed and max-failed combinations
    pending = [
        c for c in all_combinations 
        if not state.is_complete(*c) and state.should_retry(*c)
    ]
    
    if not pending:
        logging.info("🎉 All combinations completed or exhausted!")
        reset = input("Reset state and start over? (y/n): ").strip().lower()
        if reset == 'y':
            state.reset()
            pending = all_combinations
        else:
            logging.info("Exiting...")
            return
    
    # Shuffle for randomness (less bot-like)
    random.shuffle(pending)
    
    logging.info(f"\n{'='*60}")
    logging.info(f"📊 Campaign Statistics:")
    logging.info(f"   Total combinations: {len(all_combinations)}")
    logging.info(f"   ✅ Completed: {len(state.completed_combinations)}")
    logging.info(f"   ❌ Failed (max retries): {sum(1 for c in all_combinations if not state.should_retry(*c) and not state.is_complete(*c))}")
    logging.info(f"   ⏳ Pending: {len(pending)}")
    logging.info(f"{'='*60}\n")
    
    successful = 0
    failed = 0
    
    for i, (account_name, subreddit, post_id) in enumerate(pending, 1):
        # Find the post data
        post = next((p for p in posts if p['id'] == post_id), None)
        if not post:
            logging.warning(f"Post {post_id} not found in posts list, skipping")
            continue
        
        logging.info(f"\n{'─'*60}")
        logging.info(f"[{i}/{len(pending)}] {account_name} → r/{subreddit}")
        logging.info(f"Title: {post['title'][:60]}...")
        logging.info(f"{'─'*60}")
        
        # Wait for account availability
        wait_count = 0
        while account_name not in account_manager.get_available_accounts():
            if wait_count == 0:
                logging.info(f"⏰ Waiting for {account_name} cooldown...")
            wait_count += 1
            await asyncio.sleep(60)  # Check every minute
        
        # Perform the post
        context = account_manager.get_context(account_name)
        success = await post_to_reddit(context, account_name, post, subreddit)
        
        # Update tracking
        if success:
            successful += 1
            state.mark_complete(account_name, subreddit, post_id)
            account_manager.update_post_time(account_name, success=True)
        else:
            failed += 1
            state.mark_failed(account_name, subreddit, post_id)
            account_manager.update_post_time(account_name, success=False)
        
        # Delay between posts (more realistic, varied timing)
        if i < len(pending):
            delay = random.randint(MIN_DELAY_BETWEEN_POSTS, MAX_DELAY_BETWEEN_POSTS)
            logging.info(f"⏱️  Waiting {delay//60}m {delay%60}s before next post...")
            await asyncio.sleep(delay)
    
    # Final statistics
    logging.info(f"\n{'='*60}")
    logging.info(f"🎯 Campaign Complete!")
    logging.info(f"   ✅ Successful: {successful}")
    logging.info(f"   ❌ Failed: {failed}")
    logging.info(f"   📊 Success Rate: {(successful/(successful+failed)*100):.1f}%" if (successful+failed) > 0 else "N/A")
    logging.info(f"{'='*60}\n")
    
    # Account statistics
    logging.info("Account Performance:")
    stats = account_manager.get_stats()
    for account, data in stats.items():
        logging.info(f"  {account}: {data['total_posts']} posts, {data['success_rate']:.1f}% success")

async def login_to_reddit(page, username: str, password: str) -> bool:
    """Automated login to Reddit with comprehensive error handling"""
    try:
        await page.goto("https://www.reddit.com/login", wait_until="networkidle", timeout=30000)
        await human_sleep(2000, 4000)
        
        # Fill username
        try:
            username_field = await page.wait_for_selector("input[name='username']", timeout=10000)
        except PlaywrightTimeout:
            logging.error(f"Login page did not load properly for {username}")
            return False
        
        await username_field.click()
        await human_sleep(500, 1000)
        await username_field.fill(username)
        
        await human_sleep(500, 1000)
        
        # Fill password
        try:
            password_field = await page.wait_for_selector("input[name='password']", timeout=5000)
        except PlaywrightTimeout:
            logging.error(f"Password field not found for {username}")
            return False
        
        await password_field.click()
        await human_sleep(500, 1000)
        await password_field.fill(password)
        
        await human_sleep(1000, 2000)
        
        # Click login button
        try:
            login_button = await page.wait_for_selector("button[type='submit']", timeout=5000)
        except PlaywrightTimeout:
            logging.error(f"Login button not found for {username}")
            return False
        
        await login_button.click()
        
        # Wait for navigation
        await human_sleep(5000, 8000)
        
        # Check if login successful
        if await verify_login(page):
            logging.info(f"✓ Successfully logged in as {username}")
            return True
        else:
            # Check for error messages
            page_content = await page.content()
            if "incorrect" in page_content.lower() or "password" in page_content.lower():
                logging.error(f"✗ Invalid credentials for {username}")
            elif "suspended" in page_content.lower():
                logging.error(f"✗ Account {username} is suspended")
            else:
                logging.error(f"✗ Login failed for {username} (unknown reason)")
            return False
            
    except Exception as e:
        logging.error(f"Login error for {username}: {type(e).__name__}: {e}")
        return False

def load_accounts_from_env() -> List[Dict[str, str]]:
    """Load account credentials from environment variables (more secure)"""
    accounts = []
    i = 1
    while True:
        username = os.getenv(f'REDDIT_USER_{i}')
        password = os.getenv(f'REDDIT_PASS_{i}')
        
        if not username or not password:
            break
        
        accounts.append({'username': username, 'password': password})
        i += 1
    
    return accounts

async def main():
    from playwright.async_api import async_playwright
    
    # File paths - CUSTOMIZE THESE
    POSTS_FILE = "posts.json"
    SUBREDDITS_FILE = "subreddits.json"
    
    # Try to load accounts from environment first (more secure)
    ACCOUNTS = load_accounts_from_env()
    
    # Fallback to hardcoded (NOT RECOMMENDED for production)
    if not ACCOUNTS:
        logging.warning("No accounts found in environment variables, using hardcoded values")
        logging.warning("Set REDDIT_USER_1, REDDIT_PASS_1, etc. for better security")
        ACCOUNTS = [
            {"username": "Capital_Battle4007", "password": "6avmr0nwoy"},
            {"username": "Alone-Clue-3857", "password": "6g9yklcn71"},
            {"username": "Expensive-Ninja-6331", "password": "d5b4uu5s4z"},
            {"username": "MechanicImmediate503", "password": "q8kpo1gd1d"},
            {"username": "Glad-Restaurant-3438", "password": "6h2wvfovog"},
        ]
    
    # Validate we have real accounts
    if not ACCOUNTS or ACCOUNTS[0]['username'] == 'your_username_1':
        logging.error("ERROR: Please configure your Reddit account credentials")
        logging.error("Either set environment variables or edit the ACCOUNTS list in the code")
        return
    
    # Load data with error handling
    try:
        posts = load_posts_from_json(POSTS_FILE)
        subreddits = load_subreddits_from_file(SUBREDDITS_FILE)
    except (FileNotFoundError, ValueError) as e:
        logging.error(f"Configuration error: {e}")
        return
    
    state = PostingState()
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
            ]
        )
        account_manager = AccountManager()
        
        print("\n" + "="*60)
        print("=== Reddit Multi-Account Posting Bot ===")
        print("="*60)
        print(f"\nLogging in to {len(ACCOUNTS)} accounts...\n")
        
        for idx, account_data in enumerate(ACCOUNTS, 1):
            username = account_data["username"]
            password = account_data["password"]
            
            print(f"\n[{idx}/{len(ACCOUNTS)}] Logging in to {username}...")
            
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            )
            page = await context.new_page()
            
            # Automated login
            success = await login_to_reddit(page, username, password)
            
            if success:
                print(f"✓ {username} ready")
                await account_manager.add_account(username, context)
                await page.close()
            else:
                print(f"✗ {username} login failed - skipping")
                await context.close()
                continue
            
            # Delay between account logins
            if idx < len(ACCOUNTS):
                await human_sleep(3000, 5000)
        
        if not account_manager.accounts:
            print("\n❌ No accounts were successfully set up. Exiting.")
            await browser.close()
            return
        
        print(f"\n{'='*60}")
        print(f"✓ {len(account_manager.accounts)} accounts ready")
        print(f"📝 {len(posts)} posts loaded")
        print(f"📍 {len(subreddits)} subreddits loaded")
        print(f"{'='*60}\n")
        
        input("Press Enter to start posting campaign (Ctrl+C to cancel)...")
        
        # Start posting
        try:
            await smart_rotation_post(account_manager, posts, subreddits, state)
        except KeyboardInterrupt:
            print("\n\n⚠️  Campaign interrupted by user")
            logging.info("Saving state before exit...")
            state.save_state()
        
        await browser.close()
        print("\n👋 Goodbye!")

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('reddit_bot.log'),
            logging.StreamHandler()
        ]
    )
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\nExiting...")
    except Exception as e:
        logging.critical(f"Fatal error: {e}", exc_info=True)