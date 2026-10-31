"""
Sequential execution runner for High-Power Full-Cohort Benchmarks:
1. SciFact Cross-Dataset Out-of-Domain Sanity Check (5,183 Abstracts)
2. High-Power Expanded Held-Out Cohort (160 Papers, 487 Queries) with SPECTER2 Adapter & Peak RSS
3. High-Power Expanded Hybrid Retrieval Benchmark (160 Papers, 487 Queries, Dense + BM25 RRF)
"""

import subprocess
import sys
import time
from pathlib import Path

WORKSPACE_ROOT = Path(__file__).resolve()
while WORKSPACE_ROOT.parent != WORKSPACE_ROOT and not (WORKSPACE_ROOT / "backend").exists():
    WORKSPACE_ROOT = WORKSPACE_ROOT.parent

PYTHON_EXE = Path(sys.executable)


def run_script(script_path: Path):
    print(f"\n{'='*80}")
    print(f"STARTING BENCHMARK: {script_path.name}")
    print(f"Path: {script_path}")
    print(f"{'='*80}\n", flush=True)
    t0 = time.time()

    cmd = [str(PYTHON_EXE), "-u", str(script_path)]
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    if proc.stdout is not None:
        for line in proc.stdout:
            print(line, end="", flush=True)

    proc.wait()
    duration = time.time() - t0
    if proc.returncode != 0:
        print(f"\n[ERROR] {script_path.name} failed with exit code {proc.returncode} after {duration:.1f}s\n", flush=True)
        raise RuntimeError(f"Failed to execute {script_path.name}")
    else:
        print(f"\n[SUCCESS] Completed {script_path.name} in {duration:.1f}s\n", flush=True)


def main():
    t_start = time.time()
    print("Beginning High-Power Academic Benchmark Suite (All 160 Papers / 487 Queries)...", flush=True)

    phase3_scripts = WORKSPACE_ROOT / "eval" / "phases" / "phase_3_embedding" / "scripts"
    phase6_scripts = WORKSPACE_ROOT / "eval" / "phases" / "phase_6_hybrid_retrieval" / "scripts"

    # 1. SciFact Cross-Dataset Out-of-Domain Check
    run_script(phase3_scripts / "evaluate_scifact_cross_dataset.py")

    # 2. Phase 3: High-Power Expanded Cohort (160 Papers, 487 Queries)
    run_script(phase3_scripts / "evaluate_expanded_cohort_with_adapters.py")

    # 3. Phase 6: High-Power Expanded Hybrid RRF (160 Papers, 487 Queries)
    run_script(phase6_scripts / "evaluate_expanded_hybrid_rrf.py")

    total_time = time.time() - t_start
    print(f"\n{'='*80}")
    print(f"ALL HIGH-POWER BENCHMARKS FINISHED IN {total_time/60:.2f} MINUTES!")
    print(f"{'='*80}\n", flush=True)


if __name__ == "__main__":
    main()
