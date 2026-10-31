"""
Retrieval pipeline harness for the 2026-10 revalidation study (RQ1-RQ4, RQ6 retrieval stage).

Calls the production code wherever it exists, so evaluated behaviour equals application behaviour:
  sections   : apps.documents.services.chunking_utils.extract_sections_from_pdf   (pymupdf_layout)
  chunking   : chunk_hierarchical(200/40) | chunk_sections('section_overlap', 400/80) | chunk_fixed_size(400)
  prefixes   : rag_service.get_model_prefix
  expansion  : rag_service.window_around_child (+-200 words when parent > 800 tokens), 1,600 budget, <= 5 units
  rrf_prod   : identical to DocumentRAG.hybrid_search (top-50 each list, k=60, whitespace BM25Okapi)
Requires Django to be set up by the caller (setup_django()).
"""

import hashlib
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
EMB_CACHE = ROOT / "eval" / "data" / "revalidation_cache" / "emb"

RETRIEVE_K = 50
RRF_K = 60
MAX_PARENT_TOKENS = 800
PAD_WORDS = 200
CONVEX_ALPHA = 0.7


def setup_django():
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    for p in (str(BACKEND), str(BACKEND / "scripts")):
        if p not in sys.path:
            sys.path.insert(0, p)
    import django
    django.setup()


# ----------------------------------------------------------------------------- units
def build_units(sections: List[Dict[str, Any]], strategy: str, paper_id: str) -> List[Dict[str, Any]]:
    from apps.documents.services.chunkers import chunk_fixed_size, chunk_hierarchical
    from apps.documents.services.chunking_utils import chunk_sections
    if strategy == "hierarchical":
        return chunk_hierarchical(sections, child_max_tokens=200, child_overlap=40, paper_id=paper_id)
    if strategy == "section_overlap":
        return chunk_sections(sections, strategy="section_overlap", max_tokens=400, overlap=80)
    if strategy == "fixed_size":
        return chunk_fixed_size(sections, max_tokens=400, paper_id=paper_id)
    raise ValueError(strategy)


# ----------------------------------------------------------------------------- embeddings
_MODELS: Dict[str, Any] = {}


def get_model(name: str):
    if name not in _MODELS:
        from sentence_transformers import SentenceTransformer
        _MODELS[name] = SentenceTransformer(name, device="cpu")
    return _MODELS[name]


def embed(name: str, texts: Sequence[str], is_query: bool, batch_size: int = 32) -> np.ndarray:
    from apps.documents.services.rag_service import get_model_prefix
    prefix = get_model_prefix(name, is_query=is_query)
    inputs = [prefix + t if prefix and not t.startswith(prefix) else t for t in texts]
    return get_model(name).encode(inputs, batch_size=batch_size, normalize_embeddings=True,
                                  convert_to_numpy=True, show_progress_bar=False).astype(np.float32)


def cached_embed(name: str, texts: Sequence[str], is_query: bool, tag: str) -> np.ndarray:
    """Disk cache keyed by model, role and a hash of the exact input texts."""
    h = hashlib.sha256(("\x1f".join(texts)).encode("utf-8")).hexdigest()[:16]
    path = EMB_CACHE / name.replace("/", "__") / ("q" if is_query else "p") / f"{tag}_{h}.npy"
    if path.exists():
        return np.load(path)
    arr = embed(name, texts, is_query)
    path.parent.mkdir(parents=True, exist_ok=True)
    np.save(path, arr)
    return arr


# ----------------------------------------------------------------------------- ranking
_BM25_INDEX: Dict[Any, Any] = {}


def _tokenizer(name: str):
    if name == "whitespace":                 # production
        return lambda s: s.lower().split()
    if name == "regex":                      # candidate fix: regex tokens, 39 stopwords
        from eval_common.relevance import tokenize_regex
        return tokenize_regex
    raise ValueError(name)


def bm25_scores(texts: Sequence[str], query: str, tokenizer: str) -> np.ndarray:
    """BM25Okapi per document, index built once per (document, tokenizer) as in production."""
    from rank_bm25 import BM25Okapi
    tok = _tokenizer(tokenizer)
    key = (tokenizer, hashlib.sha256("\x1f".join(texts).encode("utf-8")).hexdigest())
    if key not in _BM25_INDEX:
        if len(_BM25_INDEX) > 64:
            _BM25_INDEX.clear()
        corpus = [tok(t) for t in texts]
        _BM25_INDEX[key] = BM25Okapi(corpus) if any(corpus) else None
    index = _BM25_INDEX[key]
    if index is None:
        return np.zeros(len(texts))
    return np.asarray(index.get_scores(tok(query)), dtype=float)


def rrf(dense: np.ndarray, sparse: np.ndarray) -> List[int]:
    """Exact mirror of DocumentRAG.hybrid_search fusion."""
    k = min(RETRIEVE_K, len(dense))
    d_top = list(np.argsort(dense)[::-1][:k])
    s_top = list(np.argsort(sparse)[::-1][:k])
    s: Dict[int, float] = {}
    for rank, i in enumerate(d_top):
        s[int(i)] = s.get(int(i), 0.0) + 1.0 / (RRF_K + rank + 1)
    for rank, i in enumerate(s_top):
        s[int(i)] = s.get(int(i), 0.0) + 1.0 / (RRF_K + rank + 1)
    return sorted(s, key=lambda i: s[i], reverse=True)


def convex(dense: np.ndarray, sparse: np.ndarray, alpha: float = CONVEX_ALPHA) -> List[int]:
    """Per-query min-max normalised convex combination over all candidates (identical to RQ4 convex_fuse)."""
    def mm(x):
        lo, hi = x.min(), x.max()
        return (x - lo) / max(hi - lo, 1e-6) if hi > lo else np.zeros_like(x)
    score = alpha * mm(np.asarray(dense, dtype=float)) + (1 - alpha) * mm(np.asarray(sparse, dtype=float))
    return [int(i) for i in np.argsort(score)[::-1]]


def rank(mode: str, dense: np.ndarray, texts: Sequence[str], query: str) -> List[int]:
    if mode == "dense":
        return [int(i) for i in np.argsort(dense)[::-1]]
    if mode in ("bm25_prod", "bm25_fix"):
        sp = bm25_scores(texts, query, "whitespace" if mode == "bm25_prod" else "regex")
        return [int(i) for i in np.argsort(sp)[::-1]]
    if mode in ("rrf_prod", "rrf_fix"):
        return rrf(dense, bm25_scores(texts, query, "whitespace" if mode == "rrf_prod" else "regex"))
    if mode in ("convex_prod", "convex_fix"):
        return convex(dense, bm25_scores(texts, query, "whitespace" if mode == "convex_prod" else "regex"))
    raise ValueError(mode)


# ----------------------------------------------------------------------------- context assembly
def assemble(ranked: Sequence[int], units: List[Dict[str, Any]], strategy: str,
             budget: int = 1600, max_units: int = 5) -> List[Dict[str, Any]]:
    """
    Builds the context exactly as production does. Hierarchical: deduplicate parents in rank order,
    window parents > 800 tokens around the matched child (+-200 words), stop before exceeding the budget.
    Flat: the same budget rule over chunks. Returns [{'text', 'tokens', 'unit_id'}].
    """
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
            break
        out.append({"text": text, "tokens": tok, "unit_id": uid})
        used += tok
        if len(out) >= max_units:
            break
    return out


def candidate_units_for_relevance(units: List[Dict[str, Any]], strategy: str) -> List[Dict[str, Any]]:
    """Units over which R_q is counted: unique full parents (hierarchical) or chunks (flat)."""
    if strategy != "hierarchical":
        return [{"text": u["text"]} for u in units]
    seen, out = set(), []
    for u in units:
        pid = u.get("parent_id")
        if pid and pid not in seen:
            seen.add(pid)
            out.append({"text": u.get("parent_text") or u["text"]})
    return out


def question_metrics(context: List[Dict[str, Any]], cand_units: List[Dict[str, Any]],
                     evidence: List[str], taus=(0.3, 0.5, 0.7)) -> Dict[str, Any]:
    """CEC at several tau; budgeted nDCG@10 (relevance tau=0.50, R_q floored at 1, as RQ4/E1)."""
    from eval_common.relevance import count_relevant_chunks, is_chunk_hit
    from eval_common.revalidation import context_evidence_coverage
    from eval_common.stats import compute_ndcg
    ctx_text = "\n\n".join(c["text"] for c in context)
    rel = [1 if is_chunk_hit({"text": c["text"]}, "", "", evidence, tau=0.50) else 0 for c in context]
    r_q_raw = count_relevant_chunks(cand_units, "", "", evidence, tau=0.50)
    m: Dict[str, Any] = {f"cec_{t}": context_evidence_coverage(ctx_text, evidence, tau=t) for t in taus}
    m.update({
        "ndcg10": compute_ndcg(rel + [0] * (10 - len(rel)), max(1, r_q_raw), k=10),
        "r_q": r_q_raw,
        "n_units": len(context),
        "context_tokens": sum(c["tokens"] for c in context),
    })
    return m
