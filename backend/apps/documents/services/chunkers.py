"""
Academic Document Chunking Strategies (RQ2 Controlled Ablation).
Provides unified chunking implementations across:
  1. fixed_size: Strict N-token sliding window across full document, ignoring headings, zero overlap.
  2. fixed_size_overlap: Sliding window with N max_tokens and K overlap tokens, ignoring headings.
  3. semantic: Sentence splitting + consecutive sentence embedding similarity + drop thresholding (percentile-based) with max_token ceiling.
  4. section: Pure section-based chunks (1 chunk per section).
  5. section_token: Section-aware chunking bounded to max_tokens, zero overlap.
  6. section_overlap: Section-aware chunking with token limits and sliding window overlap (production default).
"""

import math
import re
from typing import Any, Dict, List, Optional, Union
import numpy as np


def estimate_tokens(text: str) -> int:
    """Estimates token count for English scientific text (1 word approx 1.33 tokens)."""
    words = len(text.strip().split())
    return max(1, int(math.ceil(words * 1.33)))


def split_sentences(text: str) -> List[str]:
    """Splits academic text into grammatical sentences using regex lookbehinds."""
    if not text:
        return []
    raw = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9\"'`])", text.strip())
    sentences = [s.strip() for s in raw if s.strip()]
    return sentences if sentences else [text.strip()]


def chunk_fixed_size(
    text_or_sections: Union[str, List[Dict[str, Any]]],
    max_tokens: int = 400,
    paper_id: str = "doc",
) -> List[Dict[str, Any]]:
    """
    Fixed-size continuous chunking across the entire document text.
    Strictly ignores section headings and layout boundaries; zero overlap.
    """
    if isinstance(text_or_sections, list):
        full_text = "\n\n".join(
            s.get("text", "") for s in text_or_sections if s.get("text")
        )
        first_page = text_or_sections[0].get("start_page", 1) if text_or_sections else 1
    else:
        full_text = text_or_sections
        first_page = 1

    words = full_text.strip().split()
    if not words:
        return []

    # 400 tokens approx 300 words
    max_words = max(20, int(max_tokens / 1.33))
    chunks: List[Dict[str, Any]] = []

    for idx, start_idx in enumerate(range(0, len(words), max_words)):
        slice_words = words[start_idx : start_idx + max_words]
        chunk_text = " ".join(slice_words)
        token_cnt = estimate_tokens(chunk_text)
        chunks.append(
            {
                "chunk_id": f"{paper_id}_fixed_{idx:03d}",
                "paper_arxiv_id": paper_id,
                "section": "None (Fixed Continuous)",
                "page": first_page,
                "strategy": "fixed_size",
                "token_count": token_cnt,
                "text": chunk_text,
                "preview": chunk_text[:180].replace("\n", " ").strip() + "...",
            }
        )

    return chunks


def chunk_fixed_size_overlap(
    text_or_sections: Union[str, List[Dict[str, Any]]],
    max_tokens: int = 400,
    overlap: int = 80,
    paper_id: str = "doc",
) -> List[Dict[str, Any]]:
    """
    Fixed-size continuous chunking with sliding window overlap across entire document text.
    Uses identical token budget (400 max_tokens, 80 overlap) as section_overlap for fair comparison.
    """
    if isinstance(text_or_sections, list):
        full_text = "\n\n".join(
            s.get("text", "") for s in text_or_sections if s.get("text")
        )
        first_page = text_or_sections[0].get("start_page", 1) if text_or_sections else 1
    else:
        full_text = text_or_sections
        first_page = 1

    words = full_text.strip().split()
    if not words:
        return []

    max_words = max(20, int(max_tokens / 1.33))
    overlap_words = max(0, int(overlap / 1.33))
    step_words = max(10, max_words - overlap_words)

    chunks: List[Dict[str, Any]] = []
    idx = 0
    start_idx = 0

    while start_idx < len(words):
        slice_words = words[start_idx : start_idx + max_words]
        chunk_text = " ".join(slice_words)
        token_cnt = estimate_tokens(chunk_text)
        chunks.append(
            {
                "chunk_id": f"{paper_id}_fixed_overlap_{idx:03d}",
                "paper_arxiv_id": paper_id,
                "section": "None (Fixed Overlap)",
                "page": first_page,
                "strategy": "fixed_size_overlap",
                "token_count": token_cnt,
                "text": chunk_text,
                "preview": chunk_text[:180].replace("\n", " ").strip() + "...",
            }
        )
        idx += 1
        start_idx += step_words

    return chunks


def chunk_semantic(
    text_or_sections: Union[str, List[Dict[str, Any]]],
    embedder: Any,
    max_tokens: int = 400,
    min_tokens: int = 60,
    percentile_threshold: float = 25.0,
    buffer_size: int = 1,
    paper_id: str = "doc",
) -> List[Dict[str, Any]]:
    # sentences tagged with (text, section_idx, heading, page); never chunk across sections
    sents: List[Tuple[str, int, str, Any]] = []
    if isinstance(text_or_sections, list):
        for sec_idx, sec in enumerate(text_or_sections):
            heading = sec.get("heading") or sec.get("title") or "Untitled Section"
            page = sec.get("page_start", sec.get("start_page", sec.get("page", 1)))
            for s in split_sentences((sec.get("text") or "").strip()):
                sents.append((s, sec_idx, heading, page))
    else:
        sents = [(s, 0, "Semantic Group", 1) for s in split_sentences(text_or_sections)]
    if not sents:
        return []

    texts = [s[0] for s in sents]
    sec_ids = np.array([s[1] for s in sents])
    n = len(texts)

    embs = np.asarray(
        embedder.encode(
            [f"passage: {t}" for t in texts],  # drop prefix if not e5
            batch_size=32,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
    )

    # smooth within section: mean of neighbors' embeddings (approximates LangChain buffer_size)
    # smoothing: mean of in-section neighbor embeddings (cheap, no extra encode)
    if buffer_size > 0:
        sm = np.empty_like(embs)
        for i in range(n):
            lo, hi = max(0, i - buffer_size), min(n, i + buffer_size + 1)
            idx = [j for j in range(lo, hi) if sec_ids[j] == sec_ids[i]]
            sm[i] = embs[idx].mean(axis=0)
        sm /= np.linalg.norm(sm, axis=1, keepdims=True) + 1e-12
    else:
        sm = embs
    # stuff below is way slower,  but it has accuracy ig
    # alt: LangChain-parity smoothing, re-embed concatenated windows (~3x encode cost)
    # if buffer_size > 0:
    #     win = []
    #     for i in range(n):
    #         lo, hi = max(0, i - buffer_size), min(n, i + buffer_size + 1)
    #         win.append(
    #             " ".join(texts[j] for j in range(lo, hi) if sec_ids[j] == sec_ids[i])
    #         )
    #     sm = np.asarray(
    #         embedder.encode(
    #             [f"passage: {w}" for w in win],
    #             batch_size=32,
    #             normalize_embeddings=True,
    #             show_progress_bar=False,
    #         )
    #     )
    # else:
    #     sm = embs
    sims = np.sum(sm[:-1] * sm[1:], axis=1)
    same_sec = sec_ids[:-1] == sec_ids[1:]
    in_sec = sims[same_sec]
    thresh = float(np.percentile(in_sec, percentile_threshold)) if in_sec.size else -1.0

    tok = [estimate_tokens(t) for t in texts]
    groups: List[List[int]] = [[0]]
    cur_tok = tok[0]
    for i in range(n - 1):
        j = i + 1
        split = (
            not same_sec[i]
            or cur_tok + tok[j] > max_tokens
            or (sims[i] < thresh and cur_tok >= min_tokens)
        )
        if split:
            groups.append([j])
            cur_tok = tok[j]
        else:
            groups[-1].append(j)
            cur_tok += tok[j]

    # merge undersized groups into the previous one (same section, if it fits)
    merged: List[List[int]] = []
    for g in groups:
        gt = sum(tok[k] for k in g)
        if (
            merged
            and gt < min_tokens
            and sec_ids[g[0]] == sec_ids[merged[-1][0]]
            and sum(tok[k] for k in merged[-1]) + gt <= max_tokens
        ):
            merged[-1] = merged[-1] + g
        else:
            merged.append(g)

    chunks: List[Dict[str, Any]] = []
    for c_idx, g in enumerate(merged):
        text = " ".join(texts[k] for k in g)
        _, _, heading, page = sents[g[0]]
        chunks.append(
            {
                "chunk_id": f"{paper_id}_semantic_{c_idx:03d}",
                "paper_arxiv_id": paper_id,
                "section": heading,
                "page": page,
                "strategy": "semantic",
                "token_count": sum(tok[k] for k in g),
                "text": text,
                "preview": text[:180].replace("\n", " ").strip()
                + ("..." if len(text) > 180 else ""),
            }
        )
    return chunks


def chunk_hierarchical(
    sections: List[Dict[str, Any]],
    child_max_tokens: int = 200,
    child_overlap: int = 40,
    paper_id: str = "doc",
) -> List[Dict[str, Any]]:
    child_max_words = max(15, int(child_max_tokens / 1.33))
    child_overlap_words = max(0, int(child_overlap / 1.33))
    step_words = max(10, child_max_words - child_overlap_words)

    chunks: List[Dict[str, Any]] = []
    for sec_idx, sec in enumerate(sections):
        parent_text = (sec.get("text") or "").strip()
        if not parent_text:
            continue

        parent_id = f"{paper_id}_parent_{sec_idx:03d}"
        heading = sec.get("heading") or sec.get("title") or "Untitled Section"
        prefix = "" if heading == "Untitled Section" else f"[{heading}]\n"
        first_page = sec.get("page_start", sec.get("start_page", sec.get("page", 1)))
        parent_tokens = estimate_tokens(parent_text)

        spans = [m.span() for m in re.finditer(r"\S+", parent_text)]
        n = len(spans)  # >= 1 since parent_text is non-empty after strip

        start, c_idx = 0, 0
        while True:
            end = min(start + child_max_words, n)
            char_start, char_end = spans[start][0], spans[end - 1][1]
            child_text = parent_text[char_start:char_end]

            chunks.append(
                {
                    "chunk_id": f"{parent_id}_c{c_idx:03d}",
                    "paper_arxiv_id": paper_id,
                    "parent_id": parent_id,
                    "parent_text": parent_text,
                    "parent_tokens": parent_tokens,
                    "section": heading,
                    "page": first_page,
                    "strategy": "hierarchical",
                    "token_count": estimate_tokens(child_text),
                    "text": prefix + child_text,
                    "child_text": child_text,
                    "char_start": char_start,
                    "char_end": char_end,
                    "chunk_index": c_idx,
                    "preview": child_text[:180].replace("\n", " ").strip()
                    + ("..." if len(child_text) > 180 else ""),
                }
            )
            c_idx += 1
            if end >= n:  # window hit the end: stop, no subset-tail chunk
                break
            start += step_words

    return chunks


def chunk_document_unified(
    sections: List[Dict[str, Any]],
    strategy: str = "section_overlap",
    max_tokens: int = 400,
    overlap: int = 80,
    embedder: Optional[Any] = None,
    semantic_percentile: float = 25.0,
    paper_id: str = "doc",
) -> List[Dict[str, Any]]:
    """
    Unified entry point for all 7 chunking strategies.
    Preserves exact backwards compatibility with chunk_sections.
    """
    if strategy == "fixed_size":
        return chunk_fixed_size(sections, max_tokens=max_tokens, paper_id=paper_id)
    elif strategy == "fixed_size_overlap":
        return chunk_fixed_size_overlap(
            sections, max_tokens=max_tokens, overlap=overlap, paper_id=paper_id
        )
    elif strategy == "semantic":
        if embedder is None:
            raise ValueError(
                "strategy='semantic' requires an initialized embedder instance"
            )
        return chunk_semantic(
            sections,
            embedder=embedder,
            max_tokens=max_tokens,
            percentile_threshold=semantic_percentile,
            paper_id=paper_id,
        )
    elif strategy in ("hierarchical", "hierarchical_child"):
        return chunk_hierarchical(
            sections, child_max_tokens=200, child_overlap=40, paper_id=paper_id
        )
    else:
        # Standard structure-aware strategies: section, section_token, section_overlap
        from .chunking_utils import chunk_sections

        chunks = chunk_sections(
            sections, strategy=strategy, max_tokens=max_tokens, overlap=overlap
        )
        for idx, c in enumerate(chunks):
            c["paper_arxiv_id"] = paper_id
            c["chunk_id"] = f"{paper_id}_{strategy}_{idx:03d}"
        return chunks
