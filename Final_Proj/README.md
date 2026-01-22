# AI Fan Engagement Agent

A web-based application that allows sports fans to interact with an AI agent through chat, take quizzes, predict game outcomes, and earn points and badges.

## Features

- **Chat Interface**: Interact with an AI agent that uses tools to provide personalized responses
- **Quiz Generator**: AI-generated sports trivia questions with multiple difficulty levels
- **Prediction Engine**: AI-powered game outcome predictions
- **Fan Reward System**: Track points, badges, and leaderboard rankings
- **Long-Term Memory**: Persistent user profiles, quiz history, and predictions

## Project Structure

```
Final_Proj/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── agent/           # Agent logic
│   │   ├── tools/           # MCP tools
│   │   ├── memory/          # Database and storage
│   │   └── routes.py        # FastAPI routes
│   ├── data/                # SQLite database
│   └── requirements.txt
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── script.js
├── .env                     # Your API keys
└── README.md
```

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js (optional, for React frontend)
- OpenRouter API key

### Backend Setup

1. Clone the repository
2. Create a `.env` file from `.env.example`:
   ```bash
   cp .env.example .env
   ```
3. Add your OpenRouter API key to `.env`

4. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

5. Run the backend server:
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

### Frontend Setup

Open `frontend/index.html` in a browser or serve it with a simple HTTP server:
```bash
cd frontend
python -m http.server 8001
```

Access at `http://localhost:8001`

## API Endpoints

- `POST /api/chat` - Send a message to the AI agent
- `GET /api/user/<user_id>` - Get user profile
- `GET /api/leaderboard` - Get top performers
- `GET /api/quiz` - Get available quizzes
- `POST /api/quiz/submit` - Submit quiz answers

## Agent Behavior

The agent decides which action to take based on user input:
1. **Chat**: Answer general questions about sports
2. **Quiz Generation**: Create custom sports trivia
3. **Prediction**: Predict game outcomes
4. **Reward Tracking**: Update points and badges

## Tools Used

- **FastAPI**: Web framework
- **SQLite**: Persistent data storage
- **OpenRouter API**: LLM access
- **React/HTML/CSS**: Frontend UI

## Customization

Edit the following to customize:
- `SYSTEM_PROMPT` in `agent/agent.py` for agent behavior
- Teams and leagues in `memory/database.py`
- Reward values in `tools/reward_tracker.py`
