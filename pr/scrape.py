import asyncio
import json
from playwright.async_api import async_playwright
from pathlib import Path

PROFILE_URL = "https://x.com/i/communities/1501203242641932292"
OUTPUT_FILE = "my_tweets4.json"
MAX_SCROLLS = 200  # Safety limit to prevent infinite loops

async def extract_all_tweets():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1280, "height": 800}
        )
        
        page = await context.new_page()
        
        try:
            print(f"Loading profile: {PROFILE_URL}")
            await page.goto(PROFILE_URL, timeout=60000)
            
            # Wait for either tweets or "no tweets" message
            try:
                await page.wait_for_selector("article", timeout=10000)
            except:
                print("No tweets found or profile is private/doesn't exist")
                await browser.close()
                return
            
            tweets = {}
            scroll_count = 0
            no_new_tweets_count = 0
            
            print("Starting to extract tweets...")
            
            while scroll_count < MAX_SCROLLS:
                articles = await page.query_selector_all("article")
                initial_count = len(tweets)
                
                for a in articles:
                    try:
                        # More specific selectors
                        link = await a.query_selector("a[href*='/status/']")
                        text_el = await a.query_selector("div[data-testid='tweetText']")
                        time_el = await a.query_selector("time")
                        
                        if not link or not time_el:
                            continue
                        
                        url = await link.get_attribute("href")
                        timestamp = await time_el.get_attribute("datetime")
                        text = await text_el.inner_text() if text_el else ""
                        
                        # Extract engagement metrics if available
                        likes_el = await a.query_selector("div[data-testid='like']")
                        retweets_el = await a.query_selector("div[data-testid='retweet']")
                        replies_el = await a.query_selector("div[data-testid='reply']")
                        
                        likes = await likes_el.inner_text() if likes_el else "0"
                        retweets = await retweets_el.inner_text() if retweets_el else "0"
                        replies = await replies_el.inner_text() if replies_el else "0"
                        
                        tweets[url] = {
                            "url": f"https://twitter.com{url}",
                            "timestamp": timestamp,
                            "text": text,
                            "likes": likes,
                            "retweets": retweets,
                            "replies": replies
                        }
                    except Exception as e:
                        # Skip problematic tweets but continue
                        continue
                
                # Check if we found new tweets
                new_count = len(tweets) - initial_count
                if new_count == 0:
                    no_new_tweets_count += 1
                    if no_new_tweets_count >= 3:
                        print("No new tweets found after 3 scrolls. Stopping.")
                        break
                else:
                    no_new_tweets_count = 0
                    print(f"Found {len(tweets)} tweets so far...")
                
                # Scroll down
                await page.mouse.wheel(0, 5000)
                await asyncio.sleep(1.5)  # Slightly longer wait
                scroll_count += 1
            
            print(f"\nExtraction complete! Found {len(tweets)} unique tweets")
            
        except Exception as e:
            print(f"Error during scraping: {e}")
        finally:
            await browser.close()
        
        # Save results
        if tweets:
            tweet_list = sorted(
                tweets.values(), 
                key=lambda x: x['timestamp'], 
                reverse=True
            )
            
            output_path = Path(OUTPUT_FILE)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(tweet_list, f, indent=2, ensure_ascii=False)
            
            print(f"Saved to {output_path.absolute()}")
        else:
            print("No tweets to save")

if __name__ == "__main__":
    asyncio.run(extract_all_tweets())