# Pokemon TCG Social Dashboard

A comprehensive dashboard for managing your Pokemon TCG social media bot with automated posting and engagement features.

## Architecture

This project uses a **separated frontend/backend architecture**:

- **Frontend**: React dashboard hosted on **Netlify**
- **Backend**: Python FastAPI server hosted on **Railway**

## Features

- **Bot Control Center**: Start, stop, and manage posting and reply bots
- **Real-time Analytics**: Track posts, engagement, and performance metrics
- **Content Generation**: AI-powered Pokemon TCG content creation
- **Twitter Integration**: Automated posting to Twitter/X
- **Dashboard Analytics**: Visual charts and metrics tracking

## Quick Setup

### 1. Deploy Backend to Railway

1. **Create Railway Account**: Go to [Railway.app](https://railway.app) and sign up
2. **Deploy Backend**: 
   - Click "New Project" → "Deploy from GitHub repo"
   - Select the `railway-backend` folder
   - Railway will auto-detect Python and deploy
3. **Set Environment Variables** in Railway dashboard:
   ```
   TWITTER_API_KEY=your_twitter_api_key
   TWITTER_API_SECRET=your_twitter_api_secret
   TWITTER_ACCESS_TOKEN=your_twitter_access_token
   TWITTER_ACCESS_SECRET=your_twitter_access_secret
   OPENAI_API_KEY=your_openai_api_key
   ```
4. **Get Railway URL**: Copy your Railway app URL (e.g., `https://your-app.railway.app`)

### 2. Deploy Frontend to Netlify

1. **Connect Repository**: Link this repo to Netlify
2. **Set Environment Variable**:
   ```
   VITE_RAILWAY_API_URL=https://your-railway-app.railway.app
   ```
3. **Deploy**: Netlify will automatically build and deploy

### 3. Get Twitter API Credentials

1. Go to [Twitter Developer Portal](https://developer.twitter.com/)
2. Create a new app or use an existing one
3. Generate API keys and access tokens
4. Make sure your app has "Read and Write" permissions
5. Add the credentials to Railway environment variables

## Local Development

### Backend (Railway)
```bash
cd railway-backend
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn main:app --reload --port 8000
```

### Frontend (Netlify)
```bash
npm install
# Create .env.local with:
# VITE_RAILWAY_API_URL=http://localhost:8000
npm run dev
```

## How It Works

### Bot Control System

The dashboard provides an intuitive interface to manage your Pokemon TCG bots:

1. **Posting Bot**: Automatically generates and posts Pokemon TCG content
2. **Reply Bot**: Monitors and responds to Pokemon TCG related tweets
3. **Scheduling**: Set posting frequency and active hours
4. **Content Types**: Choose what types of content to generate

### Content Generation

The system uses multiple approaches:

- **Template-based**: High-quality, curated templates for consistent content
- **AI-powered**: Optional integration with OpenAI or Groq for dynamic content
- **Knowledge Base**: Learns from CSV data and web scraping

### Twitter Integration

- **Direct API Integration**: Posts directly to Twitter using official API
- **Rate Limiting**: Respects Twitter's rate limits and posting guidelines
- **Fallback Mode**: Graceful handling when credentials aren't available

## API Documentation

Once your Railway backend is deployed, visit:
`https://your-railway-app.railway.app/docs`

This provides interactive API documentation with all available endpoints.

## Project Structure

```
pokemon-tcg-dashboard/
├── src/                    # React frontend
│   ├── components/         # UI components
│   ├── hooks/             # React hooks
│   └── lib/               # Utilities
├── railway-backend/        # Python FastAPI backend
│   ├── main.py            # FastAPI application
│   ├── bot_manager.py     # Bot management
│   ├── content_generator.py # Content generation
│   ├── twitter_poster.py  # Twitter integration
│   └── requirements.txt   # Python dependencies
├── netlify.toml           # Netlify config
└── package.json           # Frontend dependencies
```

## Troubleshooting

### Bot Not Posting

1. **Check Railway Logs**: View logs in Railway dashboard
2. **Verify Twitter Credentials**: Ensure all 4 Twitter API credentials are set
3. **Check Permissions**: Make sure Twitter app has "Read and Write" permissions
4. **Test API**: Visit `/docs` endpoint to test API manually

### Frontend Not Connecting

1. **Check Railway URL**: Ensure `VITE_RAILWAY_API_URL` is correct
2. **CORS Issues**: Backend includes CORS middleware for all origins
3. **Network**: Ensure Railway backend is running and accessible

### Content Not Generating

1. **Check API Keys**: Verify OpenAI/Groq keys if using LLM generation
2. **Fallback Mode**: System falls back to templates if LLM fails
3. **Logs**: Check Railway logs for content generation errors

## Deployment Benefits

### Railway Backend
- ✅ Automatic Python environment setup
- ✅ Built-in monitoring and logging
- ✅ Auto-scaling and load balancing
- ✅ Easy environment variable management
- ✅ Git-based deployments

### Netlify Frontend
- ✅ Global CDN for fast loading
- ✅ Automatic HTTPS
- ✅ Branch previews
- ✅ Form handling
- ✅ Easy custom domains

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test locally with both frontend and backend
5. Submit a pull request

## License

This project is licensed under the MIT License.