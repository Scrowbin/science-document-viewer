"""
Academic Document Chunking Strategies (RQ2 Controlled Ablation).
Provides unified chunking implementations across:
  1. fixed_size: Strict N-token sliding window across full document, ignoring headings, zero overlap.
  2. fixed_size_overlap: Sliding window with N max_tokens and K overlap tokens, ignoring headings.
  3. semantic: Sentence splitting + consecutive sentence embedding similarity + drop thresholding (percentile-based) with max_token ceiling.
  4. section: Pure section-based chunks (1 chunk per section).
  5. section_token: Section-aware chunking bounded to max_tokens, zero overlap.
  6. section_overlap: Section-aware chunking with token limits and sliding window overlap (flat baseline; default of the /chunks/ inspection API).
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
        full_text = "\n\n".join(s.get("text", "") for s in text_or_sections if s.get("text"))
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
        chunks.append({
            "chunk_id": f"{paper_id}_fixed_{idx:03d}",
            "paper_arxiv_id": paper_id,
            "section": "None (Fixed Continuous)",
            "page": first_page,
            "strategy": "fixed_size",
            "token_count": token_cnt,
            "text": chunk_text,
            "preview": chunk_text[:180].replace("\n", " ").strip() + "...",
        })

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
        full_text = "\n\n".join(s.get("text", "") for s in text_or_sections if s.get("text"))
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
        chunks.append({
            "chunk_id": f"{paper_id}_fixed_overlap_{idx:03d}",
            "paper_arxiv_id": paper_id,
            "section": "None (Fixed Overlap)",
            "page": first_page,
            "strategy": "fixed_size_overlap",
            "token_count": token_cnt,
            "text": chunk_text,
            "preview": chunk_text[:180].replace("\n", " ").strip() + "...",
        })
        idx += 1
        start_idx += step_words

    return chunks


def chunk_semantic(
    text_or_sections: Union[str, List[Dict[str, Any]]],
    embedder: Any,
    max_tokens: int = 400,
    percentile_threshold: float = 25.0,
    paper_id: str = "doc",
) -> List[Dict[str, Any]]:
    """
    Semantic chunking:
      1. Splits document into grammatical sentences.
      2. Embeds each sentence using the same embedding model.
      3. Computes cosine similarity between consecutive sentences.
      4. Splits at similarity drops below the specified percentile threshold.
      5. Groups sentences into chunks respecting max_tokens ceiling.
    """
    if isinstance(text_or_sections, list):
        full_text = "\n\n".join(s.get("text", "") for s in text_or_sections if s.get("text"))
        first_page = text_or_sections[0].get("start_page", 1) if text_or_sections else 1
    else:
        full_text = text_or_sections
        first_page = 1

    sentences = split_sentences(full_text)
    if not sentences:
        return []
    if len(sentences) <= 2:
        chunk_text = " ".join(sentences)
        return [{
            "chunk_id": f"{paper_id}_semantic_000",
            "paper_arxiv_id": paper_id,
            "section": "Semantic Group",
            "page": first_page,
            "strategy": "semantic",
            "token_count": estimate_tokens(chunk_text),
            "text": chunk_text,
            "preview": chunk_text[:180].replace("\n", " ").strip() + "...",
        }]

    # Embed individual sentences
    sent_embs = embedder.encode(
        [f"passage: {s}" for s in sentences],
        batch_size=32,
        normalize_embeddings=True,
        show_progress_bar=False,
    )
    sent_mat = np.array(sent_embs)

    # Consecutive cosine similarities: dot product of normalized vectors
    consec_sims = np.sum(sent_mat[:-1] * sent_mat[1:], axis=1)

    # Threshold: pre-registered percentile (e.g. 25th percentile lowest similarities)
    thresh = float(np.percentile(consec_sims, percentile_threshold))

    # Form clusters
    chunks: List[Dict[str, Any]] = []
    current_sentences: List[str] = [sentences[0]]
    current_tokens = estimate_tokens(sentences[0])
    chunk_idx = 0

    for i in range(len(consec_sims)):
        next_sent = sentences[i + 1]
        next_tokens = estimate_tokens(next_sent)
        sim = consec_sims[i]

        # Split condition: similarity dropped below threshold OR max_tokens would be breached
        should_split = (sim < thresh and current_tokens >= 60) or (current_tokens + next_tokens > max_tokens)

        if should_split:
            chunk_text = " ".join(current_sentences)
            chunks.append({
                "chunk_id": f"{paper_id}_semantic_{chunk_idx:03d}",
                "paper_arxiv_id": paper_id,
                "section": "Semantic Group",
                "page": first_page,
                "strategy": "semantic",
                "token_count": current_tokens,
                "text": chunk_text,
                "preview": chunk_text[:180].replace("\n", " ").strip() + "...",
            })
            chunk_idx += 1
            current_sentences = [next_sent]
            current_tokens = next_tokens
        else:
            current_sentences.append(next_sent)
            current_tokens += next_tokens

    if current_sentences:
        chunk_text = " ".join(current_sentences)
        chunks.append({
            "chunk_id": f"{paper_id}_semantic_{chunk_idx:03d}",
            "paper_arxiv_id": paper_id,
            "section": "Semantic Group",
            "page": first_page,
            "strategy": "semantic",
            "token_count": current_tokens,
            "text": chunk_text,
            "preview": chunk_text[:180].replace("\n", " ").strip() + "...",
        })

    return chunks


def locate_span(section: Dict[str, Any], char_start: int, char_end: int) -> Dict[str, Any]:
    """
    Citation location of section text[char_start:char_end], from the section's line_map
    (rows [char_start, char_end, page, x0, y0, x1, y1]; see chunking_utils.extract_sections_from_pdf).
    Returns {} when the section has no line map. Lines cut by the span are clipped horizontally in
    proportion to the characters covered (an approximation; glyph widths vary).
    """
    rows = section.get("line_map")
    if not rows:
        return {}
    sizes = section.get("page_sizes") or {}
    by_page: Dict[int, List[List[float]]] = {}
    for ls, le, page, x0, y0, x1, y1 in rows:
        if le <= char_start or ls >= char_end or le <= ls:
            continue
        a = (max(char_start, ls) - ls) / (le - ls)
        b = (min(char_end, le) - ls) / (le - ls)
        by_page.setdefault(int(page), []).append(
            [round(x0 + a * (x1 - x0), 2), y0, round(x0 + b * (x1 - x0), 2), y1])
    if not by_page:
        return {}
    pages = sorted(by_page)
    return {
        "loc_page_start": pages[0],
        "loc_page_end": pages[-1],
        "locations": [{"page": p, "width": (sizes.get(p) or [0, 0])[0], "height": (sizes.get(p) or [0, 0])[1],
                       "rects": by_page[p]} for p in pages],
    }


def chunk_hierarchical(
    sections: List[Dict[str, Any]],
    child_max_tokens: int = 200,
    child_overlap: int = 40,
    paper_id: str = "doc",
) -> List[Dict[str, Any]]:
    """
    Hierarchical (Small-to-Big) chunking strategy:
      - Parent level: Document sections preserving full discourse boundaries.
      - Child level: Granular sub-chunks (200 tokens max, 40 overlap) for precise vector embedding.
      - Each child carries parent metadata ('parent_id', 'parent_text', 'parent_tokens')
        and formats text with parent heading context for enriched semantic matching.
    """
    child_chunks: List[Dict[str, Any]] = []
    child_max_words = max(15, int(child_max_tokens / 1.33))
    child_overlap_words = max(0, int(child_overlap / 1.33))
    step_words = max(10, child_max_words - child_overlap_words)

    for sec_idx, sec in enumerate(sections):
        parent_id = f"{paper_id}_parent_{sec_idx:03d}"
        heading = sec.get("heading") or sec.get("title") or "Untitled Section"
        parent_text = (sec.get("text") or "").strip()
        first_page = sec.get("page_start", sec.get("start_page", sec.get("page", 1)))
        if not parent_text:
            continue

        parent_tokens = estimate_tokens(parent_text)
        words = parent_text.split()
        word_spans = [(m.start(), m.end()) for m in re.finditer(r"\S+", parent_text)]

        if len(words) <= child_max_words:
            chunk_text = parent_text
            formatted_text = f"[{heading}]\n{chunk_text}" if heading != "Untitled Section" else chunk_text
            child_chunks.append({
                "chunk_id": f"{parent_id}_c000",
                "paper_arxiv_id": paper_id,
                "parent_id": parent_id,
                "parent_text": parent_text,
                "parent_tokens": parent_tokens,
                "section": heading,
                "page": first_page,
                "strategy": "hierarchical",
                "token_count": estimate_tokens(chunk_text),
                "text": formatted_text,
                "child_text": chunk_text,
                "char_start": 0,
                "char_end": len(parent_text),
                "chunk_index": 0,
                "preview": chunk_text[:180].replace("\n", " ").strip() + "...",
                **locate_span(sec, 0, len(parent_text)),
            })
            continue

        start_idx = 0
        c_idx = 0
        while start_idx < len(words):
            slice_words = words[start_idx : start_idx + child_max_words]
            if not slice_words:
                break
            
            # Compute exact character offsets within parent_text using word spans
            char_start = word_spans[start_idx][0]
            last_word_idx = min(len(word_spans) - 1, start_idx + len(slice_words) - 1)
            char_end = word_spans[last_word_idx][1]
            chunk_text = parent_text[char_start:char_end]

            formatted_text = f"[{heading}]\n{chunk_text}" if heading != "Untitled Section" else chunk_text
            child_chunks.append({
                "chunk_id": f"{parent_id}_c{c_idx:03d}",
                "paper_arxiv_id": paper_id,
                "parent_id": parent_id,
                "parent_text": parent_text,
                "parent_tokens": parent_tokens,
                "section": heading,
                "page": first_page,
                "strategy": "hierarchical",
                "token_count": estimate_tokens(chunk_text),
                "text": formatted_text,
                "child_text": chunk_text,
                "char_start": char_start,
                "char_end": char_end,
                "chunk_index": c_idx,
                "preview": chunk_text[:180].replace("\n", " ").strip() + "...",
                **locate_span(sec, char_start, char_end),
            })
            c_idx += 1
            start_idx += step_words

    return child_chunks


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
        return chunk_fixed_size_overlap(sections, max_tokens=max_tokens, overlap=overlap, paper_id=paper_id)
    elif strategy == "semantic":
        if embedder is None:
            raise ValueError("strategy='semantic' requires an initialized embedder instance")
        return chunk_semantic(sections, embedder=embedder, max_tokens=max_tokens, percentile_threshold=semantic_percentile, paper_id=paper_id)
    elif strategy in ("hierarchical", "hierarchical_child"):
        return chunk_hierarchical(sections, child_max_tokens=200, child_overlap=40, paper_id=paper_id)
    else:
        # Standard structure-aware strategies: section, section_token, section_overlap
        from .chunking_utils import chunk_sections
        chunks = chunk_sections(sections, strategy=strategy, max_tokens=max_tokens, overlap=overlap)
        for idx, c in enumerate(chunks):
            c["paper_arxiv_id"] = paper_id
            c["chunk_id"] = f"{paper_id}_{strategy}_{idx:03d}"
        return chunks
