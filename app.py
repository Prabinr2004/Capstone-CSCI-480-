#!/usr/bin/env python3
"""Flask web application for color blending and chemical formula lookup."""

import os
import requests
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)
API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def validate_api_key():
    """Check if API key is configured."""
    if not API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY not found. Please set it in your .env file."
        )


def query_openrouter(prompt: str) -> str:
    """Send a query to OpenRouter API and return the response."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/prabinroka/Capstone-CSCI-480",
        "X-Title": "Color & Chemistry Web App",
    }

    payload = {
        "model": "openrouter/auto",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.9,
    }

    response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


def blend_colors(color1: str, color2: str) -> str:
    """Blend two colors using AI."""
    prompt = (
        f"If you blend {color1} and {color2} together, what color do you get? "
        f"Provide: 1) The resulting color name, 2) A fun, creative one-sentence description. "
        f"Format: 'Color Name: [name]. Description: [description]'"
    )
    return query_openrouter(prompt)


@app.route("/")
def index():
    """Render the main page."""
    return render_template("index.html")


@app.route("/api/blend-colors", methods=["POST"])
def api_blend_colors():
    """API endpoint for blending colors."""
    try:
        validate_api_key()
        data = request.get_json()
        color1 = data.get("color1", "").strip()
        color2 = data.get("color2", "").strip()

        if not color1 or not color2:
            return jsonify({"error": "Both colors are required"}), 400

        result = blend_colors(color1, color2)
        return jsonify({"result": result, "type": "color"}), 200

    except ValueError as e:
        return jsonify({"error": str(e)}), 500
    except requests.RequestException as e:
        return jsonify({"error": f"API Error: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"error": f"Unexpected error: {str(e)}"}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(debug=True, host="0.0.0.0", port=port)
