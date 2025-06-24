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

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Add the parent directory to sys.path to access llm_manager
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)

if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Try to import LLM Manager with error handling
try:
    from llm_manager import LLMManager
    
    # Initialize the LLM Manager
    llm_manager = LLMManager()
    LLM_MANAGER_AVAILABLE = True
    logging.info("✅ Successfully imported and initialized LLM Manager")
except ImportError as e:
    logging.error(f"❌ Failed to import LLM Manager: {e}")
    LLM_MANAGER_AVAILABLE = False
    llm_manager = None
except Exception as e:
    logging.error(f"❌ Failed to initialize LLM Manager: {e}")
    LLM_MANAGER_AVAILABLE = False
    llm_manager = None

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
    Generate a custom reply to a tweet using the LLM Manager or fallback.
    
    Args:
        tweet_content: Content of the tweet to reply to
        username: Username of the tweet author (if available)
        
    Returns:
        Generated reply content
    """
    try:
        # Create the customized prompt
        prompt = create_custom_reply_prompt(tweet_content, username)
        
        if LLM_MANAGER_AVAILABLE and llm_manager:
            # Use LLM Manager to generate the response
            logging.info("🤖 Using LLM Manager for reply generation")
            response = llm_manager.generate_response(prompt)
        else:
            # Fallback if LLM Manager is not available
            logging.warning("🔄 LLM Manager not available, using fallback")
            raise Exception("LLM Manager not available")
        
        # Parse the response to extract the reply
        if "REPLY:" in response:
            reply_match = re.search(r'REPLY:\s*(.*?)$', response, re.DOTALL)
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
        fallback_replies = [
            "Awesome Pokemon card content! What's your favorite card in your collection? 🔥",
            "That's a sweet pull! The Pokemon TCG community is the best 😍",
            "Love seeing fellow collectors share their pulls! 🤩",
            "Great content! What deck are you building next? ⚡️"
        ]
        return random.choice(fallback_replies)

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
        logging.info(f"🎯 Generating reply for tweet: {tweet_text[:100]}...")
        logging.info(f"👤 Author: {tweet_author}")
        
        reply_content = generate_reply_content(tweet_text, tweet_author)
        
        return {
            "content": reply_content,
            "success": True,
            "llm_used": LLM_MANAGER_AVAILABLE
        }
    except Exception as e:
        logging.error(f"❌ Error in generate_reply: {e}")
        return {
            "content": "Thanks for sharing! Great Pokemon TCG content. 🔥",
            "success": False,
            "error": str(e),
            "llm_used": False
        }

def batch_generate_replies(tweets_data):
    """
    Generate replies for multiple tweets.
    
    Args:
        tweets_data: List of tweet dictionaries
        
    Returns:
        List of results with generated replies
    """
    results = []
    
    logging.info(f"🔄 Batch processing {len(tweets_data)} tweets...")
    
    for i, tweet_data in enumerate(tweets_data):
        try:
            tweet_content = tweet_data.get('tweet_content', tweet_data.get('text', ''))
            username = tweet_data.get('username', tweet_data.get('author', ''))
            tweet_id = tweet_data.get('tweet_id', tweet_data.get('id', ''))
            
            logging.info(f"📝 Processing tweet {i+1}/{len(tweets_data)}: {tweet_content[:50]}...")
            
            # Generate reply using individual function
            reply_result = generate_reply(tweet_content, username)
            
            result = {
                'original_tweet': tweet_content,
                'username': username,
                'tweet_id': tweet_id,
                'tweet_url': tweet_data.get('url', ''),
                'reply_content': reply_result.get('content', ''),
                'success': reply_result.get('success', False),
                'error': reply_result.get('error', None),
                'is_pokemon_related': True,  # Assume true since we're generating a reply
                'posted': False,
                'llm_used': reply_result.get('llm_used', False)
            }
            
            results.append(result)
            
        except Exception as e:
            logging.error(f"❌ Error processing tweet {i+1}: {e}")
            continue
    
    logging.info(f"✅ Batch processing complete: {len(results)} replies generated")
    return results

def test_reply_generation():
    """
    Test function to verify the reply generation is working.
    """
    test_tweets = [
        {
            "text": "Just pulled a Charizard ex from my latest Pokemon TCG pack! So excited!",
            "author": "TestUser1"
        },
        {
            "text": "Building a new deck around Pikachu VMAX! Any tips?",
            "author": "TestUser2"
        },
        {
            "text": "Attending my first Pokemon tournament tomorrow, wish me luck!",
            "author": "TestUser3"
        }
    ]
    
    print("🧪 Testing reply generation...")
    print(f"LLM Manager Available: {LLM_MANAGER_AVAILABLE}")
    print("-" * 50)
    
    for i, tweet in enumerate(test_tweets):
        print(f"\n🎯 Test {i+1}:")
        print(f"Tweet: {tweet['text']}")
        print(f"Author: {tweet['author']}")
        
        result = generate_reply(tweet['text'], tweet['author'])
        
        print(f"Reply: {result['content']}")
        print(f"Success: {result['success']}")
        print(f"LLM Used: {result.get('llm_used', False)}")
        if 'error' in result:
            print(f"Error: {result['error']}")
        print("-" * 30)

if __name__ == "__main__":
    test_reply_generation()