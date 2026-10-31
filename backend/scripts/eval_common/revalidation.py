"""
Shared definitions for the 2026-10 revalidation study (RQ1-RQ6).

Fixed before any new scoring (see reports/revalidation/RESEARCH_VALIDITY_MATRIX.md):
  - Evidence of a question = text evidence paragraphs of ANY answerable annotator (FLOAT SELECTED removed).
  - Evidence found in a text  = >= 80% of the paragraph's content words occur in the text (version check,
                                RQ1 evidence recall).
  - Context assembly          = production rule of DocumentRAG.hybrid_search: take ranked units in order,
                                stop before a unit that would exceed the budget (the first unit is always
                                taken), at most `max_units` units; tokens = estimate_tokens (words x 1.33).
  - Context Evidence Coverage = the assembled context covers >= tau (0.50) of the content words of at least
    (CEC)                       one evidence paragraph, or contains it verbatim.
Content words = tokenize_regex (regex tokens, 39 stopwords, length > 1), as in relevance.is_chunk_hit.
"""

import math
import re
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from .relevance import tokenize_regex

FOUND_THRESHOLD = 0.80
CEC_TAU = 0.50
CONTEXT_BUDGET = 1600
MAX_UNITS = 5


def estimate_tokens(text: str) -> int:
    """Same estimate as apps.documents.services.chunkers.estimate_tokens (1 word ~ 1.33 tokens)."""
    return max(1, int(math.ceil(len(text.strip().split()) * 1.33)))


def qasper_text_evidence(qa: Dict[str, Any]) -> List[str]:
    """Union of non-FLOAT text evidence paragraphs over answerable annotators (order kept, deduplicated)."""
    out: List[str] = []
    for ann in qa.get("answers", []):
        a = ann.get("answer", {})
        if a.get("unanswerable", False):
            continue
        for ev in a.get("evidence", []):
            if isinstance(ev, str) and ev.strip() and not ev.startswith("FLOAT SELECTED") and ev not in out:
                out.append(ev)
    return out


def peerqa_evidence(q: Dict[str, Any]) -> List[str]:
    """PeerQA evidence sentences written/selected by the authors (answer_evidence_sent)."""
    return [e for e in (q.get("answer_evidence_sent") or []) if isinstance(e, str) and e.strip()]


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip().lower()


def coverage(evidence: str, text_tokens: set) -> float:
    ev = set(tokenize_regex(evidence))
    if not ev:
        return 0.0
    return len(ev & text_tokens) / len(ev)


def evidence_found(evidence: str, text: str, text_tokens: set = None, threshold: float = FOUND_THRESHOLD) -> bool:
    if text_tokens is None:
        text_tokens = set(tokenize_regex(text))
    if _normalise(evidence) and _normalise(evidence) in _normalise(text):
        return True
    return coverage(evidence, text_tokens) >= threshold


def evidence_match_rate(evidence_list: Sequence[str], text: str, threshold: float = FOUND_THRESHOLD) -> Tuple[int, int]:
    """Returns (found, total) evidence paragraphs for one text."""
    tokens = set(tokenize_regex(text))
    found = sum(1 for ev in evidence_list if evidence_found(ev, text, tokens, threshold))
    return found, len(evidence_list)


def assemble_context(units: Iterable[Dict[str, Any]], budget: int = CONTEXT_BUDGET,
                     max_units: int = MAX_UNITS) -> Tuple[List[Dict[str, Any]], int]:
    """Production budget rule. Each unit needs 'text'; an optional 'tokens' overrides the estimate."""
    chosen: List[Dict[str, Any]] = []
    used = 0
    for u in units:
        t = u.get("tokens") or estimate_tokens(u["text"])
        if used + t > budget and chosen:
            break
        chosen.append(u)
        used += t
        if len(chosen) >= max_units:
            break
    return chosen, used


def context_evidence_coverage(context_text: str, evidence_list: Sequence[str], tau: float = CEC_TAU) -> int:
    """1 if the context covers at least one evidence paragraph at threshold tau, else 0."""
    if not evidence_list:
        return 0
    tokens = set(tokenize_regex(context_text))
    norm_ctx = _normalise(context_text)
    for ev in evidence_list:
        if _normalise(ev) and _normalise(ev) in norm_ctx:
            return 1
        if coverage(ev, tokens) >= tau:
            return 1
    return 0
