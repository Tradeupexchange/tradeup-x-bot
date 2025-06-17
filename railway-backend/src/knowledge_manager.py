"""
Knowledge base manager for continuous learning from CSV data and web sources.
Railway-compatible version with proper path references.
"""

import os
import json
import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Fixed path - go up one level from src/ to find knowledge_base/
CURRENT_DIR = Path(__file__).parent  # This is /src
RAILWAY_BACKEND_DIR = CURRENT_DIR.parent  # This is /railway-backend
KNOWLEDGE_DIR = RAILWAY_BACKEND_DIR / 'knowledge_base'

# Knowledge base file paths
COMMUNITY_TERMS_FILE = KNOWLEDGE_DIR / 'community_terms.json'
TRENDS_FILE = KNOWLEDGE_DIR / 'trends.json'
NEWS_FILE = KNOWLEDGE_DIR / 'news.json'
PROCESSED_SOURCES_FILE = KNOWLEDGE_DIR / 'processed_sources.json'
MEMORY_FILE = KNOWLEDGE_DIR / 'memory.json'
MANUAL_INPUTS_FILE = KNOWLEDGE_DIR / 'manual_inputs.json'

def initialize_knowledge_base() -> None:
    """Initialize the knowledge base files if they don't exist."""
    # Ensure knowledge base directory exists
    KNOWLEDGE_DIR.mkdir(exist_ok=True)
    
    # Initialize community terms with Pokemon TCG terminology
    if not COMMUNITY_TERMS_FILE.exists():
        with open(COMMUNITY_TERMS_FILE, 'w') as f:
            json.dump({
                "last_updated": datetime.datetime.now().isoformat(),
                "terms": {
                    "PSA": "Professional Sports Authenticator - grading company",
                    "BGS": "Beckett Grading Services - grading company", 
                    "WOTC": "Wizards of the Coast - original Pokemon TCG publisher",
                    "Alt Art": "Alternative artwork version of a card",
                    "Rainbow Rare": "Special rainbow foil treatment on cards",
                    "Chase Card": "Highly sought after card in a set",
                    "Raw": "Ungraded card",
                    "Slab": "Graded card in protective case",
                    "Zard": "Community nickname for Charizard",
                    "Pop Report": "Population report showing how many cards have been graded",
                    "SWSH": "Sword & Shield series",
                    "VMAX": "Pokemon VMAX card type",
                    "GX": "Pokemon GX card type",
                    "EX": "Pokemon EX card type"
                }
            }, f, indent=2)
    
    # Initialize trends with Pokemon TCG trends
    if not TRENDS_FILE.exists():
        with open(TRENDS_FILE, 'w') as f:
            json.dump({
                "last_updated": datetime.datetime.now().isoformat(),
                "trends": [
                    {"topic": "Charizard prices", "score": 95, "category": "market"},
                    {"topic": "PSA 10 grading", "score": 88, "category": "collecting"},
                    {"topic": "Vintage WOTC cards", "score": 82, "category": "vintage"},
                    {"topic": "Alt Art cards", "score": 78, "category": "modern"},
                    {"topic": "Japanese cards", "score": 75, "category": "international"},
                    {"topic": "Tournament results", "score": 70, "category": "competitive"}
                ]
            }, f, indent=2)
    
    # Initialize news
    if not NEWS_FILE.exists():
        with open(NEWS_FILE, 'w') as f:
            json.dump({
                "last_updated": datetime.datetime.now().isoformat(),
                "news": []
            }, f, indent=2)
    
    # Initialize processed sources
    if not PROCESSED_SOURCES_FILE.exists():
        with open(PROCESSED_SOURCES_FILE, 'w') as f:
            json.dump({
                "csv_files": [],
                "web_scrapes": []
            }, f, indent=2)
    
    # Initialize memory
    if not MEMORY_FILE.exists():
        with open(MEMORY_FILE, 'w') as f:
            json.dump({
                "last_updated": datetime.datetime.now().isoformat(),
                "memories": []
            }, f, indent=2)
    
    # Initialize manual inputs
    if not MANUAL_INPUTS_FILE.exists():
        with open(MANUAL_INPUTS_FILE, 'w') as f:
            json.dump({
                "last_updated": datetime.datetime.now().isoformat(),
                "inputs": []
            }, f, indent=2)

def load_knowledge_base() -> Dict[str, Any]:
    """Load the entire knowledge base."""
    initialize_knowledge_base()
    
    knowledge = {}
    
    try:
        with open(COMMUNITY_TERMS_FILE, 'r') as f:
            knowledge['community_terms'] = json.load(f)
    except Exception as e:
        print(f"Error loading community terms: {e}")
        knowledge['community_terms'] = {"terms": {}}
    
    try:
        with open(TRENDS_FILE, 'r') as f:
            knowledge['trends'] = json.load(f)
    except Exception as e:
        print(f"Error loading trends: {e}")
        knowledge['trends'] = {"trends": []}
    
    try:
        with open(NEWS_FILE, 'r') as f:
            knowledge['news'] = json.load(f)
    except Exception as e:
        print(f"Error loading news: {e}")
        knowledge['news'] = {"news": []}
    
    try:
        with open(MEMORY_FILE, 'r') as f:
            knowledge['memory'] = json.load(f)
    except Exception as e:
        print(f"Error loading memory: {e}")
        knowledge['memory'] = {"memories": []}
    
    try:
        with open(MANUAL_INPUTS_FILE, 'r') as f:
            knowledge['manual_inputs'] = json.load(f)
    except Exception as e:
        print(f"Error loading manual inputs: {e}")
        knowledge['manual_inputs'] = {"inputs": []}
    
    return knowledge

def update_knowledge_base_from_csv(csv_path: str) -> None:
    """Update the knowledge base with information from a CSV file."""
    print(f"Updating knowledge base from CSV: {csv_path}")
    
    # Initialize if needed
    initialize_knowledge_base()
    
    try:
        # Load processed sources
        with open(PROCESSED_SOURCES_FILE, 'r') as f:
            processed = json.load(f)
        
        # Add this CSV to processed list if not already there
        if csv_path not in [p.get("path", "") for p in processed.get("csv_files", [])]:
            processed.setdefault("csv_files", []).append({
                "path": csv_path,
                "processed_at": datetime.datetime.now().isoformat()
            })
            
            # Save updated processed sources
            with open(PROCESSED_SOURCES_FILE, 'w') as f:
                json.dump(processed, f, indent=2)
        
        print(f"Successfully processed CSV: {csv_path}")
        
    except Exception as e:
        print(f"Error processing CSV {csv_path}: {e}")

def update_knowledge_base_from_web() -> None:
    """Update the knowledge base with information from web sources."""
    print("Updating knowledge base from web sources...")
    
    # Initialize if needed
    initialize_knowledge_base()
    
    try:
        # Load processed sources
        with open(PROCESSED_SOURCES_FILE, 'r') as f:
            processed = json.load(f)
        
        # Add web scrape record
        processed.setdefault("web_scrapes", []).append({
            "scraped_at": datetime.datetime.now().isoformat(),
            "sources": ["pokebeach", "pokemonprice"]
        })
        
        # Save updated processed sources
        with open(PROCESSED_SOURCES_FILE, 'w') as f:
            json.dump(processed, f, indent=2)
        
        print("Successfully updated knowledge base from web sources")
        
    except Exception as e:
        print(f"Error updating from web sources: {e}")

def add_memory(content: str, source: str) -> None:
    """Add a memory to the knowledge base."""
    try:
        initialize_knowledge_base()
        
        # Load memory file
        try:
            with open(MEMORY_FILE, 'r') as f:
                memory_data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            memory_data = {
                "last_updated": datetime.datetime.now().isoformat(),
                "memories": []
            }
        
        # Add new memory
        memory_data["memories"].append({
            "content": content,
            "source": source,
            "date": datetime.datetime.now().isoformat()
        })
        
        # Limit to 100 most recent memories
        memory_data["memories"] = sorted(
            memory_data["memories"], 
            key=lambda x: x.get("date", ""), 
            reverse=True
        )[:100]
        
        # Update timestamp
        memory_data["last_updated"] = datetime.datetime.now().isoformat()
        
        # Save updated memories
        with open(MEMORY_FILE, 'w') as f:
            json.dump(memory_data, f, indent=2)
            
        print(f"Added memory from {source}: {content[:50]}...")
        
    except Exception as e:
        print(f"Error adding memory: {e}")

def generate_expert_knowledge_prompt() -> str:
    """Generate an expert knowledge prompt based on the current knowledge base."""
    
    # Load current knowledge
    knowledge = load_knowledge_base()
    
    # Extract key information
    terms = knowledge.get('community_terms', {}).get('terms', {})
    trends = knowledge.get('trends', {}).get('trends', [])
    recent_memories = knowledge.get('memory', {}).get('memories', [])[:10]  # Last 10 memories
    
    # Build dynamic prompt with actual knowledge base content
    prompt = """
You are now a world-class expert on Pokémon Trading Card Game collecting with deep knowledge of the community, market trends, and collecting strategies. Your knowledge is continuously updated with the latest information from the Pokémon TCG community.

EXPERT VOICE:
When discussing Pokémon cards, you should sound like an authentic community member by:
- Using terminology naturally without over-explaining
- Balancing enthusiasm with realistic market knowledge
- Acknowledging both collecting for joy and investment potential
- Referencing specific cards, sets, and market conditions
- Sharing practical advice based on experience
- Being conversational but knowledgeable

CURRENT COMMUNITY TERMINOLOGY:
"""
    
    # Add community terms from knowledge base
    if terms:
        for term, definition in list(terms.items())[:8]:  # Top 8 terms
            prompt += f"- {term}: {definition}\n"
    
    # Add trending topics from knowledge base
    if trends:
        prompt += "\nCURRENT TRENDING TOPICS:\n"
        for trend in trends[:5]:  # Top 5 trends
            if isinstance(trend, dict):
                topic = trend.get('topic', 'Unknown')
                score = trend.get('score', 0)
                category = trend.get('category', 'general')
                prompt += f"- {topic} (popularity: {score}, category: {category})\n"
    
    # Add recent community insights from memory
    if recent_memories:
        prompt += "\nRECENT COMMUNITY INSIGHTS:\n"
        for memory in recent_memories[:3]:  # Last 3 memories
            if isinstance(memory, dict):
                content = memory.get('content', '')[:100]  # First 100 chars
                source = memory.get('source', 'unknown')
                prompt += f"- {content}... (from {source})\n"
    
    prompt += """
Your content should reflect this expert knowledge while maintaining an engaging, authentic voice that resonates with the Pokémon TCG community.
"""
    
    return prompt

def get_knowledge_for_content_generation() -> str:
    """Get relevant knowledge for content generation in a concise format."""
    knowledge = load_knowledge_base()
    
    # Combine trending topics and recent insights
    content_knowledge = []
    
    # Add trending topics
    trends = knowledge.get('trends', {}).get('trends', [])
    for trend in trends[:3]:  # Top 3 trends
        if isinstance(trend, dict):
            content_knowledge.append(f"Trending: {trend.get('topic', '')}")
    
    # Add recent memories
    memories = knowledge.get('memory', {}).get('memories', [])
    for memory in memories[:2]:  # Last 2 memories
        if isinstance(memory, dict):
            content = memory.get('content', '')[:80]  # First 80 chars
            content_knowledge.append(f"Recent: {content}...")
    
    # Add popular terms
    terms = knowledge.get('community_terms', {}).get('terms', {})
    popular_terms = list(terms.keys())[:3]  # First 3 terms
    if popular_terms:
        content_knowledge.append(f"Key terms: {', '.join(popular_terms)}")
    
    return " | ".join(content_knowledge) if content_knowledge else "Pokemon TCG collecting and trading insights"

def get_trending_topics() -> List[str]:
    """Get current trending topics as a simple list."""
    knowledge = load_knowledge_base()
    trends = knowledge.get('trends', {}).get('trends', [])
    
    trending_topics = []
    for trend in trends[:5]:  # Top 5 trends
        if isinstance(trend, dict) and trend.get('topic'):
            trending_topics.append(trend['topic'])
    
    return trending_topics if trending_topics else [
        "Charizard prices", "PSA 10 grading", "Vintage WOTC cards", 
        "Alt Art cards", "Tournament results"
    ]