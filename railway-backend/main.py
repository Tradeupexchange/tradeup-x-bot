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

# Import your existing modules
from bot_manager import BotManager
from content_generator import generate_viral_content, optimize_content_for_engagement
from twitter_poster import post_original_tweet, get_tweet_url
from knowledge_manager import update_knowledge_base_from_csv, update_knowledge_base_from_web

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Pokemon TCG Bot API", version="1.0.0")

# Enhanced CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for now
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

# Add a middleware to handle CORS manually for better control
@app.middleware("http")
async def cors_handler(request, call_next):
    # Handle preflight requests
    if request.method == "OPTIONS":
        response = JSONResponse(content={"message": "OK"})
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "86400"
        return response
    
    # Process the request
    response = await call_next(request)
    
    # Add CORS headers to all responses
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
    response.headers["Access-Control-Allow-Headers"] = "*"
    
    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "Pokemon TCG Bot API",
        "version": "1.0.0",
        "cors": "enabled"
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "message": "Pokemon TCG Bot API", 
        "status": "running", 
        "docs": "/docs",
        "health": "/health",
        "cors": "enabled"
    }

# Bot status endpoints
@app.get("/api/bot-status")
async def get_bot_status():
    """Get current bot status and running jobs"""
    try:
        status = bot_manager.get_status()
        jobs = bot_manager.get_all_jobs()
        
        return {
            "running": any(job["status"] == "running" for job in jobs),
            "uptime": "Active" if jobs else None,
            "lastRun": max([job.get("lastRun") for job in jobs if job.get("lastRun")], default=None),
            "stats": {
                "postsToday": sum(job.get("stats", {}).get("postsToday", 0) for job in jobs),
                "repliesToday": sum(job.get("stats", {}).get("repliesToday", 0) for job in jobs),
                "successRate": status.get("stats", {}).get("successRate", 100)
            },
            "jobs": jobs
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
            "jobs": []
        }

# Job management endpoints
@app.post("/api/bot-job/create")
async def create_job(request: CreateJobRequest):
    """Create a new bot job"""
    try:
        job = bot_manager.create_job(request.type, request.settings.dict())
        return {"success": True, "job": job}
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
        job["status"] = "running"
        job["lastRun"] = datetime.now().isoformat()
        bot_manager.update_job(job_id, job)
        
        return {"success": True, "message": "Job started successfully", "job": job}
    except Exception as e:
        logger.error(f"Error starting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-job/{job_id}/stop")
async def stop_job(job_id: str):
    """Stop a bot job"""
    try:
        job = bot_manager.stop_job(job_id)
        return {"success": True, "message": "Job stopped successfully", "job": job}
    except Exception as e:
        logger.error(f"Error stopping job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/bot-job/{job_id}/pause")
async def pause_job(job_id: str):
    """Pause a bot job"""
    try:
        job = bot_manager.pause_job(job_id)
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
                "content": None
            }
        
        logger.info(f"Generated {len(viral_posts)} posts")
        
        # Optimize content for engagement
        for post in viral_posts:
            post['optimized_content'] = optimize_content_for_engagement(post['content'])
        
        result = {
            "success": True,
            "content": viral_posts[0] if request.count == 1 else viral_posts,
            "generated_at": datetime.now().isoformat(),
            "count": len(viral_posts)
        }
        
        logger.info(f"Returning content result: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Error generating content: {e}")
        return {
            "success": False,
            "error": str(e),
            "content": None
        }

# Twitter posting endpoints
@app.post("/api/post-to-twitter")
async def post_to_twitter(request: PostToTwitterRequest):
    """Post content to Twitter"""
    try:
        logger.info(f"Posting to Twitter: {request.content[:50]}...")
        
        result = post_original_tweet(request.content)
        
        if result.get('success'):
            # Add tweet URL if available
            if result.get('tweet_id'):
                result['url'] = get_tweet_url(result['tweet_id'])
                logger.info(f"Successfully posted tweet: {result['url']}")
        else:
            logger.error(f"Failed to post tweet: {result.get('error')}")
        
        return result
    except Exception as e:
        logger.error(f"Error posting to Twitter: {e}")
        return {
            "success": False,
            "error": str(e),
            "tweet_id": None
        }

# Data endpoints (for dashboard)
@app.get("/api/metrics")
async def get_metrics():
    """Get bot metrics"""
    try:
        metrics = bot_manager.get_metrics()
        return metrics
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        # Return default metrics instead of error
        return {
            "totalPosts": 0,
            "avgEngagement": 0,
            "totalLikes": 0,
            "followers": 0,
            "lastUpdated": datetime.now().isoformat()
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
        return {"posts": [], "total": 0, "hasMore": False}

@app.get("/api/topics")
async def get_topics():
    """Get trending topics"""
    try:
        topics = bot_manager.get_topics()
        return topics
    except Exception as e:
        logger.error(f"Error getting topics: {e}")
        # Return empty topics instead of error
        return []

@app.get("/api/engagement")
async def get_engagement(days: int = 7):
    """Get engagement data"""
    try:
        engagement = bot_manager.get_engagement_data(days)
        return engagement
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
            }
        }

@app.post("/api/settings")
async def update_settings(settings: dict):
    """Update bot settings"""
    try:
        updated_settings = bot_manager.update_settings(settings)
        return {"success": True, "settings": updated_settings}
    except Exception as e:
        logger.error(f"Error updating settings: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)