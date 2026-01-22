"""
Fan Reward Tracker Tool - MCP Tool for tracking points, badges, and leaderboard.
This tool does NOT use the LLM - it directly updates user data based on actions.
"""

from typing import Dict, List, Optional
from app.memory.database import Database

class RewardConfig:
    """Configuration for reward values"""
    QUIZ_POINTS = {
        "easy": 10,
        "medium": 25,
        "hard": 50
    }
    PREDICTION_CORRECT = 100
    PREDICTION_CLOSE = 25  # Within 5 points
    FIRST_PREDICTION = 10
    
    BADGES = {
        "quiz_master": "Completed 10 quizzes",
        "prediction_pro": "Made 10 accurate predictions",
        "points_collector": "Earned 1000 points",
        "perfect_quiz": "Scored 100% on a quiz",
        "leaderboard_top_10": "Ranked in top 10",
        "early_adopter": "First 100 users"
    }

class FanRewardTrackerTool:
    def __init__(self, db: Database):
        """Initialize with database connection"""
        self.db = db
        self.config = RewardConfig()

    def add_quiz_points(self, user_id: str, difficulty: str, score_percentage: float) -> Dict:
        """
        Award points for completing a quiz.
        
        Args:
            user_id: User ID
            difficulty: Quiz difficulty level
            score_percentage: Quiz score (0-100)
        
        Returns:
            Dictionary with points awarded and badges earned
        """
        # Calculate base points by difficulty
        base_points = self.config.QUIZ_POINTS.get(difficulty, 25)
        
        # Bonus for perfect score
        if score_percentage == 100:
            points = base_points * 2  # Double points for perfect
            self.db.add_badge(user_id, "perfect_quiz")
            badges_earned = ["perfect_quiz"]
        else:
            # Scale points by performance
            points = int(base_points * (score_percentage / 100))
            badges_earned = []
        
        # Award points
        self.db.update_user_points(user_id, points)
        
        # Check for quiz master badge (10 quizzes)
        history = self.db.get_user_quiz_history(user_id)
        if len(history) >= 10:
            self.db.add_badge(user_id, "quiz_master")
            if "quiz_master" not in badges_earned:
                badges_earned.append("quiz_master")
        
        return {
            "points_awarded": points,
            "badges_earned": badges_earned,
            "total_user_points": self.db.get_user(user_id)["total_points"]
        }

    def add_prediction_points(self, user_id: str, is_correct: bool, 
                             is_close: bool = False) -> Dict:
        """
        Award points for making a prediction.
        
        Args:
            user_id: User ID
            is_correct: Whether the prediction was accurate
            is_close: Whether the prediction was close (within margin)
        
        Returns:
            Dictionary with points awarded and badges earned
        """
        points = 0
        badges_earned = []
        
        if is_correct:
            points = self.config.PREDICTION_CORRECT
            badges_earned.append("prediction_pro")
        elif is_close:
            points = self.config.PREDICTION_CLOSE
        else:
            points = self.config.FIRST_PREDICTION  # Minimum points for participation
        
        # Award points
        self.db.update_user_points(user_id, points)
        
        # Add badges
        for badge in badges_earned:
            self.db.add_badge(user_id, badge)
        
        # Check for points collector badge (1000 points)
        user = self.db.get_user(user_id)
        if user["total_points"] >= 1000:
            self.db.add_badge(user_id, "points_collector")
            if "points_collector" not in badges_earned:
                badges_earned.append("points_collector")
        
        return {
            "points_awarded": points,
            "badges_earned": badges_earned,
            "total_user_points": user["total_points"] + points
        }

    def get_user_stats(self, user_id: str) -> Dict:
        """Get comprehensive user statistics"""
        user = self.db.get_user(user_id)
        if not user:
            return {"error": "User not found"}
        
        quiz_history = self.db.get_user_quiz_history(user_id)
        predictions = self.db.get_user_predictions(user_id)
        leaderboard = self.db.get_leaderboard(100)
        
        # Find user rank
        user_rank = None
        for entry in leaderboard:
            if entry["user_id"] == user_id:
                user_rank = entry["rank"]
                break
        
        return {
            "user_id": user_id,
            "username": user["username"],
            "favorite_team": user["favorite_team"],
            "total_points": user["total_points"],
            "badges": user["badges"],
            "quiz_count": len(quiz_history),
            "prediction_count": len(predictions),
            "avg_quiz_score": self._calculate_avg_quiz_score(quiz_history),
            "leaderboard_rank": user_rank,
            "created_at": user["created_at"]
        }

    def _calculate_avg_quiz_score(self, quiz_history: List[Dict]) -> float:
        """Calculate average quiz score"""
        if not quiz_history:
            return 0.0
        return sum(q["score"] for q in quiz_history) / len(quiz_history)

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get leaderboard data"""
        return self.db.get_leaderboard(limit)

    def check_and_award_leaderboard_badge(self, user_id: str) -> Optional[str]:
        """Check if user qualifies for leaderboard badge and award if so"""
        leaderboard = self.db.get_leaderboard(10)
        for entry in leaderboard:
            if entry["user_id"] == user_id:
                self.db.add_badge(user_id, "leaderboard_top_10")
                return "leaderboard_top_10"
        return None
