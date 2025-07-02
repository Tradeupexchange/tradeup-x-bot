"""
Google Sheets reader for TradeUp X Engager.
Reads tweet data directly from Google Sheets using Google Sheets API.
Modified to read from LAST entries first (most recent tweets).
Uses Google Drive API to automatically find the most recent sheet.
"""

import logging
import re
import random
import os
import json
import tempfile
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

# Configuration - using your existing environment variable setup
def get_service_account_file():
    """Get service account file path, supporting both file path and JSON content."""
    # Method 1: JSON content as environment variable (for Railway deployment)
    json_content = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE')
    if json_content:
        try:
            parsed_json = json.loads(json_content)
            # Create temporary file for the session
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
                json.dump(parsed_json, f)
                return f.name
        except json.JSONDecodeError:
            logging.error("❌ Invalid JSON in GOOGLE_SERVICE_ACCOUNT_FILE")
    
    # Method 2: File path (for local development)
    file_path = os.getenv('GOOGLE_SERVICE_ACCOUNT_FILE', 'service-account-key.json')
    if os.path.exists(file_path):
        return file_path
    
    return None

SERVICE_ACCOUNT_FILE = get_service_account_file()
DRIVE_FOLDER_ID = os.getenv('GOOGLE_DRIVE_FOLDER_ID', '')
SCOPES = [
    'https://www.googleapis.com/auth/drive.readonly',
    'https://www.googleapis.com/auth/spreadsheets.readonly'
]

def get_google_services():
    """
    Create and return Google Drive and Sheets service objects.
    
    Returns:
        Tuple of (drive_service, sheets_service) or (None, None) if setup fails
    """
    if not GOOGLE_API_AVAILABLE:
        logging.error("Google API libraries not available. Install with: pip install google-api-python-client google-auth")
        return None, None
    
    if not SERVICE_ACCOUNT_FILE:
        logging.error("Service account file not found")
        logging.info("Please set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
        return None, None
    
    if not os.path.exists(SERVICE_ACCOUNT_FILE):
        logging.error(f"Service account file not found: {SERVICE_ACCOUNT_FILE}")
        return None, None
    
    try:
        credentials = service_account.Credentials.from_service_account_file(
            SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        
        drive_service = build('drive', 'v3', credentials=credentials)
        sheets_service = build('sheets', 'v4', credentials=credentials)
        
        return drive_service, sheets_service
    
    except Exception as e:
        logging.error(f"Failed to create Google services: {e}")
        return None, None

def get_most_recent_sheet_id(folder_id: str = None) -> Optional[str]:
    """
    Get the ID of the most recently modified Google Sheet in a folder.
    
    Args:
        folder_id: Google Drive folder ID. If None, uses DRIVE_FOLDER_ID
        
    Returns:
        Sheet ID or None if not found
    """
    if not folder_id:
        folder_id = DRIVE_FOLDER_ID
    
    if not folder_id:
        logging.error("No folder ID provided. Set GOOGLE_DRIVE_FOLDER_ID environment variable")
        return None
    
    drive_service, _ = get_google_services()
    if not drive_service:
        return None
    
    try:
        # Query for Google Sheets in the specific folder, ordered by modification time
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
        
        logging.info(f"🔍 Searching for sheets in folder: {folder_id}")
        
        results = drive_service.files().list(
            q=query,
            orderBy='modifiedTime desc',  # Most recently modified first
            fields='files(id, name, modifiedTime)',
            pageSize=1  # Only get the most recent
        ).execute()
        
        files = results.get('files', [])
        
        if files:
            most_recent = files[0]
            sheet_id = most_recent['id']
            
            logging.info(f"✅ Found most recent sheet: {most_recent['name']}")
            logging.info(f"📅 Last modified: {most_recent['modifiedTime']}")
            logging.info(f"🆔 Sheet ID: {sheet_id}")
            
            return sheet_id
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
    
    drive_service, _ = get_google_services()
    if not drive_service:
        return []
    
    try:
        query = f"'{folder_id}' in parents and mimeType='application/vnd.google-apps.spreadsheet'"
        
        results = drive_service.files().list(
            q=query,
            orderBy='modifiedTime desc',
            fields='files(id, name, modifiedTime)',
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

def get_tweets_from_sheet(sheet_id: str, max_tweets: int = 50, reverse_order: bool = True) -> List[Dict]:
    """
    Get tweets from a Google Sheet using Google Sheets API directly.
    
    Args:
        sheet_id: Google Sheet ID
        max_tweets: Maximum number of tweets to read
        reverse_order: If True, reads from last entries first (most recent)
        
    Returns:
        List of tweet data dictionaries compatible with FastAPI format
    """
    tweets = []
    
    try:
        _, sheets_service = get_google_services()
        if not sheets_service:
            return tweets
        
        logging.info(f"📊 Fetching data from Google Sheet: {sheet_id}")
        if reverse_order:
            logging.info(f"🔄 Reading from LAST entries first (most recent tweets)")
        
        # Get sheet metadata to find the range
        sheet_metadata = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        sheets = sheet_metadata.get('sheets', [])
        
        if not sheets:
            logging.warning("No worksheets found in spreadsheet")
            return tweets
        
        # Use the first worksheet
        worksheet = sheets[0]
        sheet_title = worksheet['properties']['title']
        
        if reverse_order:
            # First, get headers from the top
            header_range = f"{sheet_title}!1:1"
            header_result = sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=header_range
            ).execute()
            
            header_values = header_result.get('values', [])
            if not header_values:
                logging.warning("Sheet has no headers")
                return tweets
            
            headers = header_values[0]
            
            # Then get all data to find the actual last row with data
            all_data_range = f"{sheet_title}!A:Z"
            all_result = sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=all_data_range
            ).execute()
            
            all_values = all_result.get('values', [])
            if len(all_values) <= 1:  # Only headers or empty
                logging.warning("Sheet has no data rows")
                return tweets
            
            # Find the last row with actual data
            last_row_with_data = len(all_values)
            for i in range(len(all_values) - 1, 0, -1):  # Start from end, skip header
                if any(cell.strip() for cell in all_values[i] if cell):
                    last_row_with_data = i + 1  # +1 because sheets are 1-indexed
                    break
            
            logging.info(f"📊 Last row with data: {last_row_with_data}")
            
            # Now read from bottom up, but limit to max_tweets + some buffer
            start_row = max(2, last_row_with_data - max_tweets * 2)  # Start higher up to get enough data
            range_name = f"{sheet_title}!A{start_row}:{chr(ord('A') + len(headers) - 1)}{last_row_with_data}"
            
            logging.info(f"🔄 Reading from bottom up: {range_name}")
            
        else:
            # Read normally from top
            range_name = f"{sheet_title}!A:Z"
            
            # Get headers first
            header_result = sheets_service.spreadsheets().values().get(
                spreadsheetId=sheet_id,
                range=f"{sheet_title}!1:1"
            ).execute()
            
            header_values = header_result.get('values', [])
            if not header_values:
                logging.warning("Sheet has no headers")
                return tweets
            
            headers = header_values[0]
        
        # Get the actual data
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=range_name
        ).execute()
        
        values = result.get('values', [])
        
        if not values:
            logging.warning("Sheet is empty")
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
        
        # Process data rows 
        if reverse_order:
            # For reverse order, we already got the bottom portion
            data_rows = values  # These are already the bottom rows
            # Process in reverse order (newest first)
            data_rows = list(reversed(data_rows))
            start_row_num = last_row_with_data - len(data_rows) + 1
        else:
            # For normal order, skip header row
            data_rows = values[1:] if len(values) > 1 else []
            start_row_num = 2
        
        # Filter out empty rows
        valid_rows = []
        for i, row in enumerate(data_rows):
            row_num = start_row_num + (len(data_rows) - 1 - i if reverse_order else i)
            # Ensure row has enough columns and tweet content exists
            if len(row) > tweet_idx and tweet_idx < len(row) and row[tweet_idx].strip():
                valid_rows.append((row_num, row))
            else:
                logging.debug(f"Skipping row {row_num}: insufficient columns or empty tweet")
        
        logging.info(f"📊 Found {len(valid_rows)} valid rows in sheet")
        
        if reverse_order:
            logging.info(f"🔄 Reading from bottom up - processing most recent entries first")
        
        # Process the rows (now in the desired order)
        count = 0
        for row_num, row in valid_rows:
            if count >= max_tweets:
                break
            
            # Safely get tweet content
            tweet_content = row[tweet_idx].strip() if tweet_idx < len(row) else ""
            if not tweet_content:
                continue
            
            # Create tweet data in FastAPI-compatible format
            tweet_data = {
                "id": f"sheet_tweet_{count + 1}",  # Generate ID for tweets without one
                "text": tweet_content,
                "created_at": datetime.now().isoformat(),  # Default to now
            }
            
            # Add optional fields if available
            if date_idx is not None and date_idx < len(row) and row[date_idx].strip():
                tweet_data["created_at"] = row[date_idx].strip()
                
            if url_idx is not None and url_idx < len(row) and row[url_idx].strip():
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
            if username_idx is not None and username_idx < len(row) and row[username_idx].strip():
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
        
    except Exception as e:
        logging.error(f"❌ Error reading Google Sheet: {e}")
    
    return tweets

def get_tweets_from_sheet_by_url(sheet_url: str, max_tweets: int = 50, reverse_order: bool = True) -> List[Dict]:
    """
    Get tweets from a Google Sheet using a URL.
    
    Args:
        sheet_url: URL of the Google Sheet
        max_tweets: Maximum number of tweets to read
        reverse_order: If True, reads from last entries first (most recent)
        
    Returns:
        List of tweet data dictionaries
    """
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        logging.error(f"Could not extract sheet ID from URL: {sheet_url}")
        return []
    
    return get_tweets_from_sheet(sheet_id, max_tweets, reverse_order)

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
    # Get the most recent sheet ID
    sheet_id = get_most_recent_sheet_id(folder_id)
    
    if not sheet_id:
        logging.error("❌ Could not find most recent sheet")
        return []
    
    # Use existing function to read tweets from the sheet
    return get_tweets_from_sheet(sheet_id, max_tweets, reverse_order)

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
    # Get tweets either from specific sheet or most recent sheet
    if sheet_url:
        all_tweets = get_tweets_from_sheet_by_url(sheet_url, max_tweets=100, reverse_order=reverse_order)
    else:
        all_tweets = get_tweets_from_most_recent_sheet(folder_id, max_tweets=100, reverse_order=reverse_order)
    
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
        tweets = get_tweets_from_sheet_by_url(sheet_url, max_tweets=5, reverse_order=True)
        
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
                "message": "No folder ID provided. Set GOOGLE_DRIVE_FOLDER_ID environment variable."
            }
        
        # Test getting all sheets in folder
        sheets = get_all_sheets_in_folder(folder_id, max_sheets=5)
        
        if sheets:
            most_recent_id = get_most_recent_sheet_id(folder_id)
            result = {
                "success": True,
                "sheets_found": len(sheets),
                "most_recent_sheet": sheets[0]['name'] if sheets else None,
                "most_recent_id": most_recent_id,
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
    
    print("🧪 Testing Google Drive and Sheets API connection...")
    
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
        print("2. Set GOOGLE_SERVICE_ACCOUNT_FILE or GOOGLE_SERVICE_ACCOUNT_JSON environment variable")
        print("3. Set GOOGLE_DRIVE_FOLDER_ID environment variable to your Google Drive folder ID")
        print("4. Share the folder with your service account email")