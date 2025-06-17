"""
Pokemon TCG Bot Backend - Railway Deployment
FastAPI backend for managing Pokemon TCG social media bot
"""

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Dict, List, Any, Optional
import os
import json
import uvicorn
from datetime import datetime
import asyncio
import logging
import sys

# Configure logging for Railway
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Log startup info
logger.info("Starting Pokemon TCG Bot API...")
logger.info(f"Python version: {sys.version}")
logger.info(f"PORT environment variable: {os.environ.get('PORT', 'Not set')}")

# Import your existing modules with error handling
try:
    from bot_manager import BotManager
    logger.info("Successfully imported BotManager")
except ImportError as e:
    logger.warning(f"Could not import BotManager: {e}")
    # Create a dummy BotManager for Railway deployment
    class BotManager:
        def get_status(self): return {"status": "ok"}
        def get_all_jobs(self): return []
        def create_job(self, job_type, settings): return {"id": "dummy", "type": job_type}
        def get_job(self, job_id): return {"id": job_id, "status": "stopped"}
        def start_job(self, job_id): pass
        def stop_job(self, job_id): return {"id": job_id, "status": "stopped"}
        def pause_job(self, job_id): return {"id": job_id, "status": "paused"}
        def update_job(self, job_id, job): pass
        def get_metrics(self): return {"totalPosts": 0, "avgEngagement": 0}
        def get_posts(self, limit, offset): return {"posts": [], "total": 0, "hasMore": False}
        def get_topics(self): return []
        def get_engagement_data(self, days): return []
        def get_settings(self): return {"postsPerDay": 12, "keywords": ["Pokemon", "TCG"]}
        def update_settings(self, settings): return settings

try:
    from content_generator import generate_viral_content, optimize_content_for_engagement
    logger.info("Successfully imported content generation modules")
except ImportError as e:
    logger.warning(f"Could not import content generators: {e}")
    # Create dummy functions
    def generate_viral_content(count=1):
        return [{"content": "Sample Pokemon TCG content", "engagement_score": 0.8}] * count
    def optimize_content_for_engagement(content):
        return content

try:
    from twitter_poster import post_original_tweet, get_tweet_url
    logger.info("Successfully imported Twitter modules")
except ImportError as e:
    logger.warning(f"Could not import Twitter modules: {e}")
    # Create dummy functions
    def post_original_tweet(content):
        return {"success": False, "error": "Twitter integration not available"}
    def get_tweet_url(tweet_id):
        return f"https://twitter.com/i/status/{tweet_id}"

try:
    from knowledge_manager import update_knowledge_base_from_csv, update_knowledge_base_from_web
    logger.info("Successfully imported knowledge manager")
except ImportError as e:
    logger.warning(f"Could not import knowledge manager: {e}")

app = FastAPI(
    title="Pokemon TCG Bot API", 
    version="1.0.0",
    description="FastAPI backend for managing Pokemon TCG social media bot",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Enhanced CORS configuration for Railway + Netlify
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "https://localhost:3000",
    "https://localhost:5173",
]

# Add Netlify origins from environment variables
netlify_url = os.environ.get("NETLIFY_URL")
if netlify_url:
    allowed_origins.append(netlify_url)
    logger.info(f"Added Netlify URL to CORS origins: {netlify_url}")

# Add any additional frontend URLs
frontend_url = os.environ.get("FRONTEND_URL")
if frontend_url:
    allowed_origins.append(frontend_url)
    logger.info(f"Added frontend URL to CORS origins: {frontend_url}")

# For development, allow all origins if specified
if os.environ.get("ALLOW_ALL_ORIGINS", "false").lower() == "true":
    allowed_origins = ["*"]
    logger.info("CORS configured to allow all origins (development mode)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # Set to False when using allow_origins=["*"]
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=[
        "Accept",
        "Accept-Language",
        "Content-Language",
        "Content-Type",
        "Authorization",
        "X-Requested-With",
        "Origin",
        "Access-Control-Request-Method",
        "Access-Control-Request-Headers",
    ],
    expose_headers=["*"],
)

# Global bot manager instance
bot_manager = BotManager()

# Pydantic models for request/response
class JobSettings(BaseModel):
    postsPerDay: int = 12
    postingHours: Dict[str, int] = {"start": 9, "end": 21}
    contentTypes: Dict[str, bool] = {
        "cardPulls": True,
        "deckBuilding": True,
        "marketAnalysis": True,
        "tournaments": True
    }
    keywords: List[str] = ["Pokemon", "TCG", "Charizard", "Pikachu"]
    maxRepliesPerHour: int = 10
    replyTypes: Dict[str, bool] = {
        "helpful": True,
        "engaging": True,
        "promotional": False
    }

class CreateJobRequest(BaseModel):
    type: str  # "posting" or "replying"
    settings: JobSettings

class GenerateContentRequest(BaseModel):
    topic: Optional[str] = None
    keywords: Optional[List[str]] = None
    count: int = 1

class PostToTwitterRequest(BaseModel):
    content: str

# Startup event
@app.on_event("startup")
async def startup_event():
    logger.info("Pokemon TCG Bot API is starting up...")
    logger.info(f"Environment: {os.environ.get('RAILWAY_ENVIRONMENT', 'unknown')}")
    logger.info(f"Service ID: {os.environ.get('RAILWAY_SERVICE_ID', 'unknown')}")
    logger.info(f"Deployment ID: {os.environ.get('RAILWAY_DEPLOYMENT_ID', 'unknown')}")

# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Pokemon TCG Bot API is shutting down...")

# Add a middleware to handle CORS manually for better control
@app.middleware("http")
async def cors_handler(request, call_next):
    # Log incoming requests for debugging
    logger.info(f"Incoming request: {request.method} {request.url}")
    
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = JSONResponse(content={"message": "OK"})
        origin = request.headers.get("origin")
        
        if allowed_origins == ["*"] or (origin and origin in allowed_origins):
            response.headers["Access-Control-Allow-Origin"] = origin or "*"
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
            
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response
    
    # Process the request
    try:
        response = await call_next(request)
    except Exception as e:
        logger.error(f"Error processing request: {e}")
        response = JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "detail": str(e)}
        )
    
    # Add CORS headers to all responses
    origin = request.headers.get("origin")
    if allowed_origins == ["*"] or (origin and origin in allowed_origins):
        response.headers["Access-Control-Allow-Origin"] = origin or "*"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
        
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Health check endpoint - CRITICAL for Railway
@app.get("/health")
async def health_check():
    """Health check endpoint for Railway and monitoring"""
    try:
        # Test bot manager
        status = bot_manager.get_status()
        
        return {
            "status": "healthy", 
            "timestamp": datetime.now().isoformat(),
            "service": "Pokemon TCG Bot API",
            "version": "1.0.0",
            "environment": os.environ.get("RAILWAY_ENVIRONMENT", "unknown"),
            "port": os.environ.get("PORT", "unknown"),
            "bot_manager": "connected" if status else "disconnected",
            "cors": "enabled",
            "uptime": "active"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "degraded",
            "timestamp": datetime.now().isoformat(),
            "service": "Pokemon TCG Bot API",
            "version": "1.0.0",
            "error": str(e),
            "cors": "enabled"
        }

# Root endpoint - CRITICAL for Railway
@app.get("/")
async def root():
    """Root endpoint - Railway deployment check"""
    return {
        "message": "Pokemon TCG Bot API", 
        "status": "running", 
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "cors": "enabled",
        "environment": os.environ.get("RAILWAY_ENVIRONMENT", "unknown"),
        "timestamp": datetime.now().isoformat()
    }

# Bot status endpoints
@app.get("/api/bot-status")
async def get_bot_status():
    """Get current bot status and running jobs"""
    try:
        status = bot_manager.get_status()
        jobs = bot_manager.get_all_jobs()
        
        return {
            "running": any(job["status"] == "running" for job in jobs if isinstance(job, dict) and "status" in job),
            "uptime": "Active" if jobs else None,
            "lastRun": max([job.get("lastRun") for job in jobs if isinstance(job, dict) and job.get("lastRun")], default=None),
            "stats": {
                "postsToday": sum(job.get("stats", {}).get("postsToday", 0) for job in jobs if isinstance(job, dict)),
                "repliesToday": sum(job.get("stats", {}).get("repliesToday", 0) for job in jobs if isinstance(job, dict)),
                "successRate": status.get("stats", {}).get("successRate", 100) if isinstance(status, dict) else 100
            },
            "jobs": jobs,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting bot status: {e}")
        # Return default status instead of error
        return {
            "running": False,
            "uptime": None,
            "lastRun": None,
            "stats": {
                "postsToday": 0,
                "repliesToday": 0,
                "successRate": 100
            },
            "jobs": [],
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Job management endpoints
@app.post("/api/bot-job/create")
async def create_job(request: CreateJobRequest):
    """Create a new bot job"""
    try:
        job = bot_manager.create_job(request.type, request.settings.dict())
        logger.info(f"Created job: {job}")
        return {"success": True, "job": job, "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-job/{job_id}/start")
async def start_job(job_id: str, background_tasks: BackgroundTasks):
    """Start a bot job"""
    try:
        job = bot_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Start the job in the background
        background_tasks.add_task(bot_manager.start_job, job_id)
        
        # Update job status immediately
        if isinstance(job, dict):
            job["status"] = "running"
            job["lastRun"] = datetime.now().isoformat()
            bot_manager.update_job(job_id, job)
        
        logger.info(f"Started job: {job_id}")
        return {"success": True, "message": "Job started successfully", "job": job}
    except Exception as e:
        logger.error(f"Error starting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-job/{job_id}/stop")
async def stop_job(job_id: str):
    """Stop a bot job"""
    try:
        job = bot_manager.stop_job(job_id)
        logger.info(f"Stopped job: {job_id}")
        return {"success": True, "message": "Job stopped successfully", "job": job}
    except Exception as e:
        logger.error(f"Error stopping job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-job/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a bot job"""
    try:
        job = bot_manager.pause_job(job_id)
        logger.info(f"Paused job: {job_id}")
        return {"success": True, "message": "Job paused successfully", "job": job}
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Content generation endpoints
@app.post("/api/generate-content")
async def generate_content(request: GenerateContentRequest):
    """Generate Pokemon TCG content"""
    try:
        logger.info(f"Generating content with request: {request}")
        
        # Generate viral content using your existing system
        viral_posts = generate_viral_content(request.count)
        
        if not viral_posts:
            logger.error("Failed to generate content - no posts returned")
            return {
                "success": False,
                "error": "Failed to generate content",
                "content": None,
                "timestamp": datetime.now().isoformat()
            }
        
        logger.info(f"Generated {len(viral_posts)} posts")
        
        # Optimize content for engagement
        for post in viral_posts:
            if isinstance(post, dict) and 'content' in post:
                post['optimized_content'] = optimize_content_for_engagement(post['content'])
        
        result = {
            "success": True,
            "content": viral_posts[0] if request.count == 1 else viral_posts,
            "generated_at": datetime.now().isoformat(),
            "count": len(viral_posts)
        }
        
        logger.info(f"Returning content result with {len(viral_posts)} posts")
        return result
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return {
            "success": False,
            "error": str(e),
            "content": None,
            "timestamp": datetime.now().isoformat()
        }

# Twitter posting endpoints
@app.post("/api/post-to-twitter")
async def post_to_twitter(request: PostToTwitterRequest):
    """Post content to Twitter"""
    try:
        logger.info(f"Posting to Twitter: {request.content[:50]}...")
        
        result = post_original_tweet(request.content)
        
        if isinstance(result, dict) and result.get('success'):
            # Add tweet URL if available
            if result.get('tweet_id'):
                result['url'] = get_tweet_url(result['tweet_id'])
                logger.info(f"Successfully posted tweet: {result['url']}")
        else:
            logger.error(f"Failed to post tweet: {result.get('error') if isinstance(result, dict) else 'Unknown error'}")
        
        if isinstance(result, dict):
            result['timestamp'] = datetime.now().isoformat()
        
        return result
    except Exception as e:
        logger.error(f"Error posting to Twitter: {e}")
        return {
            "success": False,
            "error": str(e),
            "tweet_id": None,
            "timestamp": datetime.now().isoformat()
        }

# Data endpoints (for dashboard)
@app.get("/api/metrics")
async def get_metrics():
    """Get bot metrics"""
    try:
        metrics = bot_manager.get_metrics()
        if isinstance(metrics, dict):
            metrics['timestamp'] = datetime.now().isoformat()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        # Return default metrics instead of error
        return {
            "totalPosts": 0,
            "avgEngagement": 0,
            "totalLikes": 0,
            "followers": 0,
            "lastUpdated": datetime.now().isoformat(),
            "error": str(e)
        }

@app.get("/api/posts")
async def get_posts(limit: int = 20, offset: int = 0):
    """Get recent posts"""
    try:
        posts = bot_manager.get_posts(limit, offset)
        return posts
    except Exception as e:
        logger.error(f"Error getting posts: {e}")
        # Return empty posts instead of error
        return {
            "posts": [], 
            "total": 0, 
            "hasMore": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.get("/api/topics")
async def get_topics():
    """Get trending topics"""
    try:
        topics = bot_manager.get_topics()
        return topics if topics else []
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        # Return empty topics instead of error
        return []

@app.get("/api/engagement")
async def get_engagement(days: int = 7):
    """Get engagement data"""
    try:
        engagement = bot_manager.get_engagement_data(days)
        return engagement if engagement else []
    except Exception as e:
        logger.error(f"Error getting engagement data: {e}")
        # Return empty engagement data instead of error
        return []

@app.get("/api/settings")
async def get_settings():
    """Get bot settings"""
    try:
        settings = bot_manager.get_settings()
        return settings
    except Exception as e:
        logger.error(f"Error getting settings: {e}")
        # Return default settings instead of error
        return {
            "postsPerDay": 12,
            "keywords": ["Pokemon", "TCG", "Charizard", "Pikachu"],
            "engagementMode": "balanced",
            "autoReply": True,
            "contentTypes": {
                "cardPulls": True,
                "deckBuilding": True,
                "marketAnalysis": True,
                "tournaments": True
            },
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@app.post("/api/settings")
async def update_settings(settings: dict):
    """Update bot settings"""
    try:
        updated_settings = bot_manager.update_settings(settings)
        logger.info(f"Updated settings: {settings}")
        return {
            "success": True, 
            "settings": updated_settings,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return {
            "success": False, 
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
    
@app.get('/debug-twitter-config')
def debug_twitter_config():
    return {
        'api_key_prefix': os.getenv('TWITTER_API_KEY', 'NOT_FOUND')[:10] + '...',
        'access_token_prefix': os.getenv('TWITTER_ACCESS_TOKEN', 'NOT_FOUND')[:15] + '...',
        'all_vars_present': bool(os.getenv('TWITTER_API_KEY') and os.getenv('TWITTER_ACCESS_TOKEN'))
    }

# Railway requires this exact pattern
if __name__ == "__main__":
    # Get port from environment (Railway sets this automatically)
    port = int(os.environ.get("PORT", 8000))
    
    logger.info(f"Starting server on host 0.0.0.0, port {port}")
    logger.info(f"Environment variables loaded: PORT={port}")
    
    # Railway deployment configuration
    uvicorn.run(
        app, 
        host="0.0.0.0",  # Must bind to all interfaces for Railway
        port=port,       # Must use Railway's PORT
        log_level="info",
        access_log=True,
        server_header=False,
        date_header=False
    )