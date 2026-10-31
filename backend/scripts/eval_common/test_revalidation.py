"""
Unit tests for eval_common.revalidation (evidence matching, production context assembly, CEC).
"""

import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from eval_common.revalidation import (
    assemble_context,
    context_evidence_coverage,
    estimate_tokens,
    evidence_found,
    evidence_match_rate,
    peerqa_evidence,
    qasper_text_evidence,
)


def test_qasper_text_evidence_skips_float_and_unanswerable():
    qa = {"answers": [
        {"answer": {"unanswerable": False, "evidence": ["Text paragraph.", "FLOAT SELECTED: Table 1"]}},
        {"answer": {"unanswerable": True, "evidence": ["Should be ignored."]}},
        {"answer": {"unanswerable": False, "evidence": ["Text paragraph.", "Second paragraph."]}},
    ]}
    assert qasper_text_evidence(qa) == ["Text paragraph.", "Second paragraph."]


def test_peerqa_evidence_drops_empty():
    assert peerqa_evidence({"answer_evidence_sent": ["a b", " ", None]}) == ["a b"]
    assert peerqa_evidence({"answer_evidence_sent": None}) == []


def test_evidence_found_verbatim_and_containment():
    text = "We train the model with Adam optimizer on the WMT dataset for ten epochs."
    assert evidence_found("Adam optimizer on the WMT dataset", text)
    assert not evidence_found("convolutional encoder residual blocks", text)
    assert evidence_match_rate(["Adam optimizer WMT dataset", "unrelated words entirely different"], text) == (1, 2)


def test_assemble_context_budget_and_cap():
    units = [{"text": "w " * 900}, {"text": "w " * 300}, {"text": "w " * 50}]
    chosen, used = assemble_context(units, budget=1600, max_units=5)
    assert len(chosen) == 2  # 1197 + 399 = 1596 tokens; the third (67) would exceed 1600
    assert used == estimate_tokens(units[0]["text"]) + estimate_tokens(units[1]["text"])
    big = [{"text": "w " * 2000}]
    assert len(assemble_context(big)[0]) == 1  # first unit always taken
    many = [{"text": "w"} for _ in range(9)]
    assert len(assemble_context(many)[0]) == 5


def test_cec_thresholds():
    ctx = "the encoder uses multi head attention with eight heads"
    ev = ["encoder multi head attention eight heads layer normalization residual"]
    assert context_evidence_coverage(ctx, ev, tau=0.5) == 1
    assert context_evidence_coverage(ctx, ev, tau=0.9) == 0
    assert context_evidence_coverage(ctx, [], tau=0.5) == 0
