#!/usr/bin/env python3
"""Simple CLI app to blend two colors using OpenRouter API."""

import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

API_KEY = os.getenv("OPENROUTER_API_KEY")
API_URL = "https://openrouter.ai/api/v1/chat/completions"


def validate_api_key():
    """Check if API key is configured."""
    if not API_KEY:
        raise ValueError(
            "OPENROUTER_API_KEY not found. "
            "Please create a .env file with your API key."
        )


def blend_colors(color1: str, color2: str) -> str:
    """Request the AI to blend two colors and describe the result."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/prabinroka/Capstone-CSCI-480",
        "X-Title": "Color Blender CLI",
    }

    payload = {
        "model": "openrouter/auto",
        "messages": [
            {
                "role": "user",
                "content": f"If you blend {color1} and {color2} together, what color do you get? "
                f"Provide: 1) The resulting color name, 2) A fun, creative one-sentence description. "
                f"Format: 'Color Name: [name]. Description: [description]'",
            }
        ],
        "temperature": 0.9,
    }

    response = requests.post(API_URL, json=payload, headers=headers, timeout=30)
    response.raise_for_status()

    return response.json()["choices"][0]["message"]["content"]


def main():
    """Main entry point."""
    try:
        validate_api_key()

        # Get user input
        print("\n🎨 Color Blender CLI\n")
        color1 = input("Enter first color: ").strip()
        color2 = input("Enter second color: ").strip()

        if not color1 or not color2:
            print("Error: Both colors must be provided.")
            exit(1)

        print(f"\n Blending {color1} and {color2}...\n")

        # Get blended color description from API
        result = blend_colors(color1, color2)
        print(result)
        print()

    except ValueError as e:
        print(f"Configuration Error: {e}")
        exit(1)
    except requests.RequestException as e:
        print(f"API Error: {e}")
        exit(1)
    except KeyError:
        print("Error: Unexpected response format from API")
        exit(1)


if __name__ == "__main__":
    main()
