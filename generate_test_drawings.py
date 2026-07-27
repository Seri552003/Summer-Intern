"""
generate_test_drawings.py
Generates simple synthetic 2D engineering-drawing-style PNGs for testing
vision_extractor.py.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = "sample_drawings"


def draw_title_block(ax, part_name, material, tolerance, x, y, width, height=1.2):
    box = patches.Rectangle((x, y), width, height, linewidth=1,
                             edgecolor="black", facecolor="none")
    ax.add_patch(box)
    ax.text(x + 0.1, y + height - 0.3, f"Part: {part_name}", fontsize=8, family="monospace")
    ax.text(x + 0.1, y + height - 0.6, f"Material: {material}", fontsize=8, family="monospace")
    ax.text(x + 0.1, y + height - 0.9, f"Tolerance: {tolerance}", fontsize=8, family="monospace")


def draw_flange_plate(save_path):
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.set_xlim(0, 10); ax.set_ylim(0, 8); ax.set_aspect("equal"); ax.axis("off")
    ax.add_patch(patches.Rectangle((2, 3), 6, 4, linewidth=1.5, edgecolor="black", facecolor="none"))
    chamfer = patches.Polygon([[8, 7], [7.3, 7], [8, 6.3]], closed=True,
                               facecolor="white", edgecolor="black", linewidth=1.5)
    ax.add_patch(chamfer)
    hole_positions = [(3, 4), (7, 4), (3, 6), (7, 6)]
    for i, (hx, hy) in enumerate(hole_positions):
        ax.add_patch(patches.Circle((hx, hy), 0.35, fill=False, edgecolor="black", linewidth=1.2))
        if i == 0:
            ax.add_patch(patches.Circle((hx, hy), 0.55, fill=False, edgecolor="black",
                                         linewidth=1.0, linestyle="--"))
    ax.annotate("", xy=(2, 2.5), xytext=(8, 2.5), arrowprops=dict(arrowstyle="<->"))
    ax.text(4.7, 2.2, "150 mm", fontsize=8)
    draw_title_block(ax, "Flange Plate", "Steel", "0.02mm", 2, 0.3, 6)
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    plt.savefig(save_path, dpi=200, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    draw_flange_plate(os.path.join(OUTPUT_DIR, "flange_plate.png"))
    print(f"Saved test drawing to {OUTPUT_DIR}/")