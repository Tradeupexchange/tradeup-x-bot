import os
import sys
import random
import re
import json

# Add the parent directory to sys.path if running directly
# This allows imports like 'from src.continuous_learning_fetcher' to work
if __name__ == "__main__" and "src" not in sys.path:
    current_dir = os.path.dirname(os.path.abspath(__file__))
    parent_dir = os.path.dirname(current_dir)
    if parent_dir not in sys.path:
        sys.path.insert(0, parent_dir)

from openai import OpenAI
from src.continuous_learning_fetcher import get_continuous_learning_data
from src.config import OPENAI_API_KEY

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# List of varied TradeUp references to use
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

def parse_llm_response(response_content):
    """
    Parses the LLM's response to extract individual posts.
    Assumes the LLM returns a JSON array of objects.
    """
    try:
        # Attempt to parse as direct JSON
        posts = json.loads(response_content)
        if isinstance(posts, list):
            return posts
    except json.JSONDecodeError:
        pass

    # Fallback for cases where LLM might not return perfect JSON
    # Try to find JSON-like structures within the response
    json_match = re.search(r'\[.*?\]', response_content, re.DOTALL)
    if json_match:
        try:
            posts = json.loads(json_match.group(0))
            if isinstance(posts, list):
                return posts
        except json.JSONDecodeError:
            pass

    # If all else fails, try to split by common separators and create a single post
    # This is a last resort to ensure at least one post is returned
    lines = [line.strip() for line in response_content.split('\n') if line.strip()]
    if lines:
        content = " ".join(lines)
        tradeup_mentioned = "tradeup" in content.lower()
        return [{
            "post_content": content,
            "tradeup_mention": tradeup_mentioned
        }]
    return []

def select_contextual_tradeup_reference(post_content):
    """
    Selects a TradeUp reference that is contextually relevant to the post content.
    
    :param post_content: The content of the post
    :return: A contextually appropriate TradeUp reference
    """
    # Keywords to match with specific references
    keywords = {
        "trade": [0, 2, 3, 4, 8, 9, 15, 16, 17],  # Indices of references mentioning "trade"
        "list": [1, 5, 7, 18],  # Indices of references mentioning "listing"
        "sell": [14, 18],  # Indices of references related to selling
        "buy": [10, 11, 13],  # Indices of references related to buying/value
        "new": [16, 19],  # Indices of references for new/hot items
        "rare": [13, 19],  # Indices of references for rare/valuable items
        "collection": [6, 12],  # Indices of references for collection-related posts
    }
    
    # Default to random selection
    possible_indices = list(range(len(TRADEUP_REFERENCES)))
    
    # Check for keyword matches to narrow down contextually appropriate references
    for keyword, indices in keywords.items():
        if keyword.lower() in post_content.lower():
            # If we find a keyword match, prioritize those references but keep others as fallback
            if indices:
                possible_indices = indices + possible_indices
                break
    
    # Select a reference, prioritizing the first few in the possible_indices list
    # which would be the contextually matched ones if any were found
    selected_index = random.choice(possible_indices[:min(5, len(possible_indices))])
    return TRADEUP_REFERENCES[selected_index]

def apply_tradeup_mention(posts, count=5):
    """
    Deterministically applies TradeUp mention to exactly 1 out of 5 posts,
    using varied and contextually relevant references.
    
    :param posts: List of post dictionaries
    :param count: Total number of posts expected (typically 5)
    :return: Updated list of posts with exactly one TradeUp mention
    """
    # Deep copy the posts to avoid modifying the original
    updated_posts = [post.copy() for post in posts]
    
    # Ensure we have posts to work with
    if not updated_posts:
        return updated_posts
    
    # Select a random post to modify (between 0 and min(len(posts)-1, count-1))
    max_index = min(len(updated_posts) - 1, count - 1)
    post_index = random.randint(0, max_index)
    
    # Reset all tradeup_mention flags to False first
    for post in updated_posts:
        post["tradeup_mention"] = False
    
    # Select a contextually appropriate TradeUp reference
    selected_post = updated_posts[post_index]
    tradeup_phrase = select_contextual_tradeup_reference(selected_post["post_content"])
    
    # Add the TradeUp mention phrase to the selected post
    updated_posts[post_index]["post_content"] += " " + tradeup_phrase
    updated_posts[post_index]["tradeup_mention"] = True
    
    return updated_posts

def generate_viral_content(manual_topic=None, count=5):
    """
    Generates multiple viral social media posts based on trending Pokémon TCG content.
    :param manual_topic: Optional, a specific topic or keyword to focus on.
    :param count: The number of posts to generate.
    :return: A list of dictionaries, each representing a post.
    """
    continuous_learning_data = get_continuous_learning_data()

    
    # Format best examples for the prompt
    best_examples_text = ""
    if best_examples:
        best_examples_text = "Here are some examples of highly-rated posts:\n"
        for i, example in enumerate(best_examples):
            best_examples_text += f"{i+1}. \"{example}\"\n"

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
    As TUPokePal, generate {count} distinct social media posts about Pokémon cards. 
    Each post should be 1-2 sentences, max 200 characters, casual, friendly, and engaging. 
    Use one emoji per post (rotate 🔥 😍 🤩 😉 🐉 ⚡️). 
    
    Here are some recent trends and data points to draw from:
    {continuous_learning_data}
    
    {learning_summary}
    
    {best_examples_text}

    If a manual topic is provided, strongly incorporate it into the posts. 
    Manual Topic: {manual_topic if manual_topic else "None"}

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

    try:
        print(f"Generating {count} posts with topic: {manual_topic}")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",  # Or "gpt-4" for higher quality
            messages=[
                {"role": "system", "content": persona_guidelines},
                {"role": "user", "content": prompt}
            ],
            max_tokens=1500,  # Adjust based on expected output length
            n=1,  # We ask for multiple posts within one response
            stop=None,  # No specific stop sequence
            temperature=0.8, # Slightly higher temperature for more creativity and variation
        )
        
        llm_response_content = response.choices[0].message.content
        print(f"LLM Raw Response: {llm_response_content}") # Debugging line
        
        # Attempt to parse the JSON response
        posts = parse_llm_response(llm_response_content)
        
        # Filter out any non-dictionary items or malformed posts
        valid_posts = [p for p in posts if isinstance(p, dict) and "post_content" in p]
        
        # Apply TradeUp mention to exactly 1 out of 5 posts
        valid_posts = apply_tradeup_mention(valid_posts, count)
        
        # Ensure we return exactly `count` posts, filling with placeholders if necessary
        while len(valid_posts) < count:
            valid_posts.append({
                "post_content": f"Placeholder post {len(valid_posts) + 1}. No content generated for this slot. Please check OpenAI API or prompt.",
                "tradeup_mention": False
            })
        
        return valid_posts[:count]

    except Exception as e:
        print(f"Error generating content: {e}")
        # Return placeholder posts in case of an error
        error_posts = []
        for i in range(count):
            error_posts.append({
                "post_content": f"Error generating post {i+1}. Please check API key or server logs. Error: {e}",
                "tradeup_mention": False
            })
        return error_posts

def optimize_content_for_engagement(post_content):
    """
    This function is a placeholder for future optimization logic.
    It currently returns the content as is.
    """
    return post_content

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate viral social media posts')
    parser.add_argument('--topic', type=str, help='Manual topic to focus on')
    parser.add_argument('--count', type=int, default=5, help='Number of posts to generate')
    parser.add_argument('--feedback', action='store_true', help='Collect feedback on generated posts')
    
    args = parser.parse_args()
    
    print("Generating content...")
    posts = generate_viral_content(manual_topic=args.topic, count=args.count)
    
    print(f"\nGenerated {len(posts)} posts:")
    for i, post in enumerate(posts):
        print(f"\nPost {i+1}: {post['post_content']}")
        print(f"TradeUp Mention: {post['tradeup_mention']}")
    
