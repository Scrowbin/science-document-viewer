"""
Unit tests for RQ2 chunking implementations in apps.documents.services.chunkers.
Tests fixed_size, fixed_size_overlap, semantic, and backwards compatibility.
"""

import sys
from pathlib import Path
import numpy as np

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(WORKSPACE_ROOT))

from apps.documents.services.chunkers import (
    chunk_fixed_size,
    chunk_fixed_size_overlap,
    chunk_semantic,
    chunk_document_unified,
    estimate_tokens,
    split_sentences,
)


class MockEmbedder:
    """Mock embedder returning deterministic vectors for fast unit testing."""
    def encode(self, texts, **kwargs):
        # Return 8-dim vectors where similar texts have high dot product
        vecs = []
        for t in texts:
            val = float(len(t) % 10) / 10.0
            vec = np.array([val] * 8, dtype=np.float32)
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec /= norm
            vecs.append(vec)
        return vecs


def test_estimate_tokens():
    text = "This is a simple sentence with eight words."
    toks = estimate_tokens(text)
    assert 9 <= toks <= 13


def test_split_sentences():
    text = "First sentence here. Second sentence follows! Third one? Yes, indeed."
    sents = split_sentences(text)
    assert len(sents) == 4
    assert sents[0] == "First sentence here."


def test_chunk_fixed_size():
    words = [f"word{i}" for i in range(120)]
    text = " ".join(words)
    # max_tokens=60 -> max_words approx 45
    chunks = chunk_fixed_size(text, max_tokens=60, paper_id="test_doc")
    assert len(chunks) >= 2
    assert chunks[0]["strategy"] == "fixed_size"
    assert chunks[0]["paper_arxiv_id"] == "test_doc"
    # verify chunks cover all words
    reconstructed_words = []
    for c in chunks:
        reconstructed_words.extend(c["text"].split())
    assert reconstructed_words == words


def test_chunk_fixed_size_overlap():
    words = [f"word{i}" for i in range(100)]
    text = " ".join(words)
    chunks = chunk_fixed_size_overlap(text, max_tokens=60, overlap=20, paper_id="test_doc")
    assert len(chunks) >= 3
    assert chunks[0]["strategy"] == "fixed_size_overlap"
    # Check that chunk 1 and chunk 2 share overlap words
    w1 = chunks[0]["text"].split()
    w2 = chunks[1]["text"].split()
    overlap = set(w1) & set(w2)
    assert len(overlap) > 0


def test_chunk_semantic():
    embedder = MockEmbedder()
    sentences = [
        "Natural language processing is a subfield of computer science.",
        "It focuses on the interactions between computers and human language.",
        "Deep residual networks have revolutionised image classification.",
        "They utilize skip connections to mitigate vanishing gradients.",
    ]
    text = " ".join(sentences)
    chunks = chunk_semantic(text, embedder=embedder, max_tokens=100, percentile_threshold=50.0, paper_id="test_p")
    assert len(chunks) >= 1
    assert chunks[0]["strategy"] == "semantic"


def test_chunk_document_unified():
    sections = [
        {"title": "Introduction", "text": "This is the introduction section.", "page_start": 1, "page_end": 1},
        {"title": "Methods", "text": "This describes the experimental methods.", "page_start": 2, "page_end": 2},
    ]
    # 1. Section
    c_sec = chunk_document_unified(sections, strategy="section")
    assert len(c_sec) == 2
    # 2. Fixed Size
    c_fixed = chunk_document_unified(sections, strategy="fixed_size", max_tokens=40)
    assert len(c_fixed) >= 1
    assert c_fixed[0]["strategy"] == "fixed_size"
    # 3. Hierarchical
    c_hier = chunk_document_unified(sections, strategy="hierarchical")
    assert len(c_hier) >= 2
    assert "parent_id" in c_hier[0]


def test_chunk_hierarchical():
    long_section_text = " ".join([f"word{i}" for i in range(250)])
    sections = [
        {"heading": "Abstract", "text": "Short abstract text.", "start_page": 1},
        {"heading": "Architecture", "text": long_section_text, "start_page": 2},
    ]
    chunks = chunk_document_unified(sections, strategy="hierarchical", paper_id="test_hier")
    assert len(chunks) >= 3
    for c in chunks:
        assert "parent_id" in c
        assert "parent_text" in c
        assert "parent_tokens" in c
        assert c["paper_arxiv_id"] == "test_hier"
        assert c["strategy"] == "hierarchical"


if __name__ == "__main__":
    test_estimate_tokens()
    test_split_sentences()
    test_chunk_fixed_size()
    test_chunk_fixed_size_overlap()
    test_chunk_semantic()
    test_chunk_document_unified()
    test_chunk_hierarchical()
    print("ALL 7 CHUNKER UNIT TESTS PASSED CLEANLY.")
