"""
Twitter posting module for TradeUp X Engager Viral Content Generator.
Posts original content and replies to tweets on the TradeUp X account.
Integrated with Google Sheets for pulling tweets and generating AI responses.
"""

import os
import sys
import time
import re
import random
import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import tweepy
from openai import OpenAI

# Add the parent directory to sys.path if running directly
if __name__ == "__main__" and "src" not in sys.path:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from src.config import (
    TWITTER_API_KEY, 
    TWITTER_API_SECRET, 
    TWITTER_ACCESS_TOKEN, 
    TWITTER_ACCESS_SECRET,
    OPENAI_API_KEY
)

try:
    from src.google_sheets_reader import get_tweets_for_reply, get_tweets_from_most_recent_sheet
except ImportError:
    print("Warning: google_sheets_reader not found. Google Sheets functionality will be limited.")
    get_tweets_for_reply = None
    get_tweets_from_most_recent_sheet = None

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Global variable to track last post time for rate limiting
last_post_time = None

def post_original_tweet(content: str) -> Dict[str, Any]:
    """
    Post an original tweet to the TradeUp X account.
    Single attempt only - no retries.
    
    Args:
        content: Text content of the tweet
        
    Returns:
        Dictionary with posting results
    """
    global last_post_time
    
    # Check if we have API credentials
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        print("Twitter API credentials not found. Please add them to your .env file.")
        return {
            'success': False,
            'error': 'Missing Twitter API credentials',
            'tweet_id': None
        }
    
    # Enforce minimum 60 seconds between posts
    if last_post_time:
        time_since_last = datetime.now() - last_post_time
        if time_since_last.total_seconds() < 60:
            wait_time = 60 - time_since_last.total_seconds()
            print(f"⏰ Waiting {wait_time:.0f}s to avoid rate limit...")
            time.sleep(wait_time)
    
    try:
        print(f"🐦 Posting tweet to Twitter...")
        print(f"📝 Content: {content}")
        print(f"📏 Length: {len(content)} characters")
        
        # Set up Tweepy client
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        
        # Single attempt to post the tweet
        response = client.create_tweet(text=content)
        
        # Check if tweet was created successfully
        if response and hasattr(response, 'data') and 'id' in response.data:
            tweet_id = response.data['id']
            last_post_time = datetime.now()
            
            print(f"✅ Successfully posted tweet!")
            print(f"🆔 Tweet ID: {tweet_id}")
            
            return {
                'success': True,
                'tweet_id': tweet_id,
                'content': content,
                'url': get_tweet_url(tweet_id),
                'posted_at': last_post_time.isoformat()
            }
        else:
            print(f"❌ Tweet creation failed: {response}")
            return {
                'success': False,
                'error': f'Tweet creation failed: {response}',
                'tweet_id': None
            }
            
    except tweepy.TooManyRequests as e:
        error_message = f"Rate limit exceeded: {str(e)}"
        print(f"🚫 {error_message}")
        
        return {
            'success': False,
            'error': error_message,
            'tweet_id': None,
            'rate_limited': True
        }
        
    except tweepy.TweepyException as e:
        error_message = f"Twitter API error: {str(e)}"
        print(f"❌ {error_message}")
        return {
            'success': False,
            'error': error_message,
            'tweet_id': None
        }
        
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(f"💥 {error_message}")
        return {
            'success': False,
            'error': error_message,
            'tweet_id': None
        }

def post_reply_tweet(content: str, tweet_id_to_reply_to: str) -> Dict[str, Any]:
    """
    Post a reply to an existing tweet.
    Single attempt only - no retries.
    
    Args:
        content: Text content of the reply
        tweet_id_to_reply_to: ID of the tweet to reply to
        
    Returns:
        Dictionary with posting results
    """
    global last_post_time
    
    # Check if we have API credentials
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        print("Twitter API credentials not found. Please add them to your .env file.")
        return {
            'success': False,
            'error': 'Missing Twitter API credentials',
            'tweet_id': None
        }
    
    # Enforce rate limiting
    if last_post_time:
        time_since_last = datetime.now() - last_post_time
        if time_since_last.total_seconds() < 60:
            wait_time = 60 - time_since_last.total_seconds()
            print(f"⏰ Waiting {wait_time:.0f}s before reply to avoid rate limit...")
            time.sleep(wait_time)
    
    try:
        print(f"🐦 Posting reply to tweet {tweet_id_to_reply_to}...")
        print(f"📝 Content: {content}")
        print(f"📏 Length: {len(content)} characters")
        
        # Set up Tweepy client
        twitter_client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        
        # Single attempt to post the reply
        response = twitter_client.create_tweet(
            text=content,
            in_reply_to_tweet_id=tweet_id_to_reply_to
        )
        
        # Check if reply was created successfully
        if response and hasattr(response, 'data') and 'id' in response.data:
            reply_id = response.data['id']
            last_post_time = datetime.now()
            
            print(f"✅ Successfully posted reply!")
            print(f"🆔 Reply ID: {reply_id}")
            
            return {
                'success': True,
                'tweet_id': reply_id,
                'replied_to': tweet_id_to_reply_to,
                'content': content,
                'url': get_tweet_url(reply_id),
                'posted_at': last_post_time.isoformat()
            }
        else:
            print(f"❌ Reply creation failed: {response}")
            return {
                'success': False,
                'error': f'Reply creation failed: {response}',
                'tweet_id': None
            }
            
    except tweepy.TooManyRequests as e:
        error_message = f"Rate limit exceeded: {str(e)}"
        print(f"🚫 {error_message}")
        
        return {
            'success': False,
            'error': error_message,
            'tweet_id': None,
            'rate_limited': True
        }
            
    except tweepy.TweepyException as e:
        error_message = f"Twitter API error: {str(e)}"
        print(f"❌ {error_message}")
        return {
            'success': False,
            'error': error_message,
            'tweet_id': None
        }
        
    except Exception as e:
        error_message = f"Unexpected error: {str(e)}"
        print(f"💥 {error_message}")
        return {
            'success': False,
            'error': error_message,
            'tweet_id': None
        }

def generate_reply_content(tweet_content: str, username: str = None) -> str:
    """
    Generate a custom reply to a tweet using the LLM.
    
    Args:
        tweet_content: Content of the tweet to reply to
        username: Username of the tweet author (if available)
        
    Returns:
        Generated reply content
    """
    # Persona and tone guidelines based on user's prompts
    persona_guidelines = """
    You are TUPokePal, a knowledgeable and passionate Pokémon-card collector. 
    You speak like a real human fan in online communities (e.g., Discord, Twitter), 
    using simple, casual language with collector slang like Alt Art, Zard, chase card, pop report. 
    You never sound like a corporate marketer. Keep replies short (under 200 characters) 
    with max 1 emoji if it fits. Rotate emojis and avoid repeating the same opening lines. 
    Focus on being genuinely helpful and interesting.
    """

    # Construct the prompt for the LLM
    prompt = f"""
    As TUPokePal, generate a friendly, engaging reply to this tweet about Pokémon cards:
    
    Tweet{f" by @{username}" if username else ""}: "{tweet_content}"
    
    Your reply should:
    1. Be 1-2 sentences, max 200 characters
    2. Use casual, friendly language
    3. Include one emoji (rotate 🔥 😍 🤩 😉 🐉 ⚡️)
    4. Respond directly to the content of the tweet
    5. Add value with a quick fact or open question
    6. Occasionally (20% chance) include a soft TradeUp mention
    7. IMPORTANT: DO NOT include any hashtags in your reply
    
    Examples of good replies:
    - "That Charizard is absolute fire! Have you considered getting it graded? 🔥"
    - "Alt arts are my weakness too! Which one is your current chase card? 😍"
    - "Those pulls are insane! If you trade it, TradeUp's got you 😉"
    
    Format your response as plain text, ready to be posted as a reply.
    """

    try:
        reply_content = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Or "gpt-4" for higher quality
            messages=[
                {"role": "system", "content": persona_guidelines},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.8, # Slightly higher temperature for more creativity and variation
        ).choices[0].message.content.strip()
        
        # Remove any hashtags that might have been included despite instructions
        reply_content = re.sub(r'#\w+', '', reply_content).strip()
        
        # Remove all double quotes from the reply content
        reply_content = reply_content.replace('"', '').strip()
        
        logging.info(f"Generated reply: {reply_content}")
        
        return reply_content

    except Exception as e:
        logging.error(f"Error generating reply content: {e}")
        return f"Interesting post about Pokémon cards! What's your favorite card in your collection? 🔥"

def get_user_confirmation(tweet: Dict[str, Any], reply: str) -> tuple[bool, str]:
    """
    Ask for user confirmation before posting a reply.
    
    Args:
        tweet: Original tweet data
        reply: Generated reply content
        
    Returns:
        Tuple: (Boolean indicating whether to post the reply, final reply content)
    """
    print("\n" + "="*60)
    print("ORIGINAL TWEET:")
    print(f"@{tweet.get('author', 'Unknown')}: {tweet.get('text', '')}")
    print(f"URL: {tweet.get('url', 'No URL available')}")
    print("-"*60)
    print("GENERATED REPLY:")
    print(reply)
    print("-"*60)
    
    while True:
        response = input("Confirm this reply? (y/n/edit): ").strip().lower()
        
        if response == 'y':
            return True, reply
        elif response == 'n':
            return False, reply
        elif response == 'edit':
            edited_reply = input("Enter your edited reply: ").strip()
            if edited_reply:
                return True, edited_reply
            else:
                print("Reply cannot be empty. Using original reply.")
                return True, reply # Return original reply if edit is empty
        else:
            print("Please enter 'y' to confirm, 'n' to skip, or 'edit' to modify the reply.")

def fetch_tweets_from_sheets() -> List[Dict[str, Any]]:
    """
    Fetch tweets from the most recent Google Sheet automatically.
    
    Returns:
        List of tweet data dictionaries
    """
    if get_tweets_from_most_recent_sheet is None:
        logging.error("Google Sheets reader not available. Cannot fetch tweets.")
        return []
    
    try:
        logging.info("📊 Starting fetch tweets from sheets...")
        logging.info("📊 Fetching tweets from Google Sheets...")
        
        # Use automatic detection - finds most recent sheet and reads from bottom up
        tweets = get_tweets_from_most_recent_sheet(max_tweets=50, reverse_order=True)
        
        if tweets:
            logging.info(f"✅ Successfully fetched {len(tweets)} tweets from most recent sheet")
            return tweets
        else:
            logging.warning("📊 No tweets found in Google Sheets, falling back to mock data")
            return []
            
    except Exception as e:
        logging.error(f"❌ Error fetching tweets from sheets: {e}")
        logging.warning("📊 Falling back to mock data")
        return []

def generate_and_post_replies(num_replies: int = 5, post_to_twitter: bool = False, require_confirmation: bool = True) -> List[Dict[str, Any]]:
    """
    Generate and optionally post replies to tweets from the Google Sheet.
    
    Args:
        num_replies: Number of replies to generate
        post_to_twitter: Whether to actually post the replies to Twitter
        require_confirmation: Whether to require user confirmation (for API use, set to False)
        
    Returns:
        List of generated replies with metadata
    """
    if get_tweets_for_reply is None:
        logging.error("Google Sheets reader not available. Cannot fetch tweets.")
        return []
    
    # Get tweets to reply to using automatic detection
    tweets_to_reply = get_tweets_for_reply(num_tweets=num_replies, reverse_order=True)
    
    if not tweets_to_reply:
        logging.warning("No tweets found to reply to")
        return []
    
    results = []
    
    for tweet in tweets_to_reply:
        tweet_content = tweet.get('text', '')  # Updated field name
        username = tweet.get('author', '')  # Updated field name
        tweet_id = tweet.get('id')  # Updated field name
        tweet_url = tweet.get('url', '')
        
        if not tweet_id or tweet_id.startswith('sheet_tweet_'):
            logging.warning(f"No valid tweet ID found for tweet: {tweet_content[:50]}...")
            continue
        
        # Generate reply content
        reply_content = generate_reply_content(tweet_content, username)
        
        # Handle confirmation based on API vs manual use
        if require_confirmation:
            should_post_current, final_reply_content = get_user_confirmation(tweet, reply_content)
        else:
            # For API use, auto-approve the generated content
            should_post_current = True
            final_reply_content = reply_content

        result = {
            'original_tweet': tweet_content,
            'username': username,
            'tweet_id': tweet_id,
            'tweet_url': tweet_url,
            'reply_content': final_reply_content, # Use the confirmed/edited reply
            'posted': False
        }
        
        # Post the reply if requested AND confirmed by user
        if post_to_twitter and should_post_current:
            logging.info(f"Posting reply to tweet ID {tweet_id}")
            post_result = post_reply_tweet(final_reply_content, tweet_id)
            
            result['posted'] = post_result.get('success', False)
            result['post_error'] = post_result.get('error', None)
            
            if result['posted']:
                result['reply_id'] = post_result.get('tweet_id')
                result['reply_url'] = f"https://x.com/TradeUpApp/status/{result['reply_id']}"
        elif post_to_twitter and not should_post_current:
            logging.info(f"User chose not to post reply to tweet ID {tweet_id}")
            result['post_error'] = "User chose not to post"
        else:
            # If not posting to Twitter, but user confirmed, just mark as reviewed
            if should_post_current:
                result['post_error'] = "Reviewed, not posted (post_to_twitter is False)"
            else:
                result['post_error'] = "Skipped by user"
        
        results.append(result)
    
    return results

def test_twitter_connection() -> Dict[str, Any]:
    """
    Test Twitter API connection without posting anything.
    Single attempt only.
    """
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        return {
            'success': False,
            'error': 'Missing Twitter API credentials'
        }
    
    try:
        print("🔐 Testing Twitter API connection...")
        
        twitter_client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        
        # Test authentication
        me = twitter_client.get_me()
        
        if me.data:
            print(f"✅ Twitter connection successful!")
            print(f"👤 Connected as: @{me.data.username}")
            
            return {
                'success': True,
                'message': 'Twitter API connection successful',
                'user': {
                    'id': me.data.id,
                    'username': me.data.username,
                    'name': me.data.name
                }
            }
        else:
            return {
                'success': False,
                'error': 'Authentication failed - no user data returned'
            }
            
    except tweepy.TooManyRequests as e:
        return {
            'success': False,
            'error': f'Rate limited even for connection test: {str(e)}',
            'rate_limited': True
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Connection test failed: {str(e)}'
        }

def test_sheets_connection() -> Dict[str, Any]:
    """
    Test Google Sheets connection and fetch sample tweets.
    """
    try:
        tweets = fetch_tweets_from_sheets()
        
        if tweets:
            return {
                'success': True,
                'message': f'Successfully fetched {len(tweets)} tweets from most recent sheet',
                'sample_tweets': tweets[:3],  # Return first 3 as samples
                'total_tweets': len(tweets)
            }
        else:
            return {
                'success': False,
                'error': 'No tweets found in sheets'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': f'Sheets connection test failed: {str(e)}'
        }

def get_tweet_url(tweet_id: str) -> str:
    """
    Generate a URL for a tweet based on its ID.
    
    Args:
        tweet_id: Twitter tweet ID
        
    Returns:
        URL to the tweet
    """
    return f"https://x.com/TradeUpApp/status/{tweet_id}"

def get_posting_stats() -> Dict[str, Any]:
    """
    Get statistics about posting activity.
    """
    global last_post_time
    
    stats = {
        'last_post_time': last_post_time.isoformat() if last_post_time else None,
        'time_since_last_post': None,
        'can_post_now': True,
        'min_interval_seconds': 60
    }
    
    if last_post_time:
        time_since = datetime.now() - last_post_time
        stats['time_since_last_post'] = time_since.total_seconds()
        stats['can_post_now'] = time_since.total_seconds() >= 60
    
    return stats

# Module is designed to be used via API requests - no command line interface