"""
Tweet reply generator for TradeUp X Engager.
Generates custom replies to tweets from the Google Sheet using LLM Manager.
"""

import os
import sys
import random
import json
import logging
import re

# Add the parent directory to sys.path if running directly
if __name__ == "__main__" and "src" not in sys.path:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from src.config import OPENAI_API_KEY
from src.google_sheets_reader import get_tweets_for_reply
from src.twitter_poster import post_reply_tweet

# Try to import LLM Manager with error handling
try:
    from src.llm_manager import llm_manager
    LLM_MANAGER_AVAILABLE = True
    logging.info("✅ Successfully imported LLM Manager")
except ImportError as e:
    logging.error(f"❌ Failed to import LLM Manager: {e}")
    LLM_MANAGER_AVAILABLE = False
    # Fallback to direct OpenAI
    from openai import OpenAI
    client = OpenAI(api_key=OPENAI_API_KEY)

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Google Sheet URL containing tweet examples
TWEETS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0"

def create_custom_reply_prompt(tweet_content, username=None):
    """
    Create a customized prompt for generating replies using the LLM Manager approach.
    
    Args:
        tweet_content: Content of the tweet to reply to
        username: Username of the tweet author (if available)
        
    Returns:
        Formatted prompt string
    """
    return f"""
You are TUPokePal, TradeUp's knowledgeable and passionate Pokémon card collector assistant.

Your personality:
- Speak like a real human fan in online communities (Discord, Twitter style)
- Use casual language with collector slang: Alt Art, Zard, chase card, pop report, banger pull, etc.
- Never sound corporate or robotic
- Be genuinely helpful and engaging
- Rotate between different emojis: 🔥 😍 🤩 😉 🐉 ⚡️ 💎 ✨

TWEET{f" by @{username}" if username else ""}: "{tweet_content}"

Task: Generate a reply that:
1. Is 1-2 sentences, max 200 characters total
2. Responds directly to the tweet content 
3. Uses casual, friendly collector language
4. Includes exactly one emoji (vary your choices)
5. Adds value with a quick insight, fact, or question
6. Occasionally (25% chance) mentions TradeUp for trading

Good reply examples:
- "That Charizard is absolute fire! Have you considered getting it graded? 🔥"
- "Alt arts are my weakness too! What's your current chase card? 😍"
- "Banger pulls! If you're looking to trade any, TradeUp's got you covered 😉"
- "Love that card! The pop report on those is getting interesting 💎"

Format your response exactly like this:
POKEMON_RELATED: YES
REPLY: [Your reply text here]
"""

def generate_reply_content(tweet_content, username=None):
    """
    Generate a custom reply to a tweet using the LLM Manager or fallback to direct OpenAI.
    
    Args:
        tweet_content: Content of the tweet to reply to
        username: Username of the tweet author (if available)
        
    Returns:
        Generated reply content
    """
    try:
        # Create the customized prompt
        prompt = create_custom_reply_prompt(tweet_content, username)
        
        if LLM_MANAGER_AVAILABLE:
            # Use LLM Manager to generate the response with rate limiting
            logging.info("🤖 Using LLM Manager for reply generation")
            response = llm_manager.call_llm(prompt, model="gpt-3.5-turbo")
        else:
            # Fallback to direct OpenAI API
            logging.info("🔄 Using direct OpenAI API (LLM Manager not available)")
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=200
            )
            response = response.choices[0].message.content
        
        # Parse the response to extract the reply
        if "REPLY:" in response:
            reply_match = re.search(r'REPLY:\s*(.*?)

def generate_reply(tweet_text, tweet_author=None, conversation_history=None):
    """
    Generate a reply to a tweet (FastAPI-compatible function).
    
    Args:
        tweet_text: Content of the tweet to reply to
        tweet_author: Username of the tweet author (optional)
        conversation_history: Previous conversation context (optional, not used currently)
        
    Returns:
        Dictionary with reply content and success status
    """
    try:
        reply_content = generate_reply_content(tweet_text, tweet_author)
        return {
            "content": reply_content,
            "success": True
        }
    except Exception as e:
        logging.error(f"Error in generate_reply: {e}")
        return {
            "content": f"Thanks for sharing! Great Pokemon TCG content. 🔥",
            "success": False,
            "error": str(e)
        }

def batch_generate_replies(tweets_data):
    """
    Generate replies for multiple tweets using LLM Manager's batch processing.
    
    Args:
        tweets_data: List of tweet dictionaries
        
    Returns:
        List of results with generated replies
    """
    try:
        # Use LLM Manager's batch processing
        logging.info(f"Batch processing {len(tweets_data)} tweets...")
        
        # Convert tweets to the format expected by LLM Manager
        formatted_tweets = []
        for tweet in tweets_data:
            formatted_tweet = {
                'text': tweet.get('tweet_content', ''),
                'id': tweet.get('tweet_id', ''),
                'username': tweet.get('username', ''),
                'url': tweet.get('url', '')
            }
            formatted_tweets.append(formatted_tweet)
        
        # Use LLM Manager's batch processing
        batch_results = llm_manager.batch_process_tweets(formatted_tweets)
        
        # Process the batch results
        results = []
        for i, (tweet, is_pokemon, reply) in enumerate(batch_results):
            original_tweet_data = tweets_data[i]
            
            # If LLM Manager determined it's Pokemon-related and generated a reply
            if is_pokemon and reply:
                result = {
                    'original_tweet': original_tweet_data.get('tweet_content', ''),
                    'username': original_tweet_data.get('username', ''),
                    'tweet_id': original_tweet_data.get('tweet_id', ''),
                    'tweet_url': original_tweet_data.get('url', ''),
                    'reply_content': reply,
                    'is_pokemon_related': True,
                    'posted': False
                }
            else:
                # Skip non-Pokemon tweets or generate a fallback
                if is_pokemon:
                    # Pokemon-related but no reply generated, create fallback
                    fallback_reply = generate_reply_content(
                        original_tweet_data.get('tweet_content', ''),
                        original_tweet_data.get('username', '')
                    )
                    result = {
                        'original_tweet': original_tweet_data.get('tweet_content', ''),
                        'username': original_tweet_data.get('username', ''),
                        'tweet_id': original_tweet_data.get('tweet_id', ''),
                        'tweet_url': original_tweet_data.get('url', ''),
                        'reply_content': fallback_reply,
                        'is_pokemon_related': True,
                        'posted': False
                    }
                else:
                    # Not Pokemon-related, skip
                    logging.info(f"Skipping non-Pokemon tweet: {original_tweet_data.get('tweet_content', '')[:50]}...")
                    continue
            
            results.append(result)
        
        return results
        
    except Exception as e:
        logging.error(f"Error in batch reply generation: {e}")
        # Fallback to individual processing
        return generate_replies_individually(tweets_data)

def generate_replies_individually(tweets_data):
    """
    Fallback function to generate replies individually if batch processing fails.
    
    Args:
        tweets_data: List of tweet dictionaries
        
    Returns:
        List of results with generated replies
    """
    results = []
    
    for tweet_data in tweets_data:
        try:
            tweet_content = tweet_data.get('tweet_content', '')
            username = tweet_data.get('username', '')
            
            # Generate reply using individual function
            reply_content = generate_reply_content(tweet_content, username)
            
            result = {
                'original_tweet': tweet_content,
                'username': username,
                'tweet_id': tweet_data.get('tweet_id', ''),
                'tweet_url': tweet_data.get('url', ''),
                'reply_content': reply_content,
                'is_pokemon_related': True,  # Assume true since we're generating a reply
                'posted': False
            }
            
            results.append(result)
            
        except Exception as e:
            logging.error(f"Error processing individual tweet: {e}")
            continue
    
    return results

def generate_and_post_replies(num_replies=5, post_to_twitter=False, require_confirmation=False):
    """
    Generate and optionally post replies to tweets from the Google Sheet.
    Uses LLM Manager for efficient batch processing and rate limiting.
    
    Args:
        num_replies: Number of replies to generate
        post_to_twitter: Whether to actually post the replies to Twitter
        require_confirmation: Whether to require user confirmation (not implemented yet)
        
    Returns:
        List of generated replies with metadata
    """
    # Get tweets to reply to
    tweets_to_reply = get_tweets_for_reply(TWEETS_SHEET_URL, num_replies)
    
    if not tweets_to_reply:
        logging.warning("No tweets found to reply to")
        return []
    
    logging.info(f"Processing {len(tweets_to_reply)} tweets for reply generation")
    
    # Use batch processing for efficiency
    results = batch_generate_replies(tweets_to_reply)
    
    if not results:
        logging.warning("No replies generated from batch processing")
        return []
    
    # Post replies if requested
    if post_to_twitter:
        logging.info(f"Posting {len(results)} replies to Twitter...")
        
        for result in results:
            try:
                tweet_id = result.get('tweet_id')
                reply_content = result.get('reply_content')
                
                if not tweet_id or not reply_content:
                    logging.warning(f"Skipping post due to missing data: tweet_id={tweet_id}, reply_content={reply_content}")
                    continue
                
                logging.info(f"Posting reply to tweet ID {tweet_id}: {reply_content[:50]}...")
                post_result = post_reply_tweet(reply_content, tweet_id)
                
                result['posted'] = post_result.get('success', False)
                result['post_error'] = post_result.get('error', None)
                
                if result['posted']:
                    result['reply_id'] = post_result.get('tweet_id')
                    result['reply_url'] = f"https://x.com/TradeUpApp/status/{result['reply_id']}"
                    logging.info(f"Successfully posted reply {result['reply_id']}")
                else:
                    logging.error(f"Failed to post reply: {result['post_error']}")
                    
            except Exception as e:
                logging.error(f"Error posting reply: {e}")
                result['posted'] = False
                result['post_error'] = str(e)
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate and post replies to tweets from Google Sheet using LLM Manager')
    parser.add_argument('--post', action='store_true', help='Actually post the replies to Twitter')
    parser.add_argument('--count', type=int, default=5, help='Number of replies to generate')
    parser.add_argument('--batch', action='store_true', help='Use batch processing (default: True)')
    
    args = parser.parse_args()
    
    print(f"Generating {args.count} replies to tweets from Google Sheet")
    print(f"Post to Twitter: {args.post}")
    print(f"Using LLM Manager with rate limiting and batch processing")
    
    results = generate_and_post_replies(args.count, args.post)
    
    print(f"\nGenerated {len(results)} replies:")
    for i, result in enumerate(results):
        print(f"\nReply {i+1}:")
        print(f"Original tweet: {result['original_tweet'][:50]}...")
        print(f"By: {result['username']}")
        print(f"URL: {result['tweet_url']}")
        print(f"Reply: {result['reply_content']}")
        print(f"Pokemon related: {result.get('is_pokemon_related', 'Unknown')}")
        
        if args.post:
            if result['posted']:
                print(f"Successfully posted! Reply URL: {result.get('reply_url', 'Unknown')}")
            else:
                print(f"Failed to post: {result.get('post_error', 'Unknown error')}")
, response, re.DOTALL)
            if reply_match:
                reply_content = reply_match.group(1).strip()
                # Clean up any extra formatting
                reply_content = reply_content.replace('\n', ' ').strip()
                
                logging.info(f"✅ Generated reply: {reply_content}")
                return reply_content
        
        # Fallback if parsing fails
        logging.warning("⚠️ Failed to parse LLM response, using fallback")
        fallback_replies = [
            "That's a sweet card! What's your favorite pull recently? 🔥",
            "Nice! The Pokemon TCG market has been wild lately 😍",
            "Love seeing fellow collectors! Any chase cards you're hunting? 🤩",
            "That pull though! Have you considered grading it? ✨"
        ]
        return random.choice(fallback_replies)

    except Exception as e:
        logging.error(f"❌ Error generating reply content: {e}")
        # Return a safe fallback reply
        return f"Awesome Pokemon card content! What's your favorite card in your collection? 🔥"

def generate_reply(tweet_text, tweet_author=None, conversation_history=None):
    """
    Generate a reply to a tweet (FastAPI-compatible function).
    
    Args:
        tweet_text: Content of the tweet to reply to
        tweet_author: Username of the tweet author (optional)
        conversation_history: Previous conversation context (optional, not used currently)
        
    Returns:
        Dictionary with reply content and success status
    """
    try:
        reply_content = generate_reply_content(tweet_text, tweet_author)
        return {
            "content": reply_content,
            "success": True
        }
    except Exception as e:
        logging.error(f"Error in generate_reply: {e}")
        return {
            "content": f"Thanks for sharing! Great Pokemon TCG content. 🔥",
            "success": False,
            "error": str(e)
        }

def batch_generate_replies(tweets_data):
    """
    Generate replies for multiple tweets using LLM Manager's batch processing.
    
    Args:
        tweets_data: List of tweet dictionaries
        
    Returns:
        List of results with generated replies
    """
    try:
        # Use LLM Manager's batch processing
        logging.info(f"Batch processing {len(tweets_data)} tweets...")
        
        # Convert tweets to the format expected by LLM Manager
        formatted_tweets = []
        for tweet in tweets_data:
            formatted_tweet = {
                'text': tweet.get('tweet_content', ''),
                'id': tweet.get('tweet_id', ''),
                'username': tweet.get('username', ''),
                'url': tweet.get('url', '')
            }
            formatted_tweets.append(formatted_tweet)
        
        # Use LLM Manager's batch processing
        batch_results = llm_manager.batch_process_tweets(formatted_tweets)
        
        # Process the batch results
        results = []
        for i, (tweet, is_pokemon, reply) in enumerate(batch_results):
            original_tweet_data = tweets_data[i]
            
            # If LLM Manager determined it's Pokemon-related and generated a reply
            if is_pokemon and reply:
                result = {
                    'original_tweet': original_tweet_data.get('tweet_content', ''),
                    'username': original_tweet_data.get('username', ''),
                    'tweet_id': original_tweet_data.get('tweet_id', ''),
                    'tweet_url': original_tweet_data.get('url', ''),
                    'reply_content': reply,
                    'is_pokemon_related': True,
                    'posted': False
                }
            else:
                # Skip non-Pokemon tweets or generate a fallback
                if is_pokemon:
                    # Pokemon-related but no reply generated, create fallback
                    fallback_reply = generate_reply_content(
                        original_tweet_data.get('tweet_content', ''),
                        original_tweet_data.get('username', '')
                    )
                    result = {
                        'original_tweet': original_tweet_data.get('tweet_content', ''),
                        'username': original_tweet_data.get('username', ''),
                        'tweet_id': original_tweet_data.get('tweet_id', ''),
                        'tweet_url': original_tweet_data.get('url', ''),
                        'reply_content': fallback_reply,
                        'is_pokemon_related': True,
                        'posted': False
                    }
                else:
                    # Not Pokemon-related, skip
                    logging.info(f"Skipping non-Pokemon tweet: {original_tweet_data.get('tweet_content', '')[:50]}...")
                    continue
            
            results.append(result)
        
        return results
        
    except Exception as e:
        logging.error(f"Error in batch reply generation: {e}")
        # Fallback to individual processing
        return generate_replies_individually(tweets_data)

def generate_replies_individually(tweets_data):
    """
    Fallback function to generate replies individually if batch processing fails.
    
    Args:
        tweets_data: List of tweet dictionaries
        
    Returns:
        List of results with generated replies
    """
    results = []
    
    for tweet_data in tweets_data:
        try:
            tweet_content = tweet_data.get('tweet_content', '')
            username = tweet_data.get('username', '')
            
            # Generate reply using individual function
            reply_content = generate_reply_content(tweet_content, username)
            
            result = {
                'original_tweet': tweet_content,
                'username': username,
                'tweet_id': tweet_data.get('tweet_id', ''),
                'tweet_url': tweet_data.get('url', ''),
                'reply_content': reply_content,
                'is_pokemon_related': True,  # Assume true since we're generating a reply
                'posted': False
            }
            
            results.append(result)
            
        except Exception as e:
            logging.error(f"Error processing individual tweet: {e}")
            continue
    
    return results

def generate_and_post_replies(num_replies=5, post_to_twitter=False, require_confirmation=False):
    """
    Generate and optionally post replies to tweets from the Google Sheet.
    Uses LLM Manager for efficient batch processing and rate limiting.
    
    Args:
        num_replies: Number of replies to generate
        post_to_twitter: Whether to actually post the replies to Twitter
        require_confirmation: Whether to require user confirmation (not implemented yet)
        
    Returns:
        List of generated replies with metadata
    """
    # Get tweets to reply to
    tweets_to_reply = get_tweets_for_reply(TWEETS_SHEET_URL, num_replies)
    
    if not tweets_to_reply:
        logging.warning("No tweets found to reply to")
        return []
    
    logging.info(f"Processing {len(tweets_to_reply)} tweets for reply generation")
    
    # Use batch processing for efficiency
    results = batch_generate_replies(tweets_to_reply)
    
    if not results:
        logging.warning("No replies generated from batch processing")
        return []
    
    # Post replies if requested
    if post_to_twitter:
        logging.info(f"Posting {len(results)} replies to Twitter...")
        
        for result in results:
            try:
                tweet_id = result.get('tweet_id')
                reply_content = result.get('reply_content')
                
                if not tweet_id or not reply_content:
                    logging.warning(f"Skipping post due to missing data: tweet_id={tweet_id}, reply_content={reply_content}")
                    continue
                
                logging.info(f"Posting reply to tweet ID {tweet_id}: {reply_content[:50]}...")
                post_result = post_reply_tweet(reply_content, tweet_id)
                
                result['posted'] = post_result.get('success', False)
                result['post_error'] = post_result.get('error', None)
                
                if result['posted']:
                    result['reply_id'] = post_result.get('tweet_id')
                    result['reply_url'] = f"https://x.com/TradeUpApp/status/{result['reply_id']}"
                    logging.info(f"Successfully posted reply {result['reply_id']}")
                else:
                    logging.error(f"Failed to post reply: {result['post_error']}")
                    
            except Exception as e:
                logging.error(f"Error posting reply: {e}")
                result['posted'] = False
                result['post_error'] = str(e)
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate and post replies to tweets from Google Sheet using LLM Manager')
    parser.add_argument('--post', action='store_true', help='Actually post the replies to Twitter')
    parser.add_argument('--count', type=int, default=5, help='Number of replies to generate')
    parser.add_argument('--batch', action='store_true', help='Use batch processing (default: True)')
    
    args = parser.parse_args()
    
    print(f"Generating {args.count} replies to tweets from Google Sheet")
    print(f"Post to Twitter: {args.post}")
    print(f"Using LLM Manager with rate limiting and batch processing")
    
    results = generate_and_post_replies(args.count, args.post)
    
    print(f"\nGenerated {len(results)} replies:")
    for i, result in enumerate(results):
        print(f"\nReply {i+1}:")
        print(f"Original tweet: {result['original_tweet'][:50]}...")
        print(f"By: {result['username']}")
        print(f"URL: {result['tweet_url']}")
        print(f"Reply: {result['reply_content']}")
        print(f"Pokemon related: {result.get('is_pokemon_related', 'Unknown')}")
        
        if args.post:
            if result['posted']:
                print(f"Successfully posted! Reply URL: {result.get('reply_url', 'Unknown')}")
            else:
                print(f"Failed to post: {result.get('post_error', 'Unknown error')}")