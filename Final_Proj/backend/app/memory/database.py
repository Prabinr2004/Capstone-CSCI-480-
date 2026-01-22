"""
Database initialization and schema setup for Fan Engagement Agent.
Uses SQLite for persistent storage of user data, quiz history, and predictions.
"""

import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, Dict, List

class Database:
    def __init__(self, db_path: str = "./backend/data/fan_engagement.db"):
        self.db_path = db_path
        # Create data directory if it doesn't exist
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database schema"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Users table - stores user profiles and long-term memory
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id TEXT PRIMARY KEY,
                username TEXT NOT NULL,
                favorite_team TEXT,
                total_points INTEGER DEFAULT 0,
                badges TEXT DEFAULT '[]',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Quiz history table - stores quiz attempts and scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                team TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                questions TEXT NOT NULL,
                answers TEXT NOT NULL,
                score REAL NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Predictions table - stores user predictions and outcomes
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                team1 TEXT NOT NULL,
                team2 TEXT NOT NULL,
                predicted_winner TEXT NOT NULL,
                predicted_score TEXT NOT NULL,
                explanation TEXT,
                actual_outcome TEXT,
                points_earned INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Chat history table - stores conversation history for context
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                message TEXT NOT NULL,
                response TEXT NOT NULL,
                tool_used TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Quiz progress table - tracks current level/question for each user+team
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS quiz_progress (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                team TEXT NOT NULL,
                current_level INTEGER DEFAULT 1,
                current_question_index INTEGER DEFAULT 0,
                level_score INTEGER DEFAULT 0,
                total_correct INTEGER DEFAULT 0,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, team),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Quiz completed levels - tracks which levels user has completed for each team
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS completed_levels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                team TEXT NOT NULL,
                level INTEGER NOT NULL,
                score REAL NOT NULL,
                completed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, team, level),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        # Asked questions history - tracks which questions have been asked to each user for each team
        # This prevents the same question from being asked twice to the same user for the same team
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS asked_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                team TEXT NOT NULL,
                question_id TEXT NOT NULL,
                asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, team, question_id),
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
        ''')

        conn.commit()
        conn.close()

    # User Management
    def create_user(self, user_id: str, username: str, favorite_team: str = "General") -> Dict:
        """Create a new user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO users (user_id, username, favorite_team)
                VALUES (?, ?, ?)
            ''', (user_id, username, favorite_team))
            conn.commit()
            return {"success": True, "user_id": user_id}
        except sqlite3.IntegrityError:
            return {"success": False, "message": "User already exists"}
        finally:
            conn.close()

    def get_user(self, user_id: str) -> Optional[Dict]:
        """Retrieve user profile"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "user_id": row["user_id"],
                "username": row["username"],
                "favorite_team": row["favorite_team"],
                "total_points": row["total_points"],
                "badges": json.loads(row["badges"]),
                "created_at": row["created_at"],
                "last_interaction": row["last_interaction"]
            }
        return None

    def update_user_points(self, user_id: str, points: int):
        """Update user's total points"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE users 
            SET total_points = total_points + ?, 
                last_interaction = CURRENT_TIMESTAMP
            WHERE user_id = ?
        ''', (points, user_id))
        
        conn.commit()
        conn.close()

    def add_badge(self, user_id: str, badge: str):
        """Add a badge to user"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT badges FROM users WHERE user_id = ?', (user_id,))
        row = cursor.fetchone()
        
        if row:
            badges = json.loads(row["badges"])
            if badge not in badges:
                badges.append(badge)
                cursor.execute('''
                    UPDATE users 
                    SET badges = ?
                    WHERE user_id = ?
                ''', (json.dumps(badges), user_id))
                conn.commit()
        
        conn.close()

    def add_quiz_points(self, user_id: str, points: int):
        """Add points to user (for quiz completion bonuses)"""
        self.update_user_points(user_id, points)

    # Quiz Progress Tracking
    def get_quiz_progress(self, user_id: str, team: str) -> Optional[Dict]:
        """Get current quiz progress for user+team combination"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM quiz_progress 
            WHERE user_id = ? AND team = ?
        ''', (user_id, team))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "current_level": row["current_level"],
                "current_question_index": row["current_question_index"],
                "level_score": row["level_score"],
                "total_correct": row["total_correct"],
                "started_at": row["started_at"]
            }
        return None

    def create_quiz_progress(self, user_id: str, team: str) -> Dict:
        """Initialize quiz progress for user+team"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO quiz_progress (user_id, team, current_level, current_question_index, level_score, total_correct)
                VALUES (?, ?, 1, 0, 0, 0)
            ''', (user_id, team))
            conn.commit()
            return {"success": True}
        except sqlite3.IntegrityError:
            # Already exists, return existing
            return {"success": True, "existing": True}
        finally:
            conn.close()

    def update_quiz_progress(self, user_id: str, team: str, 
                            current_level: int, current_question_index: int,
                            level_score: int, total_correct: int):
        """Update quiz progress"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE quiz_progress 
            SET current_level = ?, 
                current_question_index = ?,
                level_score = ?,
                total_correct = ?,
                last_updated = CURRENT_TIMESTAMP
            WHERE user_id = ? AND team = ?
        ''', (current_level, current_question_index, level_score, total_correct, user_id, team))
        
        conn.commit()
        conn.close()

    def complete_level(self, user_id: str, team: str, level: int, score: float):
        """Mark a level as completed"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO completed_levels (user_id, team, level, score, completed_at)
            VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
        ''', (user_id, team, level, score))
        
        conn.commit()
        conn.close()

    def get_completed_levels(self, user_id: str, team: str) -> List[Dict]:
        """Get list of completed levels for user+team"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT level, score FROM completed_levels 
            WHERE user_id = ? AND team = ?
            ORDER BY level ASC
        ''', (user_id, team))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{"level": row["level"], "score": row["score"]} for row in rows]

    def get_team_stats(self, user_id: str, team: str) -> Dict:
        """Get statistics for user+team combination"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT current_level, total_correct FROM quiz_progress 
            WHERE user_id = ? AND team = ?
        ''', (user_id, team))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                "highest_level_reached": row["current_level"],
                "total_correct_answers": row["total_correct"]
            }
        return {"highest_level_reached": 0, "total_correct_answers": 0}
    def add_quiz_attempt(self, user_id: str, team: str, difficulty: str, 
                         score: float, questions: Optional[List] = None, answers: Optional[List] = None):
        """Store quiz attempt"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO quiz_history 
            (user_id, team, difficulty, questions, answers, score)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, team, difficulty, json.dumps(questions or []), 
              json.dumps(answers or []), score))
        
        conn.commit()
        conn.close()

    def get_user_quiz_history(self, user_id: str) -> List[Dict]:
        """Get user's quiz history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM quiz_history 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        result = []
        for row in rows:
            # Extract level from difficulty string (e.g., "level_1" -> 1)
            difficulty_str = row["difficulty"]
            level = int(difficulty_str.replace("level_", "")) if "level_" in difficulty_str else 1
            
            result.append({
                "id": row["id"],
                "team": row["team"],
                "level": level,
                "score": row["score"],
                "accuracy": int(round(row["score"])) if row["score"] else 0,
                "correct": int(round(row["score"] / 10)) if row["score"] else 0,
                "total": 5,
                "created_at": row["created_at"]
            })
        
        return result

    # Predictions
    def add_prediction(self, user_id: str, team1: str, team2: str, 
                       predicted_winner: str, predicted_score: str, explanation: str):
        """Store a user prediction"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO predictions 
            (user_id, team1, team2, predicted_winner, predicted_score, explanation)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, team1, team2, predicted_winner, predicted_score, explanation))
        
        conn.commit()
        pred_id = cursor.lastrowid
        conn.close()
        
        return pred_id

    def get_user_predictions(self, user_id: str) -> List[Dict]:
        """Get user's predictions"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM predictions 
            WHERE user_id = ? 
            ORDER BY created_at DESC
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "id": row["id"],
            "team1": row["team1"],
            "team2": row["team2"],
            "predicted_winner": row["predicted_winner"],
            "predicted_score": row["predicted_score"],
            "created_at": row["created_at"],
            "actual_outcome": row["actual_outcome"],
            "points_earned": row["points_earned"]
        } for row in rows]

    # Chat History
    def add_chat_message(self, user_id: str, message: str, response: str, tool_used: Optional[str] = None):
        """Store chat message and response"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO chat_history 
            (user_id, message, response, tool_used)
            VALUES (?, ?, ?, ?)
        ''', (user_id, message, response, tool_used))
        
        conn.commit()
        conn.close()

    def get_user_chat_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Get recent chat history for a user (for context)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT message, response FROM chat_history 
            WHERE user_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        # Reverse to get chronological order
        return [{"user": row["message"], "assistant": row["response"]} 
                for row in reversed(rows)]

    # Leaderboard
    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get top users by points"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, total_points, favorite_team 
            FROM users 
            ORDER BY total_points DESC 
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [{
            "rank": idx + 1,
            "user_id": row["user_id"],
            "username": row["username"],
            "points": row["total_points"],
            "team": row["favorite_team"]
        } for idx, row in enumerate(rows)]
    # Question tracking - prevent repeated questions
    def record_asked_question(self, user_id: str, team: str, question_id: str):
        """Record that a question was asked to a user for a team"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO asked_questions (user_id, team, question_id)
                VALUES (?, ?, ?)
            ''', (user_id, team, question_id))
            conn.commit()
        except sqlite3.IntegrityError:
            # Question already recorded, ignore
            pass
        finally:
            conn.close()

    def get_asked_questions(self, user_id: str, team: str) -> List[str]:
        """Get all question IDs that have been asked to a user for a team"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT question_id FROM asked_questions
            WHERE user_id = ? AND team = ?
        ''', (user_id, team))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [row["question_id"] for row in rows]

    def reset_asked_questions(self, user_id: str, team: str):
        """Reset the asked questions for a user + team (with confirmation from user)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM asked_questions
            WHERE user_id = ? AND team = ?
        ''', (user_id, team))
        
        conn.commit()
        conn.close()

    # ===== Prediction Methods =====
    def save_prediction(self, user_id: str, team1: str, team2: str, user_prediction: str, 
                       system_outcome: str, points: int, explanation: str, sport: str = None) -> Dict:
        """Save a user's prediction and evaluation"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO predictions 
                (user_id, team1, team2, predicted_winner, predicted_score, actual_outcome, points_earned, explanation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, team1, team2, user_prediction, sport or '', system_outcome, points, explanation))
            
            # Update user points
            cursor.execute('''
                UPDATE users SET total_points = total_points + ?
                WHERE user_id = ?
            ''', (points, user_id))
            
            conn.commit()
            return {
                "success": True,
                "prediction_id": cursor.lastrowid,
                "points_earned": points
            }
        except Exception as e:
            conn.rollback()
            return {"success": False, "error": str(e)}
        finally:
            conn.close()
    
    def get_user_predictions(self, user_id: str, limit: int = 50) -> List[Dict]:
        """Get user's prediction history"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM predictions
            WHERE user_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        predictions = []
        for row in rows:
            predictions.append({
                'id': row['id'],
                'team1': row['team1'],
                'team2': row['team2'],
                'user_prediction': row['predicted_winner'],
                'system_outcome': row['actual_outcome'],
                'points_earned': row['points_earned'],
                'explanation': row['explanation'],
                'created_at': row['created_at'],
                'is_correct': row['predicted_winner'] == row['actual_outcome']
            })
        
        return predictions
    
    def get_prediction_stats(self, user_id: str) -> Dict:
        """Get user's prediction statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Get all predictions
        cursor.execute('''
            SELECT * FROM predictions
            WHERE user_id = ?
        ''', (user_id,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return {
                'total_predictions': 0,
                'correct_predictions': 0,
                'accuracy': 0,
                'total_points': 0,
                'average_points_per_prediction': 0
            }
        
        total = len(rows)
        correct = sum(1 for row in rows if row['predicted_winner'] == row['actual_outcome'])
        total_points = sum(row['points_earned'] for row in rows)
        accuracy = (correct / total * 100) if total > 0 else 0
        avg_points = total_points / total if total > 0 else 0
        
        return {
            'total_predictions': total,
            'correct_predictions': correct,
            'accuracy': round(accuracy, 2),
            'total_points': total_points,
            'average_points_per_prediction': round(avg_points, 2)
        }
        conn.close()