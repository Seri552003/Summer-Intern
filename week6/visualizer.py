# visualizer.py
# Charts aur Graphs banao pipeline results ke liye
# Week 6 | LLM-CAPP Project

import sys
import os
import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week3")))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../week4")))

from agents import time_agent, cost_agent, energy_agent
from nsga2 import ROUTE_VARIANTS


def load_results(path: str) -> dict:
    with open(path, "r") as f:
        return json.load(f)


def plot_route_comparison(material: str = "Aluminum", batch_size: int = 500):
    """Bar chart — saare routes ka Time/Cost/Energy comparison."""
    routes = list(ROUTE_VARIANTS.keys())
    times   = [time_agent(ROUTE_VARIANTS[r], material) for r in routes]
    costs   = [cost_agent(ROUTE_VARIANTS[r], material, batch_size) for r in routes]
    energies = [energy_agent(ROUTE_VARIANTS[r], material) for r in routes]

    x = np.arange(len(routes))
    width = 0.25

    fig, ax = plt.subplots(figsize=(12, 6))
    fig.patch.set_facecolor('#0d0f1a')
    ax.set_facecolor('#13162a')

    b1 = ax.bar(x - width, times,   width, label='Time (min)',    color='#f97316', alpha=0.85)
    b2 = ax.bar(x,         costs,   width, label='Cost ($)',      color='#60a5fa', alpha=0.85)
    b3 = ax.bar(x + width, energies,width, label='Energy (kWh)',  color='#34d399', alpha=0.85)

    ax.set_xlabel('Route', color='#9ba3bf', fontsize=11)
    ax.set_ylabel('Value', color='#9ba3bf', fontsize=11)
    ax.set_title(f'Route Comparison — {material}, Batch: {batch_size}',
                 color='#e2e5f0', fontsize=13, fontweight='bold', pad=15)
    ax.set_xticks(x)
    ax.set_xticklabels(routes, color='#9ba3bf', fontsize=9, rotation=15)
    ax.tick_params(colors='#9ba3bf')
    ax.spines['bottom'].set_color('#252a45')
    ax.spines['left'].set_color('#252a45')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(facecolor='#181c30', edgecolor='#252a45', labelcolor='#e2e5f0')
    ax.yaxis.label.set_color('#9ba3bf')

    plt.tight_layout()
    out = os.path.join(os.path.dirname(__file__), "route_comparison.png")
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#0d0f1a')
    print(f"✅ Saved: route_comparison.png")
    plt.close()


def plot_material_distribution(results_path: str):
    """Pie chart — material distribution in dataset."""
    data = load_results(results_path)
    results = data["results"]

    material_counts = {}
    for r in results:
        if r["success"]:
            mat = r["material"]
            material_counts[mat] = material_counts.get(mat, 0) + 1

    labels = list(material_counts.keys())
    sizes  = list(material_counts.values())
    colors = ['#f97316','#60a5fa','#34d399','#a78bfa','#fbbf24','#f87171','#2dd4bf']

    fig, ax = plt.subplots(figsize=(8, 6))
    fig.patch.set_facecolor('#0d0f1a')
    ax.set_facecolor('#0d0f1a')

    wedges, texts, autotexts = ax.pie(
        sizes, labels=labels, colors=colors[:len(labels)],
        autopct='%1.1f%%', startangle=140,
        textprops={'color': '#e2e5f0', 'fontsize': 10}
    )
    for at in autotexts:
        at.set_color('#0d0f1a')
        at.set_fontweight('bold')

    ax.set_title('Material Distribution — 50 Parts Dataset',
                 color='#e2e5f0', fontsize=13, fontweight='bold', pad=15)

    plt.tight_layout()
    out = os.path.join(os.path.dirname(__file__), "material_distribution.png")
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#0d0f1a')
    print(f"✅ Saved: material_distribution.png")
    plt.close()


def plot_efficiency_histogram(results_path: str):
    """Histogram — efficiency score distribution."""
    data = load_results(results_path)
    results = data["results"]

    efficiencies = [r["efficiency_score"] for r in results if r["success"]]

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor('#0d0f1a')
    ax.set_facecolor('#13162a')

    ax.hist(efficiencies, bins=10, color='#f97316', alpha=0.8, edgecolor='#fb923c')
    ax.axvline(sum(efficiencies)/len(efficiencies), color='#34d399',
               linestyle='--', linewidth=2, label=f'Mean: {sum(efficiencies)/len(efficiencies):.1f}')

    ax.set_xlabel('Efficiency Score (0–100)', color='#9ba3bf', fontsize=11)
    ax.set_ylabel('Number of Parts', color='#9ba3bf', fontsize=11)
    ax.set_title('Efficiency Score Distribution — All 50 Parts',
                 color='#e2e5f0', fontsize=13, fontweight='bold', pad=15)
    ax.tick_params(colors='#9ba3bf')
    ax.spines['bottom'].set_color('#252a45')
    ax.spines['left'].set_color('#252a45')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.legend(facecolor='#181c30', edgecolor='#252a45', labelcolor='#e2e5f0')

    plt.tight_layout()
    out = os.path.join(os.path.dirname(__file__), "efficiency_histogram.png")
    plt.savefig(out, dpi=150, bbox_inches='tight', facecolor='#0d0f1a')
    print(f"✅ Saved: efficiency_histogram.png")
    plt.close()


if __name__ == "__main__":
    print("=== Generating Charts ===\n")

    results_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../data/final_results.json")
    )

    plot_route_comparison("Aluminum", 500)
    plot_material_distribution(results_path)
    plot_efficiency_histogram(results_path)

    print("\n✅ All 3 charts generated in week6/ folder!")