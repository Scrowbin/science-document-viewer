#!/usr/bin/env python3
"""
Figures for thesis Chapter 5, generated from the experiment result files (no numbers are typed in by hand,
except the PeerQA/QASPER labels). Descriptive charts only.

Output: reports/thesis_figures/fig5_*.png (300 dpi)
Usage:  backend/venv/Scripts/python.exe eval/scripts/make_thesis_figures.py
"""

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PH = ROOT / "eval" / "phases"
OUT = ROOT / "reports" / "thesis_figures"
OUT.mkdir(parents=True, exist_ok=True)

# reference palette (validated: blue, orange, aqua, yellow, magenta in fixed order) and chart chrome
C = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4"]
GREY = "#b9b8b2"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "legend.frameon": False,
})


def J(p):
    return json.load(open(p, encoding="utf-8"))


def save(fig, name):
    fig.tight_layout()
    fig.savefig(OUT / name, dpi=300)
    plt.close(fig)
    print("wrote", name)


def hbars(ax, labels, values, highlight, fmt="{:.3f}", xlabel=""):
    """Horizontal bars, highlighted entries in blue, others grey, values labelled at the bar end."""
    y = np.arange(len(labels))[::-1]
    colors = [C[0] if h else GREY for h in highlight]
    ax.barh(y, values, color=colors, height=0.62, edgecolor=SURF, linewidth=1.5)
    ax.set_yticks(y, labels)
    ax.grid(axis="y", visible=False)
    span = max(values) if max(values) > 0 else 1
    for yi, v in zip(y, values):
        ax.text(v + span * 0.015, yi, fmt.format(v), va="center", color=INK, fontsize=8)
    ax.set_xlim(0, span * 1.18)
    ax.set_xlabel(xlabel)


# ----------------------------------------------------------------------------- data overview
def fig_qasper():
    eda = J(PH / "phase_0_baseline/artifacts/qasper_full_corpus_eda.json")
    qt = eda["question_statistics"]["type_distribution"]
    heads = eda["top_10_canonical_section_headings"]
    n_docs = eda["document_statistics"]["total_papers_analyzed"]
    words = []
    for split in ("train", "dev", "test"):
        for p in J(ROOT / "eval/data/qasper_official" / f"qasper-{split}-v0.3.json").values():
            w = sum(len(par.split()) for sec in p["full_text"] for par in sec["paragraphs"])
            if w > 0:
                words.append(w)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.2))
    labels = {"extractive": "Trích xuất", "abstractive": "Tự diễn đạt", "yes_no": "Có/Không", "unanswerable": "Không trả lời được"}
    keys = ["extractive", "abstractive", "yes_no", "unanswerable"]
    total = sum(qt.values())
    hbars(axes[0], [labels[k] for k in keys], [qt[k] for k in keys], [True, True, True, False], fmt="{:,.0f}",
          xlabel=f"Số câu hỏi (tổng {total:,})")
    ax = axes[1]
    ax.hist(np.clip(words, 0, 12000), bins=40, color=C[0], edgecolor=SURF, linewidth=0.8)
    med = float(np.median(words))
    ax.axvline(med, color=INK2, linestyle="--", linewidth=1)
    ax.annotate(f"trung vị {med:,.0f} từ", xy=(med, ax.get_ylim()[1] * 0.8), xytext=(7000, ax.get_ylim()[1] * 0.8),
                fontsize=7.5, color=INK2, va="center", arrowprops={"arrowstyle": "-", "color": INK2, "linewidth": 0.8})
    ax.set_xlabel(f"Độ dài bài báo (số từ; {len(words):,} bài)")
    ax.set_ylabel("Số bài báo")
    ax.grid(axis="x", visible=False)
    order = sorted(list(heads.items())[:7], key=lambda kv: -kv[1])
    hbars(axes[2], [k.capitalize() for k, _ in order], [v / n_docs for _, v in order], [False] * 7, fmt="{:.0%}",
          xlabel="Tỷ lệ bài báo có đề mục")
    axes[2].xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    save(fig, "fig5_1_qasper_overview.png")


# ----------------------------------------------------------------------------- extraction
def fig_extraction():
    s = J(PH / "phase_1_extraction/artifacts/extraction/summary.json")
    g = J(PH / "phase_1_extraction/artifacts/extraction_grobid/summary.json")
    names = ["pymupdf_layout", "pymupdf_plain", "pdfminer.six", "pypdf", "pdfplumber"]
    lab = {"pymupdf_layout": "PyMuPDF Layout", "pymupdf_plain": "PyMuPDF (thường)", "pdfminer.six": "pdfminer.six",
           "pypdf": "pypdf", "pdfplumber": "pdfplumber"}
    nd = [s["downstream_c_ret_150"]["means"][n]["ndcg10"] for n in names] + [g["downstream_c_ret_150"]["means"]["grobid"]["ndcg10"]]
    rec = [s["means"][n]["evidence_recall"] for n in names] + [g["means"]["grobid"]["evidence_recall"]]
    ms = [s["secondary"][n]["ms_per_page_p50"] for n in names] + [g["secondary"]["grobid"]["ms_per_page_p50"]]
    labels = [lab[n] for n in names] + ["GROBID (dịch vụ riêng)"]
    hl = [True] + [False] * 5
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.0))
    hbars(axes[0], labels, rec, hl, xlabel="Độ phủ bằng chứng (335 bài)")
    hbars(axes[1], labels, nd, hl, xlabel="nDCG@10 truy xuất phía sau (150 bài)")
    hbars(axes[2], labels, ms, hl, fmt="{:.0f}", xlabel="ms/trang (trung vị)")
    for ax in axes[1:]:
        ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)
    save(fig, "fig5_2_extraction.png")


# ----------------------------------------------------------------------------- chunking
def fig_chunking():
    base = PH / "phase_2_chunking/artifacts"
    c = J(base / "chunking/summary.json")["means"]
    sem = J(base / "chunking_semantic/summary.json")["means"]
    ch = J(base / "chunking_children/summary.json")["means"]
    rows = [("Hierarchical", c["hierarchical|dense"]), ("Fixed size", c["fixed_size|dense"]),
            ("Recursive (section_overlap)", c["section_overlap|dense"]), ("Semantic v1", sem["semantic_v1"]),
            ("Semantic v2", sem["semantic_v2"]), ("Chỉ đoạn con (không mở rộng)", ch["children_only"])]
    labels = [r[0] for r in rows]
    hl = [True, True, False, False, False, False]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.0))
    hbars(axes[0], labels, [r[1]["ndcg10"] for r in rows], hl, xlabel="nDCG@10")
    hbars(axes[1], labels, [r[1]["cec_0.5"] for r in rows], hl, xlabel="CEC@0.5 (bằng chứng trong ngữ cảnh)")
    hbars(axes[2], labels, [r[1]["context_tokens"] for r in rows], hl, fmt="{:.0f}", xlabel="Số token ngữ cảnh (TB)")
    for ax in axes[1:]:
        ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)
    save(fig, "fig5_3_chunking.png")


# ----------------------------------------------------------------------------- embedding
def fig_embedding():
    e = J(PH / "phase_3_embedding/artifacts/embedding/summary.json")
    sp = J(PH / "phase_3_embedding/artifacts/embedding_specter2/summary.json")
    short = {"intfloat/e5-small-v2": "e5-small-v2", "sentence-transformers/all-MiniLM-L6-v2": "MiniLM-L6",
             "Snowflake/snowflake-arctic-embed-s": "arctic-embed-s", "BAAI/bge-small-en-v1.5": "bge-small",
             "nomic-ai/modernbert-embed-base": "ModernBERT-embed"}
    pts = [(short[m], e["efficiency"][m]["query_latency_ms"]["p50"], e["means"][m]["ndcg10"]) for m in short]
    pts.append(("SPECTER2", sp["efficiency"]["query_latency_ms"]["p50"], sp["means"]["specter2"]["ndcg10"]))
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    for name, x, y in pts:
        sel = name in ("e5-small-v2", "ModernBERT-embed")
        ax.scatter(x, y, s=70, color=C[0] if sel else GREY, edgecolor=SURF, linewidth=2, zorder=3)
        ax.annotate(f"{name} ({y:.3f})", (x, y), xytext=(7, 4), textcoords="offset points", fontsize=8, color=INK)
    ax.set_xscale("log")
    ax.set_xticks([10, 20, 50, 100], ["10", "20", "50", "100"])
    ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
    ax.set_xlabel("Độ trễ mã hóa một truy vấn, P50 (ms, thang log)")
    ax.set_ylabel("nDCG@10")
    ax.set_xlim(6, 160)
    save(fig, "fig5_4_embedding.png")


# ----------------------------------------------------------------------------- retrieval
def fig_retrieval():
    base = PH / "phase_6_hybrid_retrieval/artifacts/retrieval_fusion"
    sets = [("QASPER\n(335 bài)", "C-RET"), ("PeerQA PDF\n(107 bài)", "PEERQA-PDF"), ("PeerQA văn bản\n(73 bài)", "PEERQA-TEXT")]
    methods = [("Dense", "dense"), ("Hybrid (convex)", "convex_fix"), ("RRF", "rrf_fix"), ("BM25", "bm25_fix")]
    vals = {k: J(base / k / "summary.json")["means"] for _, k in sets}
    fig, ax = plt.subplots(figsize=(7.2, 3.4))
    x = np.arange(len(sets))
    w = 0.19
    for i, (lab, m) in enumerate(methods):
        ys = [vals[k][m]["ndcg10"] for _, k in sets]
        bars = ax.bar(x + (i - 1.5) * w, ys, w * 0.92, color=C[i], label=lab, edgecolor=SURF, linewidth=1.2)
        for b, v in zip(bars, ys):
            ax.text(b.get_x() + b.get_width() / 2, v + 0.006, f"{v:.3f}", ha="center", fontsize=6.5, color=INK, rotation=90)
    ax.set_xticks(x, [s[0] for s in sets])
    ax.set_ylabel("nDCG@10")
    ax.set_ylim(0, 0.62)
    ax.grid(axis="x", visible=False)
    ax.legend(ncol=4, loc="upper left", fontsize=8)
    save(fig, "fig5_5_retrieval.png")


def fig_complementarity():
    base = PH / "phase_6_hybrid_retrieval/artifacts/retrieval_fusion"
    sets = [("QASPER", "C-RET"), ("PeerQA PDF", "PEERQA-PDF"), ("PeerQA văn bản", "PEERQA-TEXT")]
    cats = ["Cả hai tìm thấy", "Chỉ dense", "Chỉ BM25", "Không tìm thấy"]
    data = []
    for _, k in sets:
        rows = [json.loads(line) for line in open(base / k / "per_query.jsonl", encoding="utf-8")]
        n = len(rows)
        d = [r["dense"]["cec_0.5"] for r in rows]
        b = [r["bm25_fix"]["cec_0.5"] for r in rows]
        data.append([sum(x and y for x, y in zip(d, b)) / n, sum(x and not y for x, y in zip(d, b)) / n,
                     sum(y and not x for x, y in zip(d, b)) / n, sum(not x and not y for x, y in zip(d, b)) / n])
    data = np.array(data)
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    left = np.zeros(len(sets))
    colors = [C[0], C[1], C[2], GREY]
    y = np.arange(len(sets))[::-1]
    for j, cat in enumerate(cats):
        ax.barh(y, data[:, j], left=left, color=colors[j], label=cat, edgecolor=SURF, linewidth=1.5, height=0.6)
        for yi, l0, v in zip(y, left, data[:, j]):
            if v >= 0.04:
                ax.text(l0 + v / 2, yi, f"{v:.0%}", ha="center", va="center", fontsize=7.5,
                        color="white" if j < 2 else INK)
        left += data[:, j]
    ax.set_yticks(y, [s[0] for s in sets])
    ax.set_xlim(0, 1)
    ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
    ax.set_xlabel("Tỷ lệ câu hỏi (bằng chứng có trong ngữ cảnh, CEC@0.5)")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=4, loc="upper center", bbox_to_anchor=(0.5, 1.32), fontsize=8)
    save(fig, "fig5_6_dense_bm25_overlap.png")


def fig_alpha():
    s = J(PH / "phase_6_hybrid_retrieval/artifacts/hybrid_alpha_sweep/summary.json")
    A = s["alphas"]
    m = s["means_by_pipeline"]
    lines = [("Hierarchical + e5", "hierarchical|e5"), ("Hierarchical + ModernBERT", "hierarchical|modernbert"),
             ("Fixed + e5", "fixed_size|e5"), ("Fixed + ModernBERT", "fixed_size|modernbert")]
    fig, ax = plt.subplots(figsize=(6.6, 3.6))
    for i, (lab, k) in enumerate(lines):
        ys = [m[f"{k}|{a}"]["ndcg10"] for a in A]
        ax.plot(A, ys, color=C[i], linewidth=2, marker="o", markersize=4.5, label=lab)
        ax.annotate(lab, (A[-1], ys[-1]), xytext=(6, 0), textcoords="offset points", fontsize=7.5, color=INK2, va="center")
    ax.axvline(0.7, color=INK2, linewidth=1, linestyle="--")
    ax.text(0.69, ax.get_ylim()[0] + 0.004, "α = 0.7 (chọn)", fontsize=7.5, color=INK2, ha="right", va="bottom")
    ax.set_xlabel("α (trọng số của dense; 0 = chỉ BM25, 1 = chỉ dense)")
    ax.set_ylabel("nDCG@10")
    ax.set_xlim(-0.03, 1.38)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8, 1.0])
    ax.legend(fontsize=7.5, loc="upper left")
    save(fig, "fig5_7_alpha_sweep.png")


def fig_hybrid_grid():
    s = J(PH / "phase_12_combination/artifacts/stage1/summary.json")["means"]
    chunkers = [("Hierarchical", "hierarchical"), ("Fixed size", "fixed_size"), ("Recursive", "section_overlap")]
    embs = [("e5", "e5"), ("ModernBERT", "modernbert"), ("arctic-s", "arctic"), ("bge-small", "bge"), ("MiniLM", "minilm")]
    M = np.array([[s[f"pymupdf_layout|{c}|{e}|convex_fix"]["ndcg10"] - s[f"pymupdf_layout|{c}|{e}|dense"]["ndcg10"]
                   for _, e in embs] for _, c in chunkers])
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    cmap = LinearSegmentedColormap.from_list("div", ["#eb6834", "#f0efec", "#2a78d6"])
    lim = max(abs(M.min()), abs(M.max()))
    fig, ax = plt.subplots(figsize=(6.4, 2.6))
    im = ax.imshow(M, cmap=cmap, norm=TwoSlopeNorm(vcenter=0, vmin=-lim, vmax=lim), aspect="auto")
    for i in range(M.shape[0]):
        for j in range(M.shape[1]):
            ax.text(j, i, f"{M[i, j]:+.3f}", ha="center", va="center", fontsize=8, color=INK)
    ax.set_xticks(range(len(embs)), [e[0] for e in embs])
    ax.set_yticks(range(len(chunkers)), [c[0] for c in chunkers])
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, fraction=0.04)
    cb.set_label("nDCG@10: hybrid − dense", color=INK2)
    save(fig, "fig5_8_hybrid_gain_grid.png")


def fig_rerank():
    r = J(PH / "phase_6_hybrid_retrieval/artifacts/reranking/summary.json")
    rows = [("Không xếp hạng lại (dense)", r["means"]["dense"]["ndcg10"], 0.0),
            ("ms-marco-MiniLM-L6", r["means"]["rerank_minilm"]["ndcg10"], r["rerank_latency_ms_added_per_query"]["rerank_minilm"]["p50"] / 1000),
            ("bge-reranker-base", r["means"]["rerank_bge"]["ndcg10"], r["rerank_latency_ms_added_per_query"]["rerank_bge"]["p50"] / 1000)]
    fig, axes = plt.subplots(1, 2, figsize=(8.5, 2.3))
    hl = [True, False, False]
    hbars(axes[0], [x[0] for x in rows], [x[1] for x in rows], hl, xlabel="nDCG@10 (335 bài)")
    hbars(axes[1], [x[0] for x in rows], [x[2] for x in rows], hl, fmt="{:.1f} s", xlabel="Độ trễ cộng thêm mỗi câu hỏi, P50")
    axes[1].set_yticklabels([])
    axes[1].tick_params(axis="y", length=0)
    save(fig, "fig5_9_reranking.png")


# ----------------------------------------------------------------------------- generation
def fig_generation():
    g = J(PH / "phase_9_generation/artifacts/rq5_llm_generation_benchmark_500q.json")["model_summaries"]
    x = J(PH / "phase_9_generation/artifacts/generation_extra_llms/summary.json")
    rows = [(m, g[m]["token_f1_mean"], g[m]["refusal_rate_pct"] / 100, g[m]["timing"]["latency_p50_s"])
            for m in ("llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b")]
    for m in ("qwen2.5:1.5b", "phi4-mini"):
        rows.append((m, x["means"][m]["token_f1"], x["means"][m]["is_refusal"], x["per_model"][m]["latency_wall_s_p50"]))
    rows.sort(key=lambda r: -r[1])
    labels = [r[0] for r in rows]
    hl = [r[0] in ("llama3.2:3b", "qwen2.5:1.5b") for r in rows]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 2.8))
    hbars(axes[0], labels, [r[1] for r in rows], hl, xlabel="Token F1")
    hbars(axes[1], labels, [r[2] for r in rows], hl, fmt="{:.0%}", xlabel="Tỷ lệ từ chối trả lời")
    hbars(axes[2], labels, [r[3] for r in rows], hl, fmt="{:.1f} s", xlabel="Độ trễ P50 (s)")
    for ax in axes[1:]:
        ax.set_yticklabels([])
        ax.tick_params(axis="y", length=0)
    save(fig, "fig5_10_generation.png")


def fig_human():
    hr = PH / "phase_9_generation/artifacts/human_faithfulness_review"
    h = J(hr / "correction/corrected_human_review_summary.json")["per_model"]  # round 1
    h.update(J(hr / "extra_models/human_review_summary.json")["per_model"])  # round 2
    cats = [("Có căn cứ", ["SUPPORTED"]), ("Đúng một phần", ["MISSING_INFO - PARTIAL"]),
            ("Không căn cứ / mâu thuẫn", ["UNSUPPORTED", "CONTRADICTED"]),
            ("Từ chối hợp lệ", ["REFUSAL_VALID"]), ("Từ chối không cần thiết", ["MISSING_INFO - UNJUSTIFIED_REFUSAL"])]
    models = ["llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b", "qwen2.5:1.5b", "phi4-mini"]
    fig, ax = plt.subplots(figsize=(7.2, 3.2))
    y = np.arange(len(models))[::-1]
    left = np.zeros(len(models))
    for j, (lab, keys) in enumerate(cats):
        v = np.array([sum(h[m]["counts"].get(k, 0) for k in keys) for m in models], dtype=float)
        ax.barh(y, v, left=left, color=C[j], label=lab, edgecolor=SURF, linewidth=1.5, height=0.6)
        for yi, l0, vi in zip(y, left, v):
            if vi >= 1:
                ax.text(l0 + vi / 2, yi, f"{int(vi)}", ha="center", va="center", fontsize=8,
                        color="white" if j in (0, 1) else INK)
        left += v
    ax.set_yticks(y, models)
    ax.set_xlim(0, 20)
    ax.set_xticks(range(0, 21, 5))
    ax.set_xlabel("Số câu trả lời (20 câu hỏi mỗi mô hình, một người đánh giá)")
    ax.grid(axis="y", visible=False)
    ax.legend(ncol=3, loc="upper center", bbox_to_anchor=(0.5, 1.32), fontsize=7.5)
    save(fig, "fig5_11_human_check.png")


if __name__ == "__main__":
    fig_qasper()
    fig_extraction()
    fig_chunking()
    fig_embedding()
    fig_retrieval()
    fig_complementarity()
    fig_alpha()
    fig_hybrid_grid()
    fig_rerank()
    fig_generation()
    fig_human()
