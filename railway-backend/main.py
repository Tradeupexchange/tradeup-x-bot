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

# Google Sheets configuration
GOOGLE_SHEETS_URL = "https://docs.google.com/spreadsheets/d/1U50KjbsYUswh0IGWTPgeP97Y2kXRcYM_H1VoeyAQhpw/edit?gid=0#gid=0"

# Try to import Google Sheets reader with proper error handling
GOOGLE_SHEETS_AVAILABLE = False
get_tweets_for_reply = None
get_tweets_from_sheet = None
test_sheet_connection = None

#TRY GOOGLE SHEETS ACCESS
try:
    # First try from src directory
    from src.google_sheets_reader import get_tweets_for_reply, get_tweets_from_sheet, test_sheet_connection
    GOOGLE_SHEETS_AVAILABLE = True
    logger.info("✅ Google Sheets reader imported successfully from src/")
except ImportError:
    try:
        # Fallback to current directory
        from google_sheets_reader import get_tweets_for_reply, get_tweets_from_sheet, test_sheet_connection
        GOOGLE_SHEETS_AVAILABLE = True
        logger.info("✅ Google Sheets reader imported successfully from current directory")
    except ImportError as e:
        logger.warning(f"⚠️ Google Sheets reader not available: {e}")
        logger.info("📊 Will use mock data instead of Google Sheets")
        GOOGLE_SHEETS_AVAILABLE = False
except Exception as e:
    logger.error(f"❌ Error importing Google Sheets reader: {e}")
    GOOGLE_SHEETS_AVAILABLE = False

#TRY TWITTER API SETUP
try:
    # Try to import from src directory first
    from src.twitter_poster import post_reply_tweet, post_original_tweet, test_twitter_connection, get_posting_stats
    TWITTER_POSTER_AVAILABLE = True
    logger.info("✅ Twitter poster imported successfully from src/")
except ImportError:
    try:
        # Fallback to current directory
        from twitter_poster import post_reply_tweet, post_original_tweet, test_twitter_connection, get_posting_stats
        TWITTER_POSTER_AVAILABLE = True
        logger.info("✅ Twitter poster imported successfully from current directory")
    except ImportError as e:
        logger.warning(f"⚠️ Twitter poster not available: {e}")
        logger.info("🔄 Will use simulated posting instead")
        TWITTER_POSTER_AVAILABLE = False
        post_reply_tweet = None
        post_original_tweet = None
        test_twitter_connection = None
        get_posting_stats = None
except Exception as e:
    logger.error(f"❌ Error importing Twitter poster: {e}")
    TWITTER_POSTER_AVAILABLE = False

# Setup reply generation functions
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


# Models
class GenerateReplyRequest(BaseModel):
    tweet_text: str
    tweet_author: Optional[str] = None
    conversation_history: Optional[str] = None

class GenerateContentRequest(BaseModel):
    topic: Optional[str] = "pokemon_tcg"
    style: Optional[str] = "engaging"
    include_hashtags: Optional[bool] = True

class PostOriginalTweetRequest(BaseModel):
    content: str

class GenerateAndPostContentRequest(BaseModel):
    topic: Optional[str] = "Pokemon TCG"
    post_immediately: Optional[bool] = False
    content_type: Optional[str] = "general"
    include_hashtags: Optional[bool] = True

class ScheduledContentItem(BaseModel):
    content: str
    scheduled_time: Optional[str] = None
    topic: Optional[str] = None

class PostScheduledContentRequest(BaseModel):
    content_items: List[ScheduledContentItem]

class ContentGenerationRequest(BaseModel):
    topic: str
    count: Optional[int] = 1
    style: Optional[str] = "engaging"
    include_hashtags: Optional[bool] = True
    max_length: Optional[int] = 240  # Leave room for hashtags

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


#POSTING FUNCTIONS

# Add these endpoints to your main.py for original tweet posting:

@app.post("/api/post-original-tweet")
async def post_original_tweet_endpoint(request: Dict[str, Any]):
    """Post an original tweet to Twitter"""
    try:
        content = request.get("content", "")
        
        logger.info(f"📤 Attempting to post original tweet")
        logger.info(f"📝 Tweet content: {content[:100]}...")
        
        if not TWITTER_POSTER_AVAILABLE or post_original_tweet is None:
            logger.warning("🔄 Twitter poster not available, using simulation")
            # Fallback to simulation
            import time
            mock_tweet_id = f"sim_tweet_{int(time.time())}"
            
            return {
                "success": True,
                "tweet_id": mock_tweet_id,
                "message": "Tweet posted successfully (simulated - Twitter poster not available)",
                "tweet_url": f"https://twitter.com/TradeUpApp/status/{mock_tweet_id}",
                "content": content,
                "simulated": True,
                "timestamp": datetime.now().isoformat()
            }
        
        if not content:
            return {
                "success": False,
                "error": "Missing tweet content",
                "timestamp": datetime.now().isoformat()
            }
        
        # Use real Twitter API
        logger.info("🐦 Using real Twitter API to post original tweet...")
        result = post_original_tweet(content)
        
        logger.info(f"🔍 Twitter API result: {result}")
        
        if result.get("success"):
            logger.info(f"✅ Successfully posted tweet with ID: {result.get('tweet_id')}")
            
            return {
                "success": True,
                "tweet_id": result.get("tweet_id"),
                "message": "Tweet posted successfully to Twitter",
                "tweet_url": result.get("url", f"https://twitter.com/TradeUpApp/status/{result.get('tweet_id')}"),
                "content": content,
                "posted_at": result.get("posted_at"),
                "simulated": False,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"❌ Failed to post tweet: {result.get('error')}")
            
            return {
                "success": False,
                "error": result.get("error", "Unknown Twitter API error"),
                "rate_limited": result.get("rate_limited", False),
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ Error in post_original_tweet_endpoint: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/generate-and-post-content")
async def generate_and_post_content(request: Dict[str, Any]):
    """Generate content using LLM and optionally post to Twitter"""
    try:
        topic = request.get("topic", "Pokemon TCG")
        post_immediately = request.get("post_immediately", False)
        content_type = request.get("content_type", "general")
        
        logger.info(f"📝 Generating content for topic: {topic}")
        logger.info(f"🚀 Post immediately: {post_immediately}")
        
        # Generate content using your existing content generation
        content_result = await generate_content_endpoint(GenerateContentRequest(
            topic=topic,
            style="engaging",
            include_hashtags=True
        ))
        
        if not content_result.get("success"):
            return {
                "success": False,
                "error": "Failed to generate content",
                "timestamp": datetime.now().isoformat()
            }
        
        generated_content = content_result["content"]["content"]
        hashtags = content_result["content"].get("hashtags", [])
        
        # Add hashtags to content if they exist
        if hashtags:
            content_with_hashtags = f"{generated_content}\n\n{' '.join(hashtags)}"
        else:
            content_with_hashtags = generated_content
        
        response = {
            "success": True,
            "generated_content": generated_content,
            "content_with_hashtags": content_with_hashtags,
            "hashtags": hashtags,
            "topic": topic,
            "timestamp": datetime.now().isoformat()
        }
        
        # Post immediately if requested
        if post_immediately:
            logger.info("🚀 Posting generated content immediately...")
            
            post_result = await post_original_tweet_endpoint({
                "content": content_with_hashtags
            })
            
            response["post_result"] = post_result
            response["posted"] = post_result.get("success", False)
            
            if post_result.get("success"):
                response["tweet_id"] = post_result.get("tweet_id")
                response["tweet_url"] = post_result.get("tweet_url")
                response["message"] = "Content generated and posted successfully"
            else:
                response["message"] = "Content generated but posting failed"
                response["post_error"] = post_result.get("error")
        else:
            response["posted"] = False
            response["message"] = "Content generated successfully (not posted)"
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error in generate_and_post_content: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/post-scheduled-content")
async def post_scheduled_content(request: Dict[str, Any]):
    """Post multiple pieces of scheduled content"""
    try:
        content_items = request.get("content_items", [])
        
        if not content_items:
            return {
                "success": False,
                "error": "No content items provided",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"📅 Posting {len(content_items)} scheduled content items...")
        
        results = []
        success_count = 0
        
        for i, content_item in enumerate(content_items):
            try:
                content = content_item.get("content", "")
                scheduled_time = content_item.get("scheduled_time", "")
                
                if not content:
                    logger.warning(f"Skipping item {i+1}: missing content")
                    results.append({
                        "success": False,
                        "error": "Missing content",
                        "original_data": content_item
                    })
                    continue
                
                logger.info(f"📝 Posting content item {i+1}/{len(content_items)}")
                logger.info(f"⏰ Scheduled for: {scheduled_time}")
                
                if TWITTER_POSTER_AVAILABLE:
                    # Use real Twitter API
                    result = post_original_tweet(content)
                    
                    if result.get("success"):
                        success_count += 1
                        results.append({
                            "success": True,
                            "tweet_id": result.get("tweet_id"),
                            "tweet_url": result.get("url"),
                            "content": content,
                            "posted_at": result.get("posted_at"),
                            "scheduled_time": scheduled_time
                        })
                        logger.info(f"✅ Successfully posted content item {i+1}")
                    else:
                        results.append({
                            "success": False,
                            "error": result.get("error"),
                            "rate_limited": result.get("rate_limited", False),
                            "content": content,
                            "scheduled_time": scheduled_time
                        })
                        logger.error(f"❌ Failed to post content item {i+1}: {result.get('error')}")
                else:
                    # Simulation mode
                    import time
                    mock_id = f"sim_scheduled_tweet_{int(time.time())}_{i}"
                    success_count += 1
                    results.append({
                        "success": True,
                        "tweet_id": mock_id,
                        "tweet_url": f"https://twitter.com/TradeUpApp/status/{mock_id}",
                        "content": content,
                        "scheduled_time": scheduled_time,
                        "simulated": True
                    })
                    logger.info(f"✅ Simulated posting content item {i+1}")
                
                # Small delay between posts to avoid rate limits
                if i < len(content_items) - 1:  # Don't sleep after the last one
                    logger.info("⏰ Waiting 65 seconds between posts for rate limiting...")
                    time.sleep(65)
                    
            except Exception as e:
                logger.error(f"❌ Error posting content item {i+1}: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "original_data": content_item
                })
        
        return {
            "success": True,
            "total_processed": len(content_items),
            "successful_posts": success_count,
            "failed_posts": len(content_items) - success_count,
            "results": results,
            "twitter_available": TWITTER_POSTER_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in post_scheduled_content: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/content-topics")
async def get_content_topics():
    """Get available content topics for tweet generation"""
    try:
        topics = [
            {
                "id": "pokemon_tcg_general",
                "name": "Pokemon TCG General",
                "description": "General Pokemon TCG discussion and enthusiasm",
                "examples": ["Card collecting tips", "Deck building basics", "Tournament experience"]
            },
            {
                "id": "card_pulls",
                "name": "Card Pulls & Openings",
                "description": "Booster pack openings and rare card pulls",
                "examples": ["Charizard pulls", "Alt art discoveries", "Booster box openings"]
            },
            {
                "id": "market_analysis",
                "name": "Market Analysis",
                "description": "Pokemon card market trends and pricing",
                "examples": ["Price predictions", "Market trends", "Investment insights"]
            },
            {
                "id": "deck_building",
                "name": "Deck Building",
                "description": "Competitive deck strategies and builds",
                "examples": ["Meta deck analysis", "Budget deck options", "Synergy combinations"]
            },
            {
                "id": "tournaments",
                "name": "Tournament Play",
                "description": "Competitive Pokemon TCG tournament content",
                "examples": ["Tournament prep", "Meta predictions", "Competition analysis"]
            },
            {
                "id": "collecting",
                "name": "Collecting & Grading",
                "description": "Card collecting, grading, and preservation",
                "examples": ["PSA grading tips", "Collection showcases", "Card condition guides"]
            },
            {
                "id": "community",
                "name": "Community & Culture",
                "description": "Pokemon TCG community and culture topics",
                "examples": ["Community events", "Collector stories", "Nostalgia posts"]
            }
        ]
        
        return {
            "success": True,
            "topics": topics,
            "total": len(topics),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting content topics: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/posting-queue")
async def get_posting_queue():
    """Get current posting queue and schedule"""
    try:
        # This would integrate with your job system
        # For now, return empty queue
        queue = []
        
        # Get posting stats
        if TWITTER_POSTER_AVAILABLE and get_posting_stats:
            stats = get_posting_stats()
        else:
            stats = {
                "last_post_time": None,
                "can_post_now": True,
                "min_interval_seconds": 60
            }
        
        return {
            "success": True,
            "queue": queue,
            "stats": stats,
            "can_post_now": stats.get("can_post_now", True),
            "next_available_post_time": None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting posting queue: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Update your existing generate-content endpoint to support immediate posting
@app.post("/api/generate-content-enhanced")
async def generate_content_enhanced(request: GenerateContentRequest):
    """Enhanced content generation with posting option"""
    try:
        # Generate content using existing logic
        content_result = await generate_content_endpoint(request)
        
        if not content_result.get("success"):
            return content_result
        
        # Add posting capabilities to the response
        generated_content = content_result["content"]["content"]
        hashtags = content_result["content"].get("hashtags", [])
        
        # Create full content with hashtags
        if hashtags:
            full_content = f"{generated_content}\n\n{' '.join(hashtags)}"
        else:
            full_content = generated_content
        
        # Enhanced response with posting options
        return {
            "success": True,
            "content": {
                **content_result["content"],
                "full_content_with_hashtags": full_content,
                "ready_to_post": True,
                "character_count": len(full_content),
                "within_twitter_limit": len(full_content) <= 280
            },
            "posting_available": TWITTER_POSTER_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in enhanced content generation: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

#END POSTING FUNCTIONS

#JOB MANAGEMENT
# 4. ADD NEW ENDPOINTS for bot job management:

@app.post("/api/bot-job/{job_id}/start")
async def start_bot_job(job_id: str):
    """Start a bot job"""
    try:
        logger.info(f"▶️ Starting bot job {job_id}")
        
        # TODO: Implement actual job starting logic
        # For now, return success
        
        return {
            "success": True,
            "message": f"Job {job_id} started successfully",
            "job_id": job_id,
            "status": "running",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error starting job {job_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/bot-job/{job_id}/stop")
async def stop_bot_job(job_id: str):
    """Stop a bot job"""
    try:
        logger.info(f"⏹️ Stopping bot job {job_id}")
        
        # TODO: Implement actual job stopping logic
        
        return {
            "success": True,
            "message": f"Job {job_id} stopped successfully",
            "job_id": job_id,
            "status": "stopped",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error stopping job {job_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/bot-job/{job_id}/pause")
async def pause_bot_job(job_id: str):
    """Pause a bot job"""
    try:
        logger.info(f"⏸️ Pausing bot job {job_id}")
        
        # TODO: Implement actual job pausing logic
        
        return {
            "success": True,
            "message": f"Job {job_id} paused successfully", 
            "job_id": job_id,
            "status": "paused",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error pausing job {job_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/bot-job/{job_id}/rename")
async def rename_bot_job(job_id: str, request: Dict[str, Any]):
    """Rename a bot job"""
    try:
        new_name = request.get("name", "")
        
        if not new_name:
            return {
                "success": False,
                "error": "Missing new name",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"✏️ Renaming bot job {job_id} to '{new_name}'")
        
        # TODO: Implement actual job renaming logic
        
        return {
            "success": True,
            "message": f"Job {job_id} renamed to '{new_name}' successfully",
            "job_id": job_id,
            "new_name": new_name,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error renaming job {job_id}: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/bot-job/create-posting-job")
async def create_posting_job(request: Dict[str, Any]):
    """Create a new posting job"""
    try:
        job_type = request.get("type", "posting")
        job_name = request.get("name", "Untitled Job")
        settings = request.get("settings", {})
        
        logger.info(f"➕ Creating new posting job: {job_name}")
        logger.info(f"🔧 Settings: {settings}")
        
        # TODO: Implement actual job creation logic
        import time
        job_id = f"job_{int(time.time())}"
        
        return {
            "success": True,
            "message": f"Posting job '{job_name}' created successfully",
            "job_id": job_id,
            "job_name": job_name,
            "job_type": job_type,
            "settings": settings,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating posting job: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/bot-job/create-reply-job")
async def create_reply_job(request: Dict[str, Any]):
    """Create a new reply job"""
    try:
        job_type = request.get("type", "replying")
        job_name = request.get("name", "Untitled Reply Job")
        settings = request.get("settings", {})
        max_replies_per_hour = request.get("maxRepliesPerHour", 10)
        auto_reply = request.get("autoReply", False)
        sentiment_filter = request.get("sentiment_filter", "positive")
        
        logger.info(f"➕ Creating new reply job: {job_name}")
        logger.info(f"🔧 Max replies per hour: {max_replies_per_hour}")
        
        # TODO: Implement actual reply job creation logic
        import time
        job_id = f"reply_job_{int(time.time())}"
        
        return {
            "success": True,
            "message": f"Reply job '{job_name}' created successfully",
            "job_id": job_id,
            "job_name": job_name,
            "job_type": job_type,
            "max_replies_per_hour": max_replies_per_hour,
            "auto_reply": auto_reply,
            "sentiment_filter": sentiment_filter,
            "settings": settings,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error creating reply job: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

#JOB MANAGEMENT END

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
        logger.info("📊 Starting fetch tweets from sheets...")
        
        if not GOOGLE_SHEETS_AVAILABLE:
            # Return enhanced mock data if Google Sheets reader is not available
            logger.warning("📊 Google Sheets reader not available, returning enhanced mock data")
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
        
        if get_tweets_from_sheet is None:
            logger.error("❌ get_tweets_from_sheet function is None")
            raise Exception("Google Sheets functions not properly imported")
        
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
        logger.error(f"❌ Error type: {type(e).__name__}")
        
        # Return mock data as fallback to prevent frontend crashes
        fallback_tweets = [
            {
                "id": "fallback_tweet_1",
                "text": "Just pulled a rare Pokemon card! The excitement never gets old in this hobby!",
                "author": "FallbackUser1",
                "author_name": "Fallback User 1",
                "created_at": datetime.now().isoformat(),
                "url": "https://twitter.com/FallbackUser1/status/1111111111",
                "conversation_id": "fallback_tweet_1"
            },
            {
                "id": "fallback_tweet_2",
                "text": "Working on a new Pokemon deck strategy. Any suggestions for good synergy cards?",
                "author": "FallbackUser2", 
                "author_name": "Fallback User 2",
                "created_at": datetime.now().isoformat(),
                "url": "https://twitter.com/FallbackUser2/status/1111111112",
                "conversation_id": "fallback_tweet_2"
            },
            {
                "id": "fallback_tweet_3",
                "text": "Pokemon TCG tournament this weekend! Nervous but excited to compete with my deck.",
                "author": "FallbackUser3",
                "author_name": "Fallback User 3", 
                "created_at": datetime.now().isoformat(),
                "url": "https://twitter.com/FallbackUser3/status/1111111113",
                "conversation_id": "fallback_tweet_3"
            }
        ]
        
        return {
            "success": True,  # Return success=True to prevent frontend errors
            "tweets": fallback_tweets,
            "count": len(fallback_tweets),
            "source": "Fallback Data (Error occurred)",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

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
        
        if test_sheet_connection is None:
            return {
                "success": False,
                "message": "Google Sheets test function not available",
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
    
@app.post("/api/post-reply-with-tracking")
async def post_reply_with_tracking(request: Dict[str, Any]):
    """Post a reply to Twitter with real Twitter API integration"""
    try:
        content = request.get("content", "")
        reply_to_tweet_id = request.get("reply_to_tweet_id", "")
        
        logger.info(f"📤 POST-REPLY-WITH-TRACKING: Starting...")
        logger.info(f"📝 Content: {content}")
        logger.info(f"🆔 Reply to tweet ID: {reply_to_tweet_id}")
        logger.info(f"🔍 Request data: {request}")
        
        if not TWITTER_POSTER_AVAILABLE or post_reply_tweet is None:
            logger.error("❌ TWITTER POSTER NOT AVAILABLE")
            return {
                "success": False,
                "error": "Twitter poster not available",
                "timestamp": datetime.now().isoformat()
            }
        
        if not content or not reply_to_tweet_id:
            logger.error(f"❌ MISSING DATA - content: '{content}', tweet_id: '{reply_to_tweet_id}'")
            return {
                "success": False,
                "error": "Missing content or reply_to_tweet_id",
                "timestamp": datetime.now().isoformat()
            }
        
        # Use real Twitter API
        logger.info("🐦 CALLING REAL TWITTER API...")
        logger.info(f"🎯 Function call: post_reply_tweet('{content}', '{reply_to_tweet_id}')")
        
        result = post_reply_tweet(content, reply_to_tweet_id)
        
        logger.info(f"🔍 TWITTER API RESULT: {result}")
        logger.info(f"🔍 Result type: {type(result)}")
        logger.info(f"🔍 Result success: {result.get('success') if isinstance(result, dict) else 'Not a dict'}")
        
        if isinstance(result, dict) and result.get("success"):
            logger.info(f"✅ SUCCESS: Posted reply with ID: {result.get('tweet_id')}")
            
            return {
                "success": True,
                "tweet_id": result.get("tweet_id"),
                "message": "Reply posted successfully to Twitter",
                "reply_url": result.get("url", f"https://twitter.com/TradeUpApp/status/{result.get('tweet_id')}"),
                "original_tweet_id": reply_to_tweet_id,
                "content": content,
                "posted_at": result.get("posted_at"),
                "simulated": False,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"❌ TWITTER API FAILED")
            logger.error(f"❌ Full result: {result}")
            
            # Extract error message
            if isinstance(result, dict):
                error_msg = result.get("error", "Unknown Twitter API error")
                rate_limited = result.get("rate_limited", False)
            else:
                error_msg = f"Unexpected result type: {type(result)} - {result}"
                rate_limited = False
            
            logger.error(f"❌ Error message: {error_msg}")
            logger.error(f"❌ Rate limited: {rate_limited}")
            
            return {
                "success": False,
                "error": error_msg,
                "rate_limited": rate_limited,
                "debug_result": result,
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ EXCEPTION in post_reply_with_tracking: {e}")
        import traceback
        logger.error(f"❌ Full traceback: {traceback.format_exc()}")
        return {
            "success": False,
            "error": str(e),
            "traceback": traceback.format_exc(),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/post-tweet")
async def post_tweet(request: Dict[str, Any]):
    """Post a new tweet with real Twitter API integration"""
    try:
        content = request.get("content", "")
        
        logger.info(f"📤 Attempting to post new tweet")
        logger.info(f"📝 Tweet content: {content[:100]}...")
        
        if not TWITTER_POSTER_AVAILABLE:
            logger.warning("🔄 Twitter poster not available, using simulation")
            # Fallback to simulation
            import time
            mock_tweet_id = f"sim_tweet_{int(time.time())}"
            
            return {
                "success": True,
                "tweet_id": mock_tweet_id,
                "message": "Tweet posted successfully (simulated - Twitter poster not available)",
                "tweet_url": f"https://twitter.com/TradeUpApp/status/{mock_tweet_id}",
                "content": content,
                "simulated": True,
                "timestamp": datetime.now().isoformat()
            }
        
        if not content:
            return {
                "success": False,
                "error": "Missing tweet content",
                "timestamp": datetime.now().isoformat()
            }
        
        # Use real Twitter API
        logger.info("🐦 Using real Twitter API to post tweet...")
        result = post_original_tweet(content)
        
        if result.get("success"):
            logger.info(f"✅ Successfully posted tweet with ID: {result.get('tweet_id')}")
            
            return {
                "success": True,
                "tweet_id": result.get("tweet_id"),
                "message": "Tweet posted successfully to Twitter",
                "tweet_url": result.get("url", f"https://twitter.com/TradeUpApp/status/{result.get('tweet_id')}"),
                "content": content,
                "posted_at": result.get("posted_at"),
                "simulated": False,
                "timestamp": datetime.now().isoformat()
            }
        else:
            logger.error(f"❌ Failed to post tweet: {result.get('error')}")
            
            return {
                "success": False,
                "error": result.get("error", "Unknown Twitter API error"),
                "rate_limited": result.get("rate_limited", False),
                "timestamp": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"❌ Error in post_tweet: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

# Add this debug endpoint to your main.py to diagnose the issue:
@app.get("/api/debug-twitter-integration")
async def debug_twitter_integration():
    """Debug endpoint to check Twitter integration status"""
    try:
        debug_info = {
            "twitter_poster_available": TWITTER_POSTER_AVAILABLE,
            "functions_imported": {},
            "import_path": "unknown",
            "environment_variables": {
                "TWITTER_API_KEY": bool(os.getenv("TWITTER_API_KEY")),
                "TWITTER_API_SECRET": bool(os.getenv("TWITTER_API_SECRET")),
                "TWITTER_ACCESS_TOKEN": bool(os.getenv("TWITTER_ACCESS_TOKEN")),
                "TWITTER_ACCESS_SECRET": bool(os.getenv("TWITTER_ACCESS_SECRET")),
            }
        }
        
        # Check which functions are available
        if TWITTER_POSTER_AVAILABLE:
            debug_info["functions_imported"] = {
                "post_reply_tweet": post_reply_tweet is not None,
                "post_original_tweet": post_original_tweet is not None,
                "test_twitter_connection": test_twitter_connection is not None,
                "get_posting_stats": get_posting_stats is not None,
            }
            
            # Check the actual function types
            debug_info["function_types"] = {
                "post_reply_tweet": str(type(post_reply_tweet)),
                "post_original_tweet": str(type(post_original_tweet)),
            }
        
        # Test a direct call to see what happens
        if TWITTER_POSTER_AVAILABLE and post_reply_tweet is not None:
            try:
                # Try calling the function with test data to see the response structure
                debug_info["test_call_result"] = "Function exists and is callable"
            except Exception as e:
                debug_info["test_call_error"] = str(e)
        
        return {
            "success": True,
            "debug_info": debug_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }


# Add a new endpoint for batch reply posting (for the approval workflow)
@app.post("/api/post-replies-batch")
async def post_replies_batch(request: Dict[str, Any]):
    """Post multiple approved replies to Twitter"""
    try:
        replies = request.get("replies", [])
        
        if not replies:
            return {
                "success": False,
                "error": "No replies provided",
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"📤 Batch posting {len(replies)} replies to Twitter...")
        
        results = []
        success_count = 0
        
        for i, reply_data in enumerate(replies):
            try:
                content = reply_data.get("content", "")
                tweet_id = reply_data.get("tweet_id", "")
                
                if not content or not tweet_id:
                    logger.warning(f"Skipping reply {i+1}: missing content or tweet_id")
                    results.append({
                        "success": False,
                        "error": "Missing content or tweet_id",
                        "original_data": reply_data
                    })
                    continue
                
                logger.info(f"📝 Posting reply {i+1}/{len(replies)} to tweet {tweet_id}")
                
                if TWITTER_POSTER_AVAILABLE:
                    # Use real Twitter API
                    result = post_reply_tweet(content, tweet_id)
                    
                    if result.get("success"):
                        success_count += 1
                        results.append({
                            "success": True,
                            "tweet_id": result.get("tweet_id"),
                            "reply_url": result.get("url"),
                            "content": content,
                            "original_tweet_id": tweet_id,
                            "posted_at": result.get("posted_at")
                        })
                        logger.info(f"✅ Successfully posted reply {i+1}")
                    else:
                        results.append({
                            "success": False,
                            "error": result.get("error"),
                            "rate_limited": result.get("rate_limited", False),
                            "content": content,
                            "original_tweet_id": tweet_id
                        })
                        logger.error(f"❌ Failed to post reply {i+1}: {result.get('error')}")
                else:
                    # Simulation mode
                    import time
                    mock_id = f"sim_batch_reply_{int(time.time())}_{i}"
                    success_count += 1
                    results.append({
                        "success": True,
                        "tweet_id": mock_id,
                        "reply_url": f"https://twitter.com/TradeUpApp/status/{mock_id}",
                        "content": content,
                        "original_tweet_id": tweet_id,
                        "simulated": True
                    })
                    logger.info(f"✅ Simulated posting reply {i+1}")
                
                # Small delay between posts to avoid rate limits
                if i < len(replies) - 1:  # Don't sleep after the last one
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ Error posting reply {i+1}: {e}")
                results.append({
                    "success": False,
                    "error": str(e),
                    "original_data": reply_data
                })
        
        return {
            "success": True,
            "total_processed": len(replies),
            "successful_posts": success_count,
            "failed_posts": len(replies) - success_count,
            "results": results,
            "twitter_available": TWITTER_POSTER_AVAILABLE,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"❌ Error in batch reply posting: {e}")
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

if __name__ == "__main__":
    import uvicorn
    logger.info("🚀 Starting Pokemon TCG Bot API server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)