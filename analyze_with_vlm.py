#!/usr/bin/env python3
"""
Blue pigment analysis using Vision Language Models via OpenRouter.
Analyzes paintings to identify dominant blue objects and their RGB colors.
Merges VLM results with existing blue_objects.json data and outputs to CSV.
"""

import os
import base64
import json
from pathlib import Path
import requests
import pandas as pd
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


def load_blue_objects(json_path: str = "output/blue_objects.json") -> dict:
    """Load blue_objects.json and create a dict keyed by ID for fast lookup."""
    print(f"Loading {json_path}...")
    with open(json_path, "r") as f:
        objects = json.load(f)

    # Create dict keyed by ID
    objects_dict = {obj["id"]: obj for obj in objects}
    print(f"✓ Loaded {len(objects_dict)} objects")
    return objects_dict


def extract_id_from_filename(filename: str) -> int:
    """Extract object ID from filename (e.g., '147053.jpg' -> 147053)."""
    return int(Path(filename).stem)


def merge_and_export_csv(vlm_results: list, objects_dict: dict, output_csv: str = "output/blue_objects_with_vlm.csv"):
    """Merge VLM results with blue_objects data and export to CSV."""
    print("\nMerging results...")

    # Ensure output directory exists
    Path(output_csv).parent.mkdir(parents=True, exist_ok=True)

    merged_data = []
    for vlm_result in vlm_results:
        # Extract ID from image name
        image_name = vlm_result.get("image_name")
        if not image_name:
            continue

        try:
            obj_id = extract_id_from_filename(image_name)
        except ValueError:
            print(f"Warning: Could not extract ID from {image_name}")
            continue

        # Find matching object in blue_objects.json
        obj = objects_dict.get(obj_id)
        if not obj:
            print(f"Warning: No object found with ID {obj_id}")
            continue

        # Merge data
        merged_row = {
            "id": obj_id,
            "title": obj.get("title"),
            "classification": obj.get("classification"),
            "dated": obj.get("dated"),
            "image_name": image_name,

            # VLM results
            "vlm_dominant_blue_object": vlm_result.get("dominant_blue_object"),
            "vlm_blue_r": vlm_result.get("dominant_blue_rgb", [None, None, None])[0] if vlm_result.get("dominant_blue_rgb") else None,
            "vlm_blue_g": vlm_result.get("dominant_blue_rgb", [None, None, None])[1] if vlm_result.get("dominant_blue_rgb") else None,
            "vlm_blue_b": vlm_result.get("dominant_blue_rgb", [None, None, None])[2] if vlm_result.get("dominant_blue_rgb") else None,
            "vlm_confidence": vlm_result.get("confidence"),
            "vlm_reasoning": vlm_result.get("reasoning"),
            "vlm_model": vlm_result.get("model_used"),
            "vlm_error": vlm_result.get("error"),

            # Original colors data (first blue color if available)
            "original_blue_color": None,
            "original_blue_percent": None,
        }

        # Extract blue color with highest percentage from original data
        if "colors" in obj:
            blue_colors = [c for c in obj["colors"] if c.get("hue") == "Blue"]
            if blue_colors:
                # Sort by percent descending and pick the most prominent blue
                most_prominent_blue = max(blue_colors, key=lambda c: c.get("percent", 0))
                merged_row["original_blue_color"] = most_prominent_blue.get("color")
                merged_row["original_blue_percent"] = most_prominent_blue.get("percent")

        # Artist info
        if "people" in obj and obj["people"]:
            artist = obj["people"][0]
            merged_row["artist_name"] = artist.get("displayname")
            merged_row["artist_culture"] = artist.get("culture")
        else:
            merged_row["artist_name"] = None
            merged_row["artist_culture"] = None

        merged_data.append(merged_row)

    # Convert to DataFrame and save
    df = pd.DataFrame(merged_data)
    df.to_csv(output_csv, index=False)
    print(f"✓ Merged data saved to {output_csv}")
    print(f"  Total rows: {len(df)}")
    return df


def main():
    """Main function to analyze all images and merge with blue_objects.json."""
    # Get API key from environment
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("Error: OPENROUTER_API_KEY not found in .env file")
        print("Please create a .env file with:")
        print("OPENROUTER_API_KEY=your-key-here")
        print("\nGet your key from: https://openrouter.ai/keys")
        print("Or use Google AI Studio free tier: https://aistudio.google.com/apikey")
        return

    # Load blue_objects.json
    try:
        objects_dict = load_blue_objects()
    except FileNotFoundError:
        print("Error: blue_objects.json not found")
        return

    # Get all images
    images_dir = Path("images")
    image_files = list(images_dir.glob("*.jpg")) + list(images_dir.glob("*.jpeg")) + list(images_dir.glob("*.png"))

    if not image_files:
        print(f"No images found in {images_dir}")
        return

    print(f"\nFound {len(image_files)} image(s)")
    print(f"Using model: google/gemini-2.5-flash")
    print("-" * 60)

    # Analyze each image
    results = []
    for image_path in sorted(image_files):
        try:
            print(f"Analyzing {image_path.name}...")
            analysis = analyze_blue_pigment(str(image_path), api_key)
            results.append(analysis)

        except Exception as e:
            print(f"Error analyzing {image_path.name}: {str(e)}")
            results.append({
                "image_name": image_path.name,
                "error": str(e)
            })

    print("-" * 60)

    # Save VLM results to JSON
    vlm_json = "blue_pigment_vlm_results.json"
    with open(vlm_json, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n✓ VLM results saved to {vlm_json}")

    # Merge with blue_objects.json and export to CSV
    merge_and_export_csv(results, objects_dict)


if __name__ == "__main__":
    main()
