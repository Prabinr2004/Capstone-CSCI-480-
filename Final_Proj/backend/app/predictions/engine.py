"""
Prediction engine for sports outcomes.
Uses team ranking, recent form, history, and key players to generate predictions.
"""

import random
from datetime import datetime
from typing import Dict, Tuple

# Team data with rankings and key players
TEAM_RANKINGS = {
    # Soccer/Football Teams
    'Real Madrid': {'ranking': 1, 'strength': 95, 'recent_form': 8, 'key_players': ['Kylian Mbappe', 'Vinicius Jr.', 'Federico Valverde']},
    'Manchester City': {'ranking': 2, 'strength': 94, 'recent_form': 9, 'key_players': ['Erling Haaland', 'Ryan Cherki', 'John Stones']},
    'Barcelona': {'ranking': 3, 'strength': 92, 'recent_form': 8, 'key_players': ['Lewandowski', 'Pedri', 'Garcia']},
    'Liverpool': {'ranking': 4, 'strength': 91, 'recent_form': 8, 'key_players': ['Mohamed Salah', 'Hugo Ekitike', 'Virgil van Dijk']},
    'Bayern Munich': {'ranking': 5, 'strength': 90, 'recent_form': 8, 'key_players': ['Harry Kane', 'Joshua Kimmich', 'Manuel Neuer']},
    'Arsenal': {'ranking': 6, 'strength': 89, 'recent_form': 9, 'key_players': ['Bukayo Saka', 'Martinelli', 'Declan Rice']},
    'Juventus': {'ranking': 7, 'strength': 88, 'recent_form': 7, 'key_players': ['Juan Cuadrado', 'Alexis Sánchez', 'Gleison Bremer']},
    'Manchester United': {'ranking': 8, 'strength': 87, 'recent_form': 7, 'key_players': ['Bruno Fernandes', 'Bryan Mbeumo', 'Casemiro']},
    'Paris Saint-Germain': {'ranking': 9, 'strength': 86, 'recent_form': 8, 'key_players': ['Nuno Mendes', 'Ousmane Dembele', 'Vitinha']},
    'Inter Milan': {'ranking': 10, 'strength': 85, 'recent_form': 8, 'key_players': ['Lautaro Martínez', 'Nicolo Barella', 'Francesco Acerbi']},
    'Chelsea': {'ranking': 11, 'strength': 84, 'recent_form': 7, 'key_players': ['Cole Palmer', 'Moises Caicedo', 'Robert Sánchez']},
    'Atletico Madrid': {'ranking': 12, 'strength': 83, 'recent_form': 7, 'key_players': ['Giuliano Simeone', 'Julian Alvarez', 'Stefan Savic']},
    'Tottenham': {'ranking': 13, 'strength': 82, 'recent_form': 7, 'key_players': ['Richarlison ', 'Xavi Simons', 'Cristian Romero']},
    'Borussia Dortmund': {'ranking': 14, 'strength': 81, 'recent_form': 8, 'key_players': ['Jobe Bellingham', 'Karim Adeyemi', 'Gregor Kobel']},
    'Sevilla': {'ranking': 15, 'strength': 80, 'recent_form': 6, 'key_players': ['Jesús Navas', 'Rafa Mir', 'Lopetegui']},
    'Napoli': {'ranking': 16, 'strength': 79, 'recent_form': 7, 'key_players': ['Victor Osimhen', 'Matteo Politano', 'Kalidou Koulibaly']},
    'Villarreal': {'ranking': 17, 'strength': 78, 'recent_form': 6, 'key_players': ['Gerard Moreno', 'Samuel Chukwueze', 'Pau Torres']},
    'Valencia': {'ranking': 18, 'strength': 77, 'recent_form': 6, 'key_players': ['Hugo Duro', 'Vinícius Souza', 'Omar Alderete']},
    'Lecce': {'ranking': 19, 'strength': 76, 'recent_form': 5, 'key_players': ['Morten Hjulmand', 'Lameck Banda', 'Wladimiro Falcone']},
    'Brentford': {'ranking': 20, 'strength': 75, 'recent_form': 6, 'key_players': ['Mathias Jensen', 'Bryan Mbeumo', 'Mark Flekken']},
    
    # NBA Teams
    'Denver Nuggets': {'ranking': 1, 'strength': 96, 'recent_form': 9, 'key_players': ['Nikola Jokic', 'Jamal Murray', 'Michael Porter Jr.']},
    'Boston Celtics': {'ranking': 2, 'strength': 95, 'recent_form': 9, 'key_players': ['Jayson Tatum', 'Jaylen Brown', 'Derrick White']},
    'Los Angeles Lakers': {'ranking': 3, 'strength': 94, 'recent_form': 8, 'key_players': ['Luka Doncic', 'LeBron James', 'Austin Reaves']},
    'Golden State Warriors': {'ranking': 4, 'strength': 92, 'recent_form': 8, 'key_players': ['Stephen Curry', 'Andrew Wiggins', 'Jonathan Kuminga']},
    'Phoenix Suns': {'ranking': 5, 'strength': 91, 'recent_form': 8, 'key_players': ['Kevin Durant', 'Devin Booker', 'Bradley Beal']},
    'Miami Heat': {'ranking': 6, 'strength': 89, 'recent_form': 7, 'key_players': ['Bam Adebayo', 'Tyler Herro', 'Jaime Jaquez Jr.']},
    'Dallas Mavericks': {'ranking': 7, 'strength': 88, 'recent_form': 5, 'key_players': ['Kyrie Irving', 'Anthony Davis', 'Klay Thompson']},
    'Milwaukee Bucks': {'ranking': 8, 'strength': 87, 'recent_form': 7, 'key_players': ['Giannis Antetokounmpo', 'Damian Lillard', 'Khris Middleton']},
    'New York Knicks': {'ranking': 9, 'strength': 86, 'recent_form': 7, 'key_players': ['Jalen Brunson', 'Karl-Anthony Towns', 'Josh Hart']},
    'Chicago Bulls': {'ranking': 10, 'strength': 85, 'recent_form': 6, 'key_players': ['Coby White', 'Josh Giddey', 'Zach LaVine']},
    
    # NFL Teams
    'Kansas City Chiefs': {'ranking': 1, 'strength': 95, 'recent_form': 9, 'key_players': ['Patrick Mahomes', 'Travis Kelce', 'Rashee Rice']},
    'San Francisco 49ers': {'ranking': 2, 'strength': 94, 'recent_form': 8, 'key_players': ['Brock Purdy', 'Christian McCaffrey', 'George Kittle']},
    'Buffalo Bills': {'ranking': 3, 'strength': 93, 'recent_form': 8, 'key_players': ['Josh Allen', 'James Cook', 'Khalil Shakir']},
    'Detroit Lions': {'ranking': 4, 'strength': 92, 'recent_form': 8, 'key_players': ['Jared Goff', 'Amon-Ra St. Brown', 'Jahmyr Gibbs']},
    'Dallas Cowboys': {'ranking': 5, 'strength': 90, 'recent_form': 7, 'key_players': ['Dak Prescott', 'George Pickens', 'CeeDee Lamb']},
    'Green Bay Packers': {'ranking': 6, 'strength': 89, 'recent_form': 7, 'key_players': ['Jordan Love', 'Josh Jacobs', 'Jayden Reed']},
    'New England Patriots': {'ranking': 7, 'strength': 88, 'recent_form': 6, 'key_players': ['Drake Maye', 'Rhamondre Stevenson', 'Christian Gonzalez']},
    'Miami Dolphins': {'ranking': 8, 'strength': 87, 'recent_form': 8, 'key_players': ['Tua Tagovailoa', 'Tyreek Hill', 'Jaylen Waddle']},
    'Philadelphia Eagles': {'ranking': 9, 'strength': 86, 'recent_form': 7, 'key_players': ['Jalen Hurts', 'Saquon Barkley', 'A.J. Brown']},
    'Pittsburgh Steelers': {'ranking': 10, 'strength': 85, 'recent_form': 6, 'key_players': ['T.J. Watt', 'Jalen Ramsey', 'Najee Harris']},
}

class PredictionEngine:
    """Generates sports match predictions based on team data"""
    
    @staticmethod
    def generate_prediction(team1: str, team2: str, sport: str) -> Dict:
        """
        Generate a prediction for a match between two teams
        
        Args:
            team1: First team name
            team2: Second team name
            sport: Sport type (soccer, nba, nfl)
            
        Returns:
            Prediction dictionary with outcome and explanation
        """
        # Get team data
        t1_data = TEAM_RANKINGS.get(team1, {'ranking': 50, 'strength': 50, 'recent_form': 5, 'key_players': ['Player 1']})
        t2_data = TEAM_RANKINGS.get(team2, {'ranking': 50, 'strength': 50, 'recent_form': 5, 'key_players': ['Player 1']})
        
        # Calculate win probability
        t1_score = t1_data['strength'] * 0.6 + t1_data['recent_form'] * 5 + (100 - t1_data['ranking'])
        t2_score = t2_data['strength'] * 0.6 + t2_data['recent_form'] * 5 + (100 - t2_data['ranking'])
        
        total = t1_score + t2_score
        t1_win_prob = t1_score / total if total > 0 else 0.5
        
        # Determine outcome
        rand = random.random()
        if rand < t1_win_prob:
            winner = team1
            loser = team2
            confidence = int(t1_win_prob * 100)
        else:
            winner = team2
            loser = team1
            confidence = int((1 - t1_win_prob) * 100)
        
        # Generate explanation
        winner_data = TEAM_RANKINGS.get(winner, {})
        loser_data = TEAM_RANKINGS.get(loser, {})
        winner_strength = winner_data.get('strength', 50)
        loser_strength = loser_data.get('strength', 50)
        
        explanation = f"{winner} should win with {confidence}% confidence. "
        
        # Add reasoning based on strength difference
        if winner_strength > loser_strength + 10:
            explanation += f"Superior team strength ({winner_strength} vs {loser_strength}). "
        elif winner_data.get('recent_form', 5) > loser_data.get('recent_form', 5) + 1:
            explanation += f"Better recent form. "
        elif winner_data.get('ranking', 50) < loser_data.get('ranking', 50):
            explanation += f"Higher ranking ({winner_data.get('ranking')} vs {loser_data.get('ranking')}). "
        
        key_player = winner_data.get('key_players', ['Key Player'])[0]
        explanation += f"Key player {key_player} expected to perform well."
        
        return {
            'predicted_winner': winner,
            'predicted_loser': loser,
            'confidence': confidence,
            'explanation': explanation,
            'winner_strength': winner_strength,
            'loser_strength': loser_strength
        }
    
    @staticmethod
    def evaluate_prediction(user_prediction: str, system_outcome: str, sport: str) -> Tuple[bool, int]:
        """
        Evaluate if user prediction matches system outcome
        
        Args:
            user_prediction: User's predicted winner (team name or "Draw")
            system_outcome: System's predicted winner
            sport: Sport type
            
        Returns:
            (is_correct, points_awarded)
        """
        if sport == 'soccer':
            # In soccer, draws are possible
            if user_prediction == 'Draw':
                # Draws are harder to predict, award more points if correct
                is_correct = system_outcome == 'Draw'
                return (is_correct, 50 if is_correct else 0)
            else:
                is_correct = user_prediction == system_outcome
                return (is_correct, 30 if is_correct else 0)
        else:
            # NBA and NFL don't have draws
            is_correct = user_prediction == system_outcome
            return (is_correct, 25 if is_correct else 0)
