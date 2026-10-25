"""
Plotting script for Thesis Chapter 5: Experimental Results and Discussion.
Reads directly from authoritative JSON result files in eval/results/:
- rq1_extraction_20261024_000639.json
- rq2_chunking_20261024_013443.json
- thesis_embedding_benchmark.json

Outputs publication-quality PNG figures into docs/figures/ and eval/results/figures/.
"""

import json
import os
import matplotlib.pyplot as plt
import numpy as np

# Configure matplotlib publication styling
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Helvetica']
plt.rcParams['axes.edgecolor'] = '#333333'
plt.rcParams['axes.linewidth'] = 0.8
plt.rcParams['grid.color'] = '#e2e8f0'
plt.rcParams['grid.linestyle'] = '--'
plt.rcParams['grid.alpha'] = 0.75

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
RESULTS_DIR = os.path.join(BASE_DIR, "eval", "results")
DOCS_FIG_DIR = os.path.join(BASE_DIR, "docs", "figures")
EVAL_FIG_DIR = os.path.join(RESULTS_DIR, "figures")

os.makedirs(DOCS_FIG_DIR, exist_ok=True)
os.makedirs(EVAL_FIG_DIR, exist_ok=True)


def plot_rq1_figures():
    path = os.path.join(RESULTS_DIR, "rq1_extraction_20261024_000639.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    engines_data = [e for e in data["summary"] if e.get("available", False)]
    
    engine_names = {
        "pymupdf_plain": "PyMuPDF (Plain Text)",
        "pymupdf_layout": "PyMuPDF (Layout-Aware)",
        "pypdf": "pypdf (Pure Python)",
        "pdfminer.six": "pdfminer.six",
        "pdfplumber": "pdfplumber"
    }

    names = [engine_names.get(e["engine"], e["engine"]) for e in engines_data]
    ndcg10_means = [e["downstream_ndcg10"]["mean"] for e in engines_data]
    ci_lows = [e["downstream_ndcg10"]["mean"] - e["downstream_ndcg10"]["ci_95"][0] for e in engines_data]
    ci_highs = [e["downstream_ndcg10"]["ci_95"][1] - e["downstream_ndcg10"]["mean"] for e in engines_data]
    latencies = [e["latency_per_page_ms"] for e in engines_data]

    # Sort by nDCG@10 for graph A
    sort_idx = np.argsort(ndcg10_means)
    sorted_names = [names[i] for i in sort_idx]
    sorted_ndcg = [ndcg10_means[i] for i in sort_idx]
    sorted_err = [[ci_lows[i] for i in sort_idx], [ci_highs[i] for i in sort_idx]]

    # 1. Plot Downstream nDCG@10
    fig, ax = plt.subplots(figsize=(9.2, 4.4), dpi=300)
    y_pos = np.arange(len(sorted_names))
    
    ax.errorbar(sorted_ndcg, y_pos, xerr=sorted_err, fmt='o', color='#1a365d',
                ecolor='#2b6cb0', elinewidth=2, capsize=5, capthick=1.5, markersize=8, zorder=3)
    
    for i, val in enumerate(sorted_ndcg):
        ax.text(val + 0.012, i - 0.10, f"{val:.4f}", fontsize=9, fontweight='bold', color='#1a365d')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_names, fontsize=10)
    ax.set_xlabel("Chỉ số nDCG@10 truy xuất hạ nguồn (Kèm khoảng tin cậy 95% CI)", fontsize=10.5, labelpad=8)
    ax.set_title("Hình 5.1: So sánh chất lượng truy xuất hạ nguồn (nDCG@10) giữa các bộ trích xuất PDF (RQ1)", fontsize=11, pad=12, fontweight='bold')
    ax.set_xlim(0.25, 0.65)
    ax.grid(True, axis='x')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    
    plt.tight_layout()
    fig.savefig(os.path.join(DOCS_FIG_DIR, "fig5_1_rq1_ndcg10.png"), bbox_inches='tight')
    fig.savefig(os.path.join(EVAL_FIG_DIR, "fig5_1_rq1_ndcg10.png"), bbox_inches='tight')
    plt.close(fig)

    # 2. Plot Latency per page
    lat_sort_idx = np.argsort(latencies)
    lat_names = [names[i] for i in lat_sort_idx]
    lat_vals = [latencies[i] for i in lat_sort_idx]

    fig, ax = plt.subplots(figsize=(9.2, 4.2), dpi=300)
    y_pos = np.arange(len(lat_names))
    bar_colors = ['#2b6cb0' if 'PyMuPDF' in n else '#cbd5e0' for n in lat_names]

    bars = ax.barh(y_pos, lat_vals, color=bar_colors, height=0.55, edgecolor='#333333', linewidth=0.8, zorder=3)
    for bar, val in zip(bars, lat_vals):
        ax.text(val + 3.0, bar.get_y() + bar.get_height()/2 - 0.08, f"{val:.2f} ms/trang", fontsize=9, fontweight='bold', color='#2d3748')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(lat_names, fontsize=10)
    ax.set_xlabel("Thời gian xử lý trung bình mỗi trang (ms/trang) — Thấp hơn là tốt hơn", fontsize=10.5, labelpad=8)
    ax.set_title("Hình 5.2: Tốc độ xử lý trích xuất văn bản PDF trên CPU AMD Ryzen 5 5600 (RQ1)", fontsize=11, pad=12, fontweight='bold')
    ax.set_xlim(0, 240)
    ax.grid(True, axis='x')
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(DOCS_FIG_DIR, "fig5_2_rq1_latency.png"), bbox_inches='tight')
    fig.savefig(os.path.join(EVAL_FIG_DIR, "fig5_2_rq1_latency.png"), bbox_inches='tight')
    plt.close(fig)


def plot_rq2_figures():
    path = os.path.join(RESULTS_DIR, "rq2_chunking_20261024_013443.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    strategy_names = {
        "fixed_size": "fixed_size (Chuẩn đối chứng)",
        "fixed_size_overlap": "fixed_size_overlap",
        "semantic": "semantic (Ngưỡng ngữ nghĩa)",
        "section": "section (Đề mục thô)",
        "section_token": "section_token",
        "section_overlap": "section_overlap (Hệ thống chạy)",
        "hierarchical": "hierarchical (Small-to-Big)",
        "hierarchical_child": "hierarchical_child (Không gộp cha)"
    }

    strategies = data["summary"]
    names = [strategy_names.get(s["strategy"], s["strategy"]) for s in strategies]
    ndcg10_means = [s["primary_metrics"]["ndcg10"]["mean"] for s in strategies]
    ci_lows = [s["primary_metrics"]["ndcg10"]["mean"] - s["primary_metrics"]["ndcg10"]["ci_95"][0] for s in strategies]
    ci_highs = [s["primary_metrics"]["ndcg10"]["ci_95"][1] - s["primary_metrics"]["ndcg10"]["mean"] for s in strategies]
    sens_ndcg10 = [s["sensitivity_metrics"]["ndcg10"] for s in strategies]

    # Sort by primary nDCG@10 (tau=0.50)
    sort_idx = np.argsort(ndcg10_means)
    sorted_names = [names[i] for i in sort_idx]
    sorted_ndcg = [ndcg10_means[i] for i in sort_idx]
    sorted_sens = [sens_ndcg10[i] for i in sort_idx]
    sorted_err = [[ci_lows[i] for i in sort_idx], [ci_highs[i] for i in sort_idx]]

    baseline_val = next(s["primary_metrics"]["ndcg10"]["mean"] for s in strategies if s["strategy"] == "fixed_size")

    fig, ax = plt.subplots(figsize=(10.0, 5.8), dpi=300)
    y_pos = np.arange(len(sorted_names))

    # Plot baseline reference line
    ax.axvline(x=baseline_val, color='#e53e3e', linestyle='--', linewidth=1.5, alpha=0.85, label=f"Mốc đối chứng fixed_size ({baseline_val:.4f})", zorder=2)

    # Plot primary tau=0.50 dot-and-whisker
    ax.errorbar(sorted_ndcg, y_pos, xerr=sorted_err, fmt='o', color='#2b6cb0',
                ecolor='#4299e1', elinewidth=2, capsize=5, capthick=1.5, markersize=8, zorder=4,
                label="Ngưỡng chính τ = 0.50 (Mean ± 95% CI Bootstrap)")

    # Plot sensitivity tau=0.30 points
    ax.scatter(sorted_sens, y_pos, color='#ed8936', marker='s', s=45, zorder=5,
               label="Phân tích độ nhạy τ = 0.30")

    # Annotate primary values cleanly above the dot to prevent marker overlap
    for i, val in enumerate(sorted_ndcg):
        ax.text(val + 0.008, i + 0.18, f"{val:.4f}", fontsize=8.5, fontweight='bold', color='#1a365d')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_names, fontsize=9.5)
    ax.set_xlabel("Chỉ số nDCG@10 (Đánh giá trên ngân sách 1600 tokens cố định)", fontsize=10.5, labelpad=8)
    ax.set_title("Hình 5.3: Biểu đồ Dot-and-Whisker so sánh nDCG@10 giữa 8 chiến lược phân mảnh văn bản (RQ2)", fontsize=11, pad=14, fontweight='bold')
    ax.set_xlim(0.35, 0.80)
    ax.set_ylim(-0.6, len(sorted_names) - 0.2)
    ax.grid(True, axis='x')
    ax.legend(loc='lower right', frameon=True, fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(DOCS_FIG_DIR, "fig5_3_rq2_chunking_ndcg10.png"), bbox_inches='tight')
    fig.savefig(os.path.join(EVAL_FIG_DIR, "fig5_3_rq2_chunking_ndcg10.png"), bbox_inches='tight')
    plt.close(fig)


def plot_rq3_figures():
    path = os.path.join(RESULTS_DIR, "thesis_embedding_benchmark.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    models = data["models"]

    names = [m["short_name"] for m in models]
    ndcg10 = [m["metrics"]["ndcg10"]["mean"] for m in models]
    ci_lows = [m["metrics"]["ndcg10"]["mean"] - m["metrics"]["ndcg10"]["ci_95"][0] for m in models]
    ci_highs = [m["metrics"]["ndcg10"]["ci_95"][1] - m["metrics"]["ndcg10"]["mean"] for m in models]
    latencies = [m["efficiency"]["query_latency_p50_ms"] for m in models]
    peak_rams = [m["efficiency"]["peak_ram_mb"] for m in models]

    sort_idx = np.argsort(ndcg10)
    sorted_names = [names[i] for i in sort_idx]
    sorted_ndcg = [ndcg10[i] for i in sort_idx]
    sorted_err = [[ci_lows[i] for i in sort_idx], [ci_highs[i] for i in sort_idx]]
    sorted_models = [models[i] for i in sort_idx]

    baseline_val = next(m["metrics"]["ndcg10"]["mean"] for m in models if m["id"] == "all-MiniLM-L6-v2")

    # Figure A: Retrieval quality
    fig, ax = plt.subplots(figsize=(10.0, 6.4), dpi=300)
    y_pos = np.arange(len(sorted_names))

    ax.axvline(x=baseline_val, color='#e53e3e', linestyle='--', linewidth=1.5, alpha=0.85, label=f"Baseline MiniLM-L6-v2 ({baseline_val:.4f})", zorder=2)

    point_colors = []
    for m in sorted_models:
        if m["id"] == "all-MiniLM-L6-v2":
            point_colors.append('#e53e3e')
        elif m["id"] == "bm25":
            point_colors.append('#718096')
        elif m["id"] == "e5-small-v2":
            point_colors.append('#2b6cb0')
        elif m["id"] == "modernbert-embed-base":
            point_colors.append('#2f855a')
        else:
            point_colors.append('#4a5568')

    ax.errorbar(sorted_ndcg, y_pos, xerr=sorted_err, fmt='none', ecolor='#a0aec0', elinewidth=1.8, capsize=4, zorder=3)
    ax.scatter(sorted_ndcg, y_pos, color=point_colors, s=65, zorder=4)

    for i, (val, name) in enumerate(zip(sorted_ndcg, sorted_names)):
        weight = 'bold' if name in ['MiniLM-L6', 'E5-Small-v2', 'ModernBERT-Embed', 'BM25'] else 'normal'
        ax.text(val + 0.007, i - 0.12, f"{val:.4f}", fontsize=8.5, fontweight=weight, color='#1a202c')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(sorted_names, fontsize=9.5)
    ax.set_xlabel("Chỉ số nDCG@10 (Đo lường trên tập 207 bài báo / 615 câu hỏi / 5.207 chunks)", fontsize=10.5, labelpad=8)
    ax.set_title("Hình 5.4: So sánh chất lượng truy xuất (nDCG@10 ± 95% CI) của 11 mô hình biểu diễn vector (RQ3)", fontsize=11, pad=14, fontweight='bold')
    ax.set_xlim(0.40, 0.65)
    ax.grid(True, axis='x')
    ax.legend(loc='lower right', frameon=True, fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(DOCS_FIG_DIR, "fig5_4_rq3_embedding_ndcg10.png"), bbox_inches='tight')
    fig.savefig(os.path.join(EVAL_FIG_DIR, "fig5_4_rq3_embedding_ndcg10.png"), bbox_inches='tight')
    plt.close(fig)

    # Figure B: Quality vs Cost Trade-off (Pareto)
    fig, ax = plt.subplots(figsize=(10.0, 6.0), dpi=300)

    dense_models = [m for m in models if m["type"] != "sparse"]
    d_lat = [m["efficiency"]["query_latency_p50_ms"] for m in dense_models]
    d_ndcg = [m["metrics"]["ndcg10"]["mean"] for m in dense_models]
    d_names = [m["short_name"] for m in dense_models]
    d_rams = [m["efficiency"]["peak_ram_mb"] for m in dense_models]

    scatter = ax.scatter(d_lat, d_ndcg, c=d_rams, cmap='viridis', s=130, edgecolors='#2d3748', linewidth=1.2, zorder=4)
    cbar = plt.colorbar(scatter, ax=ax, pad=0.02)
    cbar.set_label("Bộ nhớ Process Peak RSS (MB)", fontsize=10, labelpad=8)

    # Highlight Pareto frontier candidates
    pareto_candidates = ["MiniLM-L6", "E5-Small-v2", "Arctic-Embed-M-v1.5", "ModernBERT-Embed"]
    pareto_points = sorted([(m["efficiency"]["query_latency_p50_ms"], m["metrics"]["ndcg10"]["mean"]) 
                            for m in dense_models if m["short_name"] in pareto_candidates], key=lambda x: x[0])
    
    px, py = zip(*pareto_points)
    ax.plot(px, py, '--', color='#e53e3e', linewidth=1.5, alpha=0.75, label='Đường biên Pareto (Chất lượng vs Độ trễ)', zorder=2)

    # Optimized text offsets
    offsets = {
        "MiniLM-L6": (6, -0.007),
        "E5-Small-v2": (-12, 0.007),
        "BGE-Small-v1.5": (6, -0.010),
        "GTE-Small": (6, 0.004),
        "Arctic-Embed-S": (6, 0.005),
        "Arctic-Embed-M-v1.5": (6, -0.008),
        "Nomic-Embed-v1.5": (6, -0.008),
        "ModernBERT-Embed": (-55, 0.007),
        "Arctic-Embed-M-v2.0": (6, -0.010),
        "MXBAI-Large-v1": (-50, -0.010)
    }

    for name, x, y in zip(d_names, d_lat, d_ndcg):
        ox, oy = offsets.get(name, (6, 0))
        weight = 'bold' if name in pareto_candidates else 'normal'
        ax.annotate(name, (x, y), xytext=(x + ox, y + oy), fontsize=8.8, fontweight=weight, color='#1a202c', zorder=5)

    ax.set_xlabel("Độ trễ mã hóa câu truy vấn P50 (ms, kích thước lô B=1) — Thấp hơn là tốt hơn", fontsize=10.5, labelpad=8)
    ax.set_ylabel("Chất lượng truy xuất nDCG@10 — Cao hơn là tốt hơn", fontsize=10.5, labelpad=8)
    ax.set_title("Hình 5.5: Đánh đổi Chất lượng (nDCG@10) và Chi phí tính toán (Độ trễ P50) trên CPU Ryzen 5 5600 (RQ3)", fontsize=11, pad=14, fontweight='bold')
    ax.set_ylim(0.45, 0.61)
    ax.set_xlim(10, 295)
    ax.grid(True)
    ax.legend(loc='lower right', frameon=True, fontsize=9)
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)

    plt.tight_layout()
    fig.savefig(os.path.join(DOCS_FIG_DIR, "fig5_5_rq3_quality_cost.png"), bbox_inches='tight')
    fig.savefig(os.path.join(EVAL_FIG_DIR, "fig5_5_rq3_quality_cost.png"), bbox_inches='tight')
    plt.close(fig)


if __name__ == "__main__":
    print("Generating Chapter 5 publication figures...")
    plot_rq1_figures()
    print("[OK] RQ1 figures generated.")
    plot_rq2_figures()
    print("[OK] RQ2 figures generated.")
    plot_rq3_figures()
    print("[OK] RQ3 figures generated.")
    print("All figures successfully saved to docs/figures/ and eval/results/figures/.")
