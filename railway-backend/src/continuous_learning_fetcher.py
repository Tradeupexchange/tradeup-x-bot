import requests
import random
import logging
import time
from src.google_sheets_reader import get_tweets_from_sheet

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Google Sheet URL containing tweet examples
TWEETS_SHEET_URL = "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0"

def fetch_pokeapi_data(endpoint):
    base_url = "https://pokeapi.co/api/v2/"
    try:
        response = requests.get(f"{base_url}{endpoint}", timeout=5)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f"Successfully fetched data from PokeAPI endpoint: {endpoint}")
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Network error fetching PokeAPI data for {endpoint}: {e}")
    except Exception as e:
        logging.error(f"Error fetching PokeAPI data for {endpoint}: {e}")
    return None

def fetch_google_sheet_tweets(max_tweets=10):
    """
    Fetch tweets from the Google Sheet for continuous learning.
    
    :param max_tweets: Maximum number of tweets to fetch
    :return: List of tweet content strings
    """
    try:
        tweet_data = get_tweets_from_sheet(TWEETS_SHEET_URL, max_tweets)
        tweet_contents = [tweet.get('tweet_content', '') for tweet in tweet_data if tweet.get('tweet_content')]
        logging.info(f"Successfully fetched {len(tweet_contents)} tweets from Google Sheet")
        return tweet_contents
    except Exception as e:
        logging.error(f"Error fetching tweets from Google Sheet: {e}")
        return []

def get_continuous_learning_data():
    all_data = []

    # Fetch tweets from Google Sheet (primary data source)
    google_sheet_tweets = fetch_google_sheet_tweets(max_tweets=15)
    if google_sheet_tweets:
        logging.info(f"Adding {len(google_sheet_tweets)} tweets from Google Sheet to learning data")
        all_data.extend(google_sheet_tweets)

    # Fetch some random Pokémon data from PokeAPI
    pokemon_list = fetch_pokeapi_data("pokemon?limit=1000")
    if pokemon_list and 'results' in pokemon_list and pokemon_list['results']:
        # Ensure there are enough Pokémon to sample from
        num_pokemon_to_sample = min(5, len(pokemon_list['results']))
        if num_pokemon_to_sample > 0:
            random_pokemon_names = random.sample([p['name'] for p in pokemon_list['results']], num_pokemon_to_sample)
            for name in random_pokemon_names:
                pokemon_detail = fetch_pokeapi_data(f"pokemon/{name}")
                if pokemon_detail:
                    abilities = [a['ability']['name'] for a in pokemon_detail['abilities']] if 'abilities' in pokemon_detail else []
                    types = [t['type']['name'] for t in pokemon_detail['types']] if 'types' in pokemon_detail else []
                    all_data.append(f"Pokemon fact: {pokemon_detail['name']} is a {', '.join(types)} type with abilities like {', '.join(abilities)}.")
        else:
            logging.warning("No Pokémon found in PokeAPI results to sample from.")
    else:
        logging.warning("Could not fetch Pokémon list from PokeAPI or results were empty.")

    # Add some general trending topics if data is sparse or as a fallback
    if not all_data or len(all_data) < 5: # Ensure at least 5 data points
        logging.info("Adding fallback trending topics as fetched data is sparse.")
        fallback_topics = [
            "Charizard PSA 10 prices are soaring!",
            "New Scarlet & Violet set is dropping soon.",
            "Vintage WOTC cards are making a comeback.",
            "What's your favorite Alt Art card?",
            "Tips for grading your Pokémon cards.",
            "Top 5 rarest Pokémon cards",
            "Investing in Pokémon cards",
            "Upcoming Pokémon TCG tournaments",
            "Best ways to store your card collection",
            "Pokémon card collecting tips for beginners"
        ]
        # Add unique fallback topics to ensure variety
        for topic in random.sample(fallback_topics, min(5, len(fallback_topics))):
            if topic not in all_data:
                all_data.append(topic)

    # Return a string of relevant data points, limit to a reasonable size for the prompt
    # Prioritize Google Sheet tweets by placing them first
    return " ".join(all_data[:20])  # Limit to top 20 relevant data points

if __name__ == "__main__":
    print("Fetching continuous learning data...")
    data = get_continuous_learning_data()
    print("\n--- Fetched Data ---")
    print(data)
    print(f"Total data points fetched: {len(data.split())}")
