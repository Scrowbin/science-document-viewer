"""
Plot Pareto Frontier for Thesis Embedding Benchmark.

Reads: eval/results/thesis_embedding_benchmark.json
Generates:
  - eval/results/figures/pareto_ndcg10_vs_latency.png (and .pdf)
  - eval/results/figures/pareto_ndcg10_vs_throughput.png (and .pdf)

Visualizes accuracy (nDCG@10) vs computational efficiency (query latency, indexing throughput),
identifying Pareto-optimal candidate architectures on local AMD Ryzen 5 5600 CPU.
"""

import json
import os
import sys
from typing import Any, Dict, List, Tuple

import matplotlib.pyplot as plt
import numpy as np

# Apply clean academic styling
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]
plt.rcParams["axes.edgecolor"] = "#333333"
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["grid.color"] = "#E0E0E0"
plt.rcParams["grid.linestyle"] = "--"
plt.rcParams["grid.alpha"] = 0.7


def compute_pareto_frontier(
    points: List[Tuple[float, float, str]],
    maximize_x: bool = False,
    maximize_y: bool = True,
) -> List[Tuple[float, float, str]]:
    """
    Computes 2D Pareto optimal frontier.
    x is latency (minimize) or throughput (maximize).
    y is nDCG@10 (maximize).
    """
    # Sort points:
    # If minimizing x, sort ascending x; if maximizing x, sort descending x
    sorted_pts = sorted(
        points,
        key=lambda p: (p[0] if not maximize_x else -p[0], -p[1]),
    )

    frontier = []
    current_max_y = -float("inf")

    for x, y, label in sorted_pts:
        if y > current_max_y:
            frontier.append((x, y, label))
            current_max_y = y

    # Sort frontier by x for continuous line plotting
    frontier = sorted(frontier, key=lambda p: p[0])
    return frontier


def generate_pareto_plots(json_path: str, output_dir: str):
    os.makedirs(output_dir, exist_ok=True)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    models_data: List[Dict[str, Any]] = data.get("models", [])
    if not models_data:
        print(f"[ERR] No model data found in {json_path}")
        return

    # Palette
    color_map = {
        "bm25": "#7F7F7F",                     # Gray
        "all-MiniLM-L6-v2": "#1F77B4",         # Classic Blue (Baseline)
        "e5-small-v2": "#2CA02C",              # Green (Champion)
        "bge-small-en-v1.5": "#FF7F0E",        # Orange
        "gte-small": "#9467BD",                # Purple
        "snowflake-arctic-embed-s": "#17BECF", # Cyan
        "snowflake-arctic-embed-m-v1.5": "#BCBD22", # Olive
        "nomic-embed-text-v1.5": "#E377C2",   # Pink
        "modernbert-embed-base": "#D62728",   # Red
        "snowflake-arctic-embed-m-v2.0": "#8C564B", # Brown
        "mxbai-embed-large-v1": "#393B79",    # Dark Navy
    }

    # -------------------------------------------------------------
    # Plot 1: Accuracy (nDCG@10) vs Single-Query Latency P50 (ms)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)

    latency_points = []
    for m in models_data:
        m_id = m["id"]
        short_name = m.get("short_name", m["name"].split("/")[-1])
        y = m["metrics"]["ndcg10"]["mean"]
        x = m["efficiency"]["query_latency_p50_ms"]
        params = m.get("params_m", 0.0)
        latency_points.append((x, y, short_name, m_id, params))

    # Compute Pareto frontier (minimize latency, maximize accuracy)
    pareto_pts = compute_pareto_frontier(
        [(x, y, name) for x, y, name, _, _ in latency_points],
        maximize_x=False,
        maximize_y=True,
    )

    # Plot frontier step line
    fx = [p[0] for p in pareto_pts]
    fy = [p[1] for p in pareto_pts]
    ax.plot(fx, fy, linestyle="--", color="#2CA02C", alpha=0.7, linewidth=1.8, zorder=2, label="Pareto Frontier")

    # Plot scatter points
    for x, y, name, m_id, params in latency_points:
        color = color_map.get(m_id, "#333333")
        size = max(60, min(300, params * 1.5 + 60))
        marker = "s" if m_id == "bm25" else "o"

        ax.scatter(x, y, s=size, color=color, alpha=0.9, edgecolors="#222222", linewidth=1.2, zorder=3)

        # Smart label offsets
        offset_x, offset_y = 5, 5
        if "e5-small" in m_id:
            offset_y = 7
        elif "MiniLM" in m_id:
            offset_y = -14
        elif "bge-small" in m_id:
            offset_y = -12
            offset_x = 4

        ax.annotate(
            f"{name} ({params}M)" if params > 0 else name,
            (x, y),
            xytext=(offset_x, offset_y),
            textcoords="offset points",
            fontsize=8.5,
            fontweight="bold" if m_id in ["e5-small-v2", "all-MiniLM-L6-v2"] else "normal",
            color="#111111",
            zorder=4,
        )

    ax.set_title("Pareto Frontier: Accuracy vs. Single-Query Latency (AMD Ryzen 5 5600, 4 Threads)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Single-Query Latency P50 (ms, batch_size=1) [Lower is Better]", fontsize=11, labelpad=8)
    ax.set_ylabel("Retrieval Accuracy (nDCG@10) [Higher is Better]", fontsize=11, labelpad=8)
    ax.grid(True)
    ax.legend(loc="lower right", framealpha=0.9)

    plt.tight_layout()
    p1_png = os.path.join(output_dir, "pareto_ndcg10_vs_latency.png")
    p1_pdf = os.path.join(output_dir, "pareto_ndcg10_vs_latency.pdf")
    plt.savefig(p1_png, dpi=300)
    plt.savefig(p1_pdf)
    plt.close()
    print(f"[OK] Saved {p1_png} and {p1_pdf}")

    # -------------------------------------------------------------
    # Plot 2: Accuracy (nDCG@10) vs Indexing Throughput (chunks/sec)
    # -------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(10, 6.5), dpi=300)

    tp_points = []
    for m in models_data:
        m_id = m["id"]
        short_name = m.get("short_name", m["name"].split("/")[-1])
        y = m["metrics"]["ndcg10"]["mean"]
        x = m["efficiency"]["indexing_throughput_chunks_sec"]
        params = m.get("params_m", 0.0)
        tp_points.append((x, y, short_name, m_id, params))

    # Compute Pareto frontier (maximize throughput, maximize accuracy)
    pareto_pts_tp = compute_pareto_frontier(
        [(x, y, name) for x, y, name, _, _ in tp_points],
        maximize_x=True,
        maximize_y=True,
    )

    fx_tp = [p[0] for p in pareto_pts_tp]
    fy_tp = [p[1] for p in pareto_pts_tp]
    ax.plot(fx_tp, fy_tp, linestyle="--", color="#1F77B4", alpha=0.7, linewidth=1.8, zorder=2, label="Pareto Frontier")

    for x, y, name, m_id, params in tp_points:
        color = color_map.get(m_id, "#333333")
        size = max(60, min(300, params * 1.5 + 60))
        marker = "s" if m_id == "bm25" else "o"

        ax.scatter(x, y, s=size, color=color, alpha=0.9, edgecolors="#222222", linewidth=1.2, zorder=3)

        offset_x, offset_y = 5, 5
        if "e5-small" in m_id:
            offset_y = 7
        elif "MiniLM" in m_id:
            offset_y = -14

        ax.annotate(
            f"{name} ({params}M)" if params > 0 else name,
            (x, y),
            xytext=(offset_x, offset_y),
            textcoords="offset points",
            fontsize=8.5,
            fontweight="bold" if m_id in ["e5-small-v2", "all-MiniLM-L6-v2"] else "normal",
            color="#111111",
            zorder=4,
        )

    ax.set_title("Pareto Frontier: Accuracy vs. Document Indexing Throughput (AMD Ryzen 5 5600, 4 Threads)", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Document Indexing Throughput (chunks/sec, batch_size=32) [Higher is Better]", fontsize=11, labelpad=8)
    ax.set_ylabel("Retrieval Accuracy (nDCG@10) [Higher is Better]", fontsize=11, labelpad=8)
    ax.grid(True)
    ax.legend(loc="lower left", framealpha=0.9)

    plt.tight_layout()
    p2_png = os.path.join(output_dir, "pareto_ndcg10_vs_throughput.png")
    p2_pdf = os.path.join(output_dir, "pareto_ndcg10_vs_throughput.pdf")
    plt.savefig(p2_png, dpi=300)
    plt.savefig(p2_pdf)
    plt.close()
    print(f"[OK] Saved {p2_png} and {p2_pdf}")


if __name__ == "__main__":
    benchmark_json = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "eval", "results", "thesis_embedding_benchmark.json")
    out_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "..", "eval", "results", "figures")
    if len(sys.argv) > 1:
        benchmark_json = sys.argv[1]
    if len(sys.argv) > 2:
        out_dir = sys.argv[2]

    generate_pareto_plots(os.path.abspath(benchmark_json), os.path.abspath(out_dir))
