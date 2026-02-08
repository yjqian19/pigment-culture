"""
Prepare dashboard data by exporting CSV to JSON format for web visualization.
Uses same coordinate logic as visualize_blue_semantic.py: embed unique object types,
UMAP on unique types, then map paintings to positions + jitter.
"""

import json
import pandas as pd
import numpy as np
from pathlib import Path
from sentence_transformers import SentenceTransformer
from umap import UMAP

# Match visualize_blue_semantic.py
JITTER_PERCENT = 0.05

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
    """Generate semantic embeddings for unique object types only."""
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
    unique_objects = df['vlm_dominant_blue_object'].unique()
    embeddings_dict = {obj: model.encode(obj) for obj in unique_objects}
    print(f"  Encoded {len(unique_objects)} unique object types")
    return embeddings_dict

def apply_umap(embeddings_dict):
    """Apply UMAP on unique object type embeddings, return object_type -> (x, y) mapping."""
    unique_objects = list(embeddings_dict.keys())
    embeddings_matrix = np.array([embeddings_dict[obj] for obj in unique_objects])

    reducer = UMAP(
        n_components=2,
        n_neighbors=15,
        min_dist=0.1,
        metric='cosine',
        random_state=42
    )
    umap_coords = reducer.fit_transform(embeddings_matrix)
    object_to_coords = {obj: umap_coords[i] for i, obj in enumerate(unique_objects)}
    return object_to_coords

def assign_coords_and_jitter(df, object_to_coords):
    """Assign base UMAP coords to paintings, then add deterministic jitter."""
    df = df.copy()
    df['umap_x'] = df['vlm_dominant_blue_object'].map(lambda o: object_to_coords[o][0])
    df['umap_y'] = df['vlm_dominant_blue_object'].map(lambda o: object_to_coords[o][1])

    x_range = df['umap_x'].max() - df['umap_x'].min()
    y_range = df['umap_y'].max() - df['umap_y'].min()
    jitter_x = x_range * JITTER_PERCENT
    jitter_y = y_range * JITTER_PERCENT

    # Draw both x and y jitter from a single RNG per painting
    # to get 2D cluster-like scatter (not a diagonal line)
    def _jitter_row(row):
        rng = np.random.RandomState(int(row['id']))
        angle = rng.uniform(0, 2 * np.pi)
        radius = rng.uniform(0, 1) ** 0.5  # sqrt for uniform area distribution
        dx = radius * np.cos(angle) * jitter_x
        dy = radius * np.sin(angle) * jitter_y
        return pd.Series({'plot_x': row['umap_x'] + dx, 'plot_y': row['umap_y'] + dy})

    jittered = df.apply(_jitter_row, axis=1)
    df['plot_x'] = jittered['plot_x']
    df['plot_y'] = jittered['plot_y']
    return df

def get_top_clusters(df, top_n=5):
    """Calculate centroids for top N object types (using pre-jitter UMAP coords)."""
    object_counts = df['vlm_dominant_blue_object'].value_counts()
    top_objects = object_counts.head(top_n).index.tolist()

    clusters = []
    for obj in top_objects:
        mask = df['vlm_dominant_blue_object'] == obj
        centroid_x = float(df.loc[mask, 'umap_x'].mean())
        centroid_y = float(df.loc[mask, 'umap_y'].mean())
        count = int(object_counts[obj])

        clusters.append({
            'object_type': obj,
            'count': count,
            'centroid_x': round(centroid_x, 4),
            'centroid_y': round(centroid_y, 4)
        })

    return clusters

def prepare_paintings_json(df):
    """Convert dataframe to JSON format for dashboard."""
    paintings = []

    for _, row in df.iterrows():
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

        # Original API color
        original_color = str(row.get('original_blue_color', ''))
        if original_color == 'nan':
            original_color = ''

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
            'original_blue_color': original_color,
            'coverage_percent': float(row.get('original_blue_percent', 0)),
            'plot_x': round(float(row['plot_x']), 4),
            'plot_y': round(float(row['plot_y']), 4)
        }

        paintings.append(painting)

    return paintings

def main():
    """Main export pipeline."""
    print("Loading data...")
    df = load_data()

    print("Generating embeddings (unique object types)...")
    embeddings_dict = generate_embeddings(df)

    print("Applying UMAP on unique types...")
    object_to_coords = apply_umap(embeddings_dict)

    print("Assigning coords and adding jitter...")
    df = assign_coords_and_jitter(df, object_to_coords)

    print("Calculating cluster annotations...")
    clusters = get_top_clusters(df, top_n=5)

    print("Preparing paintings JSON...")
    paintings = prepare_paintings_json(df)

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
