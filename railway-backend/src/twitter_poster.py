"""
Twitter posting module for TradeUp X Engager Viral Content Generator.
Posts original content and replies to tweets on the TradeUp X account.
Simplified version with single attempt only - no retries.
"""

import os
import time
import re
import random
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
import tweepy

from src.config import TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET

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
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        
        # Single attempt to post the reply
        response = client.create_tweet(
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
        
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        
        # Test authentication
        me = client.get_me()
        
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