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

print(f"🔑 OPENAI_API_KEY loaded: {'✅ Yes' if OPENAI_API_KEY else '❌ No'}")
if OPENAI_API_KEY:
    print(f"🔑 Key length: {len(OPENAI_API_KEY)}")
    print(f"🔑 Key starts with: {OPENAI_API_KEY[:15]}...")
    print(f"🔑 Key ends with: ...{OPENAI_API_KEY[-10:]}")
else:
    print("❌ No OPENAI_API_KEY found in environment")
    print("🔍 Available env vars with 'API':", [k for k in os.environ.keys() if 'API' in k])

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

# Pokémon Keywords for content generation
POKEMON_KEYWORDS = [
    "Pikachu", "Charizard", "Mewtwo", "Eternatus", "Arceus",
    "Pokémon TCG", "Booster Pack", "Elite Trainer Box", "Grading",
    "PSA 10", "BGS 9.5", "Collector", "Investment", "Rare Card",
    "Alt Art", "Full Art", "Secret Rare", "VMAX", "VSTAR",
    "Crown Zenith", "Scarlet & Violet", "Paldea Evolved", "Obsidian Flames",
    "151", "Paradox Rift", "Temporal Forces", "Chilling Reign",
    "Evolving Skies", "Fusion Strike", "Brilliant Stars", "Astral Radiance",
    "Lost Origin", "Silver Tempest", "Shining Fates", "Hidden Fates",
    "Vintage Pokémon", "WOTC", "Base Set", "Jungle", "Fossil",
    "Team Rocket", "Neo Genesis", "Gym Heroes", "Gym Challenge",
    "Tournament", "Deck Building", "Strategy", "Meta", "TCG Live",
    "Opening Packs", "Pull Rates", "Binder Collection", "Slab",
    "Pop Report", "Market Price", "TCGplayer", "eBay", "TradeUp"
]
