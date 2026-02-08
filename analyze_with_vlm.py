#!/usr/bin/env python3
"""
Blue pigment analysis using Vision Language Models via OpenRouter.
Analyzes paintings to identify dominant blue objects and their RGB colors.
"""

import os
import base64
import json
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


def encode_image(image_path: str) -> str:
    """Encode image to base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def analyze_blue_pigment(image_path: str, api_key: str, model: str = "google/gemini-2.5-flash") -> dict:
    """
    Analyze a painting image to identify the dominant blue object and color.

    Args:
        image_path: Path to the painting image
        api_key: OpenRouter API key
        model: Model to use (default: google/gemini-2.5-flash)

    Returns:
        dict with analysis results
    """
    # Encode image
    image_base64 = encode_image(image_path)
    image_name = Path(image_path).name

    # Determine image MIME type
    suffix = Path(image_path).suffix.lower()
    mime_type = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
    }.get(suffix, "image/jpeg")

    # Prepare the prompt
    prompt = """Analyze this painting and identify the dominant blue color and object.

Please provide your analysis in the following JSON format:

{
    "dominant_blue_object": "name of the object (e.g., 'robe', 'sky', 'vase', 'clothing')",
    "dominant_blue_rgb": [R, G, B],
    "confidence": "high/medium/low",
    "reasoning": "brief explanation of why this is the dominant blue"
}

Focus on:
1. The LARGEST area of blue in the painting
2. The most visually prominent blue object
3. Provide the approximate RGB values for that blue color (0-255 range)

If there are multiple significant blue objects, choose the one that occupies the most area."""

    # Prepare API request
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:{mime_type};base64,{image_base64}"
                        }
                    }
                ]
            }
        ],
        "temperature": 0.3,  # Lower temperature for more consistent responses
    }

    # Make API request
    print(f"Analyzing {image_name}...")
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=60
    )

    if response.status_code != 200:
        raise Exception(f"API request failed: {response.status_code} - {response.text}")

    # Parse response
    result = response.json()
    content = result["choices"][0]["message"]["content"]

    # Extract JSON from response (handle markdown code blocks)
    if "```json" in content:
        content = content.split("```json")[1].split("```")[0].strip()
    elif "```" in content:
        content = content.split("```")[1].split("```")[0].strip()

    # Parse the JSON response
    try:
        analysis = json.loads(content)
    except json.JSONDecodeError:
        # If JSON parsing fails, return raw content
        analysis = {
            "raw_response": content,
            "error": "Failed to parse JSON response"
        }

    # Add metadata
    analysis["image_name"] = image_name
    analysis["model_used"] = model

    return analysis


def main():
    """Main function to analyze all images in the images directory."""
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in .env file")
        print("Please create a .env file with:")
        print("OPENROUTER_API_KEY=your-key-here")
        print("\nGet your key from: https://openrouter.ai/keys")
        print("Or use Google AI Studio free tier: https://aistudio.google.com/apikey")
        return

    # Get all images
    images_dir = Path("images")
    image_files = list(images_dir.glob("*.jpeg")) + list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.png"))

    if not image_files:
        print(f"No images found in {images_dir}")
        return

    print(f"Found {len(image_files)} image(s)")
    print(f"Using model: google/gemini-2.5-flash")
    print("-" * 60)

    # Analyze each image
    results = []
    for image_path in sorted(image_files):
        try:
            analysis = analyze_blue_pigment(str(image_path), api_key)
            results.append(analysis)

            # Print results
            print(f"\n✓ {analysis['image_name']}")
            print(f"  Object: {analysis.get('dominant_blue_object', 'N/A')}")
            print(f"  RGB: {analysis.get('dominant_blue_rgb', 'N/A')}")
            print(f"  Confidence: {analysis.get('confidence', 'N/A')}")
            if 'reasoning' in analysis:
                print(f"  Reasoning: {analysis['reasoning']}")

        except Exception as e:
            print(f"\n✗ {image_path.name}: Error - {str(e)}")
            results.append({
                "image_name": image_path.name,
                "error": str(e)
            })

    # Save results to JSON
    output_file = "blue_pigment_vlm_results.json"
    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print("-" * 60)
    print(f"\n✓ Results saved to {output_file}")


if __name__ == "__main__":
    main()
