"""
Configuration settings for Pokemon TCG Bot Backend.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# API Keys
TWITTER_API_KEY = os.getenv('TWITTER_API_KEY', '')
TWITTER_API_SECRET = os.getenv('TWITTER_API_SECRET', '')
TWITTER_ACCESS_TOKEN = os.getenv('TWITTER_ACCESS_TOKEN', '')
TWITTER_ACCESS_SECRET = os.getenv('TWITTER_ACCESS_SECRET', '')

print(f"API Key: {os.getenv('TWITTER_API_KEY')}")
print(f"API Secret: {os.getenv('TWITTER_API_SECRET')}")  
print(f"Access Token: {os.getenv('TWITTER_ACCESS_TOKEN')}")
print(f"Access Secret: {os.getenv('TWITTER_ACCESS_SECRET')}")

# LLM API Keys
LLM_API_KEY = os.getenv('OPENAI_API_KEY', '')  # Default to OpenAI API key

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')  # Default to OpenAI

# Directory paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / 'data'
LOGS_DIR = BASE_DIR / 'logs'

# Ensure directories exist
DATA_DIR.mkdir(exist_ok=True)
LOGS_DIR.mkdir(exist_ok=True)

# File paths
REPLIED_TWEETS_LOG = LOGS_DIR / 'replied_tweets.csv'

# Rate limiting
MAX_REPLIES_PER_DAY = 20  # Maximum number of replies to post per day

# Pokemon card-related keywords
POKEMON_KEYWORDS = [
    # General terms
    "pokemon", "pokémon", "pkmn", "tcg", "trading card", "card game",
    "card collection", "card collector", "card trading", "card value",
    
    # Popular Pokémon names
    "charizard", "pikachu", "mewtwo", "mew", "eevee", "gengar", "blastoise",
    "venusaur", "snorlax", "lugia", "rayquaza", "umbreon", "sylveon",
    "dragonite", "gyarados", "jigglypuff", "bulbasaur", "squirtle", "charmander",
    
    # Card-specific terminology
    "booster", "pack", "box", "tin", "elite", "holo", "holographic", "foil",
    "rare", "ultra rare", "secret rare", "full art", "alt art", "rainbow rare",
    "gold card", "ex card", "gx card", "v card", "vmax", "vstar",
    
    # Grading and collecting terms
    "psa", "bgs", "cgc", "graded", "slab", "mint", "near mint", "gem mint",
    "sealed", "vintage", "wotc", "1st edition", "shadowless",
    
    # Sets and expansions
    "base set", "jungle", "fossil", "team rocket", "gym heroes", "neo",
    "sword shield", "brilliant stars", "astral radiance", "lost origin",
    "crown zenith", "scarlet violet", "paldea", "obsidian flames"
]