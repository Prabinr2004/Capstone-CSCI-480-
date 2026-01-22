"""
Quiz Generator Tool - MCP Tool for generating sports trivia questions.
Generates team-specific questions with difficulty levels 1-10.
"""

import os
import json
import requests
import random
from typing import List, Dict
from pydantic import BaseModel

class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str

class QuizResult(BaseModel):
    team: str
    level: int  # Level 1-10
    questions: List[QuizQuestion]

class QuizGeneratorTool:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # All available teams organized by sport
        self.nba_teams = [
            "Los Angeles Lakers", "Boston Celtics", "Golden State Warriors", "Denver Nuggets",
            "Miami Heat", "Chicago Bulls", "New York Knicks", "Brooklyn Nets",
            "Philadelphia 76ers", "Toronto Raptors", "Cleveland Cavaliers", "Detroit Pistons",
            "Indiana Pacers", "Milwaukee Bucks", "Atlanta Hawks", "Charlotte Hornets",
            "Washington Wizards", "Orlando Magic", "San Antonio Spurs", "Dallas Mavericks",
            "Houston Rockets", "New Orleans Pelicans", "Memphis Grizzlies", "Minnesota Timberwolves",
            "Oklahoma City Thunder", "Portland Trail Blazers", "Sacramento Kings", 
            "Los Angeles Clippers", "Phoenix Suns", "Utah Jazz"
        ]
        
        self.nfl_teams = [
            "New England Patriots", "New York Jets", "Buffalo Bills", "Miami Dolphins",
            "Baltimore Ravens", "Pittsburgh Steelers", "Cleveland Browns", "Cincinnati Bengals",
            "Houston Texans", "Tennessee Titans", "Indianapolis Colts", "Jacksonville Jaguars",
            "Kansas City Chiefs", "Denver Broncos", "Los Angeles Chargers", "Las Vegas Raiders",
            "Dallas Cowboys", "Philadelphia Eagles", "Washington Commanders", "New York Giants",
            "Chicago Bears", "Detroit Lions", "Minnesota Vikings", "Green Bay Packers",
            "Tampa Bay Buccaneers", "Atlanta Falcons", "New Orleans Saints", "Carolina Panthers",
            "San Francisco 49ers", "Los Angeles Rams", "Seattle Seahawks", "Arizona Cardinals"
        ]
        
        self.soccer_teams = [
            # Premier League
            "Manchester United", "Liverpool", "Manchester City", "Arsenal", "Chelsea", 
            "Tottenham Hotspur", "Brighton & Hove Albion", "Newcastle United", "Aston Villa", 
            "West Ham United", "Leicester City", "Fulham", "Nottingham Forest", "Everton", 
            "Brentford", "Crystal Palace", "Wolverhampton Wanderers", "Bournemouth", 
            "Ipswich Town", "Southampton",
            # La Liga
            "Real Madrid", "Barcelona", "Atletico Madrid", "Valencia CF", "Real Sociedad",
            "Villarreal", "Real Betis", "Sevilla", "Celta Vigo", "Rayo Vallecano",
            # Serie A
            "Juventus", "AC Milan", "Inter Milan", "Napoli", "AS Roma", "Lazio",
            "Fiorentina", "Atalanta", "Torino", "Bologna",
            # Bundesliga
            "Bayern Munich", "Borussia Dortmund", "RB Leipzig", "Schalke 04", 
            "Eintracht Frankfurt", "Bayer Leverkusen", "VfB Stuttgart", "Werder Bremen",
            "Borussia Mönchengladbach", "Hoffenheim",
            # Ligue 1
            "Paris Saint-Germain", "AS Monaco", "Olympique Lyonnais", "Olympique Marseille",
            "Lille OSC", "RC Lens", "Rennes", "Nice", "Nantes"
        ]
        
        self.all_teams = self.nba_teams + self.nfl_teams + self.soccer_teams


    def generate_quiz(self, team: str, level: int = 1) -> QuizResult:
        """
        Generate a level-based quiz for a specific team.
        
        Args:
            team: Name of the sports team
            level: Quiz level 1-10 (1=easiest, 10=hardest, with 7 questions at level 10)
        
        Returns:
            QuizResult with level-appropriate questions
        """
        
        # Validate team exists
        if team not in self.all_teams:
            # Try to find similar team name
            team = self._find_closest_team(team)
        
        # Validate level
        if not 1 <= level <= 10:
            level = 1
        
        # Determine number of questions (Level 10 has 7 questions, others have 5)
        num_questions = 7 if level == 10 else 5
        
        # Try to generate via API first
        questions = self._generate_via_api(team, level, num_questions)
        
        # Fallback to predefined questions if API fails
        if not questions:
            questions = self._get_team_specific_questions(team, level, num_questions)
        
        return QuizResult(
            team=team,
            level=level,
            questions=questions
        )

    def _find_closest_team(self, team: str) -> str:
        """Find the closest matching team name"""
        team_lower = team.lower()
        for t in self.all_teams:
            if team_lower in t.lower() or t.lower() in team_lower:
                return t
        # Default to Lakers if no match found
        return "Los Angeles Lakers"

    def _generate_via_api(self, team: str, level: int, num_questions: int) -> List[QuizQuestion]:
        """Generate questions using OpenRouter API"""
        
        # Define difficulty description based on level
        difficulty_descriptions = {
            1: "very easy (basic team facts, well-known players, recent history)",
            2: "easy (basic stats, famous seasons, key players)",
            3: "easy-medium (specific statistics, playoff history, team records)",
            4: "medium (season statistics, championship years, notable performances)",
            5: "medium (obscure records, historical trades, specific game performances)",
            6: "medium-hard (detailed statistics, specific years and records, historical context)",
            7: "hard (obscure historical facts, specific player statistics, rare records)",
            8: "hard (very specific performances, detailed historical knowledge required)",
            9: "very hard (extremely specific records, rare game details, deep historical knowledge)",
            10: "expert (only for true superfans, requires extensive team knowledge)"
        }
        
        difficulty = difficulty_descriptions.get(level, "medium")
        
        prompt = f"""Generate {num_questions} sports trivia questions EXCLUSIVELY about {team}.

CRITICAL: Every single question must be about {team} ONLY. Do not include questions about other teams, other sports, or general knowledge. Every question must test knowledge specifically of {team}.

Difficulty level: Level {level} - {difficulty}

For Level {level}, ensure:
- Questions are progressively detailed for higher levels
- Level 1-3: Focus on basic facts, colors, stadium, famous players, recent achievements
- Level 4-6: Focus on statistics, specific seasons, championship records, playoff history  
- Level 7-10: Focus on obscure records, specific game performances, historical details, hidden facts

Return ONLY a valid JSON object with this structure (no markdown, no explanations):
{{
    "questions": [
        {{
            "question": "Question text ABOUT {team} ONLY?",
            "options": ["Option 1", "Option 2", "Option 3", "Option 4"],
            "correct_answer": "Correct option",
            "explanation": "Why this is correct"
        }}
    ]
}}

Make sure:
- The correct_answer is one of the options listed
- ALL {num_questions} questions are about {team} ONLY
- NO cross-team or general knowledge questions
- Options are plausible distractors
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
                    "temperature": 0.7,
                    "max_tokens": 2000
                },
                timeout=30
            )
            
            if response.status_code != 200:
                return None
            
            result = response.json()
            content = result["choices"][0]["message"]["content"]
            
            # Parse JSON from response
            quiz_data = json.loads(content)
            
            questions = [
                QuizQuestion(**q) for q in quiz_data["questions"]
            ]
            
            return questions
        
        except Exception as e:
            print(f"Error generating quiz via API for {team}: {e}")
            return None

    def _get_team_specific_questions(self, team: str, level: int, num_questions: int) -> List[QuizQuestion]:
        """
        Return predefined team-specific questions when API fails.
        This ensures NO cross-team questions ever appear.
        """
        
        # Comprehensive team-specific question database
        team_databases = self._build_team_databases()
        
        # Get questions for this specific team
        if team in team_databases:
            team_data = team_databases[team]
        else:
            # Default to Lakers if team not found - should never happen due to find_closest_team
            team_data = team_databases.get("Los Angeles Lakers", {})
        
        # Get questions for this level
        level_key = f"level_{level}"
        if level_key in team_data:
            available_questions = team_data[level_key]
        else:
            # Fallback to level 1 if level not found
            available_questions = team_data.get("level_1", [])
        
        # Shuffle and select the required number of questions
        shuffled = available_questions.copy()
        random.shuffle(shuffled)
        questions = shuffled[:num_questions]
        
        return questions

    def _build_team_databases(self) -> Dict[str, Dict]:
        """Build the complete team-specific question database"""
        
        # For brevity, showing sample structure - in production this would be much larger
        databases = {}
        
        # NBA Teams - Example for Lakers
        databases["Los Angeles Lakers"] = self._build_lakers_questions()
        databases["Boston Celtics"] = self._build_celtics_questions()
        
        # For all other teams, create basic fallback questions
        for team in self.all_teams:
            if team not in databases:
                databases[team] = self._build_generic_team_questions(team)
        
        return databases

    def _build_lakers_questions(self) -> Dict:
        """Build Lakers-specific questions for all 10 levels"""
        return {
            "level_1": [
                QuizQuestion(question="What color are the Lakers' primary jerseys?", 
                           options=["Purple", "Gold", "Black", "White"], 
                           correct_answer="Purple", 
                           explanation="The Lakers wear purple and gold jerseys."),
                QuizQuestion(question="What city do the Lakers play in?", 
                           options=["San Francisco", "Los Angeles", "Sacramento", "San Diego"], 
                           correct_answer="Los Angeles", 
                           explanation="The Lakers are based in Los Angeles, California."),
                QuizQuestion(question="What league do the Lakers play in?", 
                           options=["ABA", "WNBA", "NBA", "NBL"], 
                           correct_answer="NBA", 
                           explanation="The Lakers compete in the National Basketball Association (NBA)."),
                QuizQuestion(question="What is the Lakers' home arena called?", 
                           options=["Forum", "Staples Center", "Crypto.com Arena", "LA Coliseum"], 
                           correct_answer="Crypto.com Arena", 
                           explanation="The Lakers play at Crypto.com Arena (formerly Staples Center)."),
                QuizQuestion(question="What is the Lakers' main rival?", 
                           options=["Warriors", "Celtics", "Heat", "Spurs"], 
                           correct_answer="Celtics", 
                           explanation="The Boston Celtics are the Lakers' greatest rival."),
            ],
            "level_2": [
                QuizQuestion(question="How many NBA championships have the Lakers won?", 
                           options=["15", "17", "19", "21"], 
                           correct_answer="17", 
                           explanation="The Lakers have won 17 NBA championships."),
                QuizQuestion(question="Who was the coach during the 'Showtime' era?", 
                           options=["Pat Riley", "Mike Dunleavy", "Phil Jackson", "Byron Scott"], 
                           correct_answer="Pat Riley", 
                           explanation="Pat Riley coached the Lakers during their famous 'Showtime' era."),
                QuizQuestion(question="What year did the Lakers move to Los Angeles?", 
                           options=["1958", "1960", "1961", "1965"], 
                           correct_answer="1960", 
                           explanation="The Lakers relocated from Minneapolis to Los Angeles in 1960."),
                QuizQuestion(question="Which player scored 81 points in a single game?", 
                           options=["LeBron James", "Kobe Bryant", "Magic Johnson", "Kareem"], 
                           correct_answer="Kobe Bryant", 
                           explanation="Kobe Bryant scored 81 points against Toronto on January 22, 2006."),
                QuizQuestion(question="In what year did the Lakers win in the bubble?", 
                           options=["2019", "2020", "2021", "2022"], 
                           correct_answer="2020", 
                           explanation="The Lakers won the NBA championship in 2020 (in the bubble)."),
            ],
            "level_3": [
                QuizQuestion(question="How many consecutive championships did Lakers win in the 1980s?", 
                           options=["3", "5", "8", "10"], 
                           correct_answer="8", 
                           explanation="The Lakers went to 8 Finals in the 1980s, winning 5 championships."),
                QuizQuestion(question="Who holds the record for most points in Lakers history?", 
                           options=["Kobe Bryant", "Kareem Abdul-Jabbar", "Magic Johnson", "Jerry West"], 
                           correct_answer="Kareem Abdul-Jabbar", 
                           explanation="Kareem holds the record with 20,089 points for the Lakers."),
                QuizQuestion(question="What was Magic Johnson's position?", 
                           options=["Shooting Guard", "Point Guard", "Power Forward", "Center"], 
                           correct_answer="Point Guard", 
                           explanation="Magic Johnson was a legendary point guard for the Lakers."),
                QuizQuestion(question="How many MVPs did Kareem win with the Lakers?", 
                           options=["1", "3", "5", "7"], 
                           correct_answer="3", 
                           explanation="Kareem won 5 MVPs total, 3 of which were with the Lakers."),
                QuizQuestion(question="What is the name of the Lakers' mascot?", 
                           options=["Laker Leo", "Lake Show", "Lakers Lightning", "Golden Jerry"], 
                           correct_answer="Laker Leo", 
                           explanation="The Lakers' mascot is Laker Leo, a lion mascot."),
            ],
            "level_4": [
                QuizQuestion(question="How many three-peats (back-to-back-to-back championships) did the Lakers win?", 
                           options=["0", "1", "2", "3"], 
                           correct_answer="2", 
                           explanation="The Lakers won three-peats in 1980-82 and 2000-02."),
                QuizQuestion(question="Who won the Finals MVP in 2020 for the Lakers?", 
                           options=["Anthony Davis", "Kobe Bryant", "LeBron James", "Kyle Kuzma"], 
                           correct_answer="LeBron James", 
                           explanation="LeBron James won Finals MVP when the Lakers won in 2020."),
                QuizQuestion(question="What was the first year the Lakers won a championship?", 
                           options=["1949", "1952", "1954", "1957"], 
                           correct_answer="1949", 
                           explanation="The Lakers won their first championship in 1949 in Minneapolis."),
                QuizQuestion(question="How many times did the Lakers make the Finals consecutively in the 1980s?", 
                           options=["4", "6", "8", "10"], 
                           correct_answer="8", 
                           explanation="The Lakers made the Finals 8 consecutive years from 1980-1989."),
                QuizQuestion(question="Who was the backup point guard to Magic Johnson?", 
                           options=["Byron Scott", "Michael Cooper", "Norm Nixon", "Scott Byron"], 
                           correct_answer="Byron Scott", 
                           explanation="Byron Scott was the backup to Magic Johnson in the 1980s."),
            ],
            "level_5": [
                QuizQuestion(question="What was Kobe's highest scoring playoff performance?", 
                           options=["50", "62", "81", "80"], 
                           correct_answer="50", 
                           explanation="Kobe scored 50 points in a playoff game against the Nuggets in 2008."),
                QuizQuestion(question="In what year did Shaq and Kobe win their first championship together?", 
                           options=["1998", "1999", "2000", "2001"], 
                           correct_answer="2000", 
                           explanation="The Shaq-Kobe duo won their first championship in 2000."),
                QuizQuestion(question="How many championships did Shaq win with the Lakers?", 
                           options=["2", "3", "4", "5"], 
                           correct_answer="3", 
                           explanation="Shaq won 3 championships with the Lakers (2000, 2001, 2002)."),
                QuizQuestion(question="What was the highest scoring game by a Lakers player in the 2000s?", 
                           options=["73", "78", "81", "85"], 
                           correct_answer="81", 
                           explanation="Kobe's 81-point game in 2006 is the highest-scoring Lakers game."),
                QuizQuestion(question="How many times did Kobe win the MVP award?", 
                           options=["1", "2", "3", "4"], 
                           correct_answer="1", 
                           explanation="Kobe won the MVP award once in 2008."),
            ],
            "level_6": [
                QuizQuestion(question="What was the Lakers' record in the 1987 championship run?", 
                           options=["55-27", "57-25", "60-22", "65-17"], 
                           correct_answer="65-17", 
                           explanation="The 1987 Lakers had a record of 65-17 before winning the championship."),
                QuizQuestion(question="How many All-Star appearances did Kobe have?", 
                           options=["15", "17", "18", "19"], 
                           correct_answer="18", 
                           explanation="Kobe made 18 All-Star appearances during his career with the Lakers."),
                QuizQuestion(question="What year did Kobe retire?", 
                           options=["2014", "2015", "2016", "2017"], 
                           correct_answer="2016", 
                           explanation="Kobe retired after the 2015-16 season."),
                QuizQuestion(question="How many times did the Lakers win the championship before moving to LA?", 
                           options=["2", "3", "4", "5"], 
                           correct_answer="5", 
                           explanation="The Lakers won 5 championships in Minneapolis before moving to LA in 1960."),
                QuizQuestion(question="What was the Lakers' winning streak in 1972?", 
                           options=["25", "30", "33", "36"], 
                           correct_answer="33", 
                           explanation="The Lakers had a 33-game winning streak in 1972."),
            ],
            "level_7": [
                QuizQuestion(question="How many points did Kobe average in the 2005-06 season?", 
                           options=["32.4", "33.4", "34.4", "35.4"], 
                           correct_answer="35.4", 
                           explanation="Kobe averaged 35.4 points in the 2005-06 season."),
                QuizQuestion(question="What was Shaq's career high with the Lakers?", 
                           options=["60", "63", "65", "69"], 
                           correct_answer="61", 
                           explanation="Shaq's career high with the Lakers was 61 points."),
                QuizQuestion(question="In what year did Phil Jackson become Lakers coach?", 
                           options=["1997", "1998", "1999", "2000"], 
                           correct_answer="1999", 
                           explanation="Phil Jackson became Lakers coach in 1999."),
                QuizQuestion(question="How many championships did Phil Jackson win with the Lakers?", 
                           options=["3", "4", "5", "6"], 
                           correct_answer="5", 
                           explanation="Phil Jackson won 5 championships with the Lakers."),
                QuizQuestion(question="What was the Lakers' Finals appearance in 2008?", 
                           options=["Won", "Lost", "Didn't make it", "Forfeit"], 
                           correct_answer="Lost", 
                           explanation="The Lakers lost to the Celtics in the 2008 Finals."),
            ],
            "level_8": [
                QuizQuestion(question="How many points did Shaq average in his first season with the Lakers?", 
                           options=["18.9", "20.3", "21.7", "23.4"], 
                           correct_answer="21.7", 
                           explanation="Shaq averaged 21.7 points in his first season with the Lakers."),
                QuizQuestion(question="What was Kobe's jersey number before 24?", 
                           options=["8", "10", "12", "16"], 
                           correct_answer="8", 
                           explanation="Kobe wore number 8 before switching to 24 in 2006."),
                QuizQuestion(question="In what year did the Lakers draft Kobe?", 
                           options=["1994", "1995", "1996", "1997"], 
                           correct_answer="1996", 
                           explanation="The Lakers drafted Kobe Bryant in 1996."),
                QuizQuestion(question="How many consecutive Finals did the Lakers make in the 1980s starting from 1980?", 
                           options=["7", "8", "9", "10"], 
                           correct_answer="8", 
                           explanation="The Lakers made 8 consecutive Finals from 1980-1987."),
                QuizQuestion(question="What was Kareem's highest scoring season with the Lakers?", 
                           options=["27", "28", "29", "30"], 
                           correct_answer="27", 
                           explanation="Kareem's highest scoring season with the Lakers was 27.7 PPG."),
            ],
            "level_9": [
                QuizQuestion(question="How many total rebounds did Wilt Chamberlain grab in his 100-point game?", 
                           options=["23", "25", "27", "29"], 
                           correct_answer="25", 
                           explanation="Wilt had 25 rebounds in his famous 100-point game (but it was with Philadelphia)."),
                QuizQuestion(question="What was the Lakers' record in 1971-72 championship season?", 
                           options=["67-15", "68-14", "69-13", "70-12"], 
                           correct_answer="69-13", 
                           explanation="The 1971-72 Lakers had a 69-13 record before winning the championship."),
                QuizQuestion(question="How many assists did Magic Johnson average in the 1980s?", 
                           options=["10", "11", "12", "13"], 
                           correct_answer="11", 
                           explanation="Magic averaged approximately 11 assists per game in the 1980s."),
                QuizQuestion(question="What was the closest Finals series win for the Lakers?", 
                           options=["4-1", "4-2", "4-3", "They never played a close series"], 
                           correct_answer="4-3", 
                           explanation="The 1970 Finals against the Celtics went to 7 games."),
                QuizQuestion(question="How many games were in Lakers' 33-game winning streak?", 
                           options=["30", "32", "33", "35"], 
                           correct_answer="33", 
                           explanation="The Lakers' winning streak was 33 consecutive games in 1971-72."),
            ],
            "level_10": [
                QuizQuestion(question="What was Kareem Abdul-Jabbar's birth name?", 
                           options=["Alcindor Ferdinand", "Lew Alcindor Jr.", "Kareem Al-Hajj", "Cassius Clay Jr."], 
                           correct_answer="Lew Alcindor Jr.", 
                           explanation="Kareem Abdul-Jabbar was born Lewis Ferdinand Alcindor Jr."),
                QuizQuestion(question="In what year did the Lakers play their first game in LA?", 
                           options=["1960", "1961", "1962", "1963"], 
                           correct_answer="1960", 
                           explanation="The Lakers played their first game in Los Angeles in November 1960."),
                QuizQuestion(question="How many players from the 1972 championship team remain in Hall of Fame?", 
                           options=["2", "3", "4", "5"], 
                           correct_answer="4", 
                           explanation="Magic, Kareem, Jerry West, and Wilt are from that era in the Hall of Fame."),
                QuizQuestion(question="What was the exact score of Kobe's 81-point game?", 
                           options=["122-104", "122-105", "120-105", "123-105"], 
                           correct_answer="122-104", 
                           explanation="Kobe's 81-point game ended with the Lakers winning 122-104."),
                QuizQuestion(question="How many different head coaches have the Lakers had since 1960?", 
                           options=["8", "10", "12", "14"], 
                           correct_answer="14", 
                           explanation="The Lakers have had 14 different head coaches since moving to LA."),
                QuizQuestion(question="What was the Lakers' longest playoff drought?", 
                           options=["5 years", "7 years", "8 years", "10 years"], 
                           correct_answer="8 years", 
                           explanation="The Lakers had an 8-year playoff drought from 2012-2019."),
                QuizQuestion(question="How many times did the Lakers win the championship in the 1950s?", 
                           options=["2", "3", "4", "5"], 
                           correct_answer="5", 
                           explanation="The Lakers won 5 championships in the 1950s as the Minneapolis Lakers."),
            ]
        }

    def _build_celtics_questions(self) -> Dict:
        """Build Celtics-specific questions for all 10 levels"""
        return {
            "level_1": [
                QuizQuestion(question="What color are the Celtics associated with?", 
                           options=["Red", "Green", "Blue", "Gold"], 
                           correct_answer="Green", 
                           explanation="The Boston Celtics play in green and white."),
                QuizQuestion(question="Which city do the Celtics call home?", 
                           options=["New York", "Boston", "Philadelphia", "Washington"], 
                           correct_answer="Boston", 
                           explanation="The Celtics are based in Boston, Massachusetts."),
                QuizQuestion(question="What is the Celtics' home arena?", 
                           options=["Boston Garden", "Fleet Center", "TD Garden", "Boston Arena"], 
                           correct_answer="TD Garden", 
                           explanation="The Celtics play at TD Garden in downtown Boston."),
                QuizQuestion(question="What symbol is on the Celtics' logo?", 
                           options=["Four-leaf clover", "Shamrock", "Leprechaun", "Celtic cross"], 
                           correct_answer="Leprechaun", 
                           explanation="The Celtics' logo features a leprechaun named Lucky."),
                QuizQuestion(question="What year were the Celtics founded?", 
                           options=["1956", "1957", "1958", "1960"], 
                           correct_answer="1957", 
                           explanation="The Boston Celtics were founded in 1957."),
            ],
            "level_2": [
                QuizQuestion(question="How many NBA championships have the Celtics won?", 
                           options=["16", "17", "18", "19"], 
                           correct_answer="18", 
                           explanation="The Celtics have won 18 NBA championships."),
                QuizQuestion(question="Who is the legendary Celtics coach?", 
                           options=["Red Auerbach", "Bill Russell", "Tom Heinsohn", "Tommy Heinsohn"], 
                           correct_answer="Red Auerbach", 
                           explanation="Red Auerbach won 9 championships as Celtics coach."),
                QuizQuestion(question="What was the Celtics' famous dynasty in the 1960s?", 
                           options=["4 titles", "6 titles", "8 titles", "10 titles"], 
                           correct_answer="8 titles", 
                           explanation="The Celtics won 8 consecutive championships from 1959-1966."),
                QuizQuestion(question="Who is Bill Russell?", 
                           options=["Famous player", "Famous coach", "Both player and coach", "Owner"], 
                           correct_answer="Both player and coach", 
                           explanation="Bill Russell was a legendary player and coach for the Celtics."),
                QuizQuestion(question="What decade did the Celtics dominate?", 
                           options=["1950s", "1960s", "1970s", "1980s"], 
                           correct_answer="1960s", 
                           explanation="The Celtics dominated in the 1960s with 8 consecutive titles."),
            ],
            "level_3": [
                QuizQuestion(question="How many championships did Red Auerbach win?", 
                           options=["7", "8", "9", "10"], 
                           correct_answer="9", 
                           explanation="Red Auerbach won 9 NBA championships as the Celtics coach."),
                QuizQuestion(question="What is the Celtics' rivalry?", 
                           options=["Lakers", "Warriors", "Heat", "Nets"], 
                           correct_answer="Lakers", 
                           explanation="The Celtics-Lakers rivalry is one of the most famous in NBA history."),
                QuizQuestion(question="Who was the first Celtics champion player?", 
                           options=["Bill Russell", "Bob Cousy", "John Havlicek", "Sam Jones"], 
                           correct_answer="Bob Cousy", 
                           explanation="Bob Cousy was a key player on the 1957 championship team."),
                QuizQuestion(question="What year did the Celtics win their first championship?", 
                           options=["1954", "1956", "1957", "1959"], 
                           correct_answer="1957", 
                           explanation="The Celtics won their first NBA championship in 1957."),
                QuizQuestion(question="Who was the Celtics' most famous player in the 1980s?", 
                           options=["Magic Johnson", "Dominique Wilkins", "Larry Bird", "Julius Erving"], 
                           correct_answer="Larry Bird", 
                           explanation="Larry Bird was the star of the 1980s Celtics."),
            ],
            "level_4": [
                QuizQuestion(question="What was the 'Big Three' nickname?", 
                           options=["Tatum, Brown, Smart", "Durant, Kyrie, Harden", "Bird, McHale, Parrish", "Cousy, Havlicek, Russell"], 
                           correct_answer="Bird, McHale, Parrish", 
                           explanation="The 1980s Celtics' Big Three were Larry Bird, Kevin McHale, and Robert Parrish."),
                QuizQuestion(question="Who was the first African American head coach?", 
                           options=["Bill Russell", "Doc Rivers", "K.C. Jones", "Tom Heinsohn"], 
                           correct_answer="Bill Russell", 
                           explanation="Bill Russell became the first African American NBA head coach."),
                QuizQuestion(question="How many consecutive championships did the Celtics win?", 
                           options=["6", "7", "8", "9"], 
                           correct_answer="8", 
                           explanation="The Celtics won 8 consecutive championships from 1959-1966."),
                QuizQuestion(question="What championship did the Celtics win in 2024?", 
                           options=["None", "Their 18th", "Their 17th", "Didn't make Finals"], 
                           correct_answer="Their 18th", 
                           explanation="The Celtics won their 18th championship in 2024."),
                QuizQuestion(question="Who is Jayson Tatum?", 
                           options=["Guard", "Forward", "Center", "Coach"], 
                           correct_answer="Forward", 
                           explanation="Jayson Tatum is a forward for the Celtics."),
            ],
            "level_5": [
                QuizQuestion(question="How many MVP awards did Larry Bird win?", 
                           options=["1", "2", "3", "4"], 
                           correct_answer="3", 
                           explanation="Larry Bird won 3 NBA MVP awards."),
                QuizQuestion(question="What year did the Celtics win the 2008 championship?", 
                           options=["2006", "2007", "2008", "2009"], 
                           correct_answer="2008", 
                           explanation="The Celtics won the championship in 2008."),
                QuizQuestion(question="How many championships did Kevin McHale win?", 
                           options=["3", "4", "5", "6"], 
                           correct_answer="3", 
                           explanation="Kevin McHale won 3 championships with the Celtics."),
                QuizQuestion(question="What is the Celtics' famous motto?", 
                           options=["Go Celtics!", "Beat LA", "Green Pride", "Celtics Nation"], 
                           correct_answer="Celtics Nation", 
                           explanation="Celtics fans are part of 'Celtics Nation'."),
                QuizQuestion(question="How many league titles has Boston won?", 
                           options=["17", "18", "19", "20"], 
                           correct_answer="18", 
                           explanation="Boston has won 18 league titles (as of 2024)."),
            ],
            "level_6": [
                QuizQuestion(question="When did John Havlicek retire?", 
                           options=["1977", "1979", "1980", "1982"], 
                           correct_answer="1979", 
                           explanation="John Havlicek retired in 1979."),
                QuizQuestion(question="How many times did the Celtics beat the Lakers in Finals?", 
                           options=["5", "6", "7", "8"], 
                           correct_answer="7", 
                           explanation="The Celtics beat the Lakers 7 times in the Finals."),
                QuizQuestion(question="What year did the Celtics move to TD Garden?", 
                           options=["1993", "1995", "1997", "1999"], 
                           correct_answer="1995", 
                           explanation="The Celtics moved to Fleet Center (now TD Garden) in 1995."),
                QuizQuestion(question="How many consecutive Finals appearances in 1960s?", 
                           options=["9", "10", "11", "12"], 
                           correct_answer="10", 
                           explanation="The Celtics made 10 consecutive Finals from 1957-1966."),
                QuizQuestion(question="Who is the current Celtics head coach?", 
                           options=["Brad Stevens", "Joe Mazzulla", "Doc Rivers", "Ime Udoka"], 
                           correct_answer="Joe Mazzulla", 
                           explanation="Joe Mazzulla is the current head coach of the Boston Celtics."),
            ],
            "level_7": [
                QuizQuestion(question="How many times did the Celtics win 60+ games?", 
                           options=["8", "10", "12", "14"], 
                           correct_answer="14", 
                           explanation="The Celtics have had 14 seasons with 60 or more wins."),
                QuizQuestion(question="What was Sam Jones' role on the Celtics?", 
                           options=["Point Guard", "Shooting Guard", "Small Forward", "Power Forward"], 
                           correct_answer="Shooting Guard", 
                           explanation="Sam Jones was a shooting guard for the Celtics in the 1960s."),
                QuizQuestion(question="How many seasons did Bill Russell play?", 
                           options=["10", "12", "13", "15"], 
                           correct_answer="13", 
                           explanation="Bill Russell played 13 seasons for the Celtics."),
                QuizQuestion(question="What year did Tommy Heinsohn become coach?", 
                           options=["1968", "1969", "1970", "1971"], 
                           correct_answer="1969", 
                           explanation="Tommy Heinsohn became Celtics coach in 1969."),
                QuizQuestion(question="How many Finals MVPs did Bill Russell win?", 
                           options=["7", "8", "9", "10"], 
                           correct_answer="8", 
                           explanation="Bill Russell won 8 Finals MVPs with the Celtics."),
            ],
            "level_8": [
                QuizQuestion(question="What was Larry Bird's career high with the Celtics?", 
                           options=["50", "53", "60", "63"], 
                           correct_answer="60", 
                           explanation="Larry Bird scored 60 points in a game against the Hawks in 1985."),
                QuizQuestion(question="How many rebounds did Bill Russell average?", 
                           options=["13", "14", "15", "16"], 
                           correct_answer="13", 
                           explanation="Bill Russell averaged 13 rebounds per game."),
                QuizQuestion(question="What year did the Celtics draft Larry Bird?", 
                           options=["1977", "1978", "1979", "1980"], 
                           correct_answer="1978", 
                           explanation="The Celtics drafted Larry Bird in 1978."),
                QuizQuestion(question="How many total wins do the Celtics have in franchise history?", 
                           options=["3000+", "3200+", "3400+", "3600+"], 
                           correct_answer="3400+", 
                           explanation="The Celtics have over 3400 total wins in franchise history."),
                QuizQuestion(question="What was the Celtics' longest winning streak?", 
                           options=["18", "20", "22", "24"], 
                           correct_answer="18", 
                           explanation="The Celtics' longest winning streak was 18 games."),
            ],
            "level_9": [
                QuizQuestion(question="How many assists per game did Bob Cousy average?", 
                           options=["7", "8", "9", "10"], 
                           correct_answer="7", 
                           explanation="Bob Cousy averaged 7.5 assists per game for the Celtics."),
                QuizQuestion(question="What position did K.C. Jones play?", 
                           options=["Point Guard", "Shooting Guard", "Small Forward", "Power Forward"], 
                           correct_answer="Point Guard", 
                           explanation="K.C. Jones was a point guard for the Celtics."),
                QuizQuestion(question="How many blocks per game did Bill Russell average?", 
                           options=["3", "4", "5", "6"], 
                           correct_answer="4", 
                           explanation="Bill Russell averaged about 4 blocks per game (unofficial stat)."),
                QuizQuestion(question="What year did Jo Jo White become a star?", 
                           options=["1969", "1970", "1971", "1972"], 
                           correct_answer="1970", 
                           explanation="Jo Jo White became a star in the early 1970s for the Celtics."),
                QuizQuestion(question="How many Finals did the 1980 Celtics make?", 
                           options=["Made Finals", "Lost in Finals", "Lost in Eastern Finals", "Made Conference Finals"], 
                           correct_answer="Made Finals", 
                           explanation="The 1980 Celtics made the Finals and beat the Lakers."),
            ],
            "level_10": [
                QuizQuestion(question="What was Bob Cousy's birth name?", 
                           options=["Robert Joseph Cousy", "Robert Jean Cousy", "Roberto Cousiello", "Robert Carl Cousy"], 
                           correct_answer="Robert Joseph Cousy", 
                           explanation="Bob Cousy's full name was Robert Joseph Cousy."),
                QuizQuestion(question="How many consecutive playoff appearances?", 
                           options=["10", "15", "20", "25"], 
                           correct_answer="20", 
                           explanation="The Celtics made the playoffs 20 consecutive seasons from 1957-1977."),
                QuizQuestion(question="What was the Celtics' winning percentage in 1960s?", 
                           options=["650", "680", "700", "720"], 
                           correct_answer="680", 
                           explanation="The Celtics had a winning percentage around 680 (68%) in the 1960s."),
                QuizQuestion(question="How many games did the Celtics win in 1972-73?", 
                           options=["56", "58", "60", "62"], 
                           correct_answer="60", 
                           explanation="The Celtics won 60 games in the 1972-73 season."),
                QuizQuestion(question="What year did the Celtics have their longest playoff streak?", 
                           options=["1968", "1969", "1970", "1977"], 
                           correct_answer="1977", 
                           explanation="The Celtics' playoff streak ended in 1978 after 20 consecutive appearances."),
                QuizQuestion(question="How many players from original Celtics in Hall of Fame?", 
                           options=["6", "7", "8", "9"], 
                           correct_answer="7", 
                           explanation="7 players from the original Celtics dynasty are in the Hall of Fame."),
                QuizQuestion(question="What was Red Auerbach's total wins as coach?", 
                           options=["938", "948", "958", "968"], 
                           correct_answer="938", 
                           explanation="Red Auerbach had 938 wins as the Celtics coach."),
            ]
        }

    def _build_generic_team_questions(self, team: str) -> Dict:
        """Build generic fallback questions for any team not in the database"""
        
        # Determine sport based on team list
        if team in self.nba_teams:
            sport = "NBA basketball"
            league = "NBA"
        elif team in self.nfl_teams:
            sport = "NFL football"
            league = "NFL"
        else:
            sport = "soccer"
            league = "soccer league"
        
        return {
            "level_1": [
                QuizQuestion(question=f"What is {team}'s primary sport?", 
                           options=[sport, "Different sport", "Unknown", "Retired"], 
                           correct_answer=sport, 
                           explanation=f"{team} plays {sport}."),
                QuizQuestion(question=f"What league does {team} play in?", 
                           options=[league, "Different league", "Independent", "Not applicable"], 
                           correct_answer=league, 
                           explanation=f"{team} competes in the {league}."),
                QuizQuestion(question=f"Is {team} a professional team?", 
                           options=["Yes", "No", "Semi-professional", "Amateur"], 
                           correct_answer="Yes", 
                           explanation=f"{team} is a professional sports team."),
                QuizQuestion(question=f"What type of sport does {team} play?", 
                           options=["Team sport", "Individual sport", "Both", "Neither"], 
                           correct_answer="Team sport", 
                           explanation=f"{team} plays a team sport."),
                QuizQuestion(question=f"Is {team} a well-known franchise?", 
                           options=["Yes", "No", "Recently founded", "Folded"], 
                           correct_answer="Yes", 
                           explanation=f"{team} is a well-established sports franchise."),
            ],
            "level_2": [
                QuizQuestion(question=f"What is a basic fact about {team}?", 
                           options=["They are competitive", "They are new", "They are retired", "None of these"], 
                           correct_answer="They are competitive", 
                           explanation=f"{team} is an active, competitive team."),
                QuizQuestion(question=f"How many players are on a {team} roster typically?", 
                           options=["15-20", "25-30", "30-50", "Varies by sport"], 
                           correct_answer="Varies by sport", 
                           explanation=f"Roster size varies depending on the sport."),
                QuizQuestion(question=f"Is {team} based in a major city?", 
                           options=["Yes", "No", "Small town", "Unknown"], 
                           correct_answer="Yes", 
                           explanation=f"{team} is based in a major metropolitan area."),
                QuizQuestion(question=f"When was {team} founded?", 
                           options=["20th century", "21st century", "19th century", "Unknown"], 
                           correct_answer="20th century", 
                           explanation=f"{team} was founded in the 20th century."),
                QuizQuestion(question=f"Has {team} won championships?", 
                           options=["Yes", "No", "Debatable", "Unknown"], 
                           correct_answer="Yes", 
                           explanation=f"{team} has a history of championship success."),
            ],
            "level_3": [
                QuizQuestion(question=f"What colors does {team} wear?", 
                           options=["Official team colors", "Rainbow", "Monochrome", "Varies yearly"], 
                           correct_answer="Official team colors", 
                           explanation=f"{team} has official team colors that they wear in all matches."),
                QuizQuestion(question=f"Does {team} have a home stadium/arena?", 
                           options=["Yes", "No", "Multiple venues", "Traveling team"], 
                           correct_answer="Yes", 
                           explanation=f"{team} has a designated home venue."),
                QuizQuestion(question=f"Is {team} part of a larger organization?", 
                           options=["Yes", "No", "Sometimes", "Unclear"], 
                           correct_answer="Yes", 
                           explanation=f"{team} is part of a professional league organization."),
                QuizQuestion(question=f"Do fans support {team}?", 
                           options=["Yes", "No", "Mixed", "Unknown"], 
                           correct_answer="Yes", 
                           explanation=f"{team} has a dedicated fan base."),
                QuizQuestion(question=f"Is {team} competitive?", 
                           options=["Often", "Rarely", "Never", "Varies yearly"], 
                           correct_answer="Varies yearly", 
                           explanation=f"{team}'s competitiveness varies from season to season."),
            ],
            "level_4": [
                QuizQuestion(question=f"What is a notable achievement of {team}?", 
                           options=["Championship wins", "Hall of Fame players", "Historical records", "All of these"], 
                           correct_answer="All of these", 
                           explanation=f"{team} has multiple notable achievements in their history."),
                QuizQuestion(question=f"How long has {team} been active?", 
                           options=["Decades", "Centuries", "Years", "Months"], 
                           correct_answer="Decades", 
                           explanation=f"{team} has been active for multiple decades."),
                QuizQuestion(question=f"Is {team} known internationally?", 
                           options=["Yes", "No", "In some regions", "Rarely"], 
                           correct_answer="Yes", 
                           explanation=f"{team} has international recognition."),
                QuizQuestion(question=f"What is {team}'s fan base like?", 
                           options=["Large and passionate", "Small", "Non-existent", "Growing"], 
                           correct_answer="Large and passionate", 
                           explanation=f"{team} has a large and passionate fan base."),
                QuizQuestion(question=f"Does {team} have rivalries?", 
                           options=["Yes", "No", "Minor", "Unknown"], 
                           correct_answer="Yes", 
                           explanation=f"{team} has established rivalries with other teams."),
            ],
            "level_5": [
                QuizQuestion(question=f"What makes {team} unique?", 
                           options=["Rich history", "Great players", "Stadium", "All of these"], 
                           correct_answer="All of these", 
                           explanation=f"{team} is unique for multiple reasons."),
                QuizQuestion(question=f"Has {team} had famous coaches?", 
                           options=["Yes", "No", "Maybe", "Rarely"], 
                           correct_answer="Yes", 
                           explanation=f"{team} has had notable coaches throughout their history."),
                QuizQuestion(question=f"Does {team} invest in talent?", 
                           options=["Yes", "No", "Moderately", "Unknown"], 
                           correct_answer="Yes", 
                           explanation=f"{team} invests in player development and recruitment."),
                QuizQuestion(question=f"What is {team}'s winning culture?", 
                           options=["Strong", "Weak", "Rebuilding", "Varies"], 
                           correct_answer="Strong", 
                           explanation=f"{team} has a strong winning culture."),
                QuizQuestion(question=f"Has {team} produced Hall of Famers?", 
                           options=["Yes", "No", "Possibly", "Unknown"], 
                           correct_answer="Yes", 
                           explanation=f"{team} has produced Hall of Fame caliber players."),
            ],
            "level_6": [
                QuizQuestion(question=f"What era was {team}'s greatest success?", 
                           options=["Past", "Recent", "Ongoing", "Unknown"], 
                           correct_answer="Past", 
                           explanation=f"{team} had significant success in past eras."),
                QuizQuestion(question=f"Does {team} have fierce competitors?", 
                           options=["Yes", "No", "Sometimes", "Rarely"], 
                           correct_answer="Yes", 
                           explanation=f"{team} competes against fierce rivals."),
                QuizQuestion(question=f"What is {team}'s playing style?", 
                           options=["Offensive", "Defensive", "Balanced", "Varied"], 
                           correct_answer="Balanced", 
                           explanation=f"{team} employs a balanced playing style."),
                QuizQuestion(question=f"Has {team} experienced rebuilding phases?", 
                           options=["Yes", "No", "Recently", "Never"], 
                           correct_answer="Yes", 
                           explanation=f"{team} has gone through rebuild phases like most franchises."),
                QuizQuestion(question=f"What is {team}'s modern roster like?", 
                           options=["Competitive", "Struggling", "Star-studded", "Average"], 
                           correct_answer="Competitive", 
                           explanation=f"{team} maintains a competitive roster in modern times."),
            ],
            "level_7": [
                QuizQuestion(question=f"What are {team}'s training facilities like?", 
                           options=["State-of-the-art", "Adequate", "Outdated", "Minimal"], 
                           correct_answer="State-of-the-art", 
                           explanation=f"{team} has modern, state-of-the-art training facilities."),
                QuizQuestion(question=f"How does {team} scout talent?", 
                           options=["Advanced analytics", "Traditional methods", "Both", "Unknown"], 
                           correct_answer="Both", 
                           explanation=f"{team} uses both traditional and analytics-based scouting."),
                QuizQuestion(question=f"What is {team}'s injury management like?", 
                           options=["Excellent", "Good", "Average", "Poor"], 
                           correct_answer="Good", 
                           explanation=f"{team} has solid injury management and medical staff."),
                QuizQuestion(question=f"Does {team} have youth development?", 
                           options=["Yes", "No", "Limited", "Excellent"], 
                           correct_answer="Yes", 
                           explanation=f"{team} invests in youth development programs."),
                QuizQuestion(question=f"What is {team}'s coaching philosophy?", 
                           options=["Aggressive", "Conservative", "Adaptive", "Rigid"], 
                           correct_answer="Adaptive", 
                           explanation=f"{team}'s coaching staff employs adaptive strategies."),
            ],
            "level_8": [
                QuizQuestion(question=f"How does {team} handle player retention?", 
                           options=["Very well", "Adequately", "Poorly", "Inconsistently"], 
                           correct_answer="Very well", 
                           explanation=f"{team} successfully retains core players."),
                QuizQuestion(question=f"What is {team}'s draft history?", 
                           options=["Strong", "Average", "Weak", "Varied"], 
                           correct_answer="Strong", 
                           explanation=f"{team} has a strong track record in the draft."),
                QuizQuestion(question=f"Does {team} make smart trades?", 
                           options=["Usually", "Sometimes", "Rarely", "Never"], 
                           correct_answer="Usually", 
                           explanation=f"{team} generally executes smart trades."),
                QuizQuestion(question=f"What is {team}'s financial situation?", 
                           options=["Strong", "Stable", "Struggling", "Unclear"], 
                           correct_answer="Strong", 
                           explanation=f"{team} has strong financial backing."),
                QuizQuestion(question=f"How competitive is {team} recently?", 
                           options=["Very", "Moderately", "Slightly", "Not at all"], 
                           correct_answer="Very", 
                           explanation=f"{team} remains very competitive in recent seasons."),
            ],
            "level_9": [
                QuizQuestion(question=f"What is {team}'s playoff history?", 
                           options=["Frequent appearances", "Occasional", "Rare", "Never"], 
                           correct_answer="Frequent appearances", 
                           explanation=f"{team} frequently makes playoff appearances."),
                QuizQuestion(question=f"How many titles has {{team}} won?", 
                           options=["Multiple", "One", "None", "Unknown"], 
                           correct_answer="Multiple", 
                           explanation=f"{team} has won multiple championships."),
                QuizQuestion(question=f"What is {{team}}'s legacy?", 
                           options=["Historic", "Notable", "Growing", "Uncertain"], 
                           correct_answer="Historic", 
                           explanation=f"{team} has a historic legacy in their sport."),
                QuizQuestion(question=f"Does {{team}} invest in analytics?", 
                           options=["Yes", "No", "Recently", "Minimally"], 
                           correct_answer="Yes", 
                           explanation=f"{team} invests heavily in sports analytics."),
                QuizQuestion(question=f"What is {{team}}'s community impact?", 
                           options=["Significant", "Moderate", "Minor", "Unknown"], 
                           correct_answer="Significant", 
                           explanation=f"{team} has significant community impact."),
            ],
            "level_10": [
                QuizQuestion(question=f"What deep lore exists about {{team}}?", 
                           options=["Rich history", "Unknown origins", "Recent founding", "Controversial past"], 
                           correct_answer="Rich history", 
                           explanation=f"{team} has a rich and storied history."),
                QuizQuestion(question=f"What makes {{team}} an institution?", 
                           options=["Tradition", "Excellence", "Stability", "All of above"], 
                           correct_answer="All of above", 
                           explanation=f"{team} is an institution due to tradition, excellence, and stability."),
                QuizQuestion(question=f"How many generations support {{team}}?", 
                           options=["Multiple", "Few", "One", "Unclear"], 
                           correct_answer="Multiple", 
                           explanation=f"Multiple generations of families support {team}."),
                QuizQuestion(question=f"What obscure fact about {{team}}?", 
                           options=["Historic achievement", "Unique tradition", "Hidden record", "Lesser known title"], 
                           correct_answer="Historic achievement", 
                           explanation=f"{team} has historic achievements that are well-documented."),
                QuizQuestion(question=f"How does {{team}} inspire?", 
                           options=["Through excellence", "Through story", "Through players", "Through tradition"], 
                           correct_answer="Through excellence", 
                           explanation=f"{team} inspires through their pursuit of excellence."),
                QuizQuestion(question=f"What is {{team}}'s future outlook?", 
                           options=["Bright", "Uncertain", "Challenging", "Rebuilding"], 
                           correct_answer="Bright", 
                           explanation=f"{team} has a bright future with strong fundamentals."),
                QuizQuestion(question=f"What defines {{team}} franchise?", 
                           options=["Winning culture", "Player development", "Stability", "All of these"], 
                           correct_answer="All of these", 
                           explanation=f"{team} is defined by winning culture, development, and stability."),
            ]
        }
        return databases

