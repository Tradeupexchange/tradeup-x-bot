import requests
import logging
import re
import csv
import random
from io import StringIO

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def extract_sheet_id(sheet_url):
    """
    Extract the sheet ID from a Google Sheets URL.
    
    :param sheet_url: URL of the Google Sheet
    :return: Sheet ID or None if not found
    """
    pattern = r"/spreadsheets/d/([a-zA-Z0-9-_]+)"
    match = re.search(pattern, sheet_url)
    if match:
        return match.group(1)
    return None

def extract_tweet_id_from_url(url):
    """
    Extract the tweet ID from a Twitter/X URL.
    
    :param url: Twitter/X URL
    :return: Tweet ID or None if not found
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

def get_tweets_from_sheet(sheet_url, max_tweets=20):
    """
    Get tweets from a public Google Sheet using direct CSV export.
    
    :param sheet_url: URL of the Google Sheet
    :param max_tweets: Maximum number of tweets to read
    :return: List of tweet data dictionaries
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
            
        # Find the indices of important columns
        tweet_idx = headers.index("Tweet") if "Tweet" in headers else None
        date_idx = headers.index("Date") if "Date" in headers else None
        username_idx = headers.index("Username") if "Username" in headers else None
        url_idx = headers.index("URL") if "URL" in headers else None
        
        if tweet_idx is None:
            logging.error("Tweet column not found in sheet")
            return tweets
        
        # Process data rows
        count = 0
        for row in reader:
            if count >= max_tweets:
                break
                
            if len(row) <= tweet_idx or not row[tweet_idx].strip():
                continue  # Skip rows that don't have enough columns or empty tweet content
            
            tweet_data = {
                "tweet_content": row[tweet_idx].strip()
            }
            
            # Add optional fields if available
            if date_idx is not None and len(row) > date_idx:
                tweet_data["date"] = row[date_idx]
            if username_idx is not None and len(row) > username_idx:
                tweet_data["username"] = row[username_idx]
            if url_idx is not None and len(row) > url_idx and row[url_idx].strip():
                tweet_data["url"] = row[url_idx].strip()
                tweet_data["tweet_id"] = extract_tweet_id_from_url(row[url_idx].strip())
            
            tweets.append(tweet_data)
            count += 1
        
        logging.info(f"Successfully read {len(tweets)} tweets from Google Sheet")
        
    except Exception as e:
        logging.error(f"Error reading Google Sheet: {e}")
    
    return tweets

def get_tweets_for_reply(sheet_url, num_tweets=5):
    """
    Get a selection of tweets from the Google Sheet that are suitable for replying to.
    
    :param sheet_url: URL of the Google Sheet
    :param num_tweets: Number of tweets to select for reply
    :return: List of tweet data dictionaries with URLs
    """
    # Get all tweets from the sheet
    all_tweets = get_tweets_from_sheet(sheet_url, max_tweets=50)  # Get more tweets to have a better selection
    
    # Filter tweets that have URLs (required for replying)
    tweets_with_urls = [tweet for tweet in all_tweets if "url" in tweet and tweet["url"] and "tweet_id" in tweet and tweet["tweet_id"]]
    
    if not tweets_with_urls:
        logging.warning("No tweets with valid URLs found in the sheet")
        return []
    
    # If we have fewer tweets with URLs than requested, return all of them
    if len(tweets_with_urls) <= num_tweets:
        return tweets_with_urls
    
    # Otherwise, randomly select the requested number of tweets
    return random.sample(tweets_with_urls, num_tweets)

if __name__ == "__main__":
    # Example usage
    sheet_url = "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0"
    tweets = get_tweets_from_sheet(sheet_url)
    
    print(f"Retrieved {len(tweets)} tweets from Google Sheet")
    for i, tweet in enumerate(tweets[:5]):  # Print first 5 tweets
        print(f"Tweet {i+1}: {tweet.get('tweet_content', 'No content')}")
        if "url" in tweet:
            print(f"  URL: {tweet['url']}")
        if "tweet_id" in tweet:
            print(f"  Tweet ID: {tweet['tweet_id']}")
    
    # Test getting tweets for reply
    reply_tweets = get_tweets_for_reply(sheet_url, 3)
    print(f"\nSelected {len(reply_tweets)} tweets for reply:")
    for i, tweet in enumerate(reply_tweets):
        print(f"Reply Tweet {i+1}: {tweet.get('tweet_content', 'No content')}")
        print(f"  URL: {tweet.get('url', 'No URL')}")
        print(f"  Tweet ID: {tweet.get('tweet_id', 'No ID')}")
