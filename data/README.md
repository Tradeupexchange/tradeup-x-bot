# Data Directory

This directory contains CSV files with your Pokemon TCG bot data. The dashboard reads from these files to display metrics, posts, and analytics.

## Expected File Structure

### posts.csv
Contains all your bot's posts with engagement data:
```csv
id,content,likes,retweets,replies,topics,timestamp
1,"Just pulled a shiny Charizard! 🔥 #PokemonTCG",45,12,8,"[""Charizard"",""Shiny""]","2024-01-15T10:30:00Z"
```

### metrics.csv
Contains daily metrics:
```csv
date,total_posts,avg_engagement,total_likes,followers
2024-01-15,1247,8.4,24700,3421
```

### topics.csv
Contains topic analysis data:
```csv
name,count,trend,percentage
Charizard,89,up,28
Pikachu,76,up,24
```

### engagement.csv
Contains daily engagement data for charts:
```csv
date,engagement,posts
2024-01-15,8.4,12
2024-01-16,7.2,15
```

### settings.json
Contains bot configuration:
```json
{
  "postsPerDay": 12,
  "keywords": ["Pokemon", "TCG", "Charizard"],
  "engagementMode": "balanced",
  "autoReply": true,
  "contentTypes": {
    "cardPulls": true,
    "deckBuilding": true,
    "marketAnalysis": true,
    "tournaments": true
  }
}
```

### bot_status.json
Contains bot status information:
```json
{
  "running": true,
  "uptime": "2 hours 15 minutes",
  "lastRun": "2024-01-15T10:30:00Z"
}
```

## Integration with Your Python Scripts

Your Python scraping and LLM scripts should output data in these CSV formats. The dashboard will automatically read and display the latest data.

To integrate:
1. Modify your Python scripts to save data in these CSV formats
2. Place the CSV files in this `data/` directory
3. The dashboard will automatically pick up changes and display them

## Local Development

When developing locally, you can create sample CSV files in this directory to test the dashboard functionality.