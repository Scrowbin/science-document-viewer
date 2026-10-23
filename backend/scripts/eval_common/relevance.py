"""
Canonical Relevance Evaluation & Containment Module.
Provides uniform relevance definitions across all chunking and embedding strategies.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple

# Canonical 39-Stopword Set
STOPWORDS: Set[str] = {
    "a", "an", "the", "in", "on", "of", "for", "to", "is", "are", "was",
    "were", "and", "or", "that", "this", "it", "by", "with", "from", "as",
    "what", "how", "why", "which", "does", "did", "do", "we", "our", "their",
    "at", "be", "have", "has", "had", "not", "but", "also"
}


def tokenize_regex(text: str) -> List[str]:
    """Canonical lexical tokenizer with 39 English stopwords and min-length 2."""
    tokens = re.findall(r"[A-Za-z0-9_\-\.\$\/]+", text.lower())
    return [t for t in tokens if t not in STOPWORDS and len(t) > 1]


def clean_evidence(
    verbatim_evidence_quote: str,
    evidence_list: Optional[List[str]],
) -> Tuple[str, List[str]]:
    """
    Strip FLOAT SELECTED markers from evidence spans.
    Returns (cleaned_quote, cleaned_evidence_list).
    """
    cleaned_quote = ""
    if verbatim_evidence_quote and not verbatim_evidence_quote.strip().upper().startswith("FLOAT SELECTED"):
        cleaned_quote = verbatim_evidence_quote

    cleaned_list = []
    if evidence_list:
        for ev in evidence_list:
            if ev and not ev.strip().upper().startswith("FLOAT SELECTED"):
                cleaned_list.append(ev)

    return cleaned_quote, cleaned_list


def is_chunk_hit(
    chunk: Dict[str, Any],
    expected_arxiv_id: str,
    verbatim_evidence_quote: str = "",
    evidence_list: Optional[List[str]] = None,
    tau: float = 0.55,
) -> bool:
    """
    Evaluates whether a retrieved chunk constitutes a true relevance hit
    using the pre-registered calibrated Evidence Containment rule:
    Formula: cov_ev >= tau  OR  (|C_tok| >= 20  AND  cov_chunk >= tau  AND  cov_ev >= 0.20)
    """
    chunk_arxiv_id = chunk.get("paper_arxiv_id", "")
    if chunk_arxiv_id and chunk_arxiv_id != expected_arxiv_id:
        return False

    chunk_text_raw = chunk.get("text", "")
    chunk_text_lower = chunk_text_raw.lower()

    clean_quote, clean_list = clean_evidence(verbatim_evidence_quote, evidence_list)

    evidence_spans: List[str] = []
    if clean_list:
        evidence_spans.extend(clean_list)
    elif clean_quote:
        evidence_spans.append(clean_quote)

    if not evidence_spans:
        return False

    for ev_span in evidence_spans:
        clean_ev = re.sub(r"\s+", " ", ev_span).strip().lower()
        if not clean_ev:
            continue

        # Exact substring containment
        if clean_ev in chunk_text_lower:
            return True

        ev_tokens = set(tokenize_regex(ev_span))
        chunk_tokens = set(tokenize_regex(chunk_text_raw))

        if not ev_tokens or not chunk_tokens:
            continue

        inter = len(ev_tokens & chunk_tokens)
        cov_ev = inter / len(ev_tokens)
        cov_chunk = inter / len(chunk_tokens)

        if cov_ev >= tau:
            return True
        if len(chunk_tokens) >= 20 and cov_chunk >= tau and cov_ev >= 0.20:
            return True

    return False


def count_relevant_chunks(
    chunks: List[Dict[str, Any]],
    paper_arxiv_id: str,
    verbatim_evidence_quote: str = "",
    evidence_list: Optional[List[str]] = None,
    tau: float = 0.55,
) -> int:
    """
    Pre-compute R_q: total number of relevant chunks in the candidate pool
    for a given query, used to compute global IDCG.
    """
    count = 0
    for c in chunks:
        if is_chunk_hit(c, paper_arxiv_id, verbatim_evidence_quote, evidence_list, tau=tau):
            count += 1
    return count
