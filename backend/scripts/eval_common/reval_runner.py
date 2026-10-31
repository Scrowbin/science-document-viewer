"""
Shared runner utilities for the revalidation experiments: cohort loading, PDF paths, memory sampling,
paired bootstrap families and output writing. Statistics follow reports/revalidation/protocol/common.json.
"""

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
COHORT_DIR = ROOT / "eval" / "phases" / "phase_0_baseline" / "artifacts" / "revalidation"
B = 10000
SEED = 42


def load_cohort(name: str) -> Dict[str, Any]:
    return json.load(open(COHORT_DIR / f"cohort_{name}.json", encoding="utf-8"))


def pdf_path(cohort: str, paper_id: str, version: str = "latest") -> Path:
    if cohort == "PEERQA-PDF":
        return ROOT / "eval" / "pdfs" / "peerqa" / (paper_id.replace("/", "__") + ".pdf")
    if cohort == "DEV47":
        return ROOT / "eval" / "pdfs" / "dev" / f"{paper_id}.pdf"
    return ROOT / "eval" / "pdfs" / "train_reservoir" / (f"{paper_id}v1.pdf" if version == "v1" else f"{paper_id}.pdf")


_PEERQA_TEXT: Dict[str, List[Dict[str, Any]]] = {}


def peerqa_text_sections(paper_id: str) -> List[Dict[str, Any]]:
    """Sections from PeerQA's shipped text (papers.jsonl): sentences/list items grouped by heading,
    paragraphs (pidx) joined with blank lines. Figures, tables and formulas are left out."""
    if not _PEERQA_TEXT:
        for line in open(ROOT / "eval" / "data" / "peerqa" / "raw" / "papers.jsonl", encoding="utf-8"):
            r = json.loads(line)
            _PEERQA_TEXT.setdefault(r["paper_id"], []).append(r)
    sections: List[Dict[str, Any]] = []
    for r in sorted(_PEERQA_TEXT.get(paper_id, []), key=lambda x: x["idx"]):
        if r["type"] not in ("sentence", "list_item"):
            continue
        title = r.get("last_heading") or "Section"
        if not sections or sections[-1]["title"] != title:
            sections.append({"title": title, "paras": {}, "page": 1})
        sections[-1]["paras"].setdefault(r["pidx"], []).append(r["content"].strip())
    return [{"title": s["title"], "page": 1,
             "text": "\n\n".join(" ".join(p) for p in s["paras"].values())} for s in sections]


def group_items(cohort: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    out: Dict[str, List[Dict[str, Any]]] = {}
    for it in cohort["items"]:
        out.setdefault(it.get("paper_arxiv_id") or it.get("paper_id"), []).append(it)
    return out


class MemorySampler:
    """Peak working set (Windows RSS) of this process, sampled every 0.1 s."""

    def __init__(self):
        import psutil
        self.proc = psutil.Process()
        self.baseline = self.peak = self.proc.memory_info().rss
        self._stop = threading.Event()
        self._t = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.is_set():
            self.peak = max(self.peak, self.proc.memory_info().rss)
            time.sleep(0.1)

    def __enter__(self):
        self._t.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()

    def report(self) -> Dict[str, float]:
        return {"python_working_set_baseline_mb": round(self.baseline / 2**20, 1),
                "python_working_set_peak_mb": round(self.peak / 2**20, 1)}


def by_paper(rows: Sequence[Dict[str, Any]], arm: str, metric: str) -> Dict[str, List[float]]:
    out: Dict[str, List[float]] = {}
    for r in rows:
        out.setdefault(r["paper_id"], []).append(float(r[arm][metric]))
    return out


def compare(rows, base: str, cand: str, metric: str, n_boot: int = B) -> Dict[str, Any]:
    from eval_common.stats import paired_cluster_bootstrap
    d, ci, p = paired_cluster_bootstrap(by_paper(rows, base, metric), by_paper(rows, cand, metric),
                                        n_bootstraps=n_boot, seed=SEED)
    return {"comparison": f"{cand} - {base}", "metric": metric, "diff": round(d, 4),
            "ci95": [round(ci[0], 4), round(ci[1], 4)], "p_raw": round(p, 4)}


def family(rows, pairs: Sequence[Sequence[str]], metric: str, n_boot: int = B) -> List[Dict[str, Any]]:
    from eval_common.stats import holm_bonferroni_correction
    res = [compare(rows, base, cand, metric, n_boot) for cand, base in pairs]
    holm = holm_bonferroni_correction([r["p_raw"] for r in res], alpha=0.05)
    for r, h in zip(res, holm):
        r["p_holm"] = round(h["adj_p"], 4)
    return res


def arm_means(rows, arms: Sequence[str], metrics: Sequence[str]) -> Dict[str, Dict[str, float]]:
    return {a: {m: round(float(np.mean([r[a][m] for r in rows])), 4) for m in metrics} for a in arms}


def write_outputs(out_dir: Path, per_query: List[Dict[str, Any]], summary: Dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    with open(out_dir / "per_query.jsonl", "w", encoding="utf-8") as f:
        for r in per_query:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False), encoding="utf-8")
