"""
Feedback database for TradeUp X Engager.
Stores and retrieves user feedback on generated posts for continuous learning.
Railway-compatible version with proper project structure.
"""

import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

class FeedbackDatabase:
    """
    A simple JSON-based database to store and retrieve feedback on generated posts.
    """
    
    def __init__(self, database_path=None):
        """
        Initialize the feedback database.
        
        Args:
            database_path: Path to the JSON database file
        """
        if database_path is None:
            # Updated path structure for Railway:
            # /src/feedback_database.py -> ../../data/feedback_database.json
            current_dir = Path(__file__).parent  # This is /src
            railway_backend_dir = current_dir.parent  # This is /railway-backend
            data_dir = railway_backend_dir / 'data'  # This is /railway-backend/data
            database_path = data_dir / 'feedback_database.json'
            
        self.database_path = Path(database_path)
        
        # Ensure the data directory exists
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.data = self._load_database()
    
    def _load_database(self) -> Dict:
        """
        Load the database from the JSON file.
        
        Returns:
            Dictionary containing the database
        """
        if self.database_path.exists():
            try:
                with open(self.database_path, 'r') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                logging.error(f"Error decoding JSON from {self.database_path}")
                return self._create_empty_database()
            except Exception as e:
                logging.error(f"Error loading database: {e}")
                return self._create_empty_database()
        else:
            return self._create_empty_database()
    
    def _create_empty_database(self) -> Dict:
        """
        Create an empty database structure.
        
        Returns:
            Empty database dictionary
        """
        return {
            "metadata": {
                "created_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "version": "1.0",
                "project": "TradeUp X Engager"
            },
            "feedback_entries": [],
            "learning_points": [],
            "best_examples": [
                # Seed with some good examples
                "Just pulled a shiny Charizard! My binder love is real right now 🔥",
                "Anyone else hunting for that Umbreon VMAX Alt Art? #PokemonTCG 😍",
                "PSA 10 Pikachu prices keep climbing! Anyone else watching the market? 🤩"
            ]
        }
    
    def _save_database(self) -> bool:
        """
        Save the database to the JSON file.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update the last_updated timestamp
            self.data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            with open(self.database_path, 'w') as f:
                json.dump(self.data, f, indent=2)
            return True
        except Exception as e:
            logging.error(f"Error saving database: {e}")
            return False
    
    def add_feedback(self, post_content: str, feedback: str, rating: int, 
                     post_metadata: Optional[Dict] = None) -> str:
        """
        Add feedback for a generated post.
        
        Args:
            post_content: The content of the post
            feedback: User feedback text
            rating: Numerical rating (1-5)
            post_metadata: Additional metadata about the post
            
        Returns:
            ID of the feedback entry
        """
        if post_metadata is None:
            post_metadata = {}
        
        # Create a feedback entry
        entry_id = f"feedback_{len(self.data['feedback_entries']) + 1}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        feedback_entry = {
            "id": entry_id,
            "timestamp": datetime.now().isoformat(),
            "post_content": post_content,
            "feedback": feedback,
            "rating": rating,
            "metadata": post_metadata
        }
        
        # Add to database
        self.data["feedback_entries"].append(feedback_entry)
        
        # Extract learning points from feedback
        self._extract_learning_points(feedback_entry)
        
        # Save the database
        self._save_database()
        
        logging.info(f"Added feedback entry: {entry_id} (rating: {rating})")
        
        return entry_id
    
    def _extract_learning_points(self, feedback_entry: Dict) -> None:
        """
        Extract learning points from feedback entry.
        
        Args:
            feedback_entry: The feedback entry to process
        """
        # Simple extraction based on rating
        rating = feedback_entry.get("rating", 0)
        feedback_text = feedback_entry.get("feedback", "")
        post_content = feedback_entry.get("post_content", "")
        
        # For high ratings (4-5), consider the post as a good example
        if rating >= 4:
            learning_point = {
                "type": "positive_example",
                "source_feedback_id": feedback_entry["id"],
                "content": post_content,
                "lesson": f"This post was rated {rating}/5. User feedback: {feedback_text}",
                "timestamp": datetime.now().isoformat()
            }
            self.data["learning_points"].append(learning_point)
            
            # Add to best examples if rating is 5
            if rating == 5 and post_content not in self.data.get("best_examples", []):
                self.data.setdefault("best_examples", []).append(post_content)
                # Keep only top 10 best examples
                self.data["best_examples"] = self.data["best_examples"][-10:]
        
        # For low ratings (1-2), extract what to avoid
        elif rating <= 2:
            learning_point = {
                "type": "negative_example",
                "source_feedback_id": feedback_entry["id"],
                "content": post_content,
                "lesson": f"This post was rated {rating}/5. User feedback: {feedback_text}",
                "timestamp": datetime.now().isoformat()
            }
            self.data["learning_points"].append(learning_point)
        
        # Limit learning points to last 50
        self.data["learning_points"] = self.data["learning_points"][-50:]
    
    def get_learning_summary(self, max_points: int = 10) -> str:
        """
        Get a summary of learning points for the LLM.
        
        Args:
            max_points: Maximum number of learning points to include
            
        Returns:
            String summary of learning points
        """
        if not self.data.get("learning_points", []):
            return "Focus on engaging Pokemon TCG content with authentic community voice. Use casual language, relevant Pokemon terms, and vary hashtag usage (0-3 per post)."
        
        # Sort learning points by timestamp (newest first)
        sorted_points = sorted(
            self.data["learning_points"], 
            key=lambda x: x.get("timestamp", ""), 
            reverse=True
        )
        
        # Take the most recent points
        recent_points = sorted_points[:max_points]
        
        # Format the summary
        summary_parts = ["Based on previous feedback:"]
        
        for i, point in enumerate(recent_points):
            point_type = "✅ DO" if point.get("type") == "positive_example" else "❌ DON'T"
            lesson = point.get("lesson", "")[:100]  # Limit length
            summary_parts.append(f"{i+1}. {point_type}: {lesson}...")
        
        return "\n".join(summary_parts)
    
    def get_best_examples(self, count: int = 3) -> List[str]:
        """
        Get the best post examples based on ratings.
        
        Args:
            count: Number of examples to return
            
        Returns:
            List of post content strings
        """
        # First try to get from stored best examples
        best_examples = self.data.get("best_examples", [])
        
        if len(best_examples) >= count:
            return best_examples[-count:]  # Return most recent
        
        # Fallback: get from highly rated feedback entries
        rated_entries = [
            entry for entry in self.data.get("feedback_entries", [])
            if entry.get("rating", 0) >= 4 and "post_content" in entry
        ]
        
        # Sort by rating (highest first)
        sorted_entries = sorted(
            rated_entries, 
            key=lambda x: x.get("rating", 0), 
            reverse=True
        )
        
        # Combine best examples with highly rated entries
        all_examples = best_examples + [entry.get("post_content", "") for entry in sorted_entries]
        
        # Remove duplicates while preserving order
        unique_examples = []
        for example in all_examples:
            if example and example not in unique_examples:
                unique_examples.append(example)
        
        return unique_examples[:count] if unique_examples else [
            "Just pulled a shiny Charizard! My binder love is real right now 🔥",
            "Anyone else hunting for that Umbreon VMAX Alt Art? #PokemonTCG 😍",
            "PSA 10 Pikachu prices keep climbing! Anyone else watching the market? 🤩"
        ]
    
    def get_feedback_stats(self) -> Dict:
        """
        Get statistics about the feedback database.
        
        Returns:
            Dictionary with statistics
        """
        entries = self.data.get("feedback_entries", [])
        
        if not entries:
            return {
                "total_entries": 0,
                "total_rated": 0,
                "average_rating": 0,
                "rating_distribution": {},
                "learning_points_count": len(self.data.get("learning_points", [])),
                "best_examples_count": len(self.data.get("best_examples", []))
            }
        
        # Calculate statistics
        ratings = [entry.get("rating", 0) for entry in entries if "rating" in entry]
        
        rating_distribution = {}
        for rating in ratings:
            rating_distribution[rating] = rating_distribution.get(rating, 0) + 1
        
        return {
            "total_entries": len(entries),
            "total_rated": len(ratings),
            "average_rating": round(sum(ratings) / len(ratings), 2) if ratings else 0,
            "rating_distribution": rating_distribution,
            "learning_points_count": len(self.data.get("learning_points", [])),
            "best_examples_count": len(self.data.get("best_examples", []))
        }
    
    def export_data(self) -> Dict:
        """Export all data for backup or analysis"""
        return self.data.copy()
    
    def clear_old_data(self, days_to_keep: int = 30) -> int:
        """
        Clear old feedback entries older than specified days.
        
        Args:
            days_to_keep: Number of days of data to keep
            
        Returns:
            Number of entries removed
        """
        from datetime import datetime, timedelta
        
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        original_count = len(self.data.get("feedback_entries", []))
        
        # Filter entries newer than cutoff date
        self.data["feedback_entries"] = [
            entry for entry in self.data.get("feedback_entries", [])
            if datetime.fromisoformat(entry.get("timestamp", "")) > cutoff_date
        ]
        
        # Filter learning points newer than cutoff date
        self.data["learning_points"] = [
            point for point in self.data.get("learning_points", [])
            if datetime.fromisoformat(point.get("timestamp", "")) > cutoff_date
        ]
        
        removed_count = original_count - len(self.data["feedback_entries"])
        
        if removed_count > 0:
            self._save_database()
            logging.info(f"Removed {removed_count} old feedback entries")
        
        return removed_count

if __name__ == "__main__":
    # Example usage for testing
    db = FeedbackDatabase()
    
    # Test data paths
    print(f"Database path: {db.database_path}")
    print(f"Database exists: {db.database_path.exists()}")
    
    # Add some example feedback
    db.add_feedback(
        "Just pulled a shiny Charizard! My binder love is real right now 🔥",
        "Great post, very engaging and authentic",
        5,
        {"hashtags": 0, "tradeup_mention": False}
    )
    
    db.add_feedback(
        "PSA 10 Pikachu prices keep climbing! Anyone else watching the market? #Pokemon #TCGCollector 🤩",
        "Too many hashtags, sounds spammy",
        2,
        {"hashtags": 2, "tradeup_mention": False}
    )
    
    # Print learning summary
    print("\nLearning Summary:")
    print(db.get_learning_summary())
    
    # Print best examples
    print("\nBest Examples:")
    for i, example in enumerate(db.get_best_examples(), 1):
        print(f"{i}. {example}")
    
    # Print statistics
    print("\nStatistics:")
    print(json.dumps(db.get_feedback_stats(), indent=2))