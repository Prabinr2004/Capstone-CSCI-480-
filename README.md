# Color Blender
Live Demo: (https://capstone-csci-480-1.onrender.com)

A simple Python web application built with Flask that uses the OpenRouter API to blend two colors and generate creative descriptions.

## Features

-  **Interactive Color Blending** - Enter two colors and get AI-generated blended color descriptions
-  **AI-Powered** - Uses OpenRouter API for creative, dynamic responses
-  **Modern Web UI** - Clean, responsive interface with beautiful gradient design
-  **Secure Configuration** - API key loaded from `.env` file (never commits secrets)
-  **Mobile Friendly** - Works great on desktop and mobile devices

## Requirements

- Python 3.8 or higher
- pip (Python package installer)
- OpenRouter API key (get one at [openrouter.ai](https://openrouter.ai))

## Setup

### 1. Clone the Repository
```bash
git clone https://github.com/prabinroka/Capstone-CSCI-480.git
cd Capstone-CSCI-480
```

### 2. Create a Virtual Environment
```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure API Key
Create a `.env` file in the project root:
```bash
cp .env.example .env
```

Edit `.env` and add your OpenRouter API key:
```
OPENROUTER_API_KEY=your_api_key_here
```

## How to Run Locally

```bash
python app.py
```

Then open your browser and go to: **http://localhost:5000**

### Example Usage

1. Enter "blue" as the first color
2. Enter "yellow" as the second color
3. Get: "Green. Like nature's perfect balance between sky and sun."

## Project Structure

```
.
├── app.py                  # Flask application server
├── main.py                 # Legacy CLI version
├── .env                    # Environment file (not tracked by git)
├── .gitignore             # Git ignore file
├── templates/
│   └── index.html         # HTML template with color blending form
├── static/
│   └── style.css          # CSS styling
└── README.md              # This file
```

## How It Works
1. User enters two colors on the web form
2. Flask sends a prompt to the OpenRouter API
3. AI generates a blended color description
4. Result is displayed dynamically on the page


