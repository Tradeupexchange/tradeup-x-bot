from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import sys
import os

try:
    # Try to import from src directory first
    from src.google_sheets_reader import get_tweets_for_reply, get_tweets_from_sheet, test_sheet_connection
    GOOGLE_SHEETS_AVAILABLE = True
    logger.info("✅ Google Sheets reader imported successfully")
except ImportError:
    try:
        # Fallback to current directory
        from google_sheets_reader import get_tweets_for_reply, get_tweets_from_sheet, test_sheet_connection
        GOOGLE_SHEETS_AVAILABLE = True
        logger.info("✅ Google Sheets reader imported from current directory")
    except ImportError as e:
        logger.warning(f"⚠️ Google Sheets reader not available: {e}")
        GOOGLE_SHEETS_AVAILABLE = False

#REPLACE WITH NEW SHEETS URL
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0"

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(title="Pokemon TCG Bot API")

# Simple CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Simple OPTIONS handler
@app.options("/{rest_of_path:path}")
async def preflight_handler(rest_of_path: str):
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

def setup_reply_functions():
    """Setup reply generation functions with error handling"""
    global generate_reply
    
    try:
        # Add current directory and subdirectories to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Common subdirectory patterns where reply_generator.py might be
        potential_paths = [
            current_dir,  # Same directory as main.py
            os.path.join(current_dir, 'src'),  # src subdirectory
            os.path.join(current_dir, 'app'),  # app subdirectory
            os.path.join(current_dir, 'bot'),  # bot subdirectory
        ]
        
        # Add all potential paths
        for path in potential_paths:
            if os.path.exists(path) and path not in sys.path:
                sys.path.insert(0, path)
                logger.info(f"📁 Added to Python path: {path}")
        
        # List all Python files for debugging
        logger.info(f"📁 Current working directory: {os.getcwd()}")
        logger.info(f"📁 Main script directory: {current_dir}")
        
        # Check which directories contain reply_generator.py
        for path in potential_paths:
            if os.path.exists(path):
                py_files = [f for f in os.listdir(path) if f.endswith('.py')]
                logger.info(f"📁 Files in {path}: {py_files}")
                
                reply_gen_path = os.path.join(path, 'reply_generator.py')
                if os.path.exists(reply_gen_path):
                    logger.info(f"✅ Found reply_generator.py at: {reply_gen_path}")
        
        # Try to import reply_generator
        logger.info("🔄 Attempting to import reply_generator...")
        from reply_generator import generate_reply as actual_generate_reply
        generate_reply = actual_generate_reply
        logger.info("✅ Successfully imported reply_generator")
        
        # Test the function
        test_result = generate_reply("test tweet about Pokemon cards", "test_user")
        logger.info(f"🧪 Test result: {test_result}")
        
        # Check if it's working properly
        if isinstance(test_result, dict) and test_result.get("success", False):
            logger.info("✅ Reply generation is working!")
            return True
        else:
            logger.warning("⚠️ Reply generation imported but not working as expected")
            return False
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("🔍 Possible issues:")
        logger.error("   - reply_generator.py not found in expected directories")
        logger.error("   - Import errors within reply_generator.py")
        logger.error("   - llm_manager.py import issues")
        logger.error("   - Missing dependencies or API keys")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        return False

# Fallback dummy function
def generate_reply(tweet_text, tweet_author=None, conversation_history=None):
    return {
        "content": f"Thanks for sharing! Great point about Pokemon TCG. The part about '{tweet_text[:50]}...' really resonates with the community!",
        "success": False,
        "error": "Reply generator not properly initialized"
    }

# Try to setup reply generation
logger.info("🚀 Setting up reply generation...")
reply_setup_success = setup_reply_functions()

if reply_setup_success:
    logger.info("✅ Reply generation is ready!")
else:
    logger.warning("⚠️ Using fallback reply generation")

def post_reply_tweet(content, reply_to_id):
    return {"success": False, "error": "Reply integration not available"}

# Models
class GenerateReplyRequest(BaseModel):
    tweet_text: str
    tweet_author: Optional[str] = None
    conversation_history: Optional[str] = None

class GenerateContentRequest(BaseModel):
    topic: Optional[str] = "pokemon_tcg"
    style: Optional[str] = "engaging"
    include_hashtags: Optional[bool] = True

# Essential endpoints
@app.get("/")
async def root():
    return {
        "message": "Pokemon TCG Bot API is running", 
        "status": "healthy",
        "reply_generator_active": reply_setup_success
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "Backend is running",
        "reply_status": "active" if reply_setup_success else "fallback"
    }

@app.get("/api/bot-status")
async def get_bot_status():
    return {
        "running": True,
        "uptime": "Just started",
        "lastRun": datetime.now().isoformat(),
        "stats": {"postsToday": 0, "repliesToday": 0, "successRate": 100.0},
        "jobs": [],
        "reply_generator_active": reply_setup_success,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/posts")
async def get_posts():
    posts = [
        {
            "id": "post_1",
            "content": "Test post about Pokemon TCG!",
            "timestamp": datetime.now().isoformat(),
            "platform": "twitter",
            "engagement": {"likes": 5, "retweets": 1, "replies": 2},
            "status": "posted"
        }
    ]
    return {"success": True, "posts": posts, "total": len(posts)}

@app.get("/api/topics")
async def get_topics():
    topics = [
        {"id": "pokemon_tcg", "name": "Pokemon TCG", "description": "General Pokemon TCG content"},
        {"id": "deck_building", "name": "Deck Building", "description": "Pokemon TCG deck building strategies"},
        {"id": "card_reveals", "name": "Card Reveals", "description": "New Pokemon card reveals and analysis"},
        {"id": "tournament_play", "name": "Tournament Play", "description": "Competitive Pokemon TCG content"}
    ]
    return {"success": True, "topics": topics, "total": len(topics)}

@app.post("/api/generate-content")
async def generate_content_endpoint(request: GenerateContentRequest):
    """Generate original Pokemon TCG content using reply generator"""
    try:
        # For content generation, we can reuse the reply generator with a content prompt
        content_prompt = f"Generate an engaging Pokemon TCG social media post about {request.topic}. Make it authentic and interesting for the Pokemon TCG community."
        
        result = generate_reply(content_prompt, "content_generator")
        
        if isinstance(result, dict) and result.get("success", False):
            content = result.get("content", "")
        else:
            # Fallback content
            content = "Just opened some new Pokemon TCG packs! The artwork on these cards is absolutely stunning. What's your favorite Pokemon card art? #PokemonTCG"
        
        # Add hashtags if requested
        hashtags = ["#PokemonTCG"]
        if request.include_hashtags:
            if "deck" in content.lower():
                hashtags.append("#DeckBuilding")
            if "tournament" in content.lower() or "competitive" in content.lower():
                hashtags.append("#PokemonTournament")
            if "pull" in content.lower() or "pack" in content.lower():
                hashtags.append("#PokemonPulls")
        
        return {
            "success": True,
            "content": {
                "content": content,
                "engagement_score": 88.5,
                "hashtags": hashtags,
                "mentions_tradeup": False,
                "reply_generator_used": reply_setup_success
            },
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/generate-reply")
async def generate_reply_endpoint(request: GenerateReplyRequest):
    """Generate a customized reply to a tweet using reply generator"""
    try:
        logger.info(f"🤖 Generating reply for tweet: {request.tweet_text[:100]}...")
        
        # Generate reply using reply generator
        result = generate_reply(
            request.tweet_text, 
            request.tweet_author, 
            request.conversation_history
        )
        
        logger.info(f"📝 Generated result: {result}")
        
        # Handle response format
        if isinstance(result, dict):
            reply_content = result.get("content", "No reply generated")
            success = result.get("success", False)
            error = result.get("error", None)
            llm_used = result.get("llm_used", False)
        else:
            reply_content = str(result)
            success = True
            error = None
            llm_used = False
        
        return {
            "success": success,
            "reply": reply_content,
            "original_tweet": request.tweet_text,
            "author": request.tweet_author,
            "reply_generator_used": reply_setup_success,
            "llm_used": llm_used,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error generating reply: {e}")
        return {
            "success": False,
            "error": str(e),
            "reply": "Sorry, I couldn't generate a reply right now.",
            "original_tweet": request.tweet_text,
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/fetch-tweets-from-sheets")
async def fetch_tweets_from_sheets():
    """Fetch tweets from Google Sheets for reply generation"""
    try:
        if not GOOGLE_SHEETS_AVAILABLE:
            # Return mock data if Google Sheets reader is not available
            logger.warning("📊 Google Sheets reader not available, returning mock data")
            mock_tweets = [
                {
                    "id": "tweet_1",
                    "text": "Just pulled a Charizard ex from my latest Pokemon TCG pack! The artwork is incredible. Building a fire deck around it now!",
                    "author": "PokemonFan123",
                    "author_name": "Pokemon Fan",
                    "created_at": (datetime.now() - timedelta(hours=2)).isoformat(),
                    "url": "https://twitter.com/PokemonFan123/status/123456789",
                    "conversation_id": "tweet_1"
                },
                {
                    "id": "tweet_2",
                    "text": "Building a new deck around Pikachu VMAX! Anyone have tips for energy management with electric decks?",
                    "author": "TCGBuilder",
                    "author_name": "TCG Builder", 
                    "created_at": (datetime.now() - timedelta(hours=1)).isoformat(),
                    "url": "https://twitter.com/TCGBuilder/status/123456790",
                    "conversation_id": "tweet_2"
                },
                {
                    "id": "tweet_3",
                    "text": "Attended my first Pokemon TCG tournament today! Lost in the second round but learned so much. The community is amazing!",
                    "author": "NewTrainer99",
                    "author_name": "New Trainer",
                    "created_at": (datetime.now() - timedelta(minutes=30)).isoformat(),
                    "url": "https://twitter.com/NewTrainer99/status/123456791",
                    "conversation_id": "tweet_3"
                },
                # Add more mock tweets to test with larger numbers
                {
                    "id": "tweet_4",
                    "text": "Finally completed my Eeveelution collection! Took me months to find that perfect condition Espeon card. The hunt was worth it!",
                    "author": "EeveeCollector",
                    "author_name": "Eevee Collector",
                    "created_at": (datetime.now() - timedelta(minutes=45)).isoformat(),
                    "url": "https://twitter.com/EeveeCollector/status/123456792",
                    "conversation_id": "tweet_4"
                },
                {
                    "id": "tweet_5",
                    "text": "New Pokemon set releases always get me excited! Pre-ordered 3 booster boxes of the upcoming expansion. Fingers crossed for chase cards!",
                    "author": "BoosterBoxBen",
                    "author_name": "Booster Box Ben",
                    "created_at": (datetime.now() - timedelta(hours=3)).isoformat(),
                    "url": "https://twitter.com/BoosterBoxBen/status/123456793",
                    "conversation_id": "tweet_5"
                },
                {
                    "id": "tweet_6",
                    "text": "Teaching my 8-year-old how to play Pokemon TCG. Love seeing the next generation get into the game! Any tips for beginner-friendly decks?",
                    "author": "PokeDadTrainer",
                    "author_name": "Poke Dad Trainer",
                    "created_at": (datetime.now() - timedelta(hours=4)).isoformat(),
                    "url": "https://twitter.com/PokeDadTrainer/status/123456794",
                    "conversation_id": "tweet_6"
                },
                {
                    "id": "tweet_7",
                    "text": "Market prices on vintage Pokemon cards are insane right now. My 1998 Charizard is worth more than my car! 🚗➡️🐉",
                    "author": "VintageCardKing",
                    "author_name": "Vintage Card King",
                    "created_at": (datetime.now() - timedelta(hours=5)).isoformat(),
                    "url": "https://twitter.com/VintageCardKing/status/123456795",
                    "conversation_id": "tweet_7"
                },
                {
                    "id": "tweet_8",
                    "text": "Local game store is hosting a Pokemon TCG tournament this weekend. Prize support looks amazing! Time to test my new deck build.",
                    "author": "CompetitivePlayer",
                    "author_name": "Competitive Player",
                    "created_at": (datetime.now() - timedelta(hours=6)).isoformat(),
                    "url": "https://twitter.com/CompetitivePlayer/status/123456796",
                    "conversation_id": "tweet_8"
                },
                {
                    "id": "tweet_9",
                    "text": "Just discovered Pokemon TCG Live and I'm hooked! The digital version is perfect for testing deck ideas before buying physical cards.",
                    "author": "DigitalTrainer",
                    "author_name": "Digital Trainer",
                    "created_at": (datetime.now() - timedelta(hours=7)).isoformat(),
                    "url": "https://twitter.com/DigitalTrainer/status/123456797",
                    "conversation_id": "tweet_9"
                },
                {
                    "id": "tweet_10",
                    "text": "Pulled my first alternate art card today! The artwork on these special cards is absolutely stunning. Pokemon artists are incredible.",
                    "author": "ArtCollector2024",
                    "author_name": "Art Collector",
                    "created_at": (datetime.now() - timedelta(hours=8)).isoformat(),
                    "url": "https://twitter.com/ArtCollector2024/status/123456798",
                    "conversation_id": "tweet_10"
                }
            ]
            
            return {
                "success": True,
                "tweets": mock_tweets,
                "count": len(mock_tweets),
                "source": "Mock Data (Google Sheets reader not available)",
                "timestamp": datetime.now().isoformat()
            }
        
        # Try to fetch real tweets from Google Sheets
        logger.info("📊 Fetching tweets from Google Sheets...")
        tweets = get_tweets_from_sheet(GOOGLE_SHEETS_URL, max_tweets=50)
        
        if not tweets:
            logger.warning("📊 No tweets found in Google Sheets, falling back to mock data")
            # Fall back to a few mock tweets if the sheet is empty
            mock_tweets = [
                {
                    "id": "mock_tweet_1",
                    "text": "Just opened a Pokemon TCG booster pack and got some amazing cards!",
                    "author": "MockUser1",
                    "author_name": "Mock User 1",
                    "created_at": datetime.now().isoformat(),
                    "url": "https://twitter.com/MockUser1/status/1234567890",
                    "conversation_id": "mock_tweet_1"
                },
                {
                    "id": "mock_tweet_2", 
                    "text": "Building a new Pokemon deck for the upcoming tournament. Excited to test it out!",
                    "author": "MockUser2",
                    "author_name": "Mock User 2",
                    "created_at": datetime.now().isoformat(),
                    "url": "https://twitter.com/MockUser2/status/1234567891",
                    "conversation_id": "mock_tweet_2"
                }
            ]
            
            return {
                "success": True,
                "tweets": mock_tweets,
                "count": len(mock_tweets),
                "source": "Mock Data (Google Sheets empty)",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"✅ Successfully fetched {len(tweets)} tweets from Google Sheets")
        
        return {
            "success": True,
            "tweets": tweets,
            "count": len(tweets),
            "source": "Google Sheets",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching tweets from Google Sheets: {e}")
        
        # Return error response
        return {
            "success": False,
            "tweets": [],
            "count": 0,
            "source": "Error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
# Add a new endpoint to test Google Sheets connection
@app.get("/api/test-google-sheets")
async def test_google_sheets_connection():
    """Test the connection to Google Sheets and return status"""
    try:
        if not GOOGLE_SHEETS_AVAILABLE:
            return {
                "success": False,
                "message": "Google Sheets reader is not available. Check if google_sheets_reader.py is installed.",
                "available": False,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info("🧪 Testing Google Sheets connection...")
        test_result = test_sheet_connection(GOOGLE_SHEETS_URL)
        
        return {
            "success": test_result["success"],
            "message": test_result["message"],
            "available": True,
            "tweets_found": test_result["tweets_found"],
            "sample_tweets": test_result["sample_tweets"],
            "sheets_url": GOOGLE_SHEETS_URL,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error testing Google Sheets: {e}")
        return {
            "success": False,
            "message": f"Error testing Google Sheets connection: {str(e)}",
            "available": GOOGLE_SHEETS_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/generate-replies-batch")
async def generate_replies_batch():
    """Generate replies for multiple tweets using reply generator"""
    try:
        # First fetch tweets
        tweets_response = await fetch_tweets_from_sheets()
        
        if not tweets_response.get("success", False):
            return {
                "success": False,
                "error": "Failed to fetch tweets",
                "timestamp": datetime.now().isoformat()
            }
        
        tweets = tweets_response.get("tweets", [])
        generated_replies = []
        
        for tweet in tweets:
            try:
                logger.info(f"🤖 Generating reply for tweet {tweet['id']}")
                
                reply_result = generate_reply(
                    tweet["text"], 
                    tweet["author"]
                )
                
                if isinstance(reply_result, dict):
                    reply_content = reply_result.get("content", "No reply generated")
                    success = reply_result.get("success", False)
                    error = reply_result.get("error", None)
                    llm_used = reply_result.get("llm_used", False)
                else:
                    reply_content = str(reply_result)
                    success = True
                    error = None
                    llm_used = False
                
                generated_replies.append({
                    "tweet_id": tweet["id"],
                    "original_tweet": tweet["text"],
                    "author": tweet["author"],
                    "generated_reply": reply_content,
                    "success": success,
                    "error": error,
                    "llm_used": llm_used,
                    "timestamp": datetime.now().isoformat(),
                    "reply_generator_used": reply_setup_success
                })
                
            except Exception as e:
                logger.error(f"Error generating reply for tweet {tweet['id']}: {e}")
                generated_replies.append({
                    "tweet_id": tweet["id"],
                    "original_tweet": tweet["text"],
                    "author": tweet["author"],
                    "generated_reply": "Error generating reply",
                    "success": False,
                    "error": str(e),
                    "llm_used": False,
                    "timestamp": datetime.now().isoformat(),
                    "reply_generator_used": False
                })
        
        return {
            "success": True,
            "replies": generated_replies,
            "total_processed": len(generated_replies),
            "reply_generator_active": reply_setup_success,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in batch reply generation: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Pokemon TCG Bot API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)