"""
Unit tests confirming embedding model task prefixes.
Validates MODEL_PREFIX_SPECS and prefix injection for symmetric and asymmetric encoders.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BACKEND_DIR))

from apps.documents.services.rag_service import MODEL_PREFIX_SPECS, get_model_prefix

EXPECTED_PREFIXES = {
    "sentence-transformers/all-MiniLM-L6-v2": {"query": "", "doc": ""},
    "all-MiniLM-L6-v2": {"query": "", "doc": ""},
    "intfloat/e5-small-v2": {"query": "query: ", "doc": "passage: "},
    "BAAI/bge-small-en-v1.5": {
        "query": "Represent this sentence for searching relevant passages: ",
        "doc": "",
    },
    "Snowflake/snowflake-arctic-embed-s": {
        "query": "Represent this sentence for searching relevant passages: ",
        "doc": "",
    },
    "nomic-ai/modernbert-embed-base": {
        "query": "search_query: ",
        "doc": "search_document: ",
    },
}


def test_model_prefix_registry():
    """Verify that MODEL_PREFIX_SPECS contains exact expected prefix mappings."""
    for model_name, expected in EXPECTED_PREFIXES.items():
        q_pfx = get_model_prefix(model_name, is_query=True)
        d_pfx = get_model_prefix(model_name, is_query=False)
        assert q_pfx == expected["query"], f"Query prefix mismatch for {model_name}: got '{q_pfx}'"
        assert d_pfx == expected["doc"], f"Doc prefix mismatch for {model_name}: got '{d_pfx}'"


def test_prefix_formatting():
    """Verify that input text receives correct prefix concatenation."""
    query = "What is the primary loss function?"
    passage = "We use cross-entropy loss with label smoothing."

    # E5-small asymmetric prefix test
    e5_q = get_model_prefix("intfloat/e5-small-v2", is_query=True) + query
    e5_d = get_model_prefix("intfloat/e5-small-v2", is_query=False) + passage
    assert e5_q.startswith("query: ")
    assert e5_d.startswith("passage: ")

    # ModernBERT prefix test
    mb_q = get_model_prefix("nomic-ai/modernbert-embed-base", is_query=True) + query
    mb_d = get_model_prefix("nomic-ai/modernbert-embed-base", is_query=False) + passage
    assert mb_q.startswith("search_query: ")
    assert mb_d.startswith("search_document: ")


if __name__ == "__main__":
    test_model_prefix_registry()
    test_prefix_formatting()
    print("ALL 2 PREFIX TESTS PASSED CLEANLY.")
