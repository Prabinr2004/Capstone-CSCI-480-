# Project Proposal: AI Fan Engagement Agent

## Overview

An agentic application where an LLM-based agent autonomously routes user requests to specialized tools. Users interact via a web interface to take adaptive quizzes, get game predictions, and track their progress on a leaderboard. The agent maintains long-term memory of user preferences and performance to personalize interactions.

## Use Case

**Users**: Sports fans who want to test knowledge, get game predictions, and compete on leaderboards through a single unified interface.

**Key Features**:
- Adaptive quiz generation (difficulty adjusts based on performance)
- Game outcome predictions with confidence scores
- Long-term user profiles with points and badges
- Leaderboard tracking and competitive engagement

## Architecture

**Components**:
1. **LLM Agent** (Claude via OpenRouter) - Routes requests to tools based on user intent
2. **Three MCP Tools**:
   - Quiz Generator: Creates adaptive questions based on difficulty
   - Prediction Engine: Analyzes team data and returns game predictions
   - Memory Manager: Stores user profiles, quiz history, predictions, and points
3. **Web UI** (HTML/CSS/JavaScript) - Chat interface + quiz interface + dashboard
4. **SQLite Database** - Persistent user data and conversation history

**Tool Integration**:
- Agent receives user message and memory context
- Determines which tool(s) to invoke
- Executes tool and formats response for user

## How It Works

**User Interaction Example 1**: "Quiz me on basketball"
1. Agent recognizes quiz intent from user input
2. Queries memory tool for user's basketball performance history
3. Calls quiz generator with difficulty level (e.g., "intermediate")
4. Returns 5 questions adapted to user's level

**User Interaction Example 2**: "Will the Lakers beat the Celtics?"
1. Agent detects prediction request
2. Calls prediction engine with team data
3. Memory tool logs prediction for tracking accuracy
4. Returns prediction with confidence score and reasoning

## Testing

**Test Coverage**:
- Tool functionality: Quiz generator creates valid questions, prediction engine handles edge cases, memory manager persists data
- Agent intent detection: Correctly routes requests to appropriate tools
- End-to-end flows: New user → quiz → points → leaderboard; user returns → agent recalls history
- Data persistence: User info survives application restart

**Success Metrics**:
- Agent correctly classifies intent 95%+ of time
- Quiz questions have 4 distinct valid options
- Memory tool enables reference to previous interactions 80%+ of the time

## Technical Stack

- **LLM**: Claude 3.5 Sonnet via OpenRouter API
- **Backend**: Python 3.8+, FastAPI
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript

## Deployment

- **Local**: Backend on `localhost:8000`, frontend on `localhost:8001`
- **Future**: Modal.com serverless deployment with $30 free credits

## Repository Structure

```
backend/app/
├── agent/agent.py              # LLM Agent logic
├── tools/
│   ├── quiz_generator.py       # Tool 1: Quiz generation
│   ├── prediction_engine.py    # Tool 2: Game predictions
│   └── reward_tracker.py       # Tool 3: Memory & rewards
├── memory/database.py          # SQLite operations
└── main.py                     # FastAPI setup

frontend/
├── index.html                  # Chat & quiz UI
├── styles.css                  # Styling
└── script.js                   # Client-side logic
```

**Q**: What if the prediction engine is inaccurate?
**A**: Inaccuracy drives engagement (users try to beat the system); tracking accuracy over time helps identify where the model needs improvement.


