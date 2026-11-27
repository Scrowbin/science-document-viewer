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
    """Phase 1, OHR-Bench: evidence coverage, LCS by evidence source, ms/page."""
    s = J(PH / "phase_1_extraction/artifacts/summary.json")["extractors"]
    names = ["pymupdf_layout", "pymupdf_plain", "pypdf", "pdfminer.six", "pdfplumber", "grobid"]
    lab = {"pymupdf_layout": "PyMuPDF Layout", "pymupdf_plain": "PyMuPDF (thường)", "pypdf": "pypdf",
           "pdfminer.six": "pdfminer.six", "pdfplumber": "pdfplumber", "grobid": "GROBID"}
    labels = [lab[n] for n in names]
    rec = [s[n]["evidence_recall"] for n in names]
    ms = [s[n]["timing"]["ms_per_page"] for n in names]
    hl = [n == "pymupdf_layout" for n in names]
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 3.2))
    hbars(axes[0], labels, rec, hl, xlabel="Độ phủ bằng chứng")
    y = np.arange(len(names))[::-1]
    srcs = [("text", "Văn bản"), ("table", "Bảng"), ("formula", "Công thức")]
    h = 0.26
    for j, (k, name) in enumerate(srcs):
        v = [s[n]["by_source"][k]["lcs"] for n in names]
        axes[1].barh(y + (1 - j) * h, v, height=h, color=C[j], edgecolor=SURF, linewidth=1, label=name)
    axes[1].set_xlim(0, 100)
    axes[1].set_xlabel("LCS (%) theo loại nguồn bằng chứng")
    axes[1].grid(axis="y", visible=False)
    axes[1].legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7)
    hbars(axes[2], labels, ms, hl, fmt="{:.1f}", xlabel="ms/trang")
    for ax in axes[1:]:
        ax.set_yticks(y, [""] * len(y))
        ax.tick_params(axis="y", length=0)
    save(fig, "fig5_2_extraction_ohr.png")


# ----------------------------------------------------------------------------- phase 2: chunking x embedding
P2_LABELS = {"e5": "e5-small-v2", "arctic": "arctic-embed-s", "modernbert": "ModernBERT-embed",
             "gemma": "embeddinggemma-300m", "qwen": "Qwen3-Embedding-0.6B"}


def phase2_ndcg(cohort="c_ret"):
    """nDCG@10 per (chunker, model label): artifacts/<cohort>/summary.json when downloaded, else the Kaggle run log."""
    import re
    summ = PH / f"phase_2_retrieval/artifacts/{cohort}/summary.json"
    if summ.exists():
        d = J(summ)
        out = {}
        for c in d["combinations"].values():
            m = c.get("common_means") or c["means"]
            out[(c["chunker"], c["model_label"])] = m["ndcg_10"]
        return out, str(summ.relative_to(ROOT))
    # The 2026-11-15 run (gemma with its model-card prompts, PeerQA with all PDFs) replaces the first run.
    log = PH / "phase_2_retrieval/artifacts/kaggle_full_run_2026-11-15.log"
    if not log.exists():
        log = PH / "phase_2_retrieval/artifacts/kaggle_full_run.log"
    txt = log.read_text(encoding="utf-8")
    block = txt.split("Cohort [C-RET]")[1].split("Cohort [")[0] if cohort == "c_ret" else txt.split("Cohort [PEERQA-PDF]")[1]
    out = {(m.group(1), m.group(2)): float(m.group(3))
           for m in re.finditer(r"Done (\w+)\|(\w+): nDCG@10=([\d.]+)", block)}
    return out, str(log.relative_to(ROOT))


def fig_retrieval_grid(cohort="c_ret"):
    """Phase 2: nDCG@10 for 3 chunkers x the embedders run on the cohort (C-RET: 5, PeerQA: 4)."""
    nd, src = phase2_ndcg(cohort)
    models = [m for m in ["e5", "arctic", "modernbert", "gemma", "qwen"] if any(k[1] == m for k in nd)]
    chunkers = [("hierarchical", "hierarchical"), ("fixed_size", "fixed_size"), ("section_overlap", "section_overlap")]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    y = np.arange(len(models))[::-1]
    h = 0.26
    for j, (ck, name) in enumerate(chunkers):
        v = [nd.get((ck, m), np.nan) for m in models]
        yy = y + (1 - j) * h
        ax.barh(yy, v, height=h, color=C[j], edgecolor=SURF, linewidth=1, label=name)
        for yi, vi in zip(yy, v):
            if not np.isnan(vi):
                ax.text(vi + 0.008, yi, f"{vi:.3f}", va="center", fontsize=7, color=INK)
    ax.set_yticks(y, [P2_LABELS[m] for m in models])
    ax.set_xlim(0, 0.82)
    ax.set_xlabel("nDCG@10 (C-RET, 335 bài báo; truy xuất dense)" if cohort == "c_ret"
                  else "nDCG@10 (PeerQA, 107 bài báo, văn bản trích xuất từ PDF; truy xuất dense)")
    ax.grid(axis="y", visible=False)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, fontsize=7.5)
    print("  phase 2 source:", src)
    save(fig, "fig5_3_retrieval_grid.png" if cohort == "c_ret" else "fig5_4_retrieval_grid_peerqa.png")


# ----------------------------------------------------------------------------- phase 3: fusion and reranking
def fig_phase3_tradeoff():
    """Phase 3: nDCG@10 against retrieval latency (log scale) for the 29 arms, per cohort."""
    d = J(PH / "phase_3_hybrid_reranking/artifacts/ndcg_latency_from_run_figures_2026-11-15.json")
    fam = {"dense": ("dense", C[0]), "rrf": ("rrf / convex", C[1]), "convex": ("rrf / convex", C[1]),
           "dense+minilm": ("+ MiniLM", C[2]), "convex+minilm": ("+ MiniLM", C[2]),
           "dense+bgem3": ("+ bge-reranker-v2-m3", C[4]), "convex+bgem3": ("+ bge-reranker-v2-m3", C[4])}
    fig, axes = plt.subplots(1, 2, figsize=(7.4, 3.5), sharey=True)
    for ax, (key, title) in zip(axes, [("c_ret", "C-RET (566 câu hỏi)"), ("peerqa_pdf", "PeerQA (284 câu hỏi)")]):
        c = d["cohorts"][key]
        lat = c["latency_ms_p50"]
        seen = set()
        for emb, vals in c["ndcg_10"].items():
            for arm, v in zip(d["arms"], vals):
                base = arm.split("+")[0]
                x = lat[base] + (lat["+minilm"] if "minilm" in arm else lat["+bgem3"] if "bgem3" in arm else 0)
                name, col = fam[arm]
                ax.scatter(x, v, s=22, color=col, edgecolor=SURF, linewidth=0.8, zorder=3,
                           label=name if name not in seen else None)
                seen.add(name)
                if emb == "gemma" and arm == "dense":
                    ax.scatter(x, v, s=90, facecolor="none", edgecolor=INK, linewidth=1.0, zorder=4)
                    ax.annotate("embeddinggemma\ndense (chọn)", (x, v), xytext=(8, -26), textcoords="offset points",
                                fontsize=7, color=INK, arrowprops={"arrowstyle": "-", "color": INK2, "lw": 0.6})
        ax.scatter(lat["bm25"], c["bm25"], s=22, marker="s", color=GREY, edgecolor=SURF, linewidth=0.8, zorder=3,
                   label="BM25")
        ax.set_xscale("log")
        ax.set_title(title, fontsize=9, color=INK)
        ax.set_xlabel("Độ trễ truy xuất (ms, thang log, GPU T4)")
    axes[0].set_ylabel("nDCG@10")
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=5, fontsize=7.5, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    fig.savefig(OUT / "fig5_5_phase3_tradeoff.png", dpi=300)
    plt.close(fig)
    print("wrote fig5_5_phase3_tradeoff.png")


# ----------------------------------------------------------------------------- generation (preliminary study)
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


# ----------------------------------------------------------------------------- phase 4: generation
P4 = PH / "phase_4_generation/artifacts/summary.json"
P4_MODELS = [("llama3.2:3b", "llama3.2:3b"), ("qwen2.5:1.5b", "qwen2.5:1.5b"), ("phi4-mini", "phi4-mini"),
             ("qwen3:4b-instruct-2507-q4_K_M", "qwen3:4b"), ("gemma3:4b", "gemma3:4b")]
P4_PANELS = [("c_ret", "gold", "C-RET, bằng chứng chuẩn"), ("c_ret", "retrieved_gemma_dense", "C-RET, ngữ cảnh truy xuất"),
             ("peerqa_pdf", "gold", "PeerQA, bằng chứng chuẩn"),
             ("peerqa_pdf", "retrieved_gemma_dense", "PeerQA, ngữ cảnh truy xuất")]
P4_CATS = [("Có căn cứ", ["SUPPORTED"]), ("Đúng một phần", ["MISSING_INFO - PARTIAL"]),
           ("Không căn cứ / mâu thuẫn", ["UNSUPPORTED", "CONTRADICTED"]),
           ("Từ chối hợp lệ", ["REFUSAL_VALID"]), ("Từ chối không cần thiết", ["MISSING_INFO - UNJUSTIFIED_REFUSAL"])]


def fig_phase4_labels():
    """Phase 4: share of judge labels per model, gold vs retrieved (embeddinggemma dense), both datasets."""
    s = J(P4)
    fig, axes = plt.subplots(2, 2, figsize=(10, 5.2), sharex=True)
    y = np.arange(len(P4_MODELS))[::-1]
    for ax, (cohort, cond, title) in zip(axes.flat, P4_PANELS):
        d = s[cohort][cond]
        left = np.zeros(len(P4_MODELS))
        for j, (lab, keys) in enumerate(P4_CATS):
            v = np.array([sum(d[m]["judge_labels"].get(k, 0) for k in keys) / d[m]["judge_n"] for m, _ in P4_MODELS])
            ax.barh(y, v, left=left, color=C[j], label=lab, edgecolor=SURF, linewidth=1.5, height=0.62)
            for yi, l0, vi in zip(y, left, v):
                if vi >= 0.08:
                    ax.text(l0 + vi / 2, yi, f"{vi:.0%}", ha="center", va="center", fontsize=7,
                            color="white" if j in (0, 1) else INK)
            left += v
        n = d[P4_MODELS[0][0]]["judge_n"]
        ax.set_title(f"{title} ({n} câu hỏi)", fontsize=9, color=INK)
        ax.set_yticks(y, [name for _, name in P4_MODELS])
        ax.set_xlim(0, 1)
        ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
        ax.grid(axis="y", visible=False)
    for ax in axes[1]:
        ax.set_xlabel("Tỷ lệ câu trả lời theo nhãn của mô hình chấm")
    h, lab = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=5, fontsize=7.5, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "fig5_12_phase4_labels.png", dpi=300)
    plt.close(fig)
    print("wrote fig5_12_phase4_labels.png")


def fig_phase4_gap():
    """Phase 4: Token F1 and refusal rate per model, gold vs retrieved context (embeddinggemma dense)."""
    s = J(P4)
    fig, axes = plt.subplots(2, 2, figsize=(10, 4.6))
    y = np.arange(len(P4_MODELS))[::-1]
    for r, (cohort, name) in enumerate([("c_ret", "C-RET"), ("peerqa_pdf", "PeerQA")]):
        for c, (key, xlabel, fmt) in enumerate([("token_f1", "Token F1", "{:.2f}"), ("refusal_rate", "Tỷ lệ từ chối", "{:.0%}")]):
            ax = axes[r, c]
            g = [s[cohort]["gold"][m][key] for m, _ in P4_MODELS]
            t = [s[cohort]["retrieved_gemma_dense"][m][key] for m, _ in P4_MODELS]
            for yi, a, b in zip(y, g, t):
                ax.plot([a, b], [yi, yi], color=GREY, linewidth=2, zorder=1)
            ax.scatter(g, y, s=46, color=C[0], edgecolor=SURF, linewidth=2, zorder=3, label="Bằng chứng chuẩn")
            ax.scatter(t, y, s=46, color=C[1], edgecolor=SURF, linewidth=2, zorder=3, label="Ngữ cảnh truy xuất")
            ax.set_yticks(y, [nm for _, nm in P4_MODELS] if c == 0 else [""] * len(y))
            ax.tick_params(axis="y", length=0)
            ax.grid(axis="y", visible=False)
            ax.set_title(f"{name}: {xlabel}", fontsize=9, color=INK)
            if key == "refusal_rate":
                ax.set_xlim(0, 1)
                ax.xaxis.set_major_formatter(matplotlib.ticker.PercentFormatter(1.0))
            else:
                ax.set_xlim(0, 0.3)
    h, lab = axes[0, 0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=2, fontsize=7.5, bbox_to_anchor=(0.5, 1.0))
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(OUT / "fig5_13_phase4_gold_vs_retrieved.png", dpi=300)
    plt.close(fig)
    print("wrote fig5_13_phase4_gold_vs_retrieved.png")


if __name__ == "__main__":
    fig_qasper()
    fig_extraction()
    fig_retrieval_grid()
    fig_retrieval_grid("peerqa_pdf")
    fig_phase3_tradeoff()
    fig_generation()
    fig_human()
    fig_phase4_labels()
    fig_phase4_gap()
