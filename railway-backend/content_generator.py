"""
Enhanced LLM-based viral content generator for TradeUp X Engager with continuous learning.
Generates original, engaging Pokémon card content with expert knowledge for posting on Twitter.
"""

import os
import requests
import json
import random
from typing import List, Dict, Any
from datetime import datetime
import time
import hashlib

from config import OPENAI_API_KEY, LLM_PROVIDER, POKEMON_KEYWORDS
from knowledge_manager import generate_expert_knowledge_prompt, update_knowledge_base_from_csv, update_knowledge_base_from_web, add_memory

# Content types for variety
CONTENT_TYPES = [
    "fun_fact",
    "price_insight",
    "collector_tip",
    "market_trend",
    "rare_card_spotlight",
    "nostalgia_post",
    "question_engagement",
    "did_you_know",
    "investment_advice",
    "grading_tip",
    "authentication_guide",
    "set_completion_strategy",
    "community_debate",
    "upcoming_release",
    "card_care_advice"
]

# Viral elements to include
VIRAL_ELEMENTS = [
    "surprising_statistic",
    "controversial_opinion",
    "insider_knowledge",
    "prediction",
    "money_saving_tip",
    "investment_advice",
    "rare_find",
    "nostalgia_trigger",
    "expert_analysis",
    "market_alert",
    "exclusive_info",
    "community_debate",
    "price_comparison",
    "collecting_hack",
    "authentication_tip"
]

def generate_viral_content(count: int = 3, csv_path: str = None) -> List[Dict[str, Any]]:
    """
    Generate viral Pokémon card content for Twitter posts with expert knowledge.
    
    Args:
        count: Number of content options to generate
        csv_path: Optional path to CSV file to learn from before generating content
        
    Returns:
        List of dictionaries with generated content
    """
    # Update knowledge base if CSV provided
    if csv_path and os.path.exists(csv_path):
        update_knowledge_base_from_csv(csv_path)
    
    # Try to update knowledge base from web (will only run once per day)
    try:
        update_knowledge_base_from_web()
    except Exception as e:
        print(f"Warning: Could not update knowledge base from web: {str(e)}")
    
    # If LLM is available, use it for advanced content generation
    if OPENAI_API_KEY or GROQ_API_KEY:
        try:
            return generate_llm_content(count)
        except Exception as e:
            print(f"LLM generation failed, falling back to templates: {e}")
    
    # Fallback to template-based generation
    return generate_template_content(count)

def generate_llm_content(count: int) -> List[Dict[str, Any]]:
    """Generate content using LLM"""
    # Select random content types and viral elements for variety
    selected_types = random.sample(CONTENT_TYPES, min(count, len(CONTENT_TYPES)))
    selected_elements = random.sample(VIRAL_ELEMENTS, min(count, len(VIRAL_ELEMENTS)))
    
    # Select random Pokémon keywords to focus on
    selected_keywords = random.sample(POKEMON_KEYWORDS, min(count*2, len(POKEMON_KEYWORDS)))
    
    # Get expert knowledge prompt with latest knowledge
    expert_prompt = generate_expert_knowledge_prompt()
    
    # Add timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
    
    # Prepare the main prompt
    prompt = f"""
{expert_prompt}

As the social media manager for TradeUp, a platform for trading Pokémon cards, generate {count} highly engaging, viral Twitter posts about Pokémon cards. Each post should:

1. Be original and attention-grabbing
2. Include interesting facts, statistics, or insights about Pokémon cards
3. Naturally promote the TradeUp platform without being overly promotional
4. Include relevant hashtags for discoverability
5. Be optimized for engagement (likes, retweets, replies)
6. Be between 200-280 characters (Twitter limit)
7. Use authentic community terminology and voice
8. Reference current trends or recent news when relevant
9. BE COMPLETELY UNIQUE - no duplicate content allowed

IMPORTANT: Make each post completely unique by including:
- Different Pokemon names
- Unique perspectives or angles
- Varied sentence structures
- Different emojis and hashtags
- Timestamp reference: {timestamp}

For variety, include these content types: {', '.join(selected_types)}
For virality, incorporate these elements: {', '.join(selected_elements)}
Focus on these Pokémon topics: {', '.join(selected_keywords[:count*2])}

Format your response exactly like this for EACH post:

POST:
CONTENT: [the full tweet text including hashtags]
TOPIC: [main topic of the post]
VIRAL_ELEMENT: [which viral element is used]
TARGET_AUDIENCE: [who this post targets]
"""

    # Call LLM API based on provider setting
    try:
        if LLM_PROVIDER.lower() == 'openai':
            response = call_openai_api(prompt)
        elif LLM_PROVIDER.lower() == 'groq':
            response = call_groq_api(prompt)
        else:
            # Default to OpenAI
            print(f"Unknown LLM provider '{LLM_PROVIDER}', defaulting to OpenAI")
            response = call_openai_api(prompt)
            
        viral_posts = parse_llm_response(response, count)
        
        # Store generated content as memories
        for post in viral_posts:
            memory_content = f"Generated viral content about {post['topic']}: \"{post['content']}\""
            add_memory(memory_content, "content_generation")
            
        return viral_posts
    except Exception as e:
        print(f"Error generating viral content: {str(e)}")
        return generate_template_content(count)

def generate_template_content(count: int) -> List[Dict[str, Any]]:
    """Generate content using templates (fallback) with uniqueness guarantees"""
    
    # Expanded templates with more variety
    templates = [
        "Just opened a booster pack and got an amazing holographic {pokemon}! The artwork is absolutely stunning 🎨 #{hashtag1} #CardPulls #TradeUp",
        "Working on a new {pokemon} deck strategy. The synergy between cards is incredible! 🃏 #{hashtag1} #DeckBuilding #TradeUp",
        "Interesting price trends for {pokemon} cards this week. Vintage cards continue to show strong performance 📈 #{hashtag1} #MarketAnalysis #TradeUp",
        "Excited for the upcoming Pokemon TCG tournament! My {pokemon} deck is ready 🏆 #{hashtag1} #Tournament #TradeUp",
        "Added a beautiful {pokemon} card to my collection today! The condition is perfect 💎 #{hashtag1} #Collecting #TradeUp",
        "That feeling when you pull a rare {pokemon} from a pack! Nothing beats the excitement 🔥 #{hashtag1} #LuckyPull #TradeUp",
        "The market for graded {pokemon} cards is evolving rapidly. PSA 10s are commanding premium prices! 💰 #{hashtag1} #Investment #TradeUp",
        "Testing out a new {pokemon} deck combo today. Theory crafting is half the fun! 🧠 #{hashtag1} #DeckTech #TradeUp",
        "Found a gem in today's pack opening - this {pokemon} is going straight to the collection! ✨ #{hashtag1} #NewCard #TradeUp",
        "The competitive scene is heating up! Love seeing new {pokemon} strategies emerge 🌟 #{hashtag1} #Competitive #TradeUp",
        "Vintage {pokemon} cards never go out of style. The nostalgia is real! 🕰️ #{hashtag1} #Vintage #TradeUp",
        "Perfecting my {pokemon} deck build - every card choice matters in competitive play! ⚡ #{hashtag1} #Strategy #TradeUp",
        "The hunt for that perfect {pokemon} card continues. The chase is part of the fun! 🎯 #{hashtag1} #CardHunt #TradeUp",
        "Completed another page in my {pokemon} binder today. Organization is key! 📖 #{hashtag1} #Organized #TradeUp",
        "Regional championships are coming up! Time to finalize my {pokemon} deck list 📝 #{hashtag1} #Regionals #TradeUp"
    ]
    
    pokemon_names = [
        'Charizard', 'Pikachu', 'Blastoise', 'Venusaur', 'Mewtwo', 'Mew',
        'Lugia', 'Ho-Oh', 'Rayquaza', 'Dragonite', 'Gyarados', 'Snorlax',
        'Eevee', 'Umbreon', 'Espeon', 'Vaporeon', 'Jolteon', 'Flareon',
        'Alakazam', 'Gengar', 'Machamp', 'Golem', 'Lapras', 'Articuno',
        'Zapdos', 'Moltres', 'Celebi', 'Kyogre', 'Groudon', 'Dialga'
    ]
    
    hashtags = [
        'PokemonTCG', 'TCG', 'Pokemon', 'Cards', 'Collecting', 'Gaming',
        'Nostalgia', 'Vintage', 'Modern', 'Competitive', 'Casual', 'Fun'
    ]
    
    posts = []
    used_combinations = set()
    
    for i in range(count):
        # Ensure uniqueness by tracking used combinations
        attempts = 0
        while attempts < 50:  # Prevent infinite loop
            template = random.choice(templates)
            pokemon = random.choice(pokemon_names)
            hashtag1 = random.choice(hashtags)
            
            # Create a unique combination identifier
            combination = f"{template}-{pokemon}-{hashtag1}"
            combination_hash = hashlib.md5(combination.encode()).hexdigest()[:8]
            
            if combination_hash not in used_combinations:
                used_combinations.add(combination_hash)
                break
            attempts += 1
        
        # Add timestamp for extra uniqueness
        timestamp = datetime.now().strftime("%H:%M")
        
        content = template.replace('{pokemon}', pokemon).replace('{hashtag1}', hashtag1)
        
        # Add unique timestamp element occasionally
        if random.random() < 0.3:  # 30% chance
            content = content.replace('!', f' at {timestamp}!')
        
        posts.append({
            'content': content,
            'topic': pokemon,
            'viral_element': 'engagement',
            'target_audience': 'Pokemon TCG collectors',
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'uniqueness_hash': combination_hash
        })
    
    return posts

def call_openai_api(prompt: str) -> str:
    """Call the OpenAI API to generate viral content."""
    url = "https://api.openai.com/v1/chat/completions"
    
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json"
    }
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,  # Higher temperature for more variety
        "max_tokens": 2000
    }
    
    time.sleep(1)  # Rate limiting
    
    response = requests.post(url, headers=headers, data=json.dumps(data))
    response.raise_for_status()
    return response.json()["choices"][0]["message"]["content"]


def parse_llm_response(response: str, expected_count: int) -> List[Dict[str, Any]]:
    """Parse the LLM response to extract viral content posts."""
    viral_posts = []
    
    # Extract post sections
    post_sections = response.split("POST:")
    
    # Skip the first section (intro text)
    for section in post_sections[1:]:
        # Extract content
        content_match = section.split("CONTENT:", 1)
        if len(content_match) > 1:
            content_text = content_match[1].split("TOPIC:", 1)[0].strip()
        else:
            continue
        
        # Extract topic
        topic_match = section.split("TOPIC:", 1)
        if len(topic_match) > 1:
            topic = topic_match[1].split("VIRAL_ELEMENT:", 1)[0].strip()
        else:
            topic = "Pokémon Cards"
        
        # Extract viral element
        viral_element_match = section.split("VIRAL_ELEMENT:", 1)
        if len(viral_element_match) > 1:
            viral_element = viral_element_match[1].split("TARGET_AUDIENCE:", 1)[0].strip()
        else:
            viral_element = "engagement"
        
        # Extract target audience
        target_audience_match = section.split("TARGET_AUDIENCE:", 1)
        if len(target_audience_match) > 1:
            target_audience = target_audience_match[1].strip()
        else:
            target_audience = "Pokémon card collectors"
        
        # Only add if we have content
        if content_text:
            post = {
                'content': content_text,
                'topic': topic,
                'viral_element': viral_element,
                'target_audience': target_audience,
                'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            viral_posts.append(post)
    
    # If we didn't get enough posts, log a warning
    if len(viral_posts) < expected_count:
        print(f"Warning: Only generated {len(viral_posts)} posts out of {expected_count} requested")
    
    return viral_posts

def optimize_content_for_engagement(content: str) -> str:
    """Optimize content for maximum engagement by adding hashtags and ensuring proper formatting."""
    # Add TradeUp hashtag if not present
    if "#TradeUp" not in content and "#tradeup" not in content:
        content += " #TradeUp"
    
    # Add Pokémon hashtag if not present
    if "#Pokemon" not in content and "#pokemon" not in content and "#Pokémon" not in content:
        content += " #Pokemon"
    
    # Add TCG hashtag if not present
    if "#TCG" not in content and "#tcg" not in content:
        content += " #TCG"
    
    # Add timestamp for uniqueness (subtle)
    timestamp = datetime.now().strftime("%m%d")
    if len(content) < 250:  # Only if we have room
        content = content.replace("!", f"! 🎮{timestamp}")
    
    # Ensure content is within Twitter character limit (280)
    if len(content) > 280:
        content = content[:277] + "..."
    
    return content