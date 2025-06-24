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
        # Add both current directory and src directory to path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(current_dir, 'src')
        
        # Add paths if they exist and aren't already added
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        if os.path.exists(src_dir) and src_dir not in sys.path:
            sys.path.insert(0, src_dir)
        
        logger.info(f"📁 Added to Python path: {current_dir}")
        logger.info(f"📁 Added to Python path: {src_dir}")
        
        # Try to import the actual reply generator
        from src.reply_generator import generate_reply as actual_generate_reply
        generate_reply = actual_generate_reply
        logger.info("✅ Successfully imported actual LLM reply generator")
        
        # Test it to make sure it works
        test_result = generate_reply("test tweet", "test_user")
        
        # Check if it's actually generating custom responses
        is_dummy = (
            isinstance(test_result, dict) and 
            test_result.get("content", "").startswith("Thanks for sharing! Great point about Pokemon TCG")
        )
        
        if is_dummy:
            logger.warning("⚠️ LLM imported but returning dummy responses")
            return False
        else:
            logger.info(f"✅ LLM generating custom responses: {str(test_result)[:50]}...")
            return True
        
    except ImportError as e:
        logger.error(f"❌ Import error: {e}")
        logger.error("🔍 This is likely because:")
        logger.error("   - llm_manager.py import path is wrong in reply_generator.py")
        logger.error("   - Missing dependencies (openai, etc.)")
        logger.error("   - Configuration issues")
        return False
    except Exception as e:
        logger.error(f"❌ Error testing reply generator: {e}")
        return False

# Dummy reply function for now
def generate_reply(tweet_text, tweet_author=None, conversation_history=None):
    return {"content": "Thanks for sharing! Great Pokemon TCG content.", "success": True}

# Try to setup real reply generation
reply_setup_success = setup_reply_functions()

def post_reply_tweet(content, reply_to_id):
    return {"success": False, "error": "Reply integration not available"}

# Basic models
class GenerateReplyRequest(BaseModel):
    tweet_text: str
    tweet_author: Optional[str] = None
    conversation_history: Optional[str] = None

# Essential endpoints only
@app.get("/")
async def root():
    return {"message": "Pokemon TCG Bot API is running", "status": "healthy"}

@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Backend is running"}

@app.get("/api/bot-status")
async def get_bot_status():
    return {
        "running": True,
        "uptime": "Just started",
        "lastRun": datetime.now().isoformat(),
        "stats": {"postsToday": 0, "repliesToday": 0, "successRate": 100.0},
        "jobs": [],
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
        {"id": "pokemon_tcg", "name": "Pokemon TCG", "description": "General Pokemon TCG content"}
    ]
    return {"success": True, "topics": topics, "total": len(topics)}

@app.post("/api/generate-content")
async def generate_content_endpoint(request: Dict[str, Any]):
    return {
        "success": True,
        "content": {
            "content": "Just pulled an amazing Pokemon card!",
            "engagement_score": 85.5,
            "hashtags": ["#PokemonTCG"],
            "mentions_tradeup": False
        },
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/generate-reply")
async def generate_reply_endpoint(request: GenerateReplyRequest):
    reply = generate_reply(request.tweet_text, request.tweet_author)
    return {
        "success": True,
        "reply": reply.get("content", reply),
        "original_tweet": request.tweet_text,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/fetch-tweets-from-sheets")
async def fetch_tweets_from_sheets():
    mock_tweets = [
        {
            "id": "tweet_1",
            "text": "Just pulled a Charizard card! So excited!",
            "author": "PokemonFan123",
            "author_name": "Pokemon Fan",
            "created_at": datetime.now().isoformat(),
            "url": "https://twitter.com/PokemonFan123/status/123456789",
            "conversation_id": "tweet_1"
        },
        {
            "id": "tweet_2",
            "text": "Building a new deck around Pikachu VMAX!",
            "author": "TCGBuilder",
            "author_name": "TCG Builder", 
            "created_at": datetime.now().isoformat(),
            "url": "https://twitter.com/TCGBuilder/status/123456790",
            "conversation_id": "tweet_2"
        }
    ]
    
    return {
        "success": True,
        "tweets": mock_tweets,
        "count": len(mock_tweets),
        "source": "Mock Data",
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/bot-job/create-posting-job")
async def create_posting_job(request: Dict[str, Any]):
    job = {
        "id": f"posting_job_{int(datetime.now().timestamp())}",
        "type": "posting",
        "name": request.get("name", "Test Job"),
        "settings": request.get("settings", {}),
        "status": "created",
        "created_at": datetime.now().isoformat(),
        "stats": {"postsToday": 0, "repliesToday": 0, "successRate": 100.0}
    }
    return {"success": True, "job": job, "message": "Job created"}

@app.get("/api/test-reply-generation")
async def test_reply_generation():
    """Test if reply generation is working"""
    try:
        test_tweet = "Just pulled a Charizard card from my Pokemon TCG pack! So excited!"
        test_result = generate_reply(test_tweet, "TestUser")
        
        is_dummy = (
            isinstance(test_result, dict) and 
            test_result.get("content", "").startswith("Thanks for sharing! Great Pokemon TCG content")
        )
        
        # Check what files exist for debugging
        current_dir = os.path.dirname(os.path.abspath(__file__))
        src_dir = os.path.join(current_dir, 'src')
        
        file_check = {
            "current_dir": current_dir,
            "src_dir_exists": os.path.exists(src_dir),
            "reply_generator_exists": os.path.exists(os.path.join(current_dir, 'src', 'reply_generator.py')),
            "direct_reply_generator_exists": os.path.exists(os.path.join(current_dir, 'reply_generator.py')),
            "sys_path_includes_current": current_dir in sys.path,
            "sys_path_includes_src": src_dir in sys.path if os.path.exists(src_dir) else False
        }
        
        return {
            "success": True,
            "using_real_llm": not is_dummy,
            "test_input": test_tweet,
            "test_output": test_result,
            "setup_success": reply_setup_success,
            "file_check": file_check,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)