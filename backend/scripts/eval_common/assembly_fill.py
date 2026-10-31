"""
Fill-budget context assembly (registered: protocol assembly_fill_amendment.json (archived)).

Same as reval_pipeline.assemble (production assembly), except that a unit that does not fit the remaining
budget is skipped and assembly continues down the ranking instead of stopping. reval_pipeline.assemble is
left unchanged (frozen hash). Mirrors DocumentRAG.hybrid_search with RAG_CONTEXT_FILL=True.
"""

from typing import Any, Dict, List, Sequence

from eval_common.reval_pipeline import MAX_PARENT_TOKENS, PAD_WORDS


def assemble_fill(ranked: Sequence[int], units: List[Dict[str, Any]], strategy: str,
                  budget: int = 1600, max_units: int = 5) -> List[Dict[str, Any]]:
    """Returns [{'text', 'tokens', 'unit_id', 'idx'}]; idx is the matched unit index (for the gate score)."""
    from apps.documents.services.chunkers import estimate_tokens
    from apps.documents.services.rag_service import window_around_child
    out: List[Dict[str, Any]] = []
    used = 0
    seen = set()
    for idx in ranked:
        u = units[idx]
        if strategy == "hierarchical":
            pid = u.get("parent_id")
            if not pid or pid in seen:
                continue
            seen.add(pid)
            ptext = u.get("parent_text") or u["text"]
            ptok = u.get("parent_tokens") or estimate_tokens(ptext)
            if ptok > MAX_PARENT_TOKENS:
                text, _ = window_around_child(ptext, u.get("char_start", 0), u.get("char_end", len(ptext)),
                                              pad_words=PAD_WORDS)
                tok = estimate_tokens(text)
            else:
                text, tok = ptext, ptok
            uid = pid
        else:
            text = u["text"]
            tok = estimate_tokens(text)
            uid = u.get("chunk_id", str(idx))
        if used + tok > budget and out:
            continue  # the only difference from production assembly: skip, don't stop
        out.append({"text": text, "tokens": tok, "unit_id": uid, "idx": int(idx)})
        used += tok
        if len(out) >= max_units:
            break
    return out
