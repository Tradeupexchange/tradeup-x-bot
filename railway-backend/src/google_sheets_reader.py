"""
Google Sheets reader for TradeUp X Engager.
Reads tweet data from public Google Sheets for reply generation.
Modified to read from LAST entries first (most recent tweets).
"""

import requests
import logging
import re
import csv
import random
from io import StringIO
from typing import List, Dict, Optional
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_sheet_id(sheet_url: str) -> Optional[str]:
    """
    Extract the sheet ID from a Google Sheets URL.
    
    Args:
        sheet_url: URL of the Google Sheet
        
    Returns:
        Sheet ID or None if not found
    """
    pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, sheet_url)
    if match:
        return match.group(1)
    return None

def extract_tweet_id_from_url(url: str) -> Optional[str]:
    """
    Extract the tweet ID from a Twitter/X URL.
    
    Args:
        url: Twitter/X URL
        
    Returns:
        Tweet ID or None if not found
    """
    if not url:
        return None
        
    # Pattern for Twitter/X URLs: https://twitter.com/username/status/1234567890123456789
    # or https://x.com/username/status/1234567890123456789
    pattern = r"(?:twitter\.com|x\.com)/\w+/status/(\d+)"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def extract_username_from_url(url: str) -> Optional[str]:
    """
    Extract the username from a Twitter/X URL.
    
    Args:
        url: Twitter/X URL
        
    Returns:
        Username or None if not found
    """
    if not url:
        return None
        
    # Pattern for Twitter/X URLs to extract username
    pattern = r"(?:twitter\.com|x\.com)/(\w+)/status/\d+"
    match = re.search(pattern, url)
    if match:
        return match.group(1)
    return None

def get_tweets_from_sheet(sheet_url: str, max_tweets: int = 50, reverse_order: bool = True) -> List[Dict]:
    """
    Get tweets from a public Google Sheet using direct CSV export.
    
    Args:
        sheet_url: URL of the Google Sheet
        max_tweets: Maximum number of tweets to read
        reverse_order: If True, reads from last entries first (most recent)
        
    Returns:
        List of tweet data dictionaries compatible with FastAPI format
    """
    tweets = []
    
    try:
        # Extract sheet ID from URL
        sheet_id = extract_sheet_id(sheet_url)
        if not sheet_id:
            logging.error(f"Could not extract sheet ID from URL: {sheet_url}")
            return tweets
            
        # Construct CSV export URL
        csv_export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv"
        
        logging.info(f"📊 Fetching data from Google Sheet: {sheet_id}")
        if reverse_order:
            logging.info(f"🔄 Reading from LAST entries first (most recent tweets)")
        
        # Fetch CSV data
        response = requests.get(csv_export_url, timeout=10)
        response.raise_for_status()
        
        # Parse CSV data
        csv_data = StringIO(response.text)
        reader = csv.reader(csv_data)
        
        # Extract header row
        headers = next(reader, None)
        if not headers:
            logging.warning("Sheet is empty or has no headers")
            return tweets
            
        # Clean headers (remove whitespace)
        headers = [header.strip() for header in headers]
        logging.info(f"📋 Sheet headers: {headers}")
        
        # Find the indices of important columns (case-insensitive)
        header_map = {header.lower(): i for i, header in enumerate(headers)}
        
        # Try different variations of column names
        tweet_idx = None
        for possible_name in ['tweet', 'tweet_content', 'content', 'text']:
            if possible_name in header_map:
                tweet_idx = header_map[possible_name]
                break
        
        date_idx = header_map.get('date') or header_map.get('created_at')
        username_idx = header_map.get('username') or header_map.get('user') or header_map.get('author')
        url_idx = header_map.get('url') or header_map.get('link') or header_map.get('tweet_url')
        
        if tweet_idx is None:
            logging.error(f"Tweet column not found. Available columns: {list(header_map.keys())}")
            return tweets
        
        logging.info(f"🎯 Using columns - Tweet: {tweet_idx}, Date: {date_idx}, Username: {username_idx}, URL: {url_idx}")
        
        # Read ALL data rows first
        all_rows = []
        for row_num, row in enumerate(reader, start=2):  # Start at 2 since we already read headers
            if len(row) <= tweet_idx or not row[tweet_idx].strip():
                logging.debug(f"Skipping row {row_num}: insufficient columns or empty tweet")
                continue
            
            all_rows.append((row_num, row))
        
        logging.info(f"📊 Found {len(all_rows)} valid rows in sheet")
        
        # REVERSE the order if requested (most recent first)
        if reverse_order:
            all_rows = list(reversed(all_rows))
            logging.info(f"🔄 Reversed order - now processing from most recent entries")
        
        # Process the rows (now in the desired order)
        count = 0
        for row_num, row in all_rows:
            if count >= max_tweets:
                break
                
            tweet_content = row[tweet_idx].strip()
            
            # Create tweet data in FastAPI-compatible format
            tweet_data = {
                "id": f"sheet_tweet_{count + 1}",  # Generate ID for tweets without one
                "text": tweet_content,
                "created_at": datetime.now().isoformat(),  # Default to now
            }
            
            # Add optional fields if available
            if date_idx is not None and len(row) > date_idx and row[date_idx].strip():
                tweet_data["created_at"] = row[date_idx].strip()
                
            if url_idx is not None and len(row) > url_idx and row[url_idx].strip():
                url = row[url_idx].strip()
                tweet_data["url"] = url
                
                # Extract tweet ID and username from URL
                tweet_id = extract_tweet_id_from_url(url)
                username = extract_username_from_url(url)
                
                if tweet_id:
                    tweet_data["id"] = tweet_id
                    tweet_data["conversation_id"] = tweet_id
                    
                if username:
                    tweet_data["author"] = username
                    tweet_data["author_name"] = username.title()  # Capitalize for display
            
            # Use username from dedicated column if available and not already set
            if username_idx is not None and len(row) > username_idx and row[username_idx].strip():
                username = row[username_idx].strip()
                tweet_data["author"] = username.replace('@', '')  # Remove @ if present
                tweet_data["author_name"] = username.replace('@', '').title()
            
            # Ensure we have at least basic author info
            if "author" not in tweet_data:
                tweet_data["author"] = "unknown_user"
                tweet_data["author_name"] = "Unknown User"
            
            tweets.append(tweet_data)
            count += 1
            
            logging.debug(f"✅ Processed tweet {count}: {tweet_content[:50]}...")
        
        if reverse_order:
            logging.info(f"✅ Successfully read {len(tweets)} tweets from Google Sheet (most recent first)")
        else:
            logging.info(f"✅ Successfully read {len(tweets)} tweets from Google Sheet (chronological order)")
        
    except requests.exceptions.RequestException as e:
        logging.error(f"❌ Network error reading Google Sheet: {e}")
    except Exception as e:
        logging.error(f"❌ Error reading Google Sheet: {e}")
    
    return tweets

def get_tweets_for_reply(sheet_url: str, num_tweets: int = 5, reverse_order: bool = True) -> List[Dict]:
    """
    Get a selection of tweets from the Google Sheet that are suitable for replying to.
    
    Args:
        sheet_url: URL of the Google Sheet
        num_tweets: Number of tweets to select for reply
        reverse_order: If True, prioritizes most recent tweets
        
    Returns:
        List of tweet data dictionaries with URLs in FastAPI format
    """
    # Get all tweets from the sheet (with reverse order)
    all_tweets = get_tweets_from_sheet(sheet_url, max_tweets=100, reverse_order=reverse_order)
    
    if not all_tweets:
        logging.warning("⚠️ No tweets found in the sheet")
        return []
    
    # Filter tweets that have URLs/IDs (required for replying)
    tweets_with_urls = []
    for tweet in all_tweets:
        # Check if tweet has the necessary info for replying
        has_id = tweet.get("id") and not tweet["id"].startswith("sheet_tweet_")
        has_url = tweet.get("url")
        
        if has_id or has_url:
            tweets_with_urls.append(tweet)
    
    if not tweets_with_urls:
        logging.warning("⚠️ No tweets with valid URLs/IDs found in the sheet")
        # Return some tweets anyway for testing, but warn about missing URLs
        selected_tweets = all_tweets[:num_tweets]
        for tweet in selected_tweets:
            if not tweet.get("url"):
                # Generate a placeholder URL for testing
                tweet["url"] = f"https://twitter.com/{tweet['author']}/status/{tweet['id']}"
        return selected_tweets
    
    # If reverse_order is True, we already have the most recent tweets first
    # So we can just take the first N tweets
    if len(tweets_with_urls) <= num_tweets:
        selected_tweets = tweets_with_urls
    else:
        if reverse_order:
            # Take the first N (which are the most recent due to reverse order)
            selected_tweets = tweets_with_urls[:num_tweets]
        else:
            # Randomly select if not prioritizing recent tweets
            selected_tweets = random.sample(tweets_with_urls, num_tweets)
    
    if reverse_order:
        logging.info(f"🎲 Selected {len(selected_tweets)} most recent tweets for reply generation")
    else:
        logging.info(f"🎲 Selected {len(selected_tweets)} random tweets for reply generation")
    
    return selected_tweets

def get_tweets_from_sheet_chronological(sheet_url: str, max_tweets: int = 50) -> List[Dict]:
    """
    Convenience function to get tweets in chronological order (oldest first).
    
    Args:
        sheet_url: URL of the Google Sheet
        max_tweets: Maximum number of tweets to read
        
    Returns:
        List of tweet data dictionaries in chronological order
    """
    return get_tweets_from_sheet(sheet_url, max_tweets, reverse_order=False)

def get_tweets_from_sheet_recent_first(sheet_url: str, max_tweets: int = 50) -> List[Dict]:
    """
    Convenience function to get tweets with most recent first.
    
    Args:
        sheet_url: URL of the Google Sheet
        max_tweets: Maximum number of tweets to read
        
    Returns:
        List of tweet data dictionaries with most recent first
    """
    return get_tweets_from_sheet(sheet_url, max_tweets, reverse_order=True)

def test_sheet_connection(sheet_url: str) -> Dict:
    """
    Test the connection to a Google Sheet and return status info.
    
    Args:
        sheet_url: URL of the Google Sheet
        
    Returns:
        Dictionary with connection test results
    """
    try:
        # Test with reverse order (most recent first)
        tweets = get_tweets_from_sheet(sheet_url, max_tweets=5, reverse_order=True)
        
        result = {
            "success": True,
            "tweets_found": len(tweets),
            "sample_tweets": tweets[:3] if tweets else [],
            "message": f"Successfully connected to Google Sheet. Found {len(tweets)} tweets (showing most recent first)."
        }
        
        if not tweets:
            result["success"] = False
            result["message"] = "Connected to sheet but no tweets found. Check your sheet format."
            
        return result
        
    except Exception as e:
        return {
            "success": False,
            "tweets_found": 0,
            "sample_tweets": [],
            "message": f"Failed to connect to Google Sheet: {str(e)}"
        }

if __name__ == "__main__":
    # Example usage and testing
    sheet_url = "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0"
    
    print("🧪 Testing Google Sheets connection...")
    test_result = test_sheet_connection(sheet_url)
    print(f"Test result: {test_result}")
    
    if test_result["success"]:
        print(f"\n📊 Retrieved {test_result['tweets_found']} tweets from Google Sheet (most recent first)")
        for i, tweet in enumerate(test_result["sample_tweets"]):
            print(f"Tweet {i+1}: {tweet.get('text', 'No content')[:100]}...")
            if tweet.get('url'):
                print(f"  URL: {tweet['url']}")
            if tweet.get('author'):
                print(f"  Author: @{tweet['author']}")
        
        # Test getting tweets for reply (most recent first)
        print(f"\n🎯 Testing reply tweet selection (most recent first)...")
        reply_tweets = get_tweets_for_reply(sheet_url, 3, reverse_order=True)
        print(f"Selected {len(reply_tweets)} most recent tweets for reply:")
        for i, tweet in enumerate(reply_tweets):
            print(f"Reply Tweet {i+1}: {tweet.get('text', 'No content')[:80]}...")
            print(f"  URL: {tweet.get('url', 'No URL')}")
            print(f"  ID: {tweet.get('id', 'No ID')}")
            print(f"  Author: @{tweet.get('author', 'unknown')}")
            
        # Test chronological order as well
        print(f"\n📈 Testing chronological order (oldest first)...")
        chrono_tweets = get_tweets_from_sheet_chronological(sheet_url, 3)
        print(f"Selected {len(chrono_tweets)} tweets in chronological order:")
        for i, tweet in enumerate(chrono_tweets):
            print(f"Chrono Tweet {i+1}: {tweet.get('text', 'No content')[:80]}...")
    else:
        print(f"❌ Connection test failed: {test_result['message']}")