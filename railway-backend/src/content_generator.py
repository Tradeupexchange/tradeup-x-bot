import os
import sys
import random
import re
import json
from datetime import datetime
from typing import List, Dict, Any

# Add the parent directory to sys.path if running directly
if __name__ == "__main__" and "src" not in sys.path:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

try:
    from openai import OpenAI
    from src.config import OPENAI_API_KEY
    
    # Initialize OpenAI client
    client = OpenAI(api_key=OPENAI_API_KEY)
    OPENAI_AVAILABLE = True
    print("✅ OpenAI client initialized successfully")
except Exception as e:
    print(f"⚠️ OpenAI not available: {e}")
    OPENAI_AVAILABLE = False
    client = None

# Try to import optional modules
try:
    from src.continuous_learning_fetcher import get_continuous_learning_data
    LEARNING_AVAILABLE = True
except:
    LEARNING_AVAILABLE = False
    def get_continuous_learning_data():
        return "Pokemon TCG trends: Charizard, Pikachu, Alt Art cards"

try:
    from src.feedback_database import FeedbackDatabase
    feedback_db = FeedbackDatabase()
    FEEDBACK_AVAILABLE = True
    print("✅ Feedback database initialized")
except Exception as e:
    print(f"⚠️ Feedback database not available: {e}")
    FEEDBACK_AVAILABLE = False
    feedback_db = None

# TradeUp references
TRADEUP_REFERENCES = [
    "Trade safely on TradeUp!",
    "Check out TradeUp for trades!",
    "TradeUp makes trading easy!",
    "List it on TradeUp!",
    "TradeUp's got great deals!"
]

def generate_simple_content(count=1, topic=None):
    """Generate simple Pokemon TCG content without complex dependencies"""
    
    templates = [
        "Just pulled a shiny {pokemon}! The artwork is incredible 🔥",
        "Anyone else collecting {pokemon} cards? The market is hot right now 📈",
        "That feeling when you get a perfect {pokemon} pull! #PokemonTCG 😍",
        "Building a {pokemon} deck - the strategy options are endless ⚡",
        "Found a gem: vintage {pokemon} card in mint condition! 💎",
        "The {pokemon} alt art cards are absolutely stunning 🎨",
        "PSA 10 {pokemon} prices climbing again! Investment potential 💰",
        "New set features amazing {pokemon} artwork - must collect! ✨",
        "Tournament ready with my {pokemon} deck build 🏆",
        "Childhood nostalgia hits different with {pokemon} cards 🌟"
    ]
    
    pokemon_names = [
        'Charizard', 'Pikachu', 'Blastoise', 'Venusaur', 'Mewtwo', 'Mew',
        'Lugia', 'Ho-Oh', 'Rayquaza', 'Dragonite', 'Gyarados', 'Snorlax',
        'Eevee', 'Umbreon', 'Espeon', 'Alakazam', 'Gengar', 'Machamp'
    ]
    
    posts = []
    for i in range(count):
        template = random.choice(templates)
        pokemon = random.choice(pokemon_names)
        content = template.replace('{pokemon}', pokemon)
        
        # Add TradeUp mention to 1 in 5 posts
        if i == 0 and count >= 1:  # Add to first post
            content += " " + random.choice(TRADEUP_REFERENCES)
            tradeup_mention = True
        else:
            tradeup_mention = False
        
        posts.append({
            "post_content": content,
            "tradeup_mention": tradeup_mention
        })
    
    return posts

def generate_openai_content(count=1, topic=None):
    """Generate content using OpenAI API"""
    
    try:
        learning_data = get_continuous_learning_data() if LEARNING_AVAILABLE else "Pokemon TCG collecting trends"
        
        prompt = f"""
        You are TUPokePal, a Pokemon card collector. Generate {count} casual, engaging tweets about Pokemon cards.
        Each should be under 200 characters with 0-2 hashtags and 1 emoji.
        
        Recent trends: {learning_data}
        Topic focus: {topic or "general Pokemon TCG"}
        
        Format as JSON array:
        [
            {{"post_content": "Your tweet here 🔥", "tradeup_mention": false}},
            {{"post_content": "Another tweet #Pokemon ⚡", "tradeup_mention": false}}
        ]
        
        DO NOT mention TradeUp in the posts - handled separately.
        """
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=800,
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        print(f"OpenAI Response: {content}")
        
        # Parse JSON response
        try:
            posts = json.loads(content)
            if isinstance(posts, list):
                # Add TradeUp mention to one random post
                if posts and count > 0:
                    random_index = random.randint(0, min(len(posts)-1, count-1))
                    tradeup_ref = random.choice(TRADEUP_REFERENCES)
                    posts[random_index]["post_content"] += f" {tradeup_ref}"
                    posts[random_index]["tradeup_mention"] = True
                
                return posts[:count]
        except json.JSONDecodeError:
            print("Failed to parse OpenAI JSON response")
            
    except Exception as e:
        print(f"OpenAI generation error: {e}")
    
    # Fallback to simple content
    return generate_simple_content(count, topic)

def generate_viral_content(count: int = 1, topic: str = None, keywords: list = None) -> List[Dict[str, Any]]:
    """
    Main content generation function for API compatibility.
    Returns content in the format expected by main.py
    """
    
    print(f"🎯 Generating {count} posts with topic: {topic}")
    print(f"🔧 OpenAI available: {OPENAI_AVAILABLE}")
    print(f"🔧 Feedback available: {FEEDBACK_AVAILABLE}")
    
    # Generate posts using best available method
    if OPENAI_AVAILABLE and client:
        posts = generate_openai_content(count, topic)
    else:
        posts = generate_simple_content(count, topic)
    
    print(f"✅ Generated {len(posts)} posts")
    
    # Convert to API format
    viral_posts = []
    for i, post in enumerate(posts):
        if isinstance(post, dict) and 'post_content' in post:
            content = post['post_content']
            hashtags = re.findall(r'#\w+', content)
            
            viral_posts.append({
                "content": content,
                "engagement_score": round(random.uniform(0.6, 0.9), 2),
                "estimated_likes": random.randint(20, 150),
                "estimated_retweets": random.randint(5, 50),
                "hashtags": hashtags,
                "mentions_tradeup": post.get('tradeup_mention', False),
                "generated_at": datetime.now().isoformat(),
                "topic": topic or "general",
                "keywords": keywords or [],
                "method": "openai" if OPENAI_AVAILABLE else "template"
            })
        
    print(f"🎉 Returning {len(viral_posts)} formatted posts")
    
    # Log first post for debugging
    if viral_posts:
        print(f"📝 Sample: {viral_posts[0]['content']}")
    
    return viral_posts

def optimize_content_for_engagement(content: str) -> str:
    """Simple content optimization"""
    # Just return content as-is for now
    return content

def extract_hashtags(content: str) -> List[str]:
    """Extract hashtags from content"""
    return re.findall(r'#\w+', content)

# For backwards compatibility
def main(count=5, topic=None):
    """Backwards compatibility function"""
    posts = generate_viral_content(count=count, topic=topic)
    return [post["content"] for post in posts]

if __name__ == "__main__":
    print("🚀 Testing content generator...")
    
    # Test generation
    test_posts = generate_viral_content(count=3, topic="Charizard")
    
    print(f"\n📋 Generated {len(test_posts)} test posts:")
    for i, post in enumerate(test_posts, 1):
        print(f"\n{i}. {post['content']}")
        print(f"   TradeUp mention: {post['mentions_tradeup']}")
        print(f"   Hashtags: {post['hashtags']}")
        print(f"   Method: {post['method']}")
    
    print("\n✅ Content generator test complete!")