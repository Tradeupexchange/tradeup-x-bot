"""
Google Sheets reader for TradeUp X Engager.
Reads tweet data from public Google Sheets for reply generation.
Modified to read from LAST entries first (most recent tweets).
Enhanced with Google Drive API to automatically find the most recent sheet.
"""

import requests
import logging
import re
import csv
import random
import os
from io import StringIO
from typing import List, Dict, Optional
from datetime import datetime

# Google API imports
try:
    from google.oauth2 import service_account
    from googleapiclient.discovery import build
    GOOGLE_API_AVAILABLE = True
except ImportError:
    GOOGLE_API_AVAILABLE = False
    logging.warning("Google API libraries not installed. Install with: pip install google-api-python-client google-auth")

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Configuration
SERVICE_ACCOUNT_FILE = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account-key.json')
DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')  # Set this to your folder ID
SCOPES = ['https://www.googleapis.com/auth/drive.readonly']

def get_drive_service():
    """
    Create and return a Google Drive service object.
    
    Returns:
        Google Drive service object or None if setup fails
    """
    if not GOOGLE_API_AVAILABLE:
        logging.error("Google API libraries not available. Install with: pip install google-api-python-client google-auth")
        return None
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logging.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        logging.info("Please download your service account JSON file and update the SERVICE_ACCOUNT_FILE path")
        return None
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        drive_service = build('drive', 'v3', credentials=credentials)
        return drive_service
    
    except Exception as e:
        logging.error(f"Failed to create Google Drive service: {e}")
        return None

def get_most_recent_sheet_url(folder_id: str = None) -> Optional[str]:
    """
    Get the URL of the most recently modified Google Sheet in a folder.
    
    Args:
        folder_id: Google Drive folder ID. If None, uses DRIVE_FOLDER_ID
        
    Returns:
        URL of the most recent sheet or None if not found
    """
    if not folder_id:
        folder_id = DRIVE_FOLDER_ID
    
    if not folder_id:
        logging.error("No folder ID provided. Set DRIVE_FOLDER_ID environment variable or pass folder_id parameter")
        return None
    
    drive_service = get_drive_service()
    if not drive_service:
        return None
    
    try:
        # Query for Google Sheets in the specific folder, ordered by modification time
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
        
        logging.info(f"🔍 Searching for sheets in folder: {folder_id}")
        
        results = drive_service.files().list(
            q=query,
            orderBy='modifiedTime desc',  # Most recently modified first
            fields='files(id, name, modifiedTime, webViewLink)',
            pageSize=1  # Only get the most recent
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            most_recent = files[0]
            sheet_url = f"https://docs.google.com/spreadsheets/d/{most_recent['id']}/edit"
            
            logging.info(f"✅ Found most recent sheet: {most_recent['name']}")
            logging.info(f"📅 Last modified: {most_recent['modifiedTime']}")
            logging.info(f"🔗 Sheet URL: {sheet_url}")
            
            return sheet_url
        else:
            logging.warning(f"❌ No Google Sheets found in folder {folder_id}")
            logging.info("Make sure:")
            logging.info("1. The folder ID is correct")
            logging.info("2. The service account has access to the folder")
            logging.info("3. There are Google Sheets in the folder")
            return None
            
    except Exception as e:
        logging.error(f"❌ Error accessing Google Drive: {e}")
        logging.info("Check that:")
        logging.info("1. Service account file is valid")
        logging.info("2. Service account has access to the folder")
        logging.info("3. Google Drive API is enabled in your project")
        return None

def get_all_sheets_in_folder(folder_id: str = None, max_sheets: int = 10) -> List[Dict]:
    """
    Get information about all Google Sheets in a folder.
    
    Args:
        folder_id: Google Drive folder ID. If None, uses DRIVE_FOLDER_ID
        max_sheets: Maximum number of sheets to return
        
    Returns:
        List of sheet information dictionaries
    """
    if not folder_id:
        folder_id = DRIVE_FOLDER_ID
    
    if not folder_id:
        logging.error("No folder ID provided")
        return []
    
    drive_service = get_drive_service()
    if not drive_service:
        return []
    
    try:
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
        
        results = drive_service.files().list(
            q=query,
            orderBy='modifiedTime desc',
            fields='files(id, name, modifiedTime, webViewLink)',
            pageSize=max_sheets
        ).execute()
        
        files = results.get('files', [])
        
        sheets_info = []
        for file in files:
            sheet_info = {
                'id': file['id'],
                'name': file['name'],
                'modified_time': file['modifiedTime'],
                'url': f"https://docs.google.com/spreadsheets/d/{file['id']}/edit"
            }
            sheets_info.append(sheet_info)
        
        logging.info(f"📊 Found {len(sheets_info)} sheets in folder")
        return sheets_info
        
    except Exception as e:
        logging.error(f"❌ Error getting sheets from folder: {e}")
        return []

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

def get_tweets_from_most_recent_sheet(folder_id: str = None, max_tweets: int = 50, reverse_order: bool = True) -> List[Dict]:
    """
    Get tweets from the most recently modified sheet in a Google Drive folder.
    
    Args:
        folder_id: Google Drive folder ID. If None, uses DRIVE_FOLDER_ID
        max_tweets: Maximum number of tweets to read
        reverse_order: If True, reads from last entries first (most recent)
        
    Returns:
        List of tweet data dictionaries
    """
    # Get the most recent sheet URL
    sheet_url = get_most_recent_sheet_url(folder_id)
    
    if not sheet_url:
        logging.error("❌ Could not find most recent sheet")
        return []
    
    # Use existing function to read tweets from the sheet
    return get_tweets_from_sheet(sheet_url, max_tweets, reverse_order)

def get_tweets_for_reply(sheet_url: str = None, folder_id: str = None, num_tweets: int = 5, reverse_order: bool = True) -> List[Dict]:
    """
    Get a selection of tweets suitable for replying to.
    Can use either a specific sheet URL or automatically find the most recent sheet in a folder.
    
    Args:
        sheet_url: URL of a specific Google Sheet (takes priority over folder_id)
        folder_id: Google Drive folder ID to find most recent sheet
        num_tweets: Number of tweets to select for reply
        reverse_order: If True, prioritizes most recent tweets
        
    Returns:
        List of tweet data dictionaries with URLs in FastAPI format
    """
    # If no sheet_url provided, try to get the most recent sheet from folder
    if not sheet_url:
        sheet_url = get_most_recent_sheet_url(folder_id)
        if not sheet_url:
            logging.error("❌ No sheet URL provided and could not find most recent sheet")
            return []
    
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

def test_drive_connection(folder_id: str = None) -> Dict:
    """
    Test the connection to Google Drive and return status info.
    
    Args:
        folder_id: Google Drive folder ID. If None, uses DRIVE_FOLDER_ID
        
    Returns:
        Dictionary with connection test results
    """
    try:
        if not folder_id:
            folder_id = DRIVE_FOLDER_ID
        
        if not folder_id:
            return {
                "success": False,
                "message": "No folder ID provided. Set DRIVE_FOLDER_ID environment variable."
            }
        
        # Test getting all sheets in folder
        sheets = get_all_sheets_in_folder(folder_id, max_sheets=5)
        
        if sheets:
            most_recent_url = get_most_recent_sheet_url(folder_id)
            result = {
                "success": True,
                "sheets_found": len(sheets),
                "most_recent_sheet": sheets[0]['name'] if sheets else None,
                "most_recent_url": most_recent_url,
                "message": f"Successfully connected to Google Drive. Found {len(sheets)} sheets in folder."
            }
        else:
            result = {
                "success": False,
                "sheets_found": 0,
                "message": "Connected to Google Drive but no sheets found in folder. Check folder ID and permissions."
            }
        
        return result
        
    except Exception as e:
        return {
            "success": False,
            "sheets_found": 0,
            "message": f"Failed to connect to Google Drive: {str(e)}"
        }

if __name__ == "__main__":
    # Example usage and testing
    
    print("🧪 Testing Google Drive API connection...")
    
    # Test 1: Drive connection
    drive_test = test_drive_connection()
    print(f"Drive test result: {drive_test}")
    
    if drive_test["success"]:
        print(f"\n📊 Found {drive_test['sheets_found']} sheets in folder")
        print(f"🏆 Most recent sheet: {drive_test['most_recent_sheet']}")
        
        # Test 2: Read from most recent sheet automatically
        print(f"\n🎯 Testing automatic most recent sheet reading...")
        recent_tweets = get_tweets_from_most_recent_sheet(max_tweets=5)
        
        if recent_tweets:
            print(f"✅ Successfully read {len(recent_tweets)} tweets from most recent sheet:")
            for i, tweet in enumerate(recent_tweets):
                print(f"Tweet {i+1}: {tweet.get('text', 'No content')[:100]}...")
                if tweet.get('url'):
                    print(f"  URL: {tweet['url']}")
                if tweet.get('author'):
                    print(f"  Author: @{tweet['author']}")
        
        # Test 3: Get tweets for reply from most recent sheet
        print(f"\n🎲 Testing reply tweet selection from most recent sheet...")
        reply_tweets = get_tweets_for_reply(num_tweets=3, reverse_order=True)
        print(f"Selected {len(reply_tweets)} tweets for reply:")
        for i, tweet in enumerate(reply_tweets):
            print(f"Reply Tweet {i+1}: {tweet.get('text', 'No content')[:80]}...")
            print(f"  URL: {tweet.get('url', 'No URL')}")
            print(f"  ID: {tweet.get('id', 'No ID')}")
            print(f"  Author: @{tweet.get('author', 'unknown')}")
    
    else:
        print(f"❌ Drive connection failed: {drive_test['message']}")
        print("\n📋 Setup checklist:")
        print("1. Install Google API libraries: pip install google-api-python-client google-auth")
        print("2. Set SERVICE_ACCOUNT_FILE environment variable or place 'service-account-key.json' in current directory")
        print("3. Set DRIVE_FOLDER_ID environment variable to your Google Drive folder ID")
        print("4. Share the folder with your service account email")
        
        # Fallback: Test with manual sheet URL if provided
        fallback_url = "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0"
        print(f"\n🔄 Falling back to manual sheet URL test...")
        manual_test = test_sheet_connection(fallback_url)
        print(f"Manual test result: {manual_test}")