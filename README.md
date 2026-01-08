# Color Blender

A simple Python web application built with Flask that uses the OpenRouter API to blend two colors and generate creative descriptions.

## Features

- 🎨 **Interactive Color Blending** - Enter two colors and get AI-generated blended color descriptions
- 🤖 **AI-Powered** - Uses OpenRouter API for creative, dynamic responses
- 💻 **Modern Web UI** - Clean, responsive interface with beautiful gradient design
- 🔐 **Secure Configuration** - API key loaded from `.env` file (never commits secrets)
- 📱 **Mobile Friendly** - Works great on desktop and mobile devices

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

### Frontend Flow
1. User enters two colors in the form
2. JavaScript sends an AJAX request to the backend
3. Result is displayed dynamically on the same page

### Backend Flow
1. Flask receives the POST request to `/api/blend-colors`
2. Validates the API key is configured
3. Constructs a prompt for the OpenRouter API
4. Sends request with appropriate headers and model settings
5. Extracts and returns the AI response as JSON
6. Frontend displays the result with appropriate styling

## Deployment Options

### Option 1: Deploy to Render (Recommended)

1. **Push to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Color blender app"
   git push
   ```

2. **Create Render Account** - Go to [render.com](https://render.com) and sign up

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Choose "Python" as runtime
   - Set **Start Command**: `python app.py`
   - Add **Environment Variables**:
     - `OPENROUTER_API_KEY`: your_api_key
     - `PORT`: 5000

4. **Deploy** - Click "Create Web Service"

Your app will be live at: `https://your-app-name.onrender.com`

### Option 2: Deploy to Railway

1. **Create Railway Account** - Go to [railway.app](https://railway.app)

2. **Link GitHub Repository**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add Environment Variables**
   - Go to Variables tab
   - Add `OPENROUTER_API_KEY`

4. **Configure Port** - Railway automatically detects Flask

Your app will be live automatically!

### Option 3: Deploy to PythonAnywhere

1. **Create Account** - Go to [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload Files**
   - Use "Upload a zip file" or Git clone
   - Create virtual environment on PythonAnywhere

3. **Configure Web App**
   - Go to Web tab → "Add a new web app"
   - Choose "Flask"
   - Point to your `app.py`
   - Set working directory

4. **Add Environment Variables**
   - Edit `wsgi.py` to load from `.env`:
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   from app import app as application
   ```

5. **Reload Web App** - Your app is now live!

## Troubleshooting

**"OPENROUTER_API_KEY not found"**
- Ensure `.env` file exists in the project root
- Verify your API key is correctly pasted in `.env`

**"API Error: 402 Client Error"**
- Your OpenRouter account needs credits
- Log in to [openrouter.ai](https://openrouter.ai) to check account status and add credits

**Port Already in Use**
- Change the port in `app.py`: `app.run(port=5001)`
- Or kill the process using port 5000

**App not working after deployment**
- Check logs on your deployment platform
- Ensure environment variables are set correctly
- Verify API key has sufficient credits

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Yes |
| `PORT` | Port to run the Flask app on (default: 5000) | No |

## License

This project is part of the Capstone CSCI-480 course.

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

1. **Color Blending**
   - Enter "blue" and "yellow"
   - Get: "Green. Like nature's perfect balance between sky and sun."

2. **Chemical Formulas**
   - Enter "water"
   - Get: "Formula: H₂O. Fun Fact: Water is essential for all known forms of life..."

## Project Structure

```
.
├── app.py                  # Flask application server
├── main.py                 # Legacy CLI version
├── requirements.txt        # Python dependencies
├── .env.example           # Example environment file
├── .env                   # Environment file (not tracked by git)
├── templates/
│   └── index.html         # HTML template with tabs and forms
├── static/
│   └── style.css          # CSS styling
└── README.md              # This file
```

## How It Works

### Frontend Flow
1. User selects a tab (Color Blender or Chemical Formula)
2. Fills in the form with their input
3. JavaScript sends an AJAX request to the backend
4. Result is displayed dynamically on the same page

### Backend Flow
1. Flask receives the POST request
2. Validates the API key is configured
3. Constructs a prompt for the OpenRouter API
4. Sends request with appropriate headers and model settings
5. Extracts and returns the AI response as JSON
6. Frontend displays the result with appropriate styling

## Deployment Options

### Option 1: Deploy to Render (Recommended)

1. **Push to GitHub** (if not already done)
   ```bash
   git add .
   git commit -m "Convert to Flask web app"
   git push
   ```

2. **Create Render Account** - Go to [render.com](https://render.com) and sign up

3. **Create New Web Service**
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Choose "Python" as runtime
   - Set **Start Command**: `python app.py`
   - Add **Environment Variables**:
     - `OPENROUTER_API_KEY`: your_api_key

4. **Deploy** - Click "Create Web Service"

Your app will be live at: `https://your-app-name.onrender.com`

### Option 2: Deploy to Railway

1. **Create Railway Account** - Go to [railway.app](https://railway.app)

2. **Link GitHub Repository**
   - Click "New Project"
   - Select "Deploy from GitHub repo"
   - Choose your repository

3. **Add Environment Variables**
   - Go to Variables tab
   - Add `OPENROUTER_API_KEY`

4. **Configure Port** - Railway automatically detects Flask

Your app will be live automatically!

### Option 3: Deploy to PythonAnywhere

1. **Create Account** - Go to [pythonanywhere.com](https://www.pythonanywhere.com)

2. **Upload Files**
   - Use "Upload a zip file" or Git clone
   - Create virtual environment on PythonAnywhere

3. **Configure Web App**
   - Go to Web tab → "Add a new web app"
   - Choose "Flask"
   - Point to your `app.py`
   - Set working directory

4. **Add Environment Variables**
   - Edit `wsgi.py` to load from `.env`:
   ```python
   import os
   from dotenv import load_dotenv
   load_dotenv()
   from app import app as application
   ```

5. **Reload Web App** - Your app is now live!

## Troubleshooting

**"OPENROUTER_API_KEY not found"**
- Ensure `.env` file exists in the project root
- Verify your API key is correctly pasted in `.env`

**"API Error: 402 Client Error"**
- Your OpenRouter account needs credits
- Log in to [openrouter.ai](https://openrouter.ai) to check account status and add credits

**Port Already in Use**
- Change the port in `app.py`: `app.run(port=5001)`
- Or kill the process using port 5000

**App not working after deployment**
- Check logs on your deployment platform
- Ensure environment variables are set correctly
- Verify API key has sufficient credits

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `OPENROUTER_API_KEY` | Your OpenRouter API key | Yes |
| `FLASK_ENV` | Set to `production` for deployment | No |

## License

This project is part of the Capstone CSCI-480 course.
