from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import logging
import sys
import os

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
        # Add current directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        logger.info(f"📁 Added to Python path: {current_dir}")
        
        # Try to import the actual reply generator (updated import path)
        from reply_generator import generate_reply as actual_generate_reply
        generate_reply = actual_generate_reply
        logger.info("✅ Successfully imported actual LLM reply generator")
        
        # Test it to make sure it works
        test_result = generate_reply("test tweet about Pokemon cards", "test_user")
        logger.info(f"🧪 Test result: {test_result}")
        
        # Check if it's actually generating custom responses
        if isinstance(test_result, dict) and test_result.get("success", False):
            logger.info("✅ LLM generating custom responses successfully")
            return True
        else:
            logger.warning("⚠️ LLM test failed or returned unexpected format")
            return False
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("🔍 Possible issues:")
        logger.error("   - reply_generator.py not found in current directory")
        logger.error("   - llm_manager.py import path is wrong in reply_generator.py")
        logger.error("   - Missing dependencies (openai, etc.)")
        logger.error("   - Configuration issues (API keys, etc.)")
        
        # Fallback to dummy function
        def dummy_reply(tweet_text, tweet_author=None, conversation_history=None):
            return {
                "content": f"Thanks for sharing! Great point about Pokemon TCG. The part about '{tweet_text[:50]}...' really resonates with the community!",
                "success": False,
                "error": "Using dummy response due to import issues"
            }
        generate_reply = dummy_reply
        return False
        
    except Exception as e:
        logger.error(f"❌ Error testing reply generator: {e}")
        
        # Fallback to dummy function
        def dummy_reply(tweet_text, tweet_author=None, conversation_history=None):
            return {
                "content": f"Thanks for sharing! Great point about Pokemon TCG. The part about '{tweet_text[:50]}...' really resonates with the community!",
                "success": False,
                "error": f"Error during setup: {str(e)}"
            }
        generate_reply = dummy_reply
        return False

# Initial dummy reply function
def generate_reply(tweet_text, tweet_author=None, conversation_history=None):
    return {
        "content": "Thanks for sharing! Great Pokemon TCG content.", 
        "success": False,
        "error": "Reply generator not initialized"
    }

# Try to setup real reply generation
logger.info("🚀 Setting up reply generation...")
reply_setup_success = setup_reply_functions()

if reply_setup_success:
    logger.info("✅ LLM reply generation is ready!")
else:
    logger.warning("⚠️ Using fallback reply generation")

def post_reply_tweet(content, reply_to_id):
    return {"success": False, "error": "Reply integration not available"}

# Basic models
class GenerateReplyRequest(BaseModel):
    tweet_text: str
    tweet_author: Optional[str] = None
    conversation_history: Optional[str] = None

class GenerateContentRequest(BaseModel):
    topic: Optional[str] = "pokemon_tcg"
    style: Optional[str] = "engaging"
    include_hashtags: Optional[bool] = True

# Essential endpoints only
@app.get("/")
async def root():
    return {
        "message": "Pokemon TCG Bot API is running", 
        "status": "healthy",
        "llm_active": reply_setup_success
    }

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy", 
        "message": "Backend is running",
        "llm_status": "active" if reply_setup_success else "fallback"
    }

@app.get("/api/bot-status")
async def get_bot_status():
    return {
        "running": True,
        "uptime": "Just started",
        "lastRun": datetime.now().isoformat(),
        "stats": {"postsToday": 0, "repliesToday": 0, "successRate": 100.0},
        "jobs": [],
        "llm_active": reply_setup_success,
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
    """Generate original Pokemon TCG content using LLM"""
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
                "llm_generated": reply_setup_success
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
    """Generate a customized reply to a tweet using LLM"""
    try:
        logger.info(f"🤖 Generating reply for tweet: {request.tweet_text[:100]}...")
        
        # Generate reply using LLM
        result = generate_reply(
            request.tweet_text, 
            request.tweet_author, 
            request.conversation_history
        )
        
        logger.info(f"📝 Generated result: {result}")
        
        # Handle different response formats
        if isinstance(result, dict):
            reply_content = result.get("content", str(result))
            success = result.get("success", True)
            error = result.get("error", None)
        else:
            reply_content = str(result)
            success = True
            error = None
        
        return {
            "success": success,
            "reply": reply_content,
            "original_tweet": request.tweet_text,
            "author": request.tweet_author,
            "llm_generated": reply_setup_success,
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
    """Fetch tweets from Google Sheets - currently returns mock data"""
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
        }
    ]
    
    return {
        "success": True,
        "tweets": mock_tweets,
        "count": len(mock_tweets),
        "source": "Mock Data (Google Sheets integration pending)",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/bot-job/create-posting-job")
async def create_posting_job(request: Dict[str, Any]):
    job = {
        "id": f"posting_job_{int(datetime.now().timestamp())}",
        "type": "posting",
        "name": request.get("name", "Pokemon TCG Posting Job"),
        "settings": request.get("settings", {}),
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "stats": {"postsToday": 0, "repliesToday": 0, "successRate": 100.0},
        "llm_enabled": reply_setup_success
    }
    return {"success": True, "job": job, "message": "Job created successfully"}

@app.get("/api/test-reply-generation")
async def test_reply_generation():
    """Test if reply generation is working properly"""
    try:
        test_cases = [
            {
                "tweet": "Just pulled a Charizard card from my Pokemon TCG pack! So excited!",
                "author": "TestUser1"
            },
            {
                "tweet": "Building a new deck around Pikachu VMAX, any tips?",
                "author": "TestUser2"
            },
            {
                "tweet": "Attending my first Pokemon tournament tomorrow, wish me luck!",
                "author": "TestUser3"
            }
        ]
        
        results = []
        
        for i, test_case in enumerate(test_cases):
            logger.info(f"🧪 Testing case {i+1}: {test_case['tweet'][:50]}...")
            
            result = generate_reply(test_case["tweet"], test_case["author"])
            
            # Determine if this is a real LLM response or dummy
            is_real_llm = True
            if isinstance(result, dict):
                content = result.get("content", "")
                if (content.startswith("Thanks for sharing! Great Pokemon TCG content") or 
                    "Reply generator not initialized" in content):
                    is_real_llm = False
            
            results.append({
                "test_input": test_case["tweet"],
                "test_author": test_case["author"],
                "output": result,
                "is_real_llm": is_real_llm
            })
        
        # Check what files exist for debugging
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        file_check = {
            "current_dir": current_dir,
            "reply_generator_exists": os.path.exists(os.path.join(current_dir, 'reply_generator.py')),
            "llm_manager_exists": os.path.exists(os.path.join(current_dir, 'llm_manager.py')),
            "sys_path_includes_current": current_dir in sys.path,
        }
        
        overall_success = all(result["is_real_llm"] for result in results)
        
        return {
            "success": True,
            "overall_llm_working": overall_success,
            "setup_success": reply_setup_success,
            "test_results": results,
            "file_check": file_check,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in test: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/generate-replies-batch")
async def generate_replies_batch():
    """Generate replies for multiple tweets (useful for batch processing)"""
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
                    reply_content = reply_result.get("content", str(reply_result))
                else:
                    reply_content = str(reply_result)
                
                generated_replies.append({
                    "tweet_id": tweet["id"],
                    "original_tweet": tweet["text"],
                    "author": tweet["author"],
                    "generated_reply": reply_content,
                    "timestamp": datetime.now().isoformat(),
                    "llm_generated": reply_setup_success
                })
                
            except Exception as e:
                logger.error(f"Error generating reply for tweet {tweet['id']}: {e}")
                generated_replies.append({
                    "tweet_id": tweet["id"],
                    "original_tweet": tweet["text"],
                    "author": tweet["author"],
                    "generated_reply": "Error generating reply",
                    "error": str(e),
                    "timestamp": datetime.now().isoformat(),
                    "llm_generated": False
                })
        
        return {
            "success": True,
            "replies": generated_replies,
            "total_processed": len(generated_replies),
            "llm_active": reply_setup_success,
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