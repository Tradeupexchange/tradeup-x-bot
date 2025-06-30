
"""
LLM Manager module for TradeUp X Engager.
Handles API calls with rate limiting and batch processing using OpenAI.
"""

import os
import time
import random
import json
import re
from typing import Dict, Any, Optional, List, Tuple
from openai import OpenAI
import logging


from src.config import OPENAI_API_KEY
logging.info(f"🔑 LLM Manager - OPENAI_API_KEY loaded: {'✅ Yes' if OPENAI_API_KEY else '❌ No'}")
if OPENAI_API_KEY:
    logging.info(f"🔑 LLM Manager - Key length: {len(OPENAI_API_KEY)}")
    logging.info(f"🔑 LLM Manager - Key starts with: {OPENAI_API_KEY[:15]}...")
else:
    logging.error("❌ LLM Manager - No OPENAI_API_KEY found in config")
    # Try direct environment access as fallback
    direct_key = os.getenv('OPENAI_API_KEY')
    logging.info(f"🔑 LLM Manager - Direct env check: {'✅ Yes' if direct_key else '❌ No'}")
    if direct_key:
        logging.info(f"🔑 LLM Manager - Direct key length: {len(direct_key)}")
        OPENAI_API_KEY = direct_key

# Constants for rate limiting
MIN_DELAY = 0.5  # Minimum delay between API calls in seconds
MAX_DELAY = 5.0  # Maximum delay for exponential backoff
MAX_RETRIES = 3  # Maximum number of retries per API call
BATCH_SIZE = 5   # Process in batches of this size
BATCH_PAUSE = 3  # Seconds to pause between batches

# Constants for batch processing
MAX_TWEETS_PER_BATCH = 5  # Maximum number of tweets to process in a single API call
MAX_TOKENS_PER_BATCH = 4000  # Maximum tokens for a batch prompt

class LLMManager:
    """
    Manager class for OpenAI API calls with rate limiting and batch processing.
    """
    
    def __init__(self):
        """Initialize the LLM Manager."""
        logging.info(f"🚀 Initializing OpenAI client with key: {'✅ Available' if OPENAI_API_KEY else '❌ Missing'}")
    
        if not OPENAI_API_KEY:
            logging.error("❌ Cannot initialize OpenAI client - no API key")
            raise ValueError("OPENAI_API_KEY is required but not found")
        
        self.client = OpenAI(api_key=OPENAI_API_KEY)
        self.call_count = 0
        self.last_call_time = 0
        self.consecutive_errors = 0
        
        logging.info("✅ LLM Manager initialized with OpenAI successfully")
        print("LLM Manager initialized with OpenAI")
        
    def _apply_rate_limiting(self):
        """Apply rate limiting between API calls."""
        current_time = time.time()
        elapsed = current_time - self.last_call_time
        
        # Calculate delay based on call count and consecutive errors
        base_delay = MIN_DELAY * (1 + (self.call_count % 10) / 10)
        error_factor = min(2 ** self.consecutive_errors, MAX_DELAY / base_delay)
        delay = min(base_delay * error_factor, MAX_DELAY)
        
        # If not enough time has elapsed, sleep
        if elapsed < delay:
            sleep_time = delay - elapsed
            print(f"Rate limiting: Waiting {sleep_time:.2f}s before next API call")
            time.sleep(sleep_time)
            
        # Add small random jitter to avoid synchronized requests
        jitter = random.uniform(0.1, 0.5)
        time.sleep(jitter)
        
        # Apply batch pausing
        if self.call_count > 0 and self.call_count % BATCH_SIZE == 0:
            print(f"Completed batch of {BATCH_SIZE} calls. Pausing for {BATCH_PAUSE}s...")
            time.sleep(BATCH_PAUSE)
            
        self.last_call_time = time.time()
        self.call_count += 1
        
    def call_llm(self, prompt: str, model: str = "gpt-3.5-turbo") -> str:
        """
        Call OpenAI API with rate limiting and retry logic.
        
        Args:
            prompt: The prompt to send to the LLM
            model: OpenAI model to use
            
        Returns:
            The generated text response
        """
        retries = 0
        
        while retries < MAX_RETRIES:
            # Apply rate limiting
            self._apply_rate_limiting()
            
            try:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=2000
                )
                
                # Reset consecutive errors on success
                self.consecutive_errors = 0
                return response.choices[0].message.content
                
            except Exception as e:
                error_message = str(e)
                retries += 1
                self.consecutive_errors += 1
                
                print(f"Error calling OpenAI API: {error_message}")
                
                # Check for rate limiting errors
                if "429" in error_message or "Too Many Requests" in error_message:
                    print(f"Rate limit hit. Attempt {retries}/{MAX_RETRIES}")
                    
                    # Use exponential backoff
                    backoff_time = min(2 ** retries, MAX_DELAY * 2)
                    print(f"Backing off for {backoff_time}s before retry...")
                    time.sleep(backoff_time)
                    continue
                    
        # If all retries failed, return error message
        return "POKEMON_RELATED: NO\nREPLY: Error: Unable to generate response after multiple attempts."
        
    def process_in_batches(self, items: List[Any], process_func, batch_size: int = None) -> List[Any]:
        """
        Process a list of items in batches with rate limiting.
        
        Args:
            items: List of items to process
            process_func: Function to process each item
            batch_size: Size of each batch (defaults to BATCH_SIZE)
            
        Returns:
            List of processed results
        """
        if batch_size is None:
            batch_size = BATCH_SIZE
            
        results = []
        total_items = len(items)
        
        for i in range(0, total_items, batch_size):
            batch = items[i:i+batch_size]
            print(f"Processing batch {i//batch_size + 1}/{(total_items + batch_size - 1)//batch_size} ({len(batch)} items)")
            
            batch_results = [process_func(item) for item in batch]
            results.extend(batch_results)
            
            # Pause between batches if not the last batch
            if i + batch_size < total_items:
                print(f"Batch complete. Pausing for {BATCH_PAUSE}s...")
                time.sleep(BATCH_PAUSE)
                
        return results
        
    def batch_process_tweets(self, tweets: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], bool, str]]:
        """
        Process multiple tweets in a single API call to reduce API usage.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            List of tuples (tweet, is_pokemon, reply)
        """
        results = []
        
        # Process tweets in batches to avoid token limits
        for i in range(0, len(tweets), MAX_TWEETS_PER_BATCH):
            batch = tweets[i:i+MAX_TWEETS_PER_BATCH]
            batch_results = self._process_tweet_batch(batch)
            results.extend(batch_results)
            
        return results
        
    def _process_tweet_batch(self, tweets: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], bool, str]]:
        """
        Process a batch of tweets in a single API call.
        
        Args:
            tweets: Batch of tweet dictionaries
            
        Returns:
            List of tuples (tweet, is_pokemon, reply)
        """
        # Create a batch prompt with all tweets
        prompt = self._create_batch_prompt(tweets)
        
        # Call LLM with the batch prompt
        try:
            response = self.call_llm(prompt)
            
            # Parse the batch response
            results = self._parse_batch_response(tweets, response)
            return results
            
        except Exception as e:
            print(f"Error processing tweet batch: {str(e)}")
            
            # Fall back to individual processing if batch fails
            print("Falling back to individual tweet processing...")
            results = []
            
            for tweet in tweets:
                try:
                    # Create individual prompt
                    individual_prompt = self._create_individual_prompt(tweet['text'])
                    
                    # Call LLM
                    response = self.call_llm(individual_prompt)
                    
                    # Parse response
                    is_pokemon = 'POKEMON_RELATED: YES' in response
                    reply = ""
                    
                    if is_pokemon:
                        reply_match = re.search(r'REPLY: (.*?)($|POKEMON_RELATED:)', response, re.DOTALL)
                        reply = reply_match.group(1).strip().strip('"').strip("'") if reply_match else "Interesting Pokémon card post! Trade safely on TradeUp!"
                        
                    results.append((tweet, is_pokemon, reply))
                    
                except Exception as e:
                    print(f"Error processing individual tweet: {str(e)}")
                    results.append((tweet, False, ""))
                    
            return results
            
    def _create_batch_prompt(self, tweets: List[Dict[str, Any]]) -> str:
        """
        Create a prompt for batch processing multiple tweets.
        
        Args:
            tweets: List of tweet dictionaries
            
        Returns:
            Batch prompt string
        """
        prompt = """
You are an AI assistant for TradeUp, a platform for trading Pokémon cards.

I will provide you with multiple tweets. For each tweet, determine if it's related to Pokémon cards or the Pokémon Trading Card Game (TCG).

For each tweet that IS related to Pokémon cards, write a friendly reply that:
1. Reacts naturally to the tweet's content
2. Adds a fun fact or mini price insight if relevant
3. Ends with "Trade safely on TradeUp!"

For tweets that are NOT related to Pokémon cards, simply indicate they are not relevant.

Format your response using the exact format below, with one section per tweet:

TWEET 1:
POKEMON_RELATED: [YES/NO]
REPLY: [Your reply text here]

TWEET 2:
POKEMON_RELATED: [YES/NO]
REPLY: [Your reply text here]

And so on for each tweet.

Here are the tweets:

"""
        
        # Add each tweet to the prompt
        for i, tweet in enumerate(tweets, 1):
            tweet_text = tweet.get('text', '').strip()
            prompt += f"TWEET {i}: {tweet_text}\n\n"
            
        return prompt
        
    def _create_individual_prompt(self, tweet_text: str) -> str:
        """
        Create a prompt for processing a single tweet.
        
        Args:
            tweet_text: Text of the tweet
            
        Returns:
            Individual prompt string
        """
        return f"""
You are an AI assistant for TradeUp, a platform for trading Pokémon cards.

TWEET: "{tweet_text}"

Task 1: Is this tweet related to Pokémon cards or the Pokémon Trading Card Game (TCG)? Answer YES or NO.

Task 2: If you answered YES, write a friendly reply tweet that:
1. Reacts naturally to the tweet's content
2. Adds a fun fact or mini price insight if relevant
3. Ends with "Trade safely on TradeUp!"

If you answered NO, just write "Not Pokémon card related."

Format your response exactly like this:
POKEMON_RELATED: [YES/NO]
REPLY: [Your reply text here]
"""
        
    def _parse_batch_response(self, tweets: List[Dict[str, Any]], response: str) -> List[Tuple[Dict[str, Any], bool, str]]:
        """
        Parse the response from a batch API call.
        
        Args:
            tweets: List of tweet dictionaries
            response: Response from the LLM
            
        Returns:
            List of tuples (tweet, is_pokemon, reply)
        """
        results = []
        
        # Split the response into sections for each tweet
        tweet_pattern = r'TWEET (\d+):\s*POKEMON_RELATED: (YES|NO)(?:\s*REPLY: (.*?))?(?=\s*TWEET \d+:|$)'
        matches = re.finditer(tweet_pattern, response, re.DOTALL)
        
        # Create a dictionary to store results by tweet number
        parsed_results = {}
        
        for match in matches:
            tweet_num = int(match.group(1))
            is_pokemon = match.group(2) == 'YES'
            reply = match.group(3).strip().strip('"').strip("'") if match.group(3) else ""
            
            parsed_results[tweet_num] = (is_pokemon, reply)
            
        # Map results back to original tweets
        for i, tweet in enumerate(tweets, 1):
            if i in parsed_results:
                is_pokemon, reply = parsed_results[i]
                results.append((tweet, is_pokemon, reply))
            else:
                # If no result for this tweet, assume it's not Pokémon-related
                print(f"Warning: No result found for tweet {i} in batch response")
                results.append((tweet, False, ""))
                
        return results

# Create a singleton instance
llm_manager = LLMManager()