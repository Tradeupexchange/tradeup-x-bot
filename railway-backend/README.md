# Pokemon TCG Bot Backend

FastAPI backend for the Pokemon TCG Social Media Bot, designed to run on Railway.

## Features

- **FastAPI Backend**: Modern, fast API with automatic documentation
- **Bot Management**: Create, start, stop, and manage posting/reply bots
- **Content Generation**: AI-powered Pokemon TCG content creation
- **Twitter Integration**: Direct posting to Twitter/X
- **Data Management**: CSV-based data storage for posts and analytics

## Deployment to Railway

### 1. Create Railway Project

1. Go to [Railway.app](https://railway.app)
2. Sign up/login with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select this repository
5. Railway will automatically detect it's a Python project

### 2. Set Environment Variables

In your Railway dashboard, go to Variables and add:

```
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret
OPENAI_API_KEY=your_openai_api_key
LLM_PROVIDER=openai
PORT=8000
```

### 3. Deploy

Railway will automatically:
- Install dependencies from `requirements.txt`
- Start the FastAPI server using the `Procfile`
- Provide you with a public URL

### 4. Update Frontend

In your Netlify frontend, set the environment variable:
```
VITE_RAILWAY_API_URL=https://your-railway-app.railway.app
```

## API Endpoints

### Bot Management
- `GET /api/bot-status` - Get bot status and running jobs
- `POST /api/bot-job/create` - Create a new bot job
- `POST /api/bot-job/{job_id}/start` - Start a bot job
- `POST /api/bot-job/{job_id}/stop` - Stop a bot job
- `POST /api/bot-job/{job_id}/pause` - Pause a bot job

### Content & Posting
- `POST /api/generate-content` - Generate Pokemon TCG content
- `POST /api/post-to-twitter` - Post content to Twitter

### Data & Analytics
- `GET /api/metrics` - Get bot metrics
- `GET /api/posts` - Get recent posts
- `GET /api/topics` - Get trending topics
- `GET /api/engagement` - Get engagement data
- `GET /api/settings` - Get bot settings
- `POST /api/settings` - Update bot settings

## Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Run the server
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`
API documentation at `http://localhost:8000/docs`

## Architecture

- **FastAPI**: Modern Python web framework
- **Background Tasks**: Handles bot jobs in separate threads
- **CSV Storage**: Simple file-based data storage
- **Twitter Integration**: Direct API integration with tweepy
- **Content Generation**: Template-based + optional LLM integration

## File Structure

```
railway-backend/
├── main.py              # FastAPI application
├── bot_manager.py       # Bot job management
├── content_generator.py # Content generation logic
├── twitter_poster.py    # Twitter API integration
├── knowledge_manager.py # Knowledge base management
├── config.py           # Configuration settings
├── requirements.txt    # Python dependencies
├── Procfile           # Railway deployment config
├── railway.json       # Railway project config
└── data/              # Data storage directory
```

## Monitoring

Railway provides built-in monitoring:
- View logs in real-time
- Monitor resource usage
- Set up alerts
- View deployment history

## Scaling

Railway automatically handles:
- Auto-scaling based on traffic
- Load balancing
- SSL certificates
- Custom domains