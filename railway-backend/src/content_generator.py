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

# Core OpenAI setup
try:
    from openai import OpenAI
    from src.config import OPENAI_API_KEY
    
    client = OpenAI(api_key=OPENAI_API_KEY)
    OPENAI_AVAILABLE = True
    print("✅ OpenAI client initialized successfully")
except Exception as e:
    print(f"⚠️ OpenAI not available: {e}")
    OPENAI_AVAILABLE = False
    client = None

# Advanced learning modules (optional)
try:
    from src.continuous_learning_fetcher import get_continuous_learning_data
    LEARNING_AVAILABLE = True
    print("✅ Continuous learning module loaded")
except Exception as e:
    print(f"⚠️ Continuous learning not available: {e}")
    LEARNING_AVAILABLE = False
    def get_continuous_learning_data():
        return "Pokemon TCG trends: Charizard Alt Arts, PSA 10 prices climbing, vintage WOTC cards popular, new set releases generating buzz"

try:
    from src.feedback_database import FeedbackDatabase
    feedback_db = FeedbackDatabase()
    FEEDBACK_AVAILABLE = True
    print("✅ Feedback database initialized")
except Exception as e:
    print(f"⚠️ Feedback database not available: {e}")
    FEEDBACK_AVAILABLE = False
    feedback_db = None

try:
    from src.knowledge_manager import generate_expert_knowledge_prompt, get_knowledge_for_content_generation
    KNOWLEDGE_AVAILABLE = True
    print("✅ Knowledge manager loaded")
except Exception as e:
    print(f"⚠️ Knowledge manager not available: {e}")
    KNOWLEDGE_AVAILABLE = False
    def generate_expert_knowledge_prompt():
        return "You are a Pokemon TCG expert with deep community knowledge."
    def get_knowledge_for_content_generation():
        return "Popular topics: Charizard, Alt Arts, PSA grading, vintage cards"

# Enhanced TradeUp references with contextual mapping
TRADEUP_REFERENCES = [
    "If you trade it, TradeUp's got you 😉",
    "Listing it? TradeUp might be the move.",
    "Trade safe, TradeUp makes it easy.",
    "Looking to swap? I'd try TradeUp.",
    "When it's time to trade, TradeUp's a solid bet.",
    "That'd be a sweet listing on TradeUp.",
    "TradeUp's where I'd go for that one.",
    "You could always list it on TradeUp.",
    "Ready to trade? TradeUp makes it smooth.",
    "Trade it with peace of mind, TradeUp's the way.",
    "Heard good things about TradeUp for that.",
    "TradeUp could be the right move here.",
    "Don't sleep on TradeUp for trades like that.",
    "That card deserves a good trade, TradeUp's worth a look.",
    "Got it? Flip it on TradeUp.",
    "Might be time to trade it, TradeUp's solid.",
    "Saw some big trades on TradeUp for that one.",
    "Thinking of trading? Give TradeUp a shot.",
    "That'd make a killer TradeUp listing.",
    "TradeUp's been buzzing for pulls like that."
]

def select_contextual_tradeup_reference(post_content):
    """Select TradeUp reference based on post context"""
    keywords = {
        "trade": [0, 2, 3, 4, 8, 9, 15, 16, 17],
        "list": [1, 5, 7, 18],
        "sell": [14, 18],
        "buy": [10, 11, 13],
        "new": [16, 19],
        "rare": [13, 19],
        "collection": [6, 12],
    }
    
    possible_indices = list(range(len(TRADEUP_REFERENCES)))
    
    for keyword, indices in keywords.items():
        if keyword.lower() in post_content.lower():
            if indices:
                possible_indices = indices + possible_indices
                break
    
    selected_index = random.choice(possible_indices[:min(5, len(possible_indices))])
    return TRADEUP_REFERENCES[selected_index]

def generate_simple_content(count=1, topic=None):
    """Fallback content generation using templates"""
    
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
        
        posts.append({
            "post_content": content,
            "tradeup_mention": False
        })
    
    return posts

def generate_advanced_content(count=1, topic=None):
    """Advanced content generation with learning and knowledge integration"""
    
    try:
        # Gather learning data
        continuous_data = get_continuous_learning_data() if LEARNING_AVAILABLE else "Pokemon TCG collecting trends"
        expert_prompt = generate_expert_knowledge_prompt() if KNOWLEDGE_AVAILABLE else "You are a Pokemon TCG expert."
        knowledge_context = get_knowledge_for_content_generation() if KNOWLEDGE_AVAILABLE else "Popular: Charizard, Alt Arts, PSA grading"
        
        # Get feedback learning if available
        learning_summary = ""
        best_examples_text = ""
        
        if FEEDBACK_AVAILABLE and feedback_db:
            try:
                learning_summary = feedback_db.get_learning_summary(max_points=5)
                best_examples = feedback_db.get_best_examples(count=3)
                
                if best_examples:
                    best_examples_text = "Here are some examples of highly-rated posts:\n"
                    for i, example in enumerate(best_examples):
                        best_examples_text += f"{i+1}. \"{example}\"\n"
                        
                print(f"📚 Using {len(best_examples)} examples from feedback database")
            except Exception as e:
                print(f"⚠️ Feedback learning error: {e}")
        
        # Enhanced persona with learning
        persona_guidelines = f"""
        {expert_prompt}
        
        You are TUPokePal, a knowledgeable and passionate Pokémon-card collector. 
        You speak like a real human fan in online communities (e.g., Discord, Twitter), 
        using simple, casual language with collector slang like Alt Art, Zard, chase card, pop report. 
        You never sound like a corporate marketer. Keep replies short (under 200 characters) 
        with max 1 emoji if it fits. Rotate emojis and avoid repeating the same opening lines. 
        Focus on being genuinely helpful and interesting.
        
        Current community context: {knowledge_context}
        """
        
        # Advanced prompt with all learning data
        prompt = f"""
        As TUPokePal, generate {count} distinct social media posts about Pokémon cards. 
        Each post should be 1-2 sentences, max 200 characters, casual, friendly, and engaging. 
        Use one emoji per post (rotate 🔥 😍 🤩 😉 🐉 ⚡️). 
        
        Here are some recent trends and data points to draw from:
        {continuous_data}
        
        LEARNING FROM FEEDBACK:
        {learning_summary}
        
        BEST PERFORMING EXAMPLES:
        {best_examples_text}

        If a manual topic is provided, strongly incorporate it into the posts. 
        Manual Topic: {topic if topic else "None"}

        Each post should be unique and cover different aspects of Pokémon cards (e.g., fun facts, price trends, collector tips, new sets, specific cards, community questions).
        
        IMPORTANT: Vary the number of hashtags between 0 and 3 per post. Some posts should have no hashtags, some should have 1, 2, or 3 hashtags.
        
        Examples of hashtag variation:
        - "Just pulled a shiny Charizard! My binder love is real right now 🔥" (0 hashtags)
        - "Anyone else hunting for that Umbreon VMAX Alt Art? #PokemonTCG 😍" (1 hashtag)
        - "PSA 10 Pikachu prices keep climbing! Anyone else watching the market? #Pokemon #TCGCollector 🤩" (2 hashtags)
        - "New Scarlet & Violet set looking fire! What's your chase card? #Pokemon #TCG #NewRelease ⚡️" (3 hashtags)
        
        DO NOT include any mentions of TradeUp in your posts - this will be handled separately.
        
        Format your response as a JSON array of objects, where each object has a "post_content" key and a "tradeup_mention" boolean key (always set to false).
        Example format:
        [
            {{
                "post_content": "Just pulled a shiny Charizard! My binder love is real right now 🔥",
                "tradeup_mention": false
            }},
            {{
                "post_content": "Anyone else hunting for that Umbreon VMAX Alt Art? #PokemonTCG 😍",
                "tradeup_mention": false
            }}
        ]
        """
        
        print(f"🧠 Using advanced generation with learning data")
        print(f"📊 Knowledge available: {KNOWLEDGE_AVAILABLE}")
        print(f"🔄 Feedback available: {FEEDBACK_AVAILABLE}")
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": persona_guidelines},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,
            temperature=0.8
        )
        
        content = response.choices[0].message.content
        print(f"🤖 OpenAI Response received: {len(content)} characters")
        
        # Parse JSON response
        try:
            posts = json.loads(content)
            if isinstance(posts, list):
                print(f"✅ Parsed {len(posts)} posts from JSON")
                return posts[:count]
        except json.JSONDecodeError as e:
            print(f"❌ JSON parse error: {e}")
            # Try to extract JSON from response
            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                try:
                    posts = json.loads(json_match.group(0))
                    if isinstance(posts, list):
                        print(f"✅ Extracted {len(posts)} posts from partial JSON")
                        return posts[:count]
                except:
                    pass
        
    except Exception as e:
        print(f"❌ Advanced generation error: {e}")
    
    # Fallback to simple content
    print("🔄 Falling back to simple content generation")
    return generate_simple_content(count, topic)

def apply_tradeup_mention(posts, count=5):
    """Apply TradeUp mention to exactly 1 out of 5 posts with contextual selection"""
    
    updated_posts = [post.copy() for post in posts]
    
    if not updated_posts:
        return updated_posts
    
    # Select random post for TradeUp mention
    max_index = min(len(updated_posts) - 1, count - 1)
    post_index = random.randint(0, max_index)
    
    # Reset all flags
    for post in updated_posts:
        post["tradeup_mention"] = False
    
    # Add contextual TradeUp reference
    selected_post = updated_posts[post_index]
    tradeup_phrase = select_contextual_tradeup_reference(selected_post["post_content"])
    
    updated_posts[post_index]["post_content"] += " " + tradeup_phrase
    updated_posts[post_index]["tradeup_mention"] = True
    
    print(f"💼 Added TradeUp mention to post {post_index + 1}: '{tradeup_phrase}'")
    
    return updated_posts

def generate_viral_content(count: int = 1, topic: str = None, keywords: list = None) -> List[Dict[str, Any]]:
    """
    Main content generation function with advanced learning capabilities.
    Falls back gracefully when advanced features aren't available.
    """
    
    print(f"🎯 Generating {count} posts with topic: {topic}")
    print(f"🔧 OpenAI: {OPENAI_AVAILABLE}, Learning: {LEARNING_AVAILABLE}, Feedback: {FEEDBACK_AVAILABLE}, Knowledge: {KNOWLEDGE_AVAILABLE}")
    
    # Generate posts using best available method
    if OPENAI_AVAILABLE and client:
        if LEARNING_AVAILABLE or FEEDBACK_AVAILABLE or KNOWLEDGE_AVAILABLE:
            print("🚀 Using advanced generation with learning")
            posts = generate_advanced_content(count, topic)
        else:
            print("🚀 Using basic OpenAI generation")
            posts = generate_openai_content_simple(count, topic)
    else:
        print("🚀 Using template-based generation")
        posts = generate_simple_content(count, topic)
    
    # Apply TradeUp mentions (1 in 5 rule)
    posts = apply_tradeup_mention(posts, count)
    
    print(f"✅ Generated {len(posts)} posts")
    
    # Convert to API format
    viral_posts = []
    for i, post in enumerate(posts):
        if isinstance(post, dict) and 'post_content' in post:
            content = post['post_content']
            hashtags = re.findall(r'#\w+', content)
            
            viral_posts.append({
                "content": content,
                "engagement_score": round(random.uniform(0.7, 0.95), 2),
                "estimated_likes": random.randint(30, 200),
                "estimated_retweets": random.randint(8, 80),
                "hashtags": hashtags,
                "mentions_tradeup": post.get('tradeup_mention', False),
                "generated_at": datetime.now().isoformat(),
                "topic": topic or "general",
                "keywords": keywords or [],
                "method": "advanced" if (LEARNING_AVAILABLE or FEEDBACK_AVAILABLE) else "basic",
                "learning_features": {
                    "feedback_learning": FEEDBACK_AVAILABLE,
                    "knowledge_base": KNOWLEDGE_AVAILABLE,
                    "continuous_learning": LEARNING_AVAILABLE
                }
            })
    
    # Log sample for debugging
    if viral_posts:
        sample = viral_posts[0]
        print(f"📝 Sample: {sample['content']}")
        print(f"🏷️ Method: {sample['method']}")
        print(f"💼 TradeUp: {sample['mentions_tradeup']}")
    
    return viral_posts

def generate_openai_content_simple(count=1, topic=None):
    """Simple OpenAI generation without advanced features"""
    
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
        
        try:
            posts = json.loads(content)
            if isinstance(posts, list):
                return posts[:count]
        except json.JSONDecodeError:
            pass
            
    except Exception as e:
        print(f"Simple OpenAI generation error: {e}")
    
    return generate_simple_content(count, topic)

def optimize_content_for_engagement(content: str) -> str:
    """Enhanced content optimization with feedback learning"""
    
    try:
        if FEEDBACK_AVAILABLE and feedback_db:
            # Get insights from feedback database
            learning_summary = feedback_db.get_learning_summary(max_points=3)
            
            # Apply optimizations based on learning
            optimized = content
            
            # Smart TradeUp mention based on feedback patterns
            if "TradeUp" not in optimized and "tradeup" not in optimized.lower():
                if random.random() < 0.2:  # 20% chance
                    tradeup_phrase = select_contextual_tradeup_reference(optimized)
                    optimized += " " + tradeup_phrase
            
            return optimized
        
    except Exception as e:
        print(f"Optimization error: {e}")
    
    # Basic optimization
    return content

def extract_hashtags(content: str) -> List[str]:
    """Extract hashtags from content"""
    return re.findall(r'#\w+', content)

def add_feedback_to_database(post_content: str, rating: int, feedback_text: str = "", metadata: dict = None):
    """Add feedback for continuous learning"""
    
    if not FEEDBACK_AVAILABLE or not feedback_db:
        print("⚠️ Feedback database not available")
        return None
    
    try:
        feedback_id = feedback_db.add_feedback(
            post_content=post_content,
            feedback=feedback_text,
            rating=rating,
            post_metadata=metadata
        )
        print(f"✅ Added feedback to database: {feedback_id}")
        return feedback_id
    except Exception as e:
        print(f"❌ Error adding feedback: {e}")
        return None

def get_feedback_stats():
    """Get current feedback statistics"""
    
    if not FEEDBACK_AVAILABLE or not feedback_db:
        return {"error": "Feedback database not available"}
    
    try:
        return feedback_db.get_feedback_stats()
    except Exception as e:
        print(f"Error getting feedback stats: {e}")
        return {"error": str(e)}

# Backwards compatibility
def main(count=5, topic=None):
    """Backwards compatibility function"""
    posts = generate_viral_content(count=count, topic=topic)
    return [post["content"] for post in posts]

if __name__ == "__main__":
    print("🚀 Testing enhanced content generator...")
    
    # Test generation
    test_posts = generate_viral_content(count=3, topic="Charizard")
    
    print(f"\n📋 Generated {len(test_posts)} test posts:")
    for i, post in enumerate(test_posts, 1):
        print(f"\n{i}. {post['content']}")
        print(f"   TradeUp mention: {post['mentions_tradeup']}")
        print(f"   Hashtags: {post['hashtags']}")
        print(f"   Method: {post['method']}")
        print(f"   Learning features: {post['learning_features']}")
    
    print("\n✅ Enhanced content generator test complete!")