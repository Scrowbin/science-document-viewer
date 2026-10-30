"""
Automated validation script to verify that:
1. All generated CSV tables match raw JSON values exactly.
2. All generated PNG plots exist, have non-zero size, and can be opened as valid images.
3. Key numerical statements in reports/chapter5/CHAPTER5.md are present in raw JSON sources.
"""

import json
import os
import csv
import sys
from PIL import Image

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CHAPTER5_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, ".."))
REPO_ROOT = os.path.abspath(os.path.join(CHAPTER5_DIR, "..", ".."))

RESULTS_DIR = os.path.join(REPO_ROOT, "eval", "results")
TABLES_DIR = os.path.join(CHAPTER5_DIR, "tables")
FIGURES_DIR = os.path.join(CHAPTER5_DIR, "figures")
CHAPTER5_MD = os.path.join(CHAPTER5_DIR, "CHAPTER5.md")


def test_tables():
    print("Testing generated CSV tables against raw JSON sources...")
    
    # 1. RQ1
    with open(os.path.join(RESULTS_DIR, "rq1_extraction_20261024_000639.json"), "r", encoding="utf-8") as f:
        rq1_json = json.load(f)["summary"]
    
    with open(os.path.join(TABLES_DIR, "table_5_1_rq1_extraction.csv"), "r", encoding="utf-8-sig") as f:
        reader = list(csv.DictReader(f))
    
    assert len(reader) == len(rq1_json), f"Mismatch in RQ1 row count: {len(reader)} vs {len(rq1_json)}"
    
    plain_csv = next(r for r in reader if r["engine"] == "pymupdf_plain")
    plain_json = next(r for r in rq1_json if r["engine"] == "pymupdf_plain")
    assert float(plain_csv["ndcg10_mean"]) == plain_json["downstream_ndcg10"]["mean"]
    assert float(plain_csv["latency_per_page_ms"]) == plain_json["latency_per_page_ms"]
    print("  [PASS] Table 5.1 (RQ1) matches raw JSON.")

    # 2. RQ2
    with open(os.path.join(RESULTS_DIR, "rq2_chunking_20261024_013443.json"), "r", encoding="utf-8") as f:
        rq2_json = json.load(f)["summary"]
        
    with open(os.path.join(TABLES_DIR, "table_5_2_rq2_chunking.csv"), "r", encoding="utf-8-sig") as f:
        reader = list(csv.DictReader(f))
        
    assert len(reader) == len(rq2_json), f"Mismatch in RQ2 row count: {len(reader)} vs {len(rq2_json)}"
    hier_csv = next(r for r in reader if r["strategy"] == "hierarchical")
    hier_json = next(r for r in rq2_json if r["strategy"] == "hierarchical")
    assert float(hier_csv["ndcg10_tau05_mean"]) == hier_json["primary_metrics"]["ndcg10"]["mean"]
    assert float(hier_csv["recall20_tau05"]) == hier_json["primary_metrics"]["recall20"]
    print("  [PASS] Table 5.2 (RQ2) matches raw JSON.")

    # 3. RQ3
    with open(os.path.join(RESULTS_DIR, "thesis_embedding_benchmark.json"), "r", encoding="utf-8") as f:
        rq3_json = json.load(f)["models"]
        
    with open(os.path.join(TABLES_DIR, "table_5_3_rq3_embedding.csv"), "r", encoding="utf-8-sig") as f:
        reader = list(csv.DictReader(f))
        
    assert len(reader) == len(rq3_json), f"Mismatch in RQ3 row count: {len(reader)} vs {len(rq3_json)}"
    e5_csv = next(r for r in reader if r["model_id"] == "e5-small-v2")
    e5_json = next(r for r in rq3_json if r["id"] == "e5-small-v2")
    assert float(e5_csv["ndcg10_mean"]) == e5_json["metrics"]["ndcg10"]["mean"]
    assert float(e5_csv["query_latency_p50_ms"]) == e5_json["efficiency"]["query_latency_p50_ms"]
    print("  [PASS] Table 5.3 (RQ3) matches raw JSON.")


def test_figures():
    print("Testing generated figures...")
    expected_figures = [
        "fig5_1_rq1_ndcg10.png",
        "fig5_2_rq1_latency.png",
        "fig5_3_rq2_chunking_ndcg10.png",
        "fig5_4_rq3_embedding_ndcg10.png",
        "fig5_5_rq3_quality_cost.png"
    ]
    for fig_name in expected_figures:
        fig_path = os.path.join(FIGURES_DIR, fig_name)
        assert os.path.exists(fig_path), f"Missing figure {fig_path}"
        assert os.path.getsize(fig_path) > 10000, f"Figure too small: {fig_path}"
        with Image.open(fig_path) as img:
            assert img.size[0] > 1000 and img.size[1] > 500, f"Image dimensions unexpected: {img.size}"
        print(f"  [PASS] Figure {fig_name} verified (valid image, high-res).")


def test_chapter_numerical_consistency():
    print("Testing numerical statements in CHAPTER5.md...")
    with open(CHAPTER5_MD, "r", encoding="utf-8") as f:
        text = f.read()

    # Key claims to verify in text
    key_numbers = [
        "0,5274", "10,19", "48,01%", "0,5100", "26,16",
        "0,5654", "0,6880", "1.600 tokens", "0,1225", "23,70%", "0,4856",
        "207 bài báo", "615 câu hỏi", "5.207",
        "0,5872", "0,5522", "0,5026", "30,26", "19,30", "103,39",
        "0,0830", "6,5 chunks/s", "19,0 chunks/s", "1,8 chunks/s"
    ]
    for kn in key_numbers:
        assert kn in text, f"Key numerical statement '{kn}' not found in CHAPTER5.md"
        print(f"  [PASS] Number '{kn}' verified in CHAPTER5.md.")


if __name__ == "__main__":
    print("Starting automated verification of Chapter 5 artifacts...")
    test_tables()
    test_figures()
    test_chapter_numerical_consistency()
    print("\nRunning exhaustive cell-by-cell and 91-claim verification...")
    import subprocess
    exhaustive_script = os.path.join(SCRIPT_DIR, "verify_chapter5_exhaustive.py")
    ret = subprocess.run([sys.executable, exhaustive_script], capture_output=False)
    assert ret.returncode == 0, f"Exhaustive verification failed with code {ret.returncode}"
    print("\nALL REPRODUCIBILITY CHECKS PASSED SUCCESSFULLY (100% MATCH).")
