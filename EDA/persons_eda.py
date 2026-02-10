"""
EDA script for Harvard Art Museums person data.
Plots top 20 artists by object count, excluding unidentified/anonymous entries.
"""

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np

# Exclusion patterns (case-insensitive substring match on displayname)
EXCLUDE_PATTERNS = (
    "unidentified",
    "anonymous",
    "unknown artist",
    "attributed to",
    "style of",
    "workshop of",
    "school of",
    "circle of",
    "follower of",
)


def is_excluded(displayname: str | None) -> bool:
    """Return True if person should be excluded from top-artist rankings."""
    if not displayname:
        return True
    lower = displayname.lower()
    return any(pattern in lower for pattern in EXCLUDE_PATTERNS)


def main():
    data_path = Path(__file__).parent / "all_persons.json"
    output_path = Path(__file__).parent / "top_20_artists_by_objects.png"

    with open(data_path) as f:
        persons = json.load(f)

    # Filter out excluded names, sort by objectcount descending
    filtered = [
        p
        for p in persons
        if not is_excluded(p.get("displayname"))
    ]
    top_20 = sorted(filtered, key=lambda p: p["objectcount"], reverse=True)[:20]

    names = [p["displayname"] for p in top_20]
    counts = [p["objectcount"] for p in top_20]

    # Horizontal bar chart (readable for 20 names)
    fig, ax = plt.subplots(figsize=(10, 8))
    y_pos = np.arange(len(names))[::-1]  # Top artist at top
    bars = ax.barh(y_pos, counts, color="steelblue", edgecolor="navy", alpha=0.85)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=11)
    ax.set_xlabel("Number of objects in collection", fontsize=12)
    ax.set_title("Top 20 Artists by Object Count\n(excluding unidentified/anonymous)", fontsize=14)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    # Optional: add count labels at end of bars
    for bar, count in zip(bars, counts):
        ax.text(bar.get_width() + max(counts) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{count:,}", va="center", fontsize=9, fontweight="medium")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
