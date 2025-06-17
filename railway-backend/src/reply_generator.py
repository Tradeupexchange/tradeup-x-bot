"""
Tweet reply generator for TradeUp X Engager.
Generates custom replies to tweets from the Google Sheet.
"""

import os
import sys
import random
import json
import logging

# Add the parent directory to sys.path if running directly
if __name__ == "__main__" and "src" not in sys.path:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from openai import OpenAI
from src.config import OPENAI_API_KEY
from src.google_sheets_reader import get_tweets_for_reply
from src.twitter_poster import post_reply_tweet

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Google Sheet URL containing tweet examples
TWEETS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0"

def generate_reply_content(tweet_content, username=None):
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
    
    Examples of good replies:
    - "That Charizard is absolute fire! Have you considered getting it graded? 🔥"
    - "Alt arts are my weakness too! Which one is your current chase card? 😍"
    - "Those pulls are insane! If you trade it, TradeUp's got you 😉"
    
    Format your response as plain text, ready to be posted as a reply.
    """

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Or "gpt-4" for higher quality
            messages=[
                {"role": "system", "content": persona_guidelines},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200,
            n=1,
            stop=None,
            temperature=0.8, # Slightly higher temperature for more creativity and variation
        )
        
        reply_content = response.choices[0].message.content.strip()
        logging.info(f"Generated reply: {reply_content}")
        
        return reply_content

    except Exception as e:
        logging.error(f"Error generating reply content: {e}")
        return f"Interesting post about Pokémon cards! What's your favorite card in your collection? 🔥"

def generate_and_post_replies(num_replies=5, post_to_twitter=False):
    """
    Generate and optionally post replies to tweets from the Google Sheet.
    
    Args:
        num_replies: Number of replies to generate
        post_to_twitter: Whether to actually post the replies to Twitter
        
    Returns:
        List of generated replies with metadata
    """
    # Get tweets to reply to
    tweets_to_reply = get_tweets_for_reply(TWEETS_SHEET_URL, num_replies)
    
    if not tweets_to_reply:
        logging.warning("No tweets found to reply to")
        return []
    
    results = []
    
    for tweet in tweets_to_reply:
        tweet_content = tweet.get('tweet_content', '')
        username = tweet.get('username', '')
        tweet_id = tweet.get('tweet_id')
        tweet_url = tweet.get('url', '')
        
        if not tweet_id:
            logging.warning(f"No tweet ID found for tweet: {tweet_content[:50]}...")
            continue
        
        # Generate reply content
        reply_content = generate_reply_content(tweet_content, username)
        
        result = {
            'original_tweet': tweet_content,
            'username': username,
            'tweet_id': tweet_id,
            'tweet_url': tweet_url,
            'reply_content': reply_content,
            'posted': False
        }
        
        # Post the reply if requested
        if post_to_twitter:
            logging.info(f"Posting reply to tweet ID {tweet_id}")
            post_result = post_reply_tweet(reply_content, tweet_id)
            
            result['posted'] = post_result.get('success', False)
            result['post_error'] = post_result.get('error', None)
            
            if result['posted']:
                result['reply_id'] = post_result.get('tweet_id')
                result['reply_url'] = f"https://x.com/TradeUpApp/status/{result['reply_id']}"
        
        results.append(result)
    
    return results

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate and post replies to tweets from Google Sheet')
    parser.add_argument('--post', action='store_true', help='Actually post the replies to Twitter')
    parser.add_argument('--count', type=int, default=5, help='Number of replies to generate')
    
    args = parser.parse_args()
    
    print(f"Generating {args.count} replies to tweets from Google Sheet")
    print(f"Post to Twitter: {args.post}")
    
    results = generate_and_post_replies(args.count, args.post)
    
    print(f"\nGenerated {len(results)} replies:")
    for i, result in enumerate(results):
        print(f"\nReply {i+1}:")
        print(f"Original tweet: {result['original_tweet'][:50]}...")
        print(f"By: {result['username']}")
        print(f"URL: {result['tweet_url']}")
        print(f"Reply: {result['reply_content']}")
        
        if args.post:
            if result['posted']:
                print(f"Successfully posted! Reply URL: {result.get('reply_url', 'Unknown')}")
            else:
                print(f"Failed to post: {result.get('post_error', 'Unknown error')}")
