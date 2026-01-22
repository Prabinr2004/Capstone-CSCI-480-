"""
Prediction Engine Tool - MCP Tool for predicting game outcomes.
Uses OpenRouter API with team statistics to make informed predictions.
"""

import requests
import json
from typing import Dict
from pydantic import BaseModel

class PredictionResult(BaseModel):
    team1: str
    team2: str
    predicted_winner: str
    predicted_score: str
    explanation: str
    confidence: float  # 0.0 to 1.0

class PredictionEngineTool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Sample team stats for context (would be fetched from real APIs in production)
        self.team_stats = {
            "Los Angeles Lakers": {"avg_points": 115.2, "avg_allowed": 110.5, "win_rate": 0.62},
            "Boston Celtics": {"avg_points": 116.8, "avg_allowed": 108.3, "win_rate": 0.68},
            "Golden State Warriors": {"avg_points": 114.5, "avg_allowed": 109.2, "win_rate": 0.59},
            "Denver Nuggets": {"avg_points": 117.3, "avg_allowed": 111.8, "win_rate": 0.65},
            "Miami Heat": {"avg_points": 111.2, "avg_allowed": 107.9, "win_rate": 0.58},
            "New England Patriots": {"avg_points": 26.3, "avg_allowed": 21.5, "win_rate": 0.65},
            "Dallas Cowboys": {"avg_points": 27.1, "avg_allowed": 22.3, "win_rate": 0.58},
            "New York Yankees": {"runs_per_game": 4.8, "era": 3.92, "win_rate": 0.56},
            "Los Angeles Dodgers": {"runs_per_game": 5.2, "era": 3.45, "win_rate": 0.62},
        }

    def predict_outcome(self, team1: str, team2: str) -> PredictionResult:
        """
        Predict the outcome of a match between two teams.
        
        Args:
            team1: First team name
            team2: Second team name
        
        Returns:
            PredictionResult with prediction, score, and explanation
        """
        
        # Get team stats (or use defaults)
        stats1 = self.team_stats.get(team1, {"avg_points": 110, "avg_allowed": 110, "win_rate": 0.50})
        stats2 = self.team_stats.get(team2, {"avg_points": 110, "avg_allowed": 110, "win_rate": 0.50})
        
        prompt = f"""Predict the outcome of a sports match between {team1} and {team2}.

Team 1 ({team1}) stats:
- Average points/goals scored: {stats1.get('avg_points', 'N/A')}
- Average points/goals allowed: {stats1.get('avg_allowed', 'N/A')}
- Recent win rate: {stats1.get('win_rate', 0.50) * 100:.1f}%

Team 2 ({team2}) stats:
- Average points/goals scored: {stats2.get('avg_points', 'N/A')}
- Average points/goals allowed: {stats2.get('avg_allowed', 'N/A')}
- Recent win rate: {stats2.get('win_rate', 0.50) * 100:.1f}%

Based on these stats, provide your prediction in this exact JSON format (no markdown):
{{
    "predicted_winner": "{team1} or {team2}",
    "predicted_score": "XX-YY",
    "explanation": "Brief explanation of prediction",
    "confidence": 0.75
}}

The confidence should be between 0.0 and 1.0 based on how clear the prediction is.
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
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.5
                }
            )
            
            if response.status_code != 200:
                return self._get_default_prediction(team1, team2, stats1, stats2)
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            prediction_data = json.loads(content)
            
            return PredictionResult(
                team1=team1,
                team2=team2,
                predicted_winner=prediction_data.get("predicted_winner", team1),
                predicted_score=prediction_data.get("predicted_score", "110-105"),
                explanation=prediction_data.get("explanation", "Based on team statistics"),
                confidence=float(prediction_data.get("confidence", 0.65))
            )
        
        except Exception as e:
            print(f"Error making prediction: {e}")
            return self._get_default_prediction(team1, team2, stats1, stats2)

    def _get_default_prediction(self, team1: str, team2: str, 
                               stats1: Dict, stats2: Dict) -> PredictionResult:
        """Generate prediction based on simple stats analysis when API fails"""
        
        # Simple logic: team with higher win rate should win
        team1_strength = stats1.get('win_rate', 0.50) * stats1.get('avg_points', 110)
        team2_strength = stats2.get('win_rate', 0.50) * stats2.get('avg_points', 110)
        
        if team1_strength > team2_strength:
            winner = team1
            team1_score = int(stats1.get('avg_points', 110))
            team2_score = int(stats2.get('avg_points', 110) - 3)
            confidence = 0.65
        else:
            winner = team2
            team1_score = int(stats1.get('avg_points', 110) - 3)
            team2_score = int(stats2.get('avg_points', 110))
            confidence = 0.65
        
        return PredictionResult(
            team1=team1,
            team2=team2,
            predicted_winner=winner,
            predicted_score=f"{team1_score}-{team2_score}",
            explanation=f"{winner} has a stronger offensive record and better recent performance.",
            confidence=confidence
        )
