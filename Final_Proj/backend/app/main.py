"""
FastAPI main application - Entry point for the AI Fan Engagement Agent
"""

import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from dotenv import load_dotenv

import sys
import os

# Add parent directory to path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.agent.agent import Agent
from app.memory.database import Database
from app.predictions.engine import PredictionEngine

# Load environment variables
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AI Fan Engagement Agent",
    description="A web-based application for sports fans to chat with AI, take quizzes, and predict game outcomes",
    version="1.0.0",
    docs_url=None,
    openapi_url=None,
    redoc_url=None
)

# Add CORS middleware to allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize database and agent
DATABASE_PATH = os.getenv("DATABASE_PATH", "./backend/data/fan_engagement.db")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY not found in environment variables")

db = Database(DATABASE_PATH)
agent = Agent(OPENROUTER_API_KEY, db)

# Pydantic models for request/response
class ChatRequest(BaseModel):
    user_id: str
    message: str

class ChatResponse(BaseModel):
    user_id: str
    message: str
    response: str
    tool_used: str
    action: str
    quiz_data: Optional[dict] = None  # Quiz questions if action is quiz

class QuizSubmissionRequest(BaseModel):
    user_id: str
    team: str
    level: str  # Level: Easy, Medium, Hard
    answers: dict  # {question_index: answer_text}
    questions: list  # Full quiz questions for evaluation

class PredictionGenerateRequest(BaseModel):
    user_id: str
    team1: str
    team2: str
    sport: str  # soccer, nba, nfl

class PredictionSubmitRequest(BaseModel):
    user_id: str
    team1: str
    team2: str
    sport: str
    user_prediction: str  # Team name or "Draw"
    
class UserCreateRequest(BaseModel):
    user_id: str
    username: str
    favorite_team: str = "General"

class UserProfile(BaseModel):
    user_id: str
    username: str
    favorite_team: str
    total_points: int
    badges: list

class LeaderboardEntry(BaseModel):
    rank: int
    user_id: str
    username: str
    points: int
    team: str

# Routes
@app.get("/", response_class=FileResponse)
async def root():
    """Serve the frontend HTML"""
    frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
    index_path = os.path.join(frontend_path, "index.html")
    if os.path.exists(index_path):
        return index_path
    return {"error": "Frontend not found"}


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat message from user.
    The agent decides which tool to use (quiz, prediction, stats, or general chat).
    
    Args:
        user_id: Unique user identifier
        message: User's message
    
    Returns:
        ChatResponse with AI response and metadata
    """
    try:
        result = agent.process_message(request.user_id, request.message)
        
        # Add quiz_data if action is quiz
        quiz_data = result.get("quiz_data")
        
        return ChatResponse(
            user_id=result["user_id"],
            message=result["message"],
            response=result["response"],
            tool_used=result["tool_used"],
            action=result["action"],
            quiz_data=quiz_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/create", response_model=dict)
async def create_user(request: UserCreateRequest):
    """
    Create a new user profile.
    
    Args:
        user_id: Unique user identifier
        username: Display name
        favorite_team: User's favorite sports team
    
    Returns:
        Success message
    """
    try:
        result = db.create_user(request.user_id, request.username, request.favorite_team)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}", response_model=dict)
async def get_user(user_id: str):
    """
    Get user profile and statistics.
    
    Args:
        user_id: User identifier
    
    Returns:
        User profile with stats
    """
    try:
        user = db.get_user(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Fetch additional stats
        quiz_history = db.get_user_quiz_history(user_id)
        predictions = db.get_user_predictions(user_id)
        
        return {
            **user,
            "quiz_count": len(quiz_history),
            "prediction_count": len(predictions)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/leaderboard")
async def get_leaderboard(limit: int = 10):
    """
    Get the leaderboard of top users by points.
    
    Args:
        limit: Number of top users to return
    
    Returns:
        List of top users with their points and ranks
    """
    try:
        leaderboard = db.get_leaderboard(limit)
        return {
            "leaderboard": leaderboard,
            "total_users": len(db.get_leaderboard(1000))
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/history/chat")
async def get_chat_history(user_id: str, limit: int = 20):
    """
    Get user's chat history.
    
    Args:
        user_id: User identifier
        limit: Number of recent messages to return
    
    Returns:
        List of chat messages
    """
    try:
        history = db.get_user_chat_history(user_id, limit)
        return {"chat_history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/history/quizzes")
async def get_quiz_history(user_id: str):
    """
    Get user's quiz history.
    
    Args:
        user_id: User identifier
    
    Returns:
        List of quiz attempts with scores
    """
    try:
        history = db.get_user_quiz_history(user_id)
        return {"quiz_history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/history/predictions")
async def get_prediction_history(user_id: str):
    """
    Get user's prediction history.
    
    Args:
        user_id: User identifier
    
    Returns:
        List of predictions with outcomes
    """
    try:
        predictions = db.get_user_predictions(user_id)
        return {"prediction_history": predictions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/quiz/submit")
async def submit_quiz(request: QuizSubmissionRequest):
    """
    Submit quiz answers and get score.
    Loads correct answers from questions.json using question ID.
    
    Args:
        user_id: User identifier
        team: Team the quiz is about
        level: Quiz level 1-10
        answers: Dict mapping question index to selected answer text
        questions: Full quiz questions for evaluation
    
    Returns:
        Score, correct answers, and points earned
    """
    try:
        import json
        
        # Initialize quiz progress if needed
        progress = db.get_quiz_progress(request.user_id, request.team)
        if not progress:
            db.create_quiz_progress(request.user_id, request.team)
        
        # Load questions from questions.json (flat list) to get correct answers
        questions_path = "./backend/data/questions.json"
        try:
            with open(questions_path, 'r') as f:
                all_questions_list = json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Questions database not found")
        
        # Create a lookup map by question ID for fast access
        question_lookup = {q["id"]: q for q in all_questions_list}
        
        # Calculate score
        correct_count = 0
        total_count = len(request.questions)
        results = []
        
        for idx, question in enumerate(request.questions):
            # Handle both dict and object formats
            if isinstance(question, dict):
                question_text = question.get("question", "")
                options = question.get("options", [])
                question_id = question.get("id", "")
                explanation = question.get("explanation", "")
            else:
                question_text = getattr(question, "question", "")
                options = getattr(question, "options", [])
                question_id = getattr(question, "id", "")
                explanation = getattr(question, "explanation", "")
            
            # Find the correct answer from questions.json by ID (flat list)
            correct_answer = ""
            correct_answer_idx = None
            
            if question_id in question_lookup:
                q_data = question_lookup[question_id]
                correct_answer_idx = q_data.get("correctAnswerIndex")
                if correct_answer_idx is not None and correct_answer_idx < len(options):
                    correct_answer = options[correct_answer_idx]
            
            # User answer is the text they selected
            user_answer = request.answers.get(str(idx), "")
            
            # Case-insensitive, trim whitespace comparison
            is_correct = user_answer.strip().lower() == correct_answer.strip().lower()
            if is_correct:
                correct_count += 1
            
            results.append({
                "question": question_text,
                "user_answer": user_answer,
                "correct_answer": correct_answer,
                "is_correct": is_correct,
                "explanation": explanation
            })
        
        # Calculate percentage score (for display only, not for reward logic)
        score_percentage = (correct_count / total_count * 100) if total_count > 0 else 0
        
        # Award points per correct answer (10 points per correct answer)
        points_per_question = 10
        points_earned = correct_count * points_per_question
        
        # Award points immediately
        db.add_quiz_points(request.user_id, points_earned)
        
        # Mark level as completed
        db.complete_level(request.user_id, request.team, request.level, score_percentage)
        
        # Update progress - advance to next level if exists (level is now string: Easy, Medium, Hard)
        # Map levels to progression
        level_progression = {"Easy": "Medium", "Medium": "Hard", "Hard": "Hard"}
        next_level = level_progression.get(request.level, request.level)
        db.update_quiz_progress(request.user_id, request.team, next_level, 0, 0, 0)
        
        # Store quiz in history
        db.add_quiz_attempt(
            request.user_id,
            request.team,
            f"level_{request.level}",
            score_percentage
        )
        
        # Get updated user info for total points
        user = db.get_user(request.user_id)
        total_points = user["total_points"] if user else 0
        
        return {
            "status": "success",
            "score": score_percentage,
            "correct": correct_count,
            "total": total_count,
            "points_earned": points_earned,
            "points_per_question": points_per_question,
            "level": request.level,
            "total_points": total_points,
            "results": results,
            "message": f"Great job! You earned {points_earned} points!"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/{user_id}/progress/{team}/level-choice")
async def handle_level_progression_choice(user_id: str, team: str, level: str, continue_to_next: bool):
    """
    Handle user's choice to continue to next level or stop after completing a level.
    
    Args:
        user_id: User identifier
        team: Team name
        level: Completed level (Easy, Medium, Hard)
        continue_to_next: True to continue to next level, False to stop
    
    Returns:
        Dictionary with next level or stop confirmation
    """
    try:
        # Level progression: Easy -> Medium -> Hard -> stop
        level_progression = {"Easy": "Medium", "Medium": "Hard", "Hard": None}
        
        if continue_to_next and level in level_progression and level_progression[level]:
            # Advance to next level
            next_level = level_progression[level]
            db.update_quiz_progress(user_id, team, next_level, 0, 0, 0)
            return {
                "success": True,
                "action": "continue",
                "next_level": next_level,
                "message": f"Starting {next_level} Level"
            }
        else:
            # Stop at current level - progress already saved
            return {
                "success": True,
                "action": "stop",
                "current_level": level,
                "message": f"Progress saved at {level} level. You can resume anytime!"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/progress/{team}/total-points")
async def get_team_total_points(user_id: str, team: str):
    """
    Get total points accumulated for a specific team.
    This is different from level score - it's the cumulative points.
    """
    try:
        user = db.get_user(user_id)
        # For now, return the user's total points
        # In the future, could track points per team
        return {
            "user_id": user_id,
            "team": team,
            "total_points": user.get("total_points", 0) if user else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Quiz Progress Tracking Endpoints
@app.post("/api/user/{user_id}/progress/{team}/init")
async def init_quiz_progress(user_id: str, team: str):
    """
    Initialize quiz progress for user+team combination.
    Called when starting a new quiz.
    """
    try:
        result = db.create_quiz_progress(user_id, team)
        return {"success": True, "message": "Quiz progress initialized"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/progress/{team}")
async def get_progress(user_id: str, team: str):
    """
    Get current quiz progress for user+team.
    Used to resume quiz from where user left off.
    """
    try:
        progress = db.get_quiz_progress(user_id, team)
        if progress:
            return {
                "user_id": user_id,
                "team": team,
                "has_progress": True,
                "current_level": progress["current_level"],
                "current_question_index": progress["current_question_index"],
                "level_score": progress["level_score"],
                "total_correct": progress["total_correct"]
            }
        return {
            "user_id": user_id,
            "team": team,
            "has_progress": False
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/{user_id}/progress/{team}/update")
async def update_progress(user_id: str, team: str, 
                         current_level: int, 
                         current_question_index: int,
                         level_score: int = 0,
                         total_correct: int = 0):
    """
    Update quiz progress after answering a question.
    """
    try:
        db.update_quiz_progress(user_id, team, 
                               current_level, current_question_index,
                               level_score, total_correct)
        return {"success": True, "message": "Progress updated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/user/{user_id}/progress/{team}/complete-level")
async def mark_level_complete(user_id: str, team: str, 
                             level: str, score: float):
    """
    Mark a level as completed and move to next level.
    """
    try:
        db.complete_level(user_id, team, level, score)
        
        # Move to next level (Easy -> Medium -> Hard)
        level_progression = {"Easy": "Medium", "Medium": "Hard", "Hard": "Hard"}
        next_level = level_progression.get(level, level)
        db.update_quiz_progress(user_id, team, next_level, 0, 0, 0)
        
        return {
            "success": True,
            "level_completed": level,
            "next_level": next_level,
            "score": score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/user/{user_id}/progress/{team}/resume")
async def get_resume_state(user_id: str, team: str):
    """
    Get full resume state including completed levels and current progress.
    Returns everything needed to show user their quiz progress.
    """
    try:
        progress = db.get_quiz_progress(user_id, team)
        completed = db.get_completed_levels(user_id, team)
        stats = db.get_team_stats(user_id, team)
        
        return {
            "user_id": user_id,
            "team": team,
            "has_progress": progress is not None,
            "current_progress": progress,
            "completed_levels": completed,
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/quiz/generate/{user_id}/{team}/{level}")
async def generate_quiz(user_id: str, team: str, level: str):
    """
    Generate 10 random quiz questions for a team and difficulty level.
    
    Args:
        user_id: User identifier
        team: Team name
        level: Difficulty level - "Easy", "Medium", or "Hard"
    
    Returns:
        List of 10 random questions for the level
    """
    try:
        import json
        import random
        
        # Normalize level input
        level = level.capitalize()
        if level not in ["Easy", "Medium", "Hard"]:
            raise HTTPException(status_code=400, detail="Level must be Easy, Medium, or Hard")
        
        # Initialize quiz progress if needed
        progress = db.get_quiz_progress(user_id, team)
        if not progress:
            db.create_quiz_progress(user_id, team)
        
        # Load questions from questions.json (flat list structure)
        questions_path = "./backend/data/questions.json"
        try:
            with open(questions_path, 'r') as f:
                all_questions_list = json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Questions database not found. Run: python backend/data/generate_questions_v2.py")
        
        # Filter questions for this team and difficulty level
        team_level_questions = [
            q for q in all_questions_list 
            if q.get("team") == team and q.get("level") == level
        ]
        
        if not team_level_questions:
            raise HTTPException(status_code=404, detail=f"No {level} questions found for {team}")
        
        # Randomly select 10 questions (with replacement if fewer than 10 available)
        # Users can retry unlimited times with random selection
        num_questions = min(10, len(team_level_questions))
        selected_questions = random.sample(team_level_questions, num_questions)
        
        # Prepare response - do NOT include correctAnswerIndex for frontend
        quiz_display = []
        for q in selected_questions:
            quiz_display.append({
                "id": q["id"],
                "level": q["level"],
                "team": q["team"],
                "question": q["question"],
                "options": q["options"],
                "explanation": q.get("explanation", "")
                # Note: correctAnswerIndex NOT included for frontend security
            })
        
        return {
            "status": "success",
            "level": level,
            "team": team,
            "questions": quiz_display,
            "total_questions": len(quiz_display),
            "total_available": len(team_level_questions)
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quiz: {str(e)}")

@app.post("/api/quiz/reset-pool/{user_id}/{team}")
async def reset_question_pool(user_id: str, team: str):
    """
    Reset the question pool for a user + team (with user confirmation).
    Allows them to start seeing questions again from the beginning.
    
    Args:
        user_id: User identifier
        team: Team name
    
    Returns:
        Confirmation of pool reset
    """
    try:
        db.reset_asked_questions(user_id, team)
        
        return {
            "status": "success",
            "message": f"Question pool reset for {team}. You can now take quizzes again!",
            "user_id": user_id,
            "team": team
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "database": "connected"}

@app.get("/api/teams/available")
async def get_available_teams():
    """
    Get list of all teams that have questions in the database.
    
    Returns:
        List of teams with their available difficulty levels
    """
    try:
        import json
        
        questions_path = "./backend/data/questions.json"
        try:
            with open(questions_path, 'r') as f:
                all_questions = json.load(f)
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Questions database not found")
        
        # Build team availability map
        teams_map = {}
        for q in all_questions:
            team = q.get("team", "Unknown")
            level = q.get("level", "Unknown")
            
            if team not in teams_map:
                teams_map[team] = {
                    "name": team,
                    "levels": [],
                    "has_easy": False,
                    "has_medium": False,
                    "has_hard": False
                }
            
            if level == "Easy" and not teams_map[team]["has_easy"]:
                teams_map[team]["has_easy"] = True
                teams_map[team]["levels"].append("Easy")
            elif level == "Medium" and not teams_map[team]["has_medium"]:
                teams_map[team]["has_medium"] = True
                teams_map[team]["levels"].append("Medium")
            elif level == "Hard" and not teams_map[team]["has_hard"]:
                teams_map[team]["has_hard"] = True
                teams_map[team]["levels"].append("Hard")
        
        # Convert to list and sort
        teams_list = sorted(list(teams_map.values()), key=lambda x: x["name"])
        
        return {
            "status": "success",
            "teams": teams_list,
            "total_teams": len(teams_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ===== PREDICTION ENDPOINTS =====

@app.post("/api/predictions/generate")
async def generate_prediction(request: PredictionGenerateRequest):
    """
    Generate a system prediction for a match
    
    Args:
        user_id: Unique user identifier
        team1: First team name
        team2: Second team name
        sport: Sport type (soccer, nba, nfl)
    
    Returns:
        System prediction with explanation
    """
    try:
        prediction = PredictionEngine.generate_prediction(request.team1, request.team2, request.sport)
        
        return {
            "status": "success",
            "prediction": {
                "team1": request.team1,
                "team2": request.team2,
                "predicted_winner": prediction['predicted_winner'],
                "predicted_loser": prediction['predicted_loser'],
                "confidence": prediction['confidence'],
                "explanation": prediction['explanation']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/predictions/submit")
async def submit_prediction(request: PredictionSubmitRequest):
    """
    Submit a user prediction and evaluate it against system outcome
    
    Args:
        user_id: Unique user identifier
        team1: First team name
        team2: Second team name
        sport: Sport type (soccer, nba, nfl)
        user_prediction: User's predicted winner (team name or "Draw")
    
    Returns:
        Prediction result with points earned
    """
    try:
        # Generate system prediction
        system_prediction = PredictionEngine.generate_prediction(request.team1, request.team2, request.sport)
        system_outcome = system_prediction['predicted_winner']
        
        # Evaluate user prediction
        is_correct, points = PredictionEngine.evaluate_prediction(request.user_prediction, system_outcome, request.sport)
        
        # Save prediction to database
        result = db.save_prediction(
            request.user_id,
            request.team1,
            request.team2,
            request.user_prediction,
            system_outcome,
            points,
            system_prediction['explanation'],
            request.sport
        )
        
        return {
            "status": "success",
            "result": {
                "user_prediction": request.user_prediction,
                "system_outcome": system_outcome,
                "is_correct": is_correct,
                "points_earned": points,
                "explanation": system_prediction['explanation'],
                "confidence": system_prediction['confidence']
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predictions/history/{user_id}")
async def get_prediction_history(user_id: str):
    """
    Get user's prediction history
    
    Args:
        user_id: Unique user identifier
    
    Returns:
        List of user's predictions
    """
    try:
        predictions = db.get_user_predictions(user_id)
        
        return {
            "status": "success",
            "predictions": predictions,
            "total": len(predictions)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/predictions/stats/{user_id}")
async def get_prediction_stats(user_id: str):
    """
    Get user's prediction statistics
    
    Args:
        user_id: Unique user identifier
    
    Returns:
        Prediction statistics (accuracy, total points, etc.)
    """
    try:
        stats = db.get_prediction_stats(user_id)
        
        return {
            "status": "success",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Serve static files (frontend)
# Serve static files (frontend)
frontend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))

# Mount static files directory
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

