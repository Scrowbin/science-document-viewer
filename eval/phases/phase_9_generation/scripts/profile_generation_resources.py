#!/usr/bin/env python3
"""
the generation experiment-M: resource and stability profile of the three local LLMs (pre-registered:
protocol rq5_rq6.json (archived) "the generation experiment-M"). Re-uses the the generation experiment prompt and gold-evidence contexts.

Questions: every 8th item of the frozen 500-question manifest (first 60).
Per model: unload (keep_alive=0) -> one cold request (load time) -> 2 warm passes over the 60 questions
(temperature 0, num_predict 256). Memory: peak working set (Windows RSS) summed over ollama.exe processes
(server + model runners; the tray app is excluded) and of this Python process, sampled every 0.1 s; CPU-only
(checked via /api/ps size_vram). Stability: identical outputs across the two warm passes. Agreement with the
stored the generation experiment answers is descriptive only (the stored run did not record the Ollama version or model digests).
Output: eval/phases/phase_9_generation/artifacts/profile_generation_resources/
"""

import json
import sys
import threading
import time
from pathlib import Path

import psutil
import requests

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from evaluate_generation import build_prompt  # noqa: E402

ART = ROOT / "eval" / "phases" / "phase_9_generation" / "artifacts"
OUT = ART / "profile_generation_resources"
URL = "http://localhost:11434"
MODELS = ["llama3.2:3b", "llama3.2:1b", "qwen2.5:0.5b"]
OPTIONS = {"temperature": 0, "num_predict": 256}


class TreeSampler:
    def __init__(self):
        self.peak_ollama = 0
        self.peak_python = 0
        self.me = psutil.Process()
        self._stop = threading.Event()
        threading.Thread(target=self._run, daemon=True).start()

    def _run(self):
        while not self._stop.is_set():
            # ollama.exe server plus all its descendants (model runners: llama-server.exe in Ollama 0.40,
            # ollama_llama_server.exe / "ollama runner" in older versions). The tray app is not a descendant.
            total, seen = 0, set()
            for p in psutil.process_iter(["name"]):
                if (p.info["name"] or "").lower() != "ollama.exe":
                    continue
                try:
                    for q in [p] + p.children(recursive=True):
                        if q.pid not in seen:
                            seen.add(q.pid)
                            total += q.memory_info().rss
                except psutil.Error:
                    pass
            self.peak_ollama = max(self.peak_ollama, total)
            self.peak_python = max(self.peak_python, self.me.memory_info().rss)
            time.sleep(0.1)

    def stop(self):
        self._stop.set()
        return {"ollama_tree_working_set_peak_mb": round(self.peak_ollama / 2**20, 1),
                "python_working_set_peak_mb": round(self.peak_python / 2**20, 1)}


def unload_all(timeout_s=60):
    """Unload every resident model and wait until /api/ps is empty."""
    for x in requests.get(f"{URL}/api/ps", timeout=10).json().get("models", []):
        requests.post(f"{URL}/api/generate", json={"model": x["name"], "keep_alive": 0}, timeout=120)
    for _ in range(timeout_s):
        if not requests.get(f"{URL}/api/ps", timeout=10).json().get("models", []):
            return
        time.sleep(1)
    raise RuntimeError("models still resident after unload")


def generate(model, prompt, keep_alive="10m"):
    t = time.perf_counter()
    r = requests.post(f"{URL}/api/generate", json={"model": model, "prompt": prompt, "stream": False,
                                                   "options": OPTIONS, "keep_alive": keep_alive}, timeout=600)
    r.raise_for_status()
    d = r.json()
    d["wall_s"] = time.perf_counter() - t
    return d


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    man = json.load(open(ART / "eval_sample_manifest_500q.json", encoding="utf-8"))["selected_eval_items"][::8][:60]
    stored = json.load(open(ART / "rq5_llm_generation_benchmark_500q.json", encoding="utf-8"))["detailed_records"]
    version = requests.get(f"{URL}/api/version", timeout=10).json().get("version")
    tags = {m["name"]: m["digest"] for m in requests.get(f"{URL}/api/tags", timeout=10).json()["models"]}
    prompts = [build_prompt(it["paper_title"], "\n\n".join(it["ground_truth_evidence"]), it["question_text"]) for it in man]
    result = {"ollama_version": version, "questions": [it["question_id"] for it in man], "options": OPTIONS, "models": {}}
    for m in MODELS:
        unload_all()  # no other model may stay resident, or the tree peak includes it
        time.sleep(3)
        sampler = TreeSampler()
        cold = generate(m, prompts[0])
        ps = requests.get(f"{URL}/api/ps", timeout=10).json().get("models", [])
        passes = []
        for _ in range(2):
            outs = [generate(m, p) for p in prompts]
            passes.append(outs)
        mem = sampler.stop()
        warm = [o for p in passes for o in p]
        s_map = {r["question_id"]: r["prediction"] for r in stored[m]}
        same_runs = sum(1 for a, b in zip(passes[0], passes[1]) if a["response"].strip() == b["response"].strip())
        same_stored = sum(1 for it, o in zip(man, passes[0]) if o["response"].strip() == s_map[it["question_id"]].strip())
        tok_s = [o["eval_count"] / (o["eval_duration"] / 1e9) for o in warm if o.get("eval_duration")]
        result["models"][m] = {
            "digest": tags.get(m), "size_vram": next((x.get("size_vram") for x in ps if x["name"] == m), None),
            "cold_load_s": round(cold.get("load_duration", 0) / 1e9, 2), "cold_total_s": round(cold["wall_s"], 2),
            "warm_total_s_p50": round(sorted(o["wall_s"] for o in warm)[len(warm) // 2], 2),
            "warm_prompt_eval_s_mean": round(sum(o.get("prompt_eval_duration", 0) for o in warm) / len(warm) / 1e9, 3),
            "warm_tokens_per_s_mean": round(sum(tok_s) / len(tok_s), 1) if tok_s else None,
            "memory": mem,
            "stability_identical_across_2_warm_passes": f"{same_runs}/{len(prompts)}",
            "identical_to_stored_rq5_answer_descriptive": f"{same_stored}/{len(prompts)}",
        }
        requests.post(f"{URL}/api/generate", json={"model": m, "keep_alive": 0}, timeout=120)
        print(m, result["models"][m], flush=True)
    (OUT / "summary.json").write_text(json.dumps(result, indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
