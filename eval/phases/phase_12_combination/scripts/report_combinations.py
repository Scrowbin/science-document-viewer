#!/usr/bin/env python3
"""
Thesis tables and figures for the 16-configuration combination experiment (Chapter 5, section 5.8).

Reads the files written by run_combinations.py (retrieval.csv, generation.csv, summary.json) and writes
  <run>/thesis_tables.md          Vietnamese Markdown tables to paste into the thesis
  <figdir>/fig5_12_combo_retrieval.png, fig5_13_combo_generation.png
Descriptive only: means, differences between methods and costs. No statistical tests, no composite score.

Usage (backend/venv):
  python eval/phases/phase_12_combination/scripts/report_combinations.py                  # full run
  python eval/phases/phase_12_combination/scripts/report_combinations.py --run <dir> --figdir <dir>
"""

import argparse
import csv
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[4]
RUN = ROOT / "eval" / "phases" / "phase_12_combination" / "artifacts" / "combinations"
FIGDIR = ROOT / "reports" / "thesis_figures"

PRODUCTION = "HIER_E5_DENSE"          # current app setting
IBCC = "HIER_MBERT_DENSE"             # best method of each component experiment, combined
FACTORS = {  # component -> (position in the ID, {code: readable name}), first method listed first
    "Phân mảnh": (0, {"HIER": "hierarchical", "FIXED": "fixed_size"}),
    "Mô hình nhúng": (1, {"E5": "e5-small-v2", "MBERT": "ModernBERT-embed"}),
    "Truy xuất": (2, {"DENSE": "dense", "HYBRID": "hybrid"}),
    "Mô hình sinh": (3, {"LLAMA3B": "llama3.2:3b", "QWEN15B": "qwen2.5:1.5b"}),
}
SPLITS = ("train", "dev", "test")
TYPES = (("extractive", "trích xuất"), ("abstractive", "diễn giải"), ("boolean", "Có/Không"))

# same chart style as eval/scripts/make_thesis_figures.py
C = ["#2a78d6", "#eb6834"]
GREY = "#b9b8b2"
INK, INK2, GRID, SURF = "#0b0b0b", "#52514e", "#e6e5e0", "#fcfcfb"
plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": GRID, "axes.labelcolor": INK2,
    "xtick.color": INK2, "ytick.color": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
    "axes.axisbelow": True, "axes.spines.top": False, "axes.spines.right": False,
    "figure.facecolor": SURF, "axes.facecolor": SURF, "savefig.facecolor": SURF, "legend.frameon": False,
})


COMMA = FuncFormatter(lambda v, _: f"{v:g}".replace(".", ","))


def read_csv(p):
    with open(p, encoding="utf-8") as f:
        return list(csv.DictReader(f))


def num(x):
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def vn(x, d=3):
    """Vietnamese number format: decimal comma, dot as thousands separator."""
    if x is None:
        return "–"
    s = f"{x:,.{d}f}"
    return s.replace(",", "_").replace(".", ",").replace("_", ".")


def name(pid):
    parts = pid.split("_")
    return " + ".join(FACTORS[f][1][parts[i]] for f, (i, _) in FACTORS.items() if i < len(parts))


def table(head, rows, caption):
    out = ["| " + " | ".join(head) + " |", "| " + " | ".join([":---"] + ["---:"] * (len(head) - 1)) + " |"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out + ["", f"*{caption}*", ""])


def bold_best(vals, higher=True):
    ok = [v for v in vals if v is not None]
    best = (max if higher else min)(ok) if ok else None
    return [v is not None and v == best for v in vals]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", type=Path, default=RUN)
    ap.add_argument("--figdir", type=Path, default=FIGDIR)
    a = ap.parse_args()
    ret = read_csv(a.run / "retrieval.csv")
    gen = read_csv(a.run / "generation.csv")
    summ = json.load(open(a.run / "summary.json", encoding="utf-8"))
    R = {r["retrieval_pipeline"]: {k: num(v) for k, v in r.items()} for r in ret}
    G = {g["config"]: {**{k: num(v) for k, v in g.items()}, "boolean_correct": g.get("boolean_correct", "")} for g in gen}
    pipes = [r["retrieval_pipeline"] for r in ret]
    cfgs = [g["config"] for g in gen]
    nq_ret = int(R[pipes[0]]["n_questions"])
    nq_gen = int(G[cfgs[0]]["n_questions"])
    src = a.run.resolve()
    src = src.relative_to(ROOT).as_posix() if src.is_relative_to(ROOT) else src.as_posix()
    md = [f"# Bảng kết quả thực nghiệm kết hợp (tự sinh từ `{src}`)", "",
          f"Truy xuất: {nq_ret} câu hỏi; sinh câu trả lời: {nq_gen} câu hỏi. "
          f"Cấu hình hiện tại của hệ thống: `{PRODUCTION}` + llama3.2:3b. "
          f"Cấu hình ghép từ các phương pháp tốt nhất của từng thành phần: `{IBCC}`. "
          "Giá trị tốt nhất của mỗi cột được in đậm.", ""]

    # --- retrieval layer
    cols = [("ndcg10", 3, True), ("mrr10", 3, True), ("cec_0.5", 3, True), ("context_tokens", 0, None),
            ("n_units", 2, None), ("retrieve_ms_p50", 2, False)]
    best = {c: bold_best([R[p][c] for p in pipes], h) for c, _, h in cols if h is not None}
    rows = []
    for i, p in enumerate(pipes):
        cells = [f"`{p}` ({name(p)})"]
        for c, d, h in cols:
            s = vn(R[p][c], d)
            cells.append(f"**{s}**" if h is not None and best[c][i] else s)
        rows.append(cells)
    md.append(table(["Đường ống truy xuất", "nDCG@10", "MRR@10", "CEC@0,5", "Token ngữ cảnh", "Số đơn vị",
                     "Truy xuất p50 (ms)"], rows, "Bảng 5.7: Kết quả tầng truy xuất và ghép ngữ cảnh của 8 đường ống."))

    # --- generation layer
    cols = [("token_f1", 3, True), ("refusal_rate", 3, None), ("containment_proxy", 3, True),
            ("generate_s_p50", 1, False), ("generate_s_p95", 1, False)]
    best = {c: bold_best([G[k][c] for k in cfgs], h) for c, _, h in cols if h is not None}
    rows = []
    for i, k in enumerate(cfgs):
        cells = [f"`{k}`"]
        for c, d, h in cols:
            s = vn(G[k][c], d)
            cells.append(f"**{s}**" if h is not None and best[c][i] else s)
        cells.insert(3, G[k]["boolean_correct"])
        rows.append(cells)
    md.append(table(["Cấu hình", "Token F1", "Tỷ lệ từ chối", "Có/Không đúng", "Tỷ lệ chứa (proxy)",
                     "Sinh p50 (s)", "Sinh p95 (s)"], rows,
                    "Bảng 5.8: Kết quả tầng sinh câu trả lời của 16 cấu hình."))

    # --- refusals vs evidence in context
    rows = [[f"`{k}`", vn(G[k]["refusal_rate_ctx_has_evidence"]), vn(G[k]["refusal_rate_ctx_lacks_evidence"]),
             vn(G[k]["token_f1_ctx_has_evidence"]), vn(G[k]["token_f1_ctx_lacks_evidence"]),
             str(int(G[k]["n_ctx_has_evidence"] or 0))] for k in cfgs]
    md.append(table(["Cấu hình", "Từ chối (ngữ cảnh có bằng chứng)", "Từ chối (ngữ cảnh thiếu bằng chứng)",
                     "Token F1 (có)", "Token F1 (thiếu)", "Số câu có bằng chứng"], rows,
                    "Bảng 5.9: Từ chối và Token F1 tách theo việc ngữ cảnh có chứa bằng chứng (CEC@0,5) hay không."))

    # --- component effects (descriptive marginal means; spread of paired differences shows interactions)
    rows = []
    for comp, (pos, codes) in FACTORS.items():
        a_code, b_code = list(codes)
        for metric, label, src, keys in (("ndcg10", "nDCG@10", R, pipes), ("cec_0.5", "CEC@0,5", R, pipes),
                                         ("token_f1", "Token F1", G, cfgs), ("refusal_rate", "Tỷ lệ từ chối", G, cfgs)):
            if pos >= len(keys[0].split("_")):
                continue  # the LLM does not affect retrieval metrics
            diffs, va, vb = [], [], []
            for k in keys:
                parts = k.split("_")
                if parts[pos] != a_code:
                    continue
                kb = "_".join(parts[:pos] + [b_code] + parts[pos + 1:])
                va.append(src[k][metric])
                vb.append(src[kb][metric])
                diffs.append(src[kb][metric] - src[k][metric])
            rows.append([comp, label, f"{vn(np.mean(va))} ({codes[a_code]})", f"{vn(np.mean(vb))} ({codes[b_code]})",
                         vn(np.mean(diffs)), f"{vn(min(diffs))} đến {vn(max(diffs))}", f"{sum(d > 0 for d in diffs)}/{len(diffs)}"])
    md.append(table(["Thành phần", "Chỉ số", "Trung bình phương pháp 1", "Trung bình phương pháp 2",
                     "Chênh lệch (2 − 1)", "Khoảng chênh lệch theo cặp", "Số cặp 2 > 1"], rows,
                    "Bảng 5.10: Ảnh hưởng của từng thành phần, lấy trung bình trên các lựa chọn của các thành phần "
                    "còn lại. Khoảng chênh lệch rộng hoặc đổi dấu cho thấy tương tác giữa các thành phần."))

    # --- per split
    rows = [[f"`{p}`"] + [vn(R[p][f"ndcg10_{s}"]) for s in SPLITS] + [vn(R[p][f"cec_0.5_{s}"]) for s in SPLITS]
            for p in pipes]
    by = summ.get("questions_by_split", {})
    md.append(table(["Đường ống"] + [f"nDCG@10 {s.capitalize()}" for s in SPLITS] + [f"CEC {s.capitalize()}" for s in SPLITS],
                    rows, "Bảng 5.11: Kết quả truy xuất theo tập Train, Dev, Test"
                    + (f" (số câu hỏi: {', '.join(f'{s} {by[s]}' for s in SPLITS if s in by)})." if by else ".")))
    rows = [[f"`{k}`"] + [vn(G[k][f"token_f1_{s}"]) for s in SPLITS] + [vn(G[k][f"token_f1_{t}"]) for t, _ in TYPES]
            + [vn(G[k][f"refusal_rate_{t}"]) for t, _ in TYPES] for k in cfgs]
    bt = summ.get("generation_questions_by_type", {})
    md.append(table(["Cấu hình"] + [f"F1 {s.capitalize()}" for s in SPLITS] + [f"F1 {v}" for _, v in TYPES]
                    + [f"Từ chối {v}" for _, v in TYPES], rows,
                    "Bảng 5.12: Token F1 theo tập và theo loại câu trả lời, tỷ lệ từ chối theo loại câu trả lời"
                    + (f" (số câu hỏi: {', '.join(f'{v} {bt[t]}' for t, v in TYPES if t in bt)})." if bt else ".")))

    # --- best per layer vs IBCC and production
    def best_of(src, keys, metric, higher=True):
        return (max if higher else min)(keys, key=lambda k: src[k][metric])
    picks = [("Truy xuất (nDCG@10 cao nhất)", best_of(R, pipes, "ndcg10")),
             ("Ghép ngữ cảnh (CEC@0,5 cao nhất)", best_of(R, pipes, "cec_0.5")),
             ("Sinh câu trả lời (Token F1 cao nhất)", best_of(G, cfgs, "token_f1")),
             ("Chi phí (sinh p50 thấp nhất)", best_of(G, cfgs, "generate_s_p50", False)),
             ("Ghép phương pháp tốt nhất của từng thành phần", f"{IBCC}_LLAMA3B"),
             ("Ghép phương pháp tốt nhất của từng thành phần", f"{IBCC}_QWEN15B"),
             ("Cấu hình hiện tại của hệ thống", f"{PRODUCTION}_LLAMA3B")]
    rows = []
    for why, k in picks:
        p = k if k in R else "_".join(k.split("_")[:3])
        g = G.get(k) if k in G else None
        rows.append([why, f"`{k}`", vn(R[p]["ndcg10"]), vn(R[p]["cec_0.5"]),
                     vn(g["token_f1"]) if g else "–", vn(g["refusal_rate"]) if g else "–",
                     vn(g["generate_s_p50"], 1) if g else "–"])
    md.append(table(["Tiêu chí", "Cấu hình", "nDCG@10", "CEC@0,5", "Token F1", "Tỷ lệ từ chối", "Sinh p50 (s)"], rows,
                    "Bảng 5.13: Cấu hình tốt nhất ở từng tầng so với cấu hình ghép từ các phương pháp tốt nhất "
                    "và cấu hình hiện tại."))

    # --- resources
    res = summ.get("resources", {})
    rows = [[k.replace("_", " "), vn(v.get("python_peak_mb"), 0), vn(v.get("ollama_peak_mb"), 0),
             vn(v.get("system_min_available_mb"), 0), vn(v.get("pagefile_growth_max_mb"), 0)] for k, v in res.items()]
    if rows:
        md.append(table(["Giai đoạn", "Python đỉnh (MB)", "Ollama đỉnh (MB)", "Bộ nhớ trống thấp nhất (MB)",
                         "Tăng pagefile (MB)"], rows, "Bảng 5.14: Bộ nhớ trong từng giai đoạn của thực nghiệm kết hợp."))
    el = summ.get("elapsed_s") or {}
    if el:
        md.append("Thời gian chạy: " + ", ".join(f"{k} {vn(v / 3600, 1)} giờ" for k, v in el.items())
                  + f" (tổng {vn(sum(el.values()) / 3600, 1)} giờ).\n")

    out_md = a.run / "thesis_tables.md"
    out_md.write_text("\n".join(md), encoding="utf-8")
    print("wrote", out_md)

    # --- figures
    a.figdir.mkdir(parents=True, exist_ok=True)
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), sharey=True)
    y = np.arange(len(pipes))[::-1]
    for ax, (metric, label) in zip(axes, (("ndcg10", "nDCG@10"), ("cec_0.5", "CEC@0,5"))):
        vals = [R[p][metric] for p in pipes]
        hi = bold_best(vals)
        ax.barh(y, vals, color=[C[0] if h else GREY for h in hi], height=0.62, edgecolor=SURF, linewidth=1.5)
        for yi, v in zip(y, vals):
            ax.text(v + 0.01, yi, vn(v), va="center", color=INK, fontsize=8)
        ax.set_xlim(0, max(vals) * 1.22)
        ax.set_xlabel(label)
        ax.xaxis.set_major_formatter(COMMA)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(y, pipes)
    fig.suptitle(f"Truy xuất của 8 đường ống ({nq_ret} câu hỏi; giá trị cao nhất tô xanh)", fontsize=9, color=INK2)
    fig.tight_layout()
    fig.savefig(a.figdir / "fig5_12_combo_retrieval.png", dpi=300)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7.2, 3.6))
    h = 0.38
    for j, (llm, label) in enumerate((("LLAMA3B", "llama3.2:3b"), ("QWEN15B", "qwen2.5:1.5b"))):
        vals = [G[f"{p}_{llm}"]["token_f1"] for p in pipes]
        yy = y + (h / 2 if j == 0 else -h / 2)
        ax.barh(yy, vals, height=h, color=C[j], edgecolor=SURF, linewidth=1.5, label=label)
        for yi, v in zip(yy, vals):
            ax.text(v + 0.004, yi, vn(v), va="center", color=INK, fontsize=7)
    ax.set_yticks(y, pipes)
    ax.grid(axis="y", visible=False)
    ax.set_xlabel(f"Token F1 ({nq_gen} câu hỏi)")
    ax.xaxis.set_major_formatter(COMMA)
    ax.set_xlim(0, max(G[k]["token_f1"] for k in cfgs) * 1.2)
    ax.legend(loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=2)
    fig.tight_layout()
    fig.savefig(a.figdir / "fig5_13_combo_generation.png", dpi=300)
    plt.close(fig)
    print("wrote figures to", a.figdir)


if __name__ == "__main__":
    main()
