"""
Twitter posting module for TradeUp X Engager Viral Content Generator.
Posts original content to the TradeUp X account.
"""

import os
import time
import re
from typing import Dict, Any, List, Optional
import tweepy

from config import TWITTER_API_KEY, TWITTER_API_SECRET, TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET

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
    
    try:
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
            
    except Exception as e:
        error_message = str(e)
        print(f"Error posting tweet: {error_message}")
        return {
            'success': False,
            'error': error_message,
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