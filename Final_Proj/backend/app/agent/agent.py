"""
Agent Logic - The brain of the Fan Engagement System.
This agent uses OpenRouter API to decide which tool to use based on user input.
"""

import requests
import json
import re
from typing import Dict, List, Optional, Tuple
from app.memory.database import Database
from app.tools.quiz_generator import QuizGeneratorTool
from app.tools.prediction_engine import PredictionEngineTool
from app.tools.reward_tracker import FanRewardTrackerTool

class ActionType:
    """Types of actions the agent can take"""
    CHAT = "chat"
    QUIZ = "quiz"
    PREDICTION = "prediction"
    STATS = "stats"

class Agent:
    def __init__(self, api_key: str, db: Database):
        """Initialize the agent with API key and database"""
        self.api_key = api_key
        self.db = db
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Initialize tools
        self.quiz_tool = QuizGeneratorTool(api_key)
        self.prediction_tool = PredictionEngineTool(api_key)
        self.reward_tool = FanRewardTrackerTool(db)
        
        # System prompt that defines agent behavior
        self.system_prompt = """You are an AI Sports Fan Engagement Agent. Your role is to help sports fans by:

1. CHAT: Answer questions about sports, teams, players, and games
2. QUIZ: Generate or discuss sports trivia quizzes
3. PREDICTION: Make informed predictions about game outcomes
4. STATS: Provide user statistics and leaderboard information

Based on user input, decide which action to take. You have access to three tools:
- quiz_tool: Generate sports trivia questions
- prediction_tool: Make game outcome predictions  
- reward_tool: Track user points and badges (no LLM required)

Guidelines:
- Always be helpful and engaging
- If user asks about quizzes, use quiz_tool
- If user asks about game outcomes/predictions, use prediction_tool
- If user asks about their stats or leaderboard, use reward_tool
- For general sports discussion, just chat without tools
- Remember user context from their history
- Be encouraging and celebrate their achievements

Keep responses friendly, concise, and focused on the user's needs."""

    def decide_action(self, user_id: str, message: str) -> Tuple[str, str]:
        """
        Decide which action to take based on user message.
        Uses OpenRouter to understand intent.
        
        Returns:
            Tuple of (action_type, tool_input)
        """
        
        # Get user context
        user = self.db.get_user(user_id)
        user_context = f"User: {user['username']}, Team: {user['favorite_team']}" if user else "New user"
        
        # Recent chat history for context
        chat_history = self.db.get_user_chat_history(user_id, limit=3)
        
        intent_prompt = f"""Given this user message, decide what action to take.

User Context: {user_context}
User Message: "{message}"

Available actions:
1. "chat" - For general sports questions and conversation
2. "quiz" - For quiz generation requests (extract team and difficulty if mentioned)
3. "prediction" - For game outcome predictions (extract team names if mentioned)
4. "stats" - For requests about user stats, leaderboard, achievements

Respond in JSON format ONLY (no markdown):
{{
    "action": "chat|quiz|prediction|stats",
    "reasoning": "brief explanation",
    "extracted_params": {{"key": "value"}}
}}

For quiz action, extract: team, difficulty (easy/medium/hard)
For prediction action, extract: team1, team2
For other actions, extracted_params can be empty.
"""

        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openrouter/auto",
                    "messages": [{"role": "user", "content": intent_prompt}],
                    "temperature": 0.3  # Lower temp for more consistent decision-making
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                decision = json.loads(content)
                
                action = decision.get("action", "chat")
                params = decision.get("extracted_params", {})
                
                return action, json.dumps(params)
        
        except Exception as e:
            print(f"Error in decide_action: {e}")
        
        # Fallback: use keyword matching
        return self._fallback_action_decision(message)

    def _fallback_action_decision(self, message: str) -> Tuple[str, str]:
        """Fallback action decision using keyword matching"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["quiz", "trivia", "question", "test"]):
            return ActionType.QUIZ, "{}"
        elif any(word in message_lower for word in ["predict", "prediction", "score", "win", "outcome", "vs"]):
            return ActionType.PREDICTION, "{}"
        elif any(word in message_lower for word in ["stats", "leaderboard", "points", "badges", "rank", "score"]):
            return ActionType.STATS, "{}"
        else:
            return ActionType.CHAT, "{}"

    def process_message(self, user_id: str, message: str) -> Dict:
        """
        Main method to process user message and generate response.
        
        Returns:
            Dictionary with response and metadata
        """
        
        # Ensure user exists
        user = self.db.get_user(user_id)
        if not user:
            self.db.create_user(user_id, f"User_{user_id[:8]}")
            user = self.db.get_user(user_id)
        
        # Decide which action to take
        action, params_str = self.decide_action(user_id, message)
        params = json.loads(params_str)
        
        # Execute appropriate action
        if action == ActionType.QUIZ:
            response_text, tool_name, quiz_data = self._handle_quiz(message, user, params)
        elif action == ActionType.PREDICTION:
            response_text, tool_name = self._handle_prediction(message, user, params)
            quiz_data = None
        elif action == ActionType.STATS:
            response_text, tool_name = self._handle_stats(user_id, user)
            quiz_data = None
        else:  # CHAT
            response_text, tool_name = self._handle_chat(message, user)
            quiz_data = None
        
        # Store in database
        self.db.add_chat_message(user_id, message, response_text, tool_name)
        
        return {
            "user_id": user_id,
            "message": message,
            "response": response_text,
            "tool_used": tool_name,
            "action": action,
            "quiz_data": quiz_data
        }

    def _handle_chat(self, message: str, user: Dict) -> Tuple[str, str]:
        """Handle general chat requests"""
        user_context = f"User is a fan of the {user['favorite_team']}."
        
        prompt = f"""{self.system_prompt}

User Profile: {user_context}
User Message: {message}

Provide a helpful, engaging response about sports. Keep it concise and friendly."""

        try:
            response = requests.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "openrouter/auto",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"], "chat"
        
        except Exception as e:
            print(f"Error in chat: {e}")
        
        return f"I appreciate your question about sports! I'd be happy to discuss more about {user['favorite_team']} or any sports topic. What would you like to know?", "chat"

    def _handle_quiz(self, message: str, user: Dict, params: Dict) -> Tuple[str, str, Optional[Dict]]:
        """Handle quiz generation with levels 1-10"""
        team = params.get("team", user["favorite_team"])
        level = params.get("level", 1)
        
        # Validate level
        if not isinstance(level, int):
            try:
                level = int(level)
            except:
                level = 1
        level = max(1, min(10, level))  # Clamp between 1-10
        
        # Generate quiz
        quiz = self.quiz_tool.generate_quiz(team, level)
        
        # Format quiz response
        response = f"🎯 **Sports Trivia Quiz: {team}**\n"
        response += f"Level: {level}/10\n"
        num_questions = 7 if level == 10 else 5
        response += f"Questions: {num_questions}\n\n"
        response += "Click the button below to take the quiz!\n\n"
        response += f"Good luck! 🏆 You'll earn {self._get_level_points(level)} points if you score 70% or higher."
        
        # Prepare quiz data for frontend
        quiz_data = {
            "team": team,
            "level": level,
            "questions": [
                {
                    "question": q.question,
                    "options": q.options,
                    "correct_answer": q.correct_answer,
                    "explanation": q.explanation
                }
                for q in quiz.questions
            ]
        }
        
        return response, "quiz", quiz_data

    def _handle_prediction(self, message: str, user: Dict, params: Dict) -> Tuple[str, str]:
        """Handle game outcome prediction"""
        
        # Extract team names from message or params
        team1 = params.get("team1")
        team2 = params.get("team2")
        
        if not team1 or not team2:
            # Try to extract from message
            teams = self._extract_teams_from_message(message)
            if len(teams) >= 2:
                team1, team2 = teams[0], teams[1]
            else:
                return "Please specify two teams for prediction (e.g., 'Lakers vs Celtics')", "prediction"
        
        # Make prediction
        pred = self.prediction_tool.predict_outcome(team1, team2)
        
        response = f"🔮 **Game Prediction: {pred.team1} vs {pred.team2}**\n\n"
        response += f"🏆 Predicted Winner: {pred.predicted_winner}\n"
        response += f"📊 Score: {pred.predicted_score}\n"
        response += f"📈 Confidence: {pred.confidence * 100:.0f}%\n\n"
        response += f"💡 Analysis: {pred.explanation}\n\n"
        response += "Make this prediction official? You'll earn points when the game result is known!"
        
        # Store prediction
        self.db.add_prediction(
            user_id=self._get_user_id_from_user_dict(user),
            team1=pred.team1,
            team2=pred.team2,
            predicted_winner=pred.predicted_winner,
            predicted_score=pred.predicted_score,
            explanation=pred.explanation
        )
        
        return response, "prediction"

    def _handle_stats(self, user_id: str, user: Dict) -> Tuple[str, str]:
        """Handle user statistics and leaderboard requests"""
        stats = self.reward_tool.get_user_stats(user_id)
        leaderboard = self.reward_tool.get_leaderboard(5)
        
        response = f"📊 **Your Stats**\n\n"
        response += f"Username: {stats['username']}\n"
        response += f"Team: {stats['favorite_team']}\n"
        response += f"Total Points: {stats['total_points']} 🏆\n"
        response += f"Rank: #{stats['leaderboard_rank'] or 'Unranked'}\n\n"
        
        response += f"Achievements:\n"
        response += f"  • Quizzes Completed: {stats['quiz_count']}\n"
        response += f"  • Predictions Made: {stats['prediction_count']}\n"
        response += f"  • Avg Quiz Score: {stats['avg_quiz_score']:.1f}%\n\n"
        
        if stats['badges']:
            response += f"Badges: {', '.join(stats['badges'])}\n\n"
        
        response += "🏅 **Leaderboard (Top 5)**\n"
        for entry in leaderboard:
            response += f"  #{entry['rank']}. {entry['username']} - {entry['points']} pts\n"
        
        return response, "stats"

    def _extract_teams_from_message(self, message: str) -> List[str]:
        """Extract team names from message"""
        # Known teams
        known_teams = [
            "Lakers", "Celtics", "Warriors", "Denver", "Nuggets", "Heat", "Miami",
            "Patriots", "Cowboys", "Broncos", "Chiefs", "Yankees", "Dodgers",
            "Manchester United", "Liverpool", "Real Madrid", "Barcelona"
        ]
        
        found_teams = []
        for team in known_teams:
            if team.lower() in message.lower():
                found_teams.append(team)
        
        return found_teams

    def _get_level_points(self, level: int) -> int:
        """Get points for quiz level (1-10)"""
        # Points increase with level difficulty
        points = {
            1: 10, 2: 15, 3: 20, 4: 25, 5: 30,
            6: 40, 7: 50, 8: 60, 9: 75, 10: 100
        }
        return points.get(level, 25)

    def _get_user_id_from_user_dict(self, user: Dict) -> str:
        """Extract user_id from user dict"""
        return user.get("user_id") or user.get("id") or ""
