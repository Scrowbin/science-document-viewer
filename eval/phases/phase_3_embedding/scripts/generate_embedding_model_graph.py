"""
Generate publication-quality grouped bar charts matching user reference style.
Compares Top 3 Embedding Models (e5-small-v2, bge-small-en-v1.5, all-MiniLM-L6-v2)
across Precision, Recall, F1, and nDCG on the QASPER 159-paper / 487-query benchmark.
Generates both @5 (matching reference image) and @4 (matching LLM prompt budget).
"""

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Set publication style
plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica"]

colors = {
    "e5-small-v2": "#16a085",        # Teal / Emerald
    "bge-small-en-v1.5": "#e7785c",  # Coral / Salmon
    "all-MiniLM-L6-v2": "#806fad",   # Slate Purple
}

labels = {
    "e5-small-v2": "e5-small-v2",
    "bge-small-en-v1.5": "bge-small-en-v1.5",
    "all-MiniLM-L6-v2": "all-MiniLM-L6-v2",
}

def plot_grouped_chart(metrics, scores, title, y_max, out_filename):
    x = np.arange(len(metrics))
    width = 0.24  # bar width

    fig, ax = plt.subplots(figsize=(13, 7.2), dpi=300)
    fig.patch.set_facecolor("white")
    ax.set_facecolor("white")

    rects1 = ax.bar(x - width, scores["e5-small-v2"], width, label=labels["e5-small-v2"], color=colors["e5-small-v2"], zorder=3)
    rects2 = ax.bar(x, scores["bge-small-en-v1.5"], width, label=labels["bge-small-en-v1.5"], color=colors["bge-small-en-v1.5"], zorder=3)
    rects3 = ax.bar(x + width, scores["all-MiniLM-L6-v2"], width, label=labels["all-MiniLM-L6-v2"], color=colors["all-MiniLM-L6-v2"], zorder=3)

    def autolabel(rects):
        for rect in rects:
            height = rect.get_height()
            ax.annotate(
                f"{height:.3f}",
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9.5,
                color="#4a5568",
                fontweight="normal",
            )

    autolabel(rects1)
    autolabel(rects2)
    autolabel(rects3)

    ax.set_title(title, fontsize=14, fontweight="bold", pad=25, color="#1a202c")
    ax.set_ylabel("Score", fontsize=11, color="#2d3748", labelpad=10)
    ax.set_xticks(x)
    ax.set_xticklabels(metrics, fontsize=11, color="#2d3748")

    ax.set_ylim(0.0, y_max)
    ax.set_yticks(np.arange(0.0, y_max + 0.01, 0.1))
    ax.tick_params(axis="y", labelsize=10, colors="#4a5568")
    ax.tick_params(axis="x", labelsize=11, colors="#2d3748", length=0)

    ax.yaxis.grid(True, linestyle="--", alpha=0.35, color="#cbd5e1", zorder=0)
    ax.xaxis.grid(False)

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)
    ax.spines["bottom"].set_color("#cbd5e1")
    ax.spines["bottom"].set_linewidth(1.0)

    ax.legend(
        loc="upper right",
        frameon=False,
        fontsize=10.5,
        handlelength=1.4,
        handleheight=0.8,
        labelcolor="#2d3748",
    )

    plt.tight_layout()

    out_dir = Path("eval/figures")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / out_filename
    plt.savefig(out_path, dpi=300, bbox_inches="tight")
    print(f"[SUCCESS] Saved figure to {out_path}")

    artifact_dir = Path(r"C:\Users\HJII\.gemini\antigravity-ide\brain\b1b653ac-9e4b-48d3-b774-19f02437c845")
    artifact_path = artifact_dir / out_filename
    plt.savefig(artifact_path, dpi=300, bbox_inches="tight")
    print(f"[SUCCESS] Saved copy to artifact directory: {artifact_path}")
    plt.close()


if __name__ == "__main__":
    # 1. Plot @5 (exact mirror of reference image)
    metrics_5 = ["Precision@5", "Recall@5", "F1@5", "nDCG@5"]
    scores_5 = {
        "e5-small-v2": [0.179, 0.609, 0.257, 0.466],
        "bge-small-en-v1.5": [0.171, 0.574, 0.245, 0.426],
        "all-MiniLM-L6-v2": [0.166, 0.549, 0.237, 0.405],
    }
    plot_grouped_chart(metrics_5, scores_5, "Embedding Model Performance Comparison (QASPER / @5 Metrics)", 0.70, "embedding_model_performance_comparison.png")

    # 2. Plot @4 (prompt context budget)
    metrics_4 = ["Precision@4", "Recall@4", "F1@4", "nDCG@4"]
    scores_4 = {
        "e5-small-v2": [0.200, 0.556, 0.273, 0.446],
        "bge-small-en-v1.5": [0.185, 0.499, 0.250, 0.397],
        "all-MiniLM-L6-v2": [0.179, 0.486, 0.244, 0.379],
    }
    plot_grouped_chart(metrics_4, scores_4, "Embedding Model Performance Comparison (QASPER / @4 Context Budget)", 0.70, "embedding_model_performance_comparison_at_4.png")
