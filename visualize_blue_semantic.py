"""
2D Semantic Visualization of Blue Objects in Paintings

Creates a scatter plot where:
- Each point represents one painting
- Position based on semantic similarity of blue object types (using UMAP on sentence embeddings)
- Color indicates the painting's cultural origin
- Similar object types cluster together naturally
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sentence_transformers import SentenceTransformer
import umap
from pathlib import Path

# Configuration
INPUT_FILE = "output/blue_objects_with_vlm.csv"
OUTPUT_FILE = "output/blue_objects_semantic_visualization.png"
FIG_WIDTH = 14
FIG_HEIGHT = 10
DPI = 300

# UMAP parameters
UMAP_N_NEIGHBORS = 15  # Balance local/global structure
UMAP_MIN_DIST = 0.1    # Minimum distance between points
UMAP_METRIC = 'cosine' # Best for sentence embeddings
RANDOM_SEED = 42

# Jitter parameters (% of coordinate range)
JITTER_PERCENT = 0.05

# Culture color mapping (tab10 colormap)
CULTURE_COLORS = {
    'Japanese': '#1f77b4',   # Blue
    'American': '#ff7f0e',   # Orange
    'German': '#2ca02c',     # Green
    'Australian': '#d62728', # Red
    'French': '#9467bd',     # Purple
    'British': '#8c564b'     # Brown
}

def load_data(filepath):
    """Load and clean the VLM analysis results."""
    print(f"Loading data from {filepath}...")
    df = pd.read_csv(filepath)

    # Drop rows with missing required fields
    initial_count = len(df)
    df = df.dropna(subset=['vlm_dominant_blue_object', 'artist_culture'])
    final_count = len(df)

    if initial_count > final_count:
        print(f"  Dropped {initial_count - final_count} rows with missing data")

    print(f"  Loaded {final_count} paintings with complete data")
    return df

def generate_embeddings(object_types):
    """Generate semantic embeddings for object types using Sentence-BERT."""
    print("\nGenerating semantic embeddings...")
    print(f"  Loading sentence-transformers model...")
    model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')

    unique_objects = object_types.unique()
    print(f"  Found {len(unique_objects)} unique object types")
    print(f"  Encoding {len(unique_objects)} object types...")

    # Generate embeddings for each unique object type
    embeddings_dict = {}
    for obj in unique_objects:
        embeddings_dict[obj] = model.encode(obj)

    print(f"  Generated embeddings of dimension {len(embeddings_dict[unique_objects[0]])}")
    return embeddings_dict

def apply_umap(df, embeddings_dict):
    """Apply UMAP dimensionality reduction to convert embeddings to 2D coordinates."""
    print("\nApplying UMAP dimensionality reduction...")

    # Create embeddings matrix for all unique object types
    unique_objects = list(embeddings_dict.keys())
    embeddings_matrix = np.array([embeddings_dict[obj] for obj in unique_objects])

    # Apply UMAP
    print(f"  UMAP configuration: n_neighbors={UMAP_N_NEIGHBORS}, min_dist={UMAP_MIN_DIST}, metric='{UMAP_METRIC}'")
    reducer = umap.UMAP(
        n_components=2,
        n_neighbors=UMAP_N_NEIGHBORS,
        min_dist=UMAP_MIN_DIST,
        metric=UMAP_METRIC,
        random_state=RANDOM_SEED
    )

    umap_coords = reducer.fit_transform(embeddings_matrix)

    # Create mapping from object type to UMAP coordinates
    object_to_coords = {obj: umap_coords[i] for i, obj in enumerate(unique_objects)}

    # Assign UMAP coordinates to each painting based on its object type
    df['umap_x'] = df['vlm_dominant_blue_object'].map(lambda obj: object_to_coords[obj][0])
    df['umap_y'] = df['vlm_dominant_blue_object'].map(lambda obj: object_to_coords[obj][1])

    print(f"  UMAP complete: X range [{df['umap_x'].min():.2f}, {df['umap_x'].max():.2f}], Y range [{df['umap_y'].min():.2f}, {df['umap_y'].max():.2f}]")
    return df

def add_jitter(df):
    """Add deterministic jitter to prevent overlapping points with same object type."""
    print("\nAdding jitter to prevent overlaps...")

    # Calculate jitter magnitude based on coordinate range
    x_range = df['umap_x'].max() - df['umap_x'].min()
    y_range = df['umap_y'].max() - df['umap_y'].min()
    jitter_x = x_range * JITTER_PERCENT
    jitter_y = y_range * JITTER_PERCENT

    print(f"  Jitter magnitude: X ±{jitter_x:.3f}, Y ±{jitter_y:.3f} ({JITTER_PERCENT*100}% of range)")

    # Apply deterministic jitter based on painting ID
    df['plot_x'] = df.apply(
        lambda row: row['umap_x'] + np.random.RandomState(int(row['id'])).uniform(-jitter_x, jitter_x),
        axis=1
    )
    df['plot_y'] = df.apply(
        lambda row: row['umap_y'] + np.random.RandomState(int(row['id'])).uniform(-jitter_y, jitter_y),
        axis=1
    )

    return df

def create_visualization(df):
    """Create the 2D semantic visualization."""
    print("\nCreating visualization...")

    # Create figure
    fig, ax = plt.subplots(figsize=(FIG_WIDTH, FIG_HEIGHT), facecolor='white')

    # Get culture counts for legend
    culture_counts = df['artist_culture'].value_counts().to_dict()

    # Plot each culture separately for legend
    for culture, color in CULTURE_COLORS.items():
        if culture in culture_counts:
            culture_df = df[df['artist_culture'] == culture]
            ax.scatter(
                culture_df['plot_x'],
                culture_df['plot_y'],
                c=color,
                s=100,
                alpha=0.7,
                edgecolors='white',
                linewidths=0.5,
                label=f"{culture} (n={culture_counts[culture]})"
            )

    # Calculate centroids for top object types
    object_counts = df['vlm_dominant_blue_object'].value_counts()
    top_objects = object_counts.head(5).index.tolist()

    print(f"  Top 5 object types: {', '.join([f'{obj} (n={object_counts[obj]})' for obj in top_objects])}")

    # Annotate top object types at their centroids
    for obj in top_objects:
        obj_df = df[df['vlm_dominant_blue_object'] == obj]
        centroid_x = obj_df['umap_x'].mean()  # Use base UMAP coords, not jittered
        centroid_y = obj_df['umap_y'].mean()

        ax.annotate(
            f"{obj}\n(n={len(obj_df)})",
            xy=(centroid_x, centroid_y),
            fontsize=9,
            ha='center',
            va='center',
            bbox=dict(boxstyle='round,pad=0.3', facecolor='white', alpha=0.8, edgecolor='gray'),
            zorder=100
        )

    # Styling
    ax.grid(True, alpha=0.3, linestyle='--', linewidth=0.5)
    ax.set_xlabel('')  # UMAP dimensions are not interpretable
    ax.set_ylabel('')
    ax.set_xticks([])
    ax.set_yticks([])

    # Legend
    ax.legend(
        loc='upper right',
        frameon=True,
        facecolor='white',
        edgecolor='gray',
        framealpha=0.9,
        fontsize=10
    )

    # Title and caption
    ax.set_title(
        '2D Semantic Visualization of Blue Objects in Paintings',
        fontsize=16,
        fontweight='bold',
        pad=20
    )

    caption = (
        "Each point represents one painting, positioned based on semantic similarity of the dominant blue object.\n"
        "Similar objects (e.g., 'water' and 'sea') cluster together naturally. Point color indicates cultural origin.\n"
        "Methodology: Sentence-BERT embeddings → UMAP dimensionality reduction → 2D semantic space."
    )

    fig.text(
        0.5, 0.02,
        caption,
        ha='center',
        fontsize=9,
        style='italic',
        color='gray',
        wrap=True
    )

    plt.tight_layout(rect=[0, 0.05, 1, 1])  # Leave space for caption

    return fig

def print_summary(df):
    """Print summary statistics."""
    print("\n" + "="*60)
    print("SUMMARY STATISTICS")
    print("="*60)

    print(f"\nTotal paintings: {len(df)}")

    print("\nCulture distribution:")
    culture_counts = df['artist_culture'].value_counts()
    for culture, count in culture_counts.items():
        print(f"  {culture:15s}: {count:3d} ({count/len(df)*100:5.1f}%)")

    print(f"\nUnique object types: {df['vlm_dominant_blue_object'].nunique()}")

    print("\nTop 10 object types:")
    object_counts = df['vlm_dominant_blue_object'].value_counts()
    for i, (obj, count) in enumerate(object_counts.head(10).items(), 1):
        print(f"  {i:2d}. {obj:30s}: {count:3d} ({count/len(df)*100:5.1f}%)")

    print("\n" + "="*60)

def main():
    """Main execution pipeline."""
    print("\n" + "="*60)
    print("2D SEMANTIC VISUALIZATION OF BLUE OBJECTS")
    print("="*60)

    # Load data
    df = load_data(INPUT_FILE)

    # Generate semantic embeddings
    embeddings_dict = generate_embeddings(df['vlm_dominant_blue_object'])

    # Apply UMAP dimensionality reduction
    df = apply_umap(df, embeddings_dict)

    # Add jitter to prevent overlaps
    df = add_jitter(df)

    # Print summary statistics
    print_summary(df)

    # Create visualization
    fig = create_visualization(df)

    # Save output
    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"\nSaving visualization to {OUTPUT_FILE}...")
    fig.savefig(OUTPUT_FILE, dpi=DPI, bbox_inches='tight', facecolor='white')
    print(f"  Saved successfully: {FIG_WIDTH}\" × {FIG_HEIGHT}\" at {DPI} DPI")
    print(f"  File size: {output_path.stat().st_size / 1024:.1f} KB")

    print("\n" + "="*60)
    print("VISUALIZATION COMPLETE")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
