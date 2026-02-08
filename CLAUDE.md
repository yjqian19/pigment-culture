# Pigment Culture

## Project Goal

Analyze blue pigments in paintings: given images in `images/`, identify the **dominant blue color** (RGB) and the **object** it belongs to (e.g., robe, sky, vase).

**Dominant blue color** = the most frequently occurring blue color across the painting. Since lighting conditions (highlights, shadows, reflections) cause the same pigment to appear as slightly different RGB values, we use HSV color space with binned quantization to group perceptually similar blues together. The most common HSV bin is treated as the "dominant" blue — this way, a single blue robe under varying light is correctly identified as one dominant color rather than many scattered shades.

## Current Status

- Two sample images: `chinese_portrait.jpeg`, `american_portrait.jpeg`
- Segmentation approach implemented in `blue_pigment_analysis.ipynb` — not yet producing correct results (outputs "No blue found" for both test images)
- VLM approach implemented in `analyze_with_vlm.py` — uses OpenRouter + Gemini Flash to identify dominant blue objects
- **Semantic visualization implemented in `visualize_blue_semantic.py`** — creates 2D semantic space showing how different cultures use blue in different object types
- Output files stored in `output/` directory (JSON, CSV, and PNG visualizations)

## Approaches Under Consideration

### Approach 1: Segmentation Model (current)

- **Pipeline:** Image segmentation → per-segment dominant color extraction (HSV quantization) → blue detection → largest blue segment
- **Models tried:**
  - **OneFormer** (Swin-Large, ADE20K) — semantic segmentation with 150 class labels. Provides object labels directly but may not segment blue regions accurately in paintings. Only got one large "painting" class segmented.
  - **SAM2** (facebook/sam2.1-hiera-large) — class-agnostic mask generation. Good at finding regions but no semantic labels (segments named `segment_1`, `segment_2`, etc.)
- **Key issue:** Neither model reliably identifies and labels the blue objects in these painting images. The HSV-based blue detection (hue 180-270°, saturation > 15%) may need tuning, or the segmentation boundaries may not align with the blue objects.

### Approach 2: Vision Language Model (VLM) API (implemented)

- **Status:** Implemented in `analyze_with_vlm.py`
- **Model:** Gemini 2.5 Flash via OpenRouter (supports Google AI Studio free tier keys)
- **Cost:** ~$0.001 for 143 images
- Send images to a VLM (e.g., Claude, GPT-4V) and ask it to identify the dominant blue object and its color.
- Advantages: understands semantic context, can describe objects naturally, no local GPU needed.
- Disadvantages: less precise pixel-level color extraction, API cost.
- Could combine with approach 1: use VLM for object identification + segmentation for precise color measurement.
- **Output:** Merges VLM results with `blue_objects.json` data → `output/blue_objects_with_vlm.csv`

## Technical Details

- **Python version:** >= 3.10 (tested on 3.12.11)
- **Package manager:** uv (`uv pip install` for dependencies)
- **Key dependencies:** transformers, torch, torchvision, pillow, numpy, matplotlib, pandas, sentence-transformers, umap-learn
- **HuggingFace auth:** Required for some models. Use `huggingface-cli login` locally or Colab secrets.
- **Device:** Runs on CPU (no CUDA required), but GPU recommended for speed.

## Project Structure

```
images/              # Input painting images (jpeg/jpg/png)
output/              # Generated JSON, CSV, and visualization files
  blue_objects.json                      # Museum data (large, ~30MB)
  blue_pigment_vlm_results.json          # Raw VLM analysis results
  blue_objects_with_vlm.csv              # Merged dataset for analysis
  blue_objects_semantic_visualization.png # 2D semantic visualization (416 KB, 300 DPI)
  semantic_visualization_report.md       # Comprehensive methodology & results report
blue_pigment_analysis.ipynb  # Main analysis notebook
analyze_with_vlm.py          # VLM-based blue pigment analysis script
visualize_blue_semantic.py   # 2D semantic visualization script
pyproject.toml               # Project config & dependencies
uv.lock                      # Dependency lock file
.env                         # API keys (gitignored, use .env.example as template)
```

## Color Detection Method

- Convert RGB → HSV for lighting-invariant color grouping
- Quantize HSV (18 hue bins, 3 saturation bins, 3 value bins) to find dominant color per segment
- The binning approach groups similar shades together: e.g., a blue robe in shadow (darker) and in light (brighter) falls into the same hue bin, so they count as one color
- Blue defined as: hue 180-270°, saturation > 15%
- Select largest blue segment by pixel area

## Data Structure

- Image filenames are object IDs: `147053.jpg` corresponds to `id: 147053` in `blue_objects.json`
- Not all objects in `blue_objects.json` have images — only a subset (143 images) selected for analysis
- VLM script matches images to objects by extracting ID from filename
- Original data includes multiple colors per object; script selects blue with highest percentage

## Visualization

### 2D Semantic Visualization (`visualize_blue_semantic.py`)

Creates a scatter plot showing cultural patterns in blue pigment usage:

- **Methodology:**
  1. Convert object type strings to semantic embeddings using Sentence-BERT (`all-MiniLM-L6-v2`)
  2. Apply UMAP dimensionality reduction to project 384D embeddings into 2D semantic space
  3. Add deterministic jitter based on painting ID to prevent overlaps
  4. Detect outliers: points far from main clusters (top 15th percentile)
  5. Color points by cultural origin

- **Features:**
  - Semantically similar objects cluster together (e.g., "water", "sea", "ocean")
  - 135 paintings from 6 cultures visualized
  - Top 5 object types annotated at cluster centroids (white labels)
  - 8 outlier points annotated with yellow labels (unusual/geometric blue objects)
  - Publication-quality output (4170 × 2969 px at 300 DPI)

- **Key Findings:**
  - Japanese paintings concentrate in sky/water clusters (landscape tradition)
  - American paintings dispersed across all object types (diverse usage)
  - Outliers reveal geometric/abstract blue forms (rare artistic choices)

- **Usage:** `python visualize_blue_semantic.py`
- **Output:**
  - `output/blue_objects_semantic_visualization.png` (visualization)
  - `output/semantic_visualization_report.md` (detailed methodology & results)

## Development Conventions

- **Console output:** Keep minimal — progress tracking only, detailed results in files
- **API keys:** Store in `.env` file (already gitignored), use `python-dotenv` to load
- **Dependencies:** Add to `pyproject.toml`, install with `uv pip install`
