# Pigment Culture

## Project Goal

Analyze blue pigments in paintings: given images in `images/`, identify the **dominant blue color** (RGB) and the **object** it belongs to (e.g., robe, sky, vase).

**Dominant blue color** = the most frequently occurring blue color across the painting. Since lighting conditions (highlights, shadows, reflections) cause the same pigment to appear as slightly different RGB values, we use HSV color space with binned quantization to group perceptually similar blues together. The most common HSV bin is treated as the "dominant" blue — this way, a single blue robe under varying light is correctly identified as one dominant color rather than many scattered shades.

## Current Status

- Two sample images: `chinese_portrait.jpeg`, `american_portrait.jpeg`
- Segmentation approach implemented in `blue_pigment_analysis.ipynb` — not yet producing correct results (outputs "No blue found" for both test images)

## Approaches Under Consideration

### Approach 1: Segmentation Model (current)

- **Pipeline:** Image segmentation → per-segment dominant color extraction (HSV quantization) → blue detection → largest blue segment
- **Models tried:**
  - **OneFormer** (Swin-Large, ADE20K) — semantic segmentation with 150 class labels. Provides object labels directly but may not segment blue regions accurately in paintings. Only got one large "painting" class segmented.
  - **SAM2** (facebook/sam2.1-hiera-large) — class-agnostic mask generation. Good at finding regions but no semantic labels (segments named `segment_1`, `segment_2`, etc.)
- **Key issue:** Neither model reliably identifies and labels the blue objects in these painting images. The HSV-based blue detection (hue 180-270°, saturation > 15%) may need tuning, or the segmentation boundaries may not align with the blue objects.

### Approach 2: Vision Language Model (VLM) API (under consideration)

- Send images to a VLM (e.g., Claude, GPT-4V) and ask it to identify the dominant blue object and its color.
- Advantages: understands semantic context, can describe objects naturally, no local GPU needed.
- Disadvantages: less precise pixel-level color extraction, API cost.
- Could combine with approach 1: use VLM for object identification + segmentation for precise color measurement.

## Technical Details

- **Python version:** >= 3.10
- **Package manager:** uv (`uv sync` to install)
- **Key dependencies:** transformers, torch, torchvision, pillow, numpy, matplotlib, pandas
- **HuggingFace auth:** Required for some models. Use `huggingface-cli login` locally or Colab secrets.
- **Device:** Runs on CPU (no CUDA required), but GPU recommended for speed.

## Project Structure

```
images/              # Input painting images (jpeg/jpg/png)
blue_pigment_analysis.ipynb  # Main analysis notebook
blue_objects.json    # Output data (large, ~30MB)
pyproject.toml       # Project config & dependencies
uv.lock              # Dependency lock file
```

## Color Detection Method

- Convert RGB → HSV for lighting-invariant color grouping
- Quantize HSV (18 hue bins, 3 saturation bins, 3 value bins) to find dominant color per segment
- The binning approach groups similar shades together: e.g., a blue robe in shadow (darker) and in light (brighter) falls into the same hue bin, so they count as one color
- Blue defined as: hue 180-270°, saturation > 15%
- Select largest blue segment by pixel area
