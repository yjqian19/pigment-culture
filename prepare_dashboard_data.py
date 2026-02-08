"""
Prepare dashboard data by exporting CSV to JSON format for web visualization.
Reuses functions from visualize_blue_semantic.py for coordinate generation.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from umap import UMAP

def load_data():
    """Load and prepare painting data."""
    df = pd.read_csv('output/blue_objects_with_vlm.csv')

    # Filter for paintings with VLM results and images
    df = df[df['vlm_dominant_blue_object'].notna()].copy()

    # Add image filename
    df['image_name'] = df['id'].astype(str) + '.jpg'

    # Verify images exist
    image_dir = Path('images')
    df['has_image'] = df['image_name'].apply(lambda x: (image_dir / x).exists())
    df = df[df['has_image']].copy()

    print(f"Loaded {len(df)} paintings with images and VLM results")
    return df

def generate_embeddings(df):
    """Generate semantic embeddings for object types."""
    model = SentenceTransformer('all-MiniLM-L6-v2')
    object_types = df['vlm_dominant_blue_object'].tolist()
    embeddings = model.encode(object_types, show_progress_bar=True)
    return embeddings

def apply_umap(embeddings):
    """Apply UMAP dimensionality reduction."""
    reducer = UMAP(
        n_components=2,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=42
    )
    coords = reducer.fit_transform(embeddings)
    return coords

def add_jitter(coords, painting_ids, jitter_strength=0.05):
    """Add deterministic jitter to prevent overlaps."""
    np.random.seed(42)
    jittered = coords.copy()

    for i in range(len(coords)):
        seed_value = int(painting_ids[i])
        np.random.seed(seed_value)
        jitter = np.random.randn(2) * jitter_strength
        jittered[i] += jitter

    return jittered

def get_top_clusters(df, coords, top_n=5):
    """Calculate centroids for top N most common object types."""
    object_counts = df['vlm_dominant_blue_object'].value_counts()
    top_objects = object_counts.head(top_n).index.tolist()

    clusters = []
    for obj in top_objects:
        mask = df['vlm_dominant_blue_object'] == obj
        obj_coords = coords[mask]
        centroid_x = float(np.mean(obj_coords[:, 0]))
        centroid_y = float(np.mean(obj_coords[:, 1]))
        count = int(object_counts[obj])

        clusters.append({
            'object_type': obj,
            'count': count,
            'centroid_x': round(centroid_x, 4),
            'centroid_y': round(centroid_y, 4)
        })

    return clusters

def prepare_paintings_json(df, coords):
    """Convert dataframe to JSON format for dashboard."""
    paintings = []

    for idx, row in df.iterrows():
        coord_idx = df.index.get_loc(idx)

        # Parse RGB values (columns are vlm_blue_r, vlm_blue_g, vlm_blue_b)
        r = row.get('vlm_blue_r', 128)
        g = row.get('vlm_blue_g', 128)
        b = row.get('vlm_blue_b', 200)

        if pd.notna(r) and pd.notna(g) and pd.notna(b):
            rgb = [int(r), int(g), int(b)]
            blue_hex = '#{:02x}{:02x}{:02x}'.format(rgb[0], rgb[1], rgb[2])
        else:
            rgb = [128, 128, 200]
            blue_hex = '#8080c8'

        # Truncate reasoning
        reasoning = str(row.get('vlm_reasoning', ''))
        if len(reasoning) > 500:
            reasoning = reasoning[:497] + '...'

        painting = {
            'id': int(row['id']),
            'title': str(row.get('title', 'Untitled')),
            'artist_name': str(row.get('artist_name', 'Unknown')),
            'artist_culture': str(row.get('artist_culture', 'Unknown')),
            'classification': str(row.get('classification', '')),
            'dated': str(row.get('dated', '')),
            'image_name': row['image_name'],
            'dominant_blue_object': str(row['vlm_dominant_blue_object']),
            'blue_rgb': rgb,
            'blue_hex': blue_hex,
            'confidence': str(row.get('vlm_confidence', 'medium')),
            'reasoning': reasoning,
            'coverage_percent': float(row.get('original_blue_percent', 0)),
            'plot_x': round(float(coords[coord_idx, 0]), 4),
            'plot_y': round(float(coords[coord_idx, 1]), 4)
        }

        paintings.append(painting)

    return paintings

def main():
    """Main export pipeline."""
    print("Loading data...")
    df = load_data()

    print("Generating embeddings...")
    embeddings = generate_embeddings(df)

    print("Applying UMAP...")
    coords = apply_umap(embeddings)

    print("Adding jitter...")
    coords = add_jitter(coords, df['id'].values)

    print("Calculating cluster annotations...")
    clusters = get_top_clusters(df, coords, top_n=5)

    print("Preparing paintings JSON...")
    paintings = prepare_paintings_json(df, coords)

    # Create output directory
    output_dir = Path('dashboard/data')
    output_dir.mkdir(parents=True, exist_ok=True)

    # Export paintings data
    paintings_file = output_dir / 'paintings.json'
    with open(paintings_file, 'w') as f:
        json.dump(paintings, f, indent=2)
    print(f"Exported {len(paintings)} paintings to {paintings_file}")

    # Export cluster annotations
    clusters_file = output_dir / 'cluster_annotations.json'
    cluster_data = {'top_clusters': clusters}
    with open(clusters_file, 'w') as f:
        json.dump(cluster_data, f, indent=2)
    print(f"Exported {len(clusters)} cluster annotations to {clusters_file}")

    print("\nData preparation complete!")
    print(f"Total file size: ~{paintings_file.stat().st_size // 1024} KB")

if __name__ == '__main__':
    main()
