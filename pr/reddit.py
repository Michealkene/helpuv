import asyncio
import logging
import random
from datetime import datetime, timedelta
from playwright.async_api import TimeoutError as PlaywrightTimeout

# Configuration
COOLDOWN_HOURS = 24
MAX_RETRIES = 3
last_post_times = {}

async def human_sleep(min_ms, max_ms):
    """Simulate human-like delays with randomization"""
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)

async def human_type(page, selector, text, delay_range=(50, 150)):
    """Type text with human-like delays between keystrokes"""
    element = await page.wait_for_selector(selector)
    await element.click()
    await human_sleep(300, 800)
    
    for char in text:
        await element.type(char, delay=random.randint(*delay_range))
        # Occasional longer pauses (thinking)
        if random.random() < 0.1:
            await human_sleep(300, 1000)

async def detect_captcha(page):
    """Check for CAPTCHA presence and wait for manual solving"""
    captcha_selectors = [
        "iframe[src*='recaptcha']",
        "iframe[src*='hcaptcha']",
        ".g-recaptcha",
        "#captcha"
    ]
    
    for selector in captcha_selectors:
        try:
            if await page.locator(selector).count() > 0:
                logging.warning("⚠️ CAPTCHA detected! Waiting for manual solve...")
                logging.warning("Please solve the CAPTCHA in the browser window")
                
                # Wait up to 5 minutes for CAPTCHA to be solved
                for _ in range(60):
                    await asyncio.sleep(5)
                    if await page.locator(selector).count() == 0:
                        logging.info("✓ CAPTCHA appears to be solved")
                        return True
                
                logging.error("CAPTCHA not solved within timeout")
                return False
        except:
            continue
    
    return False

async def verify_login(page):
    """Verify user is logged in before attempting to post"""
    try:
        # Check for user menu (indicates logged in)
        await page.wait_for_selector("[id*='user-menu']", timeout=5000)
        return True
    except:
        logging.error("Not logged in! Please log in first.")
        return False

async def post_to_reddit(context, post, headless=False):
    """
    Post to Reddit with human-like behavior and error handling
    
    Args:
        context: Playwright browser context
        post: Dict with keys: subreddit, title, body (optional), flair (optional)
        headless: Whether browser is headless (affects CAPTCHA handling)
    """
    subreddit = post["subreddit"]
    title = post["title"]
    body = post.get("body", "")
    flair = post.get("flair")
    
    # Check cooldown
    last_time = last_post_times.get(subreddit)
    if last_time and datetime.now() - last_time < timedelta(hours=COOLDOWN_HOURS):
        time_remaining = timedelta(hours=COOLDOWN_HOURS) - (datetime.now() - last_time)
        logging.info(f"⏸️ Skipping r/{subreddit}: cooldown active. {time_remaining} remaining.")
        return False
    
    page = await context.new_page()
    logging.info(f"📝 Attempting to post to r/{subreddit}: '{title[:50]}...'")
    
    try:
        # Initial human-like pause
        await human_sleep(2000, 5000)
        
        # Navigate to submit page
        submit_url = f"https://www.reddit.com/r/{subreddit}/submit"
        await page.goto(submit_url, wait_until="networkidle")
        
        # Verify login status
        if not await verify_login(page):
            logging.error("Login required. Aborting post.")
            return False
        
        # Wait for title field
        try:
            await page.wait_for_selector("textarea[name='title']", timeout=15000)
        except PlaywrightTimeout:
            logging.error(f"Submit page didn't load for r/{subreddit}")
            return False
        
        # Type title with human-like behavior
        logging.info("Typing title...")
        await human_type(page, "textarea[name='title']", title)
        
        # Type body if provided
        if body:
            logging.info("Typing body content...")
            await human_sleep(500, 1500)
            
            # Try multiple selectors for the body field
            body_selectors = [
                "div[role='textbox']",
                "div.public-DraftEditor-content",
                "textarea[name='text']"
            ]
            
            body_typed = False
            for selector in body_selectors:
                try:
                    if await page.locator(selector).count() > 0:
                        await human_type(page, selector, body)
                        body_typed = True
                        break
                except:
                    continue
            
            if not body_typed:
                logging.warning("Couldn't find body field, skipping body text")
        
        # Select flair if provided
        if flair:
            try:
                await page.click("button:has-text('Select flair')")
                await human_sleep(500, 1000)
                await page.click(f"button:has-text('{flair}')")
                await human_sleep(500, 1000)
                logging.info(f"Selected flair: {flair}")
            except:
                logging.warning(f"Couldn't select flair '{flair}'")
        
        # Human hesitation before submitting
        await human_sleep(3000, 7000)
        
        # Find and click submit button
        submit_selectors = [
            "button:has-text('Post')",
            "button[type='submit']",
            "button:has-text('Submit')"
        ]
        
        submitted = False
        for selector in submit_selectors:
            try:
                if await page.locator(selector).count() > 0:
                    await page.click(selector)
                    submitted = True
                    logging.info("Submit button clicked")
                    break
            except:
                continue
        
        if not submitted:
            logging.error("Couldn't find submit button")
            return False
        
        # Wait for submission to process
        await page.wait_for_timeout(5000)
        
        # Check for CAPTCHA
        if await detect_captcha(page):
            if headless:
                logging.error("CAPTCHA detected in headless mode - cannot solve")
                return False
            logging.info("CAPTCHA solved, continuing...")
        
        # Check if post was successful by looking for success indicators
        try:
            # Wait for URL change or success message
            await page.wait_for_url(f"**/r/{subreddit}/comments/**", timeout=10000)
            logging.info(f"✓ Post successfully submitted to r/{subreddit}")
            last_post_times[subreddit] = datetime.now()
            
            # Get the post URL
            post_url = page.url
            logging.info(f"Post URL: {post_url}")
            
            return True
        except PlaywrightTimeout:
            # Check for error messages
            error_selectors = [
                "text='You are doing that too much'",
                "text='Please try again later'",
                "[role='alert']"
            ]
            
            for selector in error_selectors:
                if await page.locator(selector).count() > 0:
                    error_text = await page.locator(selector).inner_text()
                    logging.error(f"Reddit error: {error_text}")
                    return False
            
            logging.warning("Post status unclear - check manually")
            return False
            
    except Exception as e:
        logging.error(f"❌ Post failed for r/{subreddit}: {type(e).__name__}: {e}")
        return False
        
    finally:
        # Keep page open briefly to avoid suspicious behavior
        await human_sleep(2000, 4000)
        await page.close()

async def batch_post(context, posts, headless=False):
    """
    Post multiple items with delays between them
    
    Args:
        context: Playwright browser context
        posts: List of post dictionaries
        headless: Whether browser is headless
    """
    successful = 0
    failed = 0
    
    for i, post in enumerate(posts, 1):
        logging.info(f"\n[{i}/{len(posts)}] Processing post...")
        
        success = await post_to_reddit(context, post, headless)
        
        if success:
            successful += 1
        else:
            failed += 1
        
        # Long delay between posts (very important!)
        if i < len(posts):
            delay = random.randint(300, 900)  # 5-15 minutes
            logging.info(f"Waiting {delay}s before next post...")
            await asyncio.sleep(delay)
    
    logging.info(f"\n=== Batch Complete ===")
    logging.info(f"Successful: {successful}")
    logging.info(f"Failed: {failed}")

# Example usage
async def main():
    from playwright.async_api import async_playwright
    
    posts = [
        {
            "subreddit": "test",
            "title": "This is a test post",
            "body": "Testing automated posting with safety measures.",
            "flair": None
        }
    ]
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)  # Use headless=False for CAPTCHA
        context = await browser.new_context()
        
        # You'll need to log in first - either manually or with saved session
        logging.info("Please log in to Reddit manually...")
        page = await context.new_page()
        await page.goto("https://www.reddit.com/login")
        
        # Wait for manual login
        input("Press Enter after logging in...")
        await page.close()
        
        # Now post
        await batch_post(context, posts, headless=False)
        
        await browser.close()

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    asyncio.run(main())