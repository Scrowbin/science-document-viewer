#!/usr/bin/env python3
"""
E0 (2026-10-29): append the RQ5 exposure events that were never recorded.

The 250 papers evaluated in EXP-RQ5-MAIN-SAMPLED kept empty `exposure_events` after the run,
so they still looked unexposed to future sampling. This script only APPENDS:
  - one `EVALUATED_GENERATION_GOLD_EVIDENCE` event per sampled paper,
  - one `HUMAN_FAITHFULNESS_REVIEW` event per paper in the 20-question human review,
  - a `post_hoc_exposure_correction` note on each touched record,
  - an entry in the top-level `audit_corrections` list.
Existing fields (including the historical `is_unexposed_to_repository_experiments` flag and
`exposure_classifications`) are left unchanged; the appended events take precedence in
`check_experiment_overlap.py`. The script refuses to run twice.

Run from the repository root:
  python eval/scripts/append_rq5_exposure_events.py
"""

import json
import sys
from pathlib import Path

REG = Path("eval/experiment_provenance_registry.json")
MANIFEST = Path("eval/phases/phase_9_generation/artifacts/eval_sample_manifest_500q.json")
MAPPING = Path("eval/phases/phase_9_generation/artifacts/human_faithfulness_review/restricted_model_label_mapping.json")
EXP_ID = "EXP-RQ5-MAIN-SAMPLED"
DATE = "2026-10-29"


def main():
    raw = REG.read_text(encoding="utf-8")
    nl = "\r\n" if "\r\n" in raw else "\n"
    reg = json.loads(raw)
    index = reg["paper_index"]

    sampled = sorted({it["paper_arxiv_id"] for it in json.loads(MANIFEST.read_text(encoding="utf-8"))["selected_eval_items"]})
    reviewed = sorted({r["paper_arxiv_id"] for r in json.loads(MAPPING.read_text(encoding="utf-8"))["records"]})
    registered = set(reg["registered_experiments"][EXP_ID]["paper_ids"])
    if set(sampled) != registered:
        sys.exit("Manifest papers differ from the registered EXP-RQ5-MAIN-SAMPLED paper_ids; aborting.")
    if not set(reviewed) <= set(sampled):
        sys.exit("Human-review papers are not a subset of the RQ5 sample; aborting.")
    if any(ev.get("experiment_id") == EXP_ID for pid in sampled for ev in index[pid].get("exposure_events", [])):
        sys.exit("RQ5 exposure events already present; nothing to do.")

    for pid in sampled:
        rec = index[pid]
        rec.setdefault("exposure_events", []).append({
            "experiment_id": EXP_ID,
            "phase": "RQ5",
            "role": "EVALUATED_GENERATION_GOLD_EVIDENCE",
            "outputs_inspected": True,
            "influenced_decision": "Selection of llama3.2:3b as default generator",
            "classification": "CONFIRMATORY_EVALUATION_EXPOSURE",
            "recorded_retroactively_on": DATE,
        })
        if pid in reviewed:
            rec["exposure_events"].append({
                "experiment_id": EXP_ID,
                "phase": "RQ5",
                "role": "HUMAN_FAITHFULNESS_REVIEW",
                "outputs_inspected": True,
                "influenced_decision": "Exploratory faithfulness audit (60 answers)",
                "classification": "CONFIRMATORY_EVALUATION_EXPOSURE",
                "recorded_retroactively_on": DATE,
            })
        rec["post_hoc_exposure_correction"] = (
            f"{DATE}: RQ5 exposure appended retroactively (E0). The fields "
            "'is_unexposed_to_repository_experiments' and 'exposure_classifications' are historical "
            "(state at sampling time) and are superseded by 'exposure_events'."
        )

    reg.setdefault("audit_corrections", []).append({
        "date": DATE,
        "experiment_id": EXP_ID,
        "field_corrections": {"exposure_events_appended_papers": len(sampled),
                              "human_review_events_appended_papers": len(reviewed)},
        "note": "RQ5 exposure was never written to paper_index after the run, and check_experiment_overlap.py "
                "excluded RQ5 events unconditionally, so the 250 sampled papers still passed as unexposed. "
                "Events appended (append-only); the checker now excludes an experiment only on request "
                "(--exclude-experiment).",
    })
    REG.write_text(json.dumps(reg, indent=2, ensure_ascii=False).replace("\n", nl) + nl, encoding="utf-8", newline="")
    print(f"appended RQ5 events to {len(sampled)} papers ({len(reviewed)} also human-reviewed)")


if __name__ == "__main__":
    main()
