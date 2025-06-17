"""
Twitter posting module for TradeUp X Engager Viral Content Generator.
Posts original content and replies to tweets on the TradeUp X account.
Enhanced with rate limit debugging and improved error handling.
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

def get_rate_limit_info(client):
    """Get current rate limit information from Twitter API"""
    try:
        # This endpoint shows rate limit status
        me = client.get_me()
        return {"authenticated": True, "user": me.data.username if me.data else "unknown"}
    except Exception as e:
        return {"authenticated": False, "error": str(e)}

def post_original_tweet_simple(content: str) -> Dict[str, Any]:
    """
    Simple single-attempt tweet posting for debugging rate limit issues.
    Use this to test if the issue is with retry logic.
    """
    global last_post_time
    
    # Check if we have API credentials
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
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
        print(f"🐦 Making single Twitter API request...")
        print(f"📝 Content: {content}")
        print(f"📏 Length: {len(content)} characters")
        
        # Set up Tweepy client
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        
        # Get rate limit info
        rate_info = get_rate_limit_info(client)
        print(f"🔐 Auth status: {rate_info}")
        
        # Single attempt - no retries for testing
        print(f"🚀 Posting tweet...")
        response = client.create_tweet(text=content)
        
        if response and hasattr(response, 'data') and 'id' in response.data:
            tweet_id = response.data['id']
            last_post_time = datetime.now()  # Update last post time
            
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
        
        # Try to get rate limit reset time
        try:
            reset_time = e.response.headers.get('x-rate-limit-reset')
            if reset_time:
                reset_datetime = datetime.fromtimestamp(int(reset_time))
                print(f"⏰ Rate limit resets at: {reset_datetime}")
        except:
            pass
            
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

def post_original_tweet(content: str) -> Dict[str, Any]:
    """
    Post an original tweet to the TradeUp X account.
    Now with improved rate limiting and debugging.
    
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
    
    # First try the simple approach to avoid hammering the API
    print("🧪 Attempting simple post first...")
    simple_result = post_original_tweet_simple(content)
    
    # If simple approach worked, return it
    if simple_result['success']:
        return simple_result
    
    # If it's rate limited, don't retry
    if simple_result.get('rate_limited'):
        print("🛑 Rate limited - not retrying to avoid making it worse")
        return simple_result
    
    # Only retry for non-rate-limit errors
    print("🔄 Simple approach failed with non-rate-limit error, trying with retries...")
    
    max_retries = 3  # Reduced from 5 to avoid API abuse
    initial_delay = 30  # Increased initial delay
    
    for attempt in range(max_retries):
        try:
            # Longer delays to be more respectful of rate limits
            delay = initial_delay * (attempt + 1)  # Linear instead of exponential
            print(f"Attempt {attempt + 1}/{max_retries}: Waiting {delay} seconds before posting...")
            time.sleep(delay)

            # Print detailed debug info
            print(f"Posting original tweet as TradeUp X account")
            print(f"API credentials available: {bool(TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_SECRET)}")
            print(f"Content length: {len(content)} characters")
            
            # Set up Tweepy client
            client = tweepy.Client(
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_SECRET
            )
            
            # Post the tweet
            response = client.create_tweet(text=content)
            
            # Check if tweet was created successfully
            if response and hasattr(response, 'data') and 'id' in response.data:
                tweet_id = response.data['id']
                last_post_time = datetime.now()
                
                print(f"Successfully posted original tweet")
                print(f"Tweet ID: {tweet_id}")
                
                # Create result object
                result = {
                    'success': True,
                    'tweet_id': tweet_id,
                    'content': content,
                    'url': get_tweet_url(tweet_id),
                    'posted_at': last_post_time.isoformat()
                }
                
                return result
            else:
                print(f"Failed to post tweet. Response: {response}")
                return {
                    'success': False,
                    'error': f'Failed to post tweet: {response}',
                    'tweet_id': None
                }
                
        except tweepy.TooManyRequests as e:
            error_message = f"Rate limit exceeded: {str(e)}"
            print(f"Rate limit hit (Attempt {attempt + 1}/{max_retries}): {error_message}")
            
            # Don't retry rate limit errors - they just make it worse
            return {
                'success': False,
                'error': error_message,
                'tweet_id': None,
                'rate_limited': True
            }
            
        except tweepy.TweepyException as e:
            error_message = str(e)
            print(f"Error posting tweet: {error_message}")
            if "Too Many Requests" in error_message:
                print(f"Rate limit hit (Attempt {attempt + 1}/{max_retries}). Stopping retries.")
                return {
                    'success': False,
                    'error': error_message,
                    'tweet_id': None,
                    'rate_limited': True
                }
            elif attempt < max_retries - 1:
                print(f"Non-rate-limit error, will retry...")
            else:
                return {
                    'success': False,
                    'error': error_message,
                    'tweet_id': None
                }
        except Exception as e:
            error_message = str(e)
            print(f"Error posting tweet: {error_message}")
            return {
                'success': False,
                'error': error_message,
                'tweet_id': None
            }
    
    return {
        'success': False,
        'error': 'Failed to post tweet after multiple retries.',
        'tweet_id': None
    }

def post_reply_tweet(content: str, tweet_id_to_reply_to: str) -> Dict[str, Any]:
    """
    Post a reply to an existing tweet.
    
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
    
    max_retries = 3  # Reduced retries
    initial_delay = 30

    for attempt in range(max_retries):
        try:
            # Add a delay before making the request to avoid rate limiting
            delay = initial_delay * (attempt + 1)
            if attempt > 0:  # No delay on first attempt
                print(f"Attempt {attempt + 1}/{max_retries}: Waiting {delay} seconds before posting reply...")
                time.sleep(delay)

            # Print detailed debug info
            print(f"Posting reply to tweet {tweet_id_to_reply_to} as TradeUp X account")
            print(f"API credentials available: {bool(TWITTER_API_KEY and TWITTER_API_SECRET and TWITTER_ACCESS_TOKEN and TWITTER_ACCESS_SECRET)}")
            print(f"Content length: {len(content)} characters")
            
            # Set up Tweepy client
            client = tweepy.Client(
                consumer_key=TWITTER_API_KEY,
                consumer_secret=TWITTER_API_SECRET,
                access_token=TWITTER_ACCESS_TOKEN,
                access_token_secret=TWITTER_ACCESS_SECRET
            )
            
            # Post the reply
            response = client.create_tweet(
                text=content,
                in_reply_to_tweet_id=tweet_id_to_reply_to
            )
            
            # Check if reply was created successfully
            if response and hasattr(response, 'data') and 'id' in response.data:
                reply_id = response.data['id']
                last_post_time = datetime.now()
                
                print(f"Successfully posted reply tweet")
                print(f"Reply Tweet ID: {reply_id}")
                
                # Create result object
                result = {
                    'success': True,
                    'tweet_id': reply_id,
                    'replied_to': tweet_id_to_reply_to,
                    'content': content,
                    'url': get_tweet_url(reply_id),
                    'posted_at': last_post_time.isoformat()
                }
                
                return result
            else:
                print(f"Failed to post reply. Response: {response}")
                return {
                    'success': False,
                    'error': f'Failed to post reply: {response}',
                    'tweet_id': None
                }
                
        except tweepy.TooManyRequests as e:
            error_message = f"Rate limit exceeded: {str(e)}"
            print(f"Rate limit hit during reply (Attempt {attempt + 1}/{max_retries}): {error_message}")
            return {
                'success': False,
                'error': error_message,
                'tweet_id': None,
                'rate_limited': True
            }
            
        except tweepy.TweepyException as e:
            error_message = str(e)
            print(f"Error posting reply: {error_message}")
            if "Too Many Requests" in error_message:
                return {
                    'success': False,
                    'error': error_message,
                    'tweet_id': None,
                    'rate_limited': True
                }
            elif attempt < max_retries - 1:
                print(f"Non-rate-limit error, will retry...")
            else:
                return {
                    'success': False,
                    'error': error_message,
                    'tweet_id': None
                }
        except Exception as e:
            error_message = str(e)
            print(f"Error posting reply: {error_message}")
            return {
                'success': False,
                'error': error_message,
                'tweet_id': None
            }
    
    return {
        'success': False,
        'error': 'Failed to post reply after multiple retries.',
        'tweet_id': None
    }

def test_twitter_connection() -> Dict[str, Any]:
    """
    Test Twitter API connection without posting anything.
    Use this to debug authentication and rate limit issues.
    """
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        return {
            'success': False,
            'error': 'Missing Twitter API credentials'
        }
    
    try:
        client = tweepy.Client(
            consumer_key=TWITTER_API_KEY,
            consumer_secret=TWITTER_API_SECRET,
            access_token=TWITTER_ACCESS_TOKEN,
            access_token_secret=TWITTER_ACCESS_SECRET
        )
        
        # Test authentication
        me = client.get_me()
        
        if me.data:
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
        'can_post_now': True
    }
    
    if last_post_time:
        time_since = datetime.now() - last_post_time
        stats['time_since_last_post'] = time_since.total_seconds()
        stats['can_post_now'] = time_since.total_seconds() >= 60
    
    return stats