"""
Twitter posting module for TradeUp X Engager Viral Content Generator.
Posts original content and replies to tweets on the TradeUp X account.
"""

import os
import time
import re
import random
from typing import Dict, Any, List, Optional
import tweepy

from src.config import TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET

def post_original_tweet(content: str) -> Dict[str, Any]:
    """
    Post an original tweet to the TradeUp X account.
    
    Args:
        content: Text content of the tweet
        
    Returns:
        Dictionary with posting results
    """
    # Check if we have API credentials
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        print("Twitter API credentials not found. Please add them to your .env file.")
        return {
            'success': False,
            'error': 'Missing Twitter API credentials',
            'tweet_id': None
        }
    
    max_retries = 5 # Increased retries
    initial_delay = 10 # Increased initial delay to 10 seconds

    for attempt in range(max_retries):
        try:
            # Add a delay before making the request to avoid rate limiting
            delay = initial_delay * (2 ** attempt)
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
                print(f"Successfully posted original tweet")
                print(f"Tweet ID: {tweet_id}")
                
                # Create result object
                result = {
                    'success': True,
                    'tweet_id': tweet_id,
                    'content': content
                }
                
                return result
            else:
                print(f"Failed to post tweet. Response: {response}")
                return {
                    'success': False,
                    'error': f'Failed to post tweet: {response}',
                    'tweet_id': None
                }
                
        except tweepy.TweepyException as e:
            error_message = str(e)
            print(f"Error posting tweet: {error_message}")
            if "Too Many Requests" in error_message and attempt < max_retries - 1:
                print(f"Rate limit hit (Attempt {attempt + 1}/{max_retries}). Retrying...")
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
        'error': 'Failed to post tweet after multiple retries due to rate limiting.',
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
    # Check if we have API credentials
    if not all([TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET]):
        print("Twitter API credentials not found. Please add them to your .env file.")
        return {
            'success': False,
            'error': 'Missing Twitter API credentials',
            'tweet_id': None
        }
    
    max_retries = 5
    initial_delay = 10

    for attempt in range(max_retries):
        try:
            # Add a delay before making the request to avoid rate limiting
            delay = initial_delay * (2 ** attempt)
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
                print(f"Successfully posted reply tweet")
                print(f"Reply Tweet ID: {reply_id}")
                
                # Create result object
                result = {
                    'success': True,
                    'tweet_id': reply_id,
                    'replied_to': tweet_id_to_reply_to,
                    'content': content
                }
                
                return result
            else:
                print(f"Failed to post reply. Response: {response}")
                return {
                    'success': False,
                    'error': f'Failed to post reply: {response}',
                    'tweet_id': None
                }
                
        except tweepy.TweepyException as e:
            error_message = str(e)
            print(f"Error posting reply: {error_message}")
            if "Too Many Requests" in error_message and attempt < max_retries - 1:
                print(f"Rate limit hit (Attempt {attempt + 1}/{max_retries}). Retrying...")
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
        'error': 'Failed to post reply after multiple retries due to rate limiting.',
        'tweet_id': None
    }

def get_tweet_url(tweet_id: str) -> str:
    """
    Generate a URL for a tweet based on its ID.
    
    Args:
        tweet_id: Twitter tweet ID
        
    Returns:
        URL to the tweet
    """
    # We don't know the exact username from the API response,
    # but we can use the TradeUp account name since we're posting from it
    return f"https://x.com/TradeUpApp/status/{tweet_id}"
