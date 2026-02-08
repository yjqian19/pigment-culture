# Blue Pigment Analysis - Interactive Dashboard

An interactive web dashboard for exploring blue pigment usage across 143 paintings from 6 cultures.

## Features

- **Interactive Scatter Plot**: 2D visualization using semantic similarity (UMAP)
- **Cultural Comparison**: Color-coded by artist culture (Japanese, American, German, Australian, French, British)
- **Detailed Views**: Click any point to see:
  - Full painting image
  - Artist and metadata
  - Dominant blue object identification
  - Precise RGB/Hex color values
  - Blue coverage percentage
  - VLM analysis reasoning
- **Cluster Annotations**: Top 5 most common blue object types labeled on the plot
- **Responsive Design**: Works on desktop and mobile devices

## Quick Start

### Local Development

```bash
# From the project root directory
cd /Volumes/yjbolt/projects/pigment-culture

# Start local web server
python3 -m http.server 8000

# Open in browser
open http://localhost:8000/dashboard/index.html
```

Or simply:

```bash
cd /Volumes/yjbolt/projects/pigment-culture/dashboard
open index.html
```

**Note:** Opening `index.html` directly may have CORS limitations. Using a local server is recommended.

## File Structure

```
dashboard/
├── index.html                      # Main HTML structure
├── styles.css                      # Styling
├── app.js                          # Interactivity logic
├── data/
│   ├── paintings.json              # 143 paintings with coordinates (111 KB)
│   └── cluster_annotations.json    # Top 5 cluster positions (619 B)
└── images/                         # Symlink to ../images/ (143 .jpg files)
```

## Data Preparation

The dashboard data is generated from `output/blue_objects_with_vlm.csv` using:

```bash
python prepare_dashboard_data.py
```

This script:
1. Loads paintings with VLM analysis results
2. Generates semantic embeddings for object types
3. Applies UMAP dimensionality reduction
4. Adds deterministic jitter to prevent overlaps
5. Calculates top 5 cluster centroids
6. Exports JSON files for web consumption

## Technology Stack

- **Plotly.js**: Interactive scatter plot with zoom/pan
- **Vanilla JavaScript**: No framework dependencies
- **HTML/CSS**: Responsive two-panel layout
- **Python**: Data preparation pipeline

## Visualization Method

Points are positioned using:
1. **Sentence-BERT embeddings** (`all-MiniLM-L6-v2`) to convert object type strings to 384D vectors
2. **UMAP** to reduce to 2D while preserving semantic similarity
3. **Deterministic jitter** to prevent exact overlaps

This means paintings with similar blue objects cluster together (e.g., "sky", "clouds", "atmosphere").

## Browser Compatibility

- Modern browsers with JavaScript enabled
- Chrome/Edge/Firefox/Safari (latest versions)
- Mobile browsers supported

## Data Sources

- **Painting images**: 143 museum artworks (JPEG format)
- **Metadata**: Cleveland Museum of Art collection data
- **VLM analysis**: Gemini 2.5 Flash via OpenRouter
- **Blue object identification**: Vision Language Model analysis
- **Color extraction**: RGB values from VLM analysis

## Known Limitations

1. Not all paintings in the source data have images (only 143/~30K)
2. VLM analysis quality varies by painting complexity
3. Blue coverage percentages may not be perfectly accurate
4. Some images may fail to load (404 error handling included)

## Future Enhancements

Possible additions (not implemented in v1):
- Search/filter by object type or artist
- Multi-select comparison mode
- Time slider for date filtering
- Export filtered CSV
- 3D view option
- Full-screen image modal

## Deployment

### GitHub Pages

```bash
git add dashboard/
git commit -m "Add interactive dashboard"
git push origin main

# Enable GitHub Pages in repo settings
# Select /dashboard folder as source
```

### Static Hosting

Upload the entire `dashboard/` directory to any static hosting service:
- Netlify
- Vercel
- AWS S3 + CloudFront
- Firebase Hosting

**Important:** Ensure the `images/` directory is deployed (either as symlink or copied files).

## License

Same as parent project (Pigment Culture analysis).

## Credits

- Data visualization: Claude Code
- Museum data: Cleveland Museum of Art
- VLM analysis: Google Gemini 2.5 Flash
- Embeddings: Sentence-BERT (`all-MiniLM-L6-v2`)
- Dimensionality reduction: UMAP
