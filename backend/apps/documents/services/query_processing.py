"""
Technical Acronym Expansion & Query Preprocessing Service (Step 5 / RAG-5).
Provides domain-specific academic abbreviation expansion, query normalization,
and conversational fluff removal for academic information retrieval.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

# Canonical academic STEM / Computer Science / NLP / ML acronym dictionary
ACADEMIC_ACRONYMS: Dict[str, str] = {
    # Architectures & Models
    "LLM": "Large Language Model",
    "LLMs": "Large Language Models",
    "RAG": "Retrieval-Augmented Generation",
    "LoRA": "Low-Rank Adaptation",
    "QLoRA": "Quantized Low-Rank Adaptation",
    "BERT": "Bidirectional Encoder Representations from Transformers",
    "RoBERTa": "Robustly Optimized BERT Approach",
    "CNN": "Convolutional Neural Network",
    "CNNs": "Convolutional Neural Networks",
    "RNN": "Recurrent Neural Network",
    "RNNs": "Recurrent Neural Networks",
    "LSTM": "Long Short-Term Memory",
    "GRU": "Gated Recurrent Unit",
    "GNN": "Graph Neural Network",
    "GNNs": "Graph Neural Networks",
    "GCN": "Graph Convolutional Network",
    "ViT": "Vision Transformer",
    "MLP": "Multilayer Perceptron",
    "GAN": "Generative Adversarial Network",
    "GANs": "Generative Adversarial Networks",
    "VAE": "Variational Autoencoder",
    "VAEs": "Variational Autoencoders",
    "MoE": "Mixture of Experts",
    "SSM": "State Space Model",
    "SSMs": "State Space Models",

    # NLP & Speech Tasks
    "NER": "Named Entity Recognition",
    "NLP": "Natural Language Processing",
    "NLI": "Natural Language Inference",
    "POS": "Part of Speech",
    "QA": "Question Answering",
    "IR": "Information Retrieval",
    "OCR": "Optical Character Recognition",
    "ASR": "Automatic Speech Recognition",
    "MT": "Machine Translation",
    "KG": "Knowledge Graph",
    "KGs": "Knowledge Graphs",
    "SOTA": "State of the Art",

    # Training, Alignment & Optimization
    "RL": "Reinforcement Learning",
    "RLHF": "Reinforcement Learning from Human Feedback",
    "RLAIF": "Reinforcement Learning from AI Feedback",
    "DPO": "Direct Preference Optimization",
    "PEFT": "Parameter-Efficient Fine-Tuning",
    "SGD": "Stochastic Gradient Descent",
    "SVD": "Singular Value Decomposition",
    "PCA": "Principal Component Analysis",
    "CV": "Computer Vision",
    "KD": "Knowledge Distillation",

    # Indexing & Vector Search
    "ANN": "Approximate Nearest Neighbor",
    "HNSW": "Hierarchical Navigable Small World",
    "LSH": "Locality-Sensitive Hashing",
    "IVF": "Inverted File Index",
    "PQ": "Product Quantization",
    "SQ": "Scalar Quantization",
    "RRF": "Reciprocal Rank Fusion",
    "BM25": "Best Matching 25",
    "TF-IDF": "Term Frequency-Inverse Document Frequency",

    # Evaluation Metrics
    "NDCG": "Normalized Discounted Cumulative Gain",
    "MRR": "Mean Reciprocal Rank",
    "MAP": "Mean Average Precision",
    "BLEU": "Bilingual Evaluation Understudy",
    "ROUGE": "Recall-Oriented Understudy for Gisting Evaluation",
    "CER": "Character Error Rate",
    "WER": "Word Error Rate",
    "MMLU": "Massive Multitask Language Understanding",
    "GSM8K": "Grade School Math 8K",

    # Hardware & Precision
    "GPU": "Graphics Processing Unit",
    "GPUs": "Graphics Processing Units",
    "TPU": "Tensor Processing Unit",
    "TPUs": "Tensor Processing Units",
    "CPU": "Central Processing Unit",
    "CPUs": "Central Processing Units",
    "FP32": "Single-Precision Floating Point",
    "FP16": "Half-Precision Floating Point",
    "BF16": "Brain Floating Point",
    "INT8": "8-Bit Integer Quantization",
    "INT4": "4-Bit Integer Quantization",
}

# Conversational prefixes and filler phrases common in user queries
CONVERSATIONAL_FILLERS: List[re.Pattern[str]] = [
    re.compile(r"^(?:can\s+you\s+(?:please\s+)?tell\s+me|tell\s+me|please\s+tell\s+me)\s+", re.IGNORECASE),
    re.compile(r"^(?:what\s+(?:is|are|was|were)|how\s+(?:does|do|can|is)|why\s+(?:does|do|is|did))\s+", re.IGNORECASE),
    re.compile(r"^(?:in\s+this\s+paper|according\s+to\s+the\s+authors?|the\s+paper\s+states)\s*,?\s*", re.IGNORECASE),
    re.compile(r"\?+$"),
]


class QueryPreprocessor:
    """
    Handles academic query normalization, acronym expansion, and conversational fluff stripping.
    """

    def __init__(
        self,
        acronym_dict: Optional[Dict[str, str]] = None,
        min_acronym_len: int = 2,
    ):
        self.acronyms = acronym_dict or ACADEMIC_ACRONYMS
        self.min_acronym_len = min_acronym_len

        # Precompile exact-word-boundary regexes for fast lookup
        # Case-sensitive for acronyms to prevent expanding ordinary words (e.g., 'it', 'me', 'be')
        escaped_keys = sorted(self.acronyms.keys(), key=lambda k: -len(k))
        pattern = r"\b(" + "|".join(re.escape(k) for k in escaped_keys) + r")\b"
        self._acronym_regex = re.compile(pattern)

    def extract_acronyms(self, query: str) -> List[Tuple[str, str]]:
        """Finds all known technical acronyms present in the query."""
        found: List[Tuple[str, str]] = []
        for match in self._acronym_regex.finditer(query):
            token = match.group(0)
            if token in self.acronyms:
                found.append((token, self.acronyms[token]))
        return found

    def expand_inline(self, query: str) -> str:
        """
        Expands acronyms inline: 'How does LoRA work?' -> 'How does LoRA (Low-Rank Adaptation) work?'
        """
        def _replace(match: re.Match[str]) -> str:
            token = match.group(0)
            expansion = self.acronyms.get(token)
            if expansion and token not in query[max(0, match.start() - 20) : match.start()]:
                return f"{token} ({expansion})"
            return token

        return self._acronym_regex.sub(_replace, query)

    def expand_append(self, query: str) -> str:
        """
        Appends expanded acronym meanings to the end of the query without altering query syntax:
        'How does LoRA work?' -> 'How does LoRA work? Low-Rank Adaptation'
        """
        acronyms = self.extract_acronyms(query)
        if not acronyms:
            return query

        seen: Set[str] = set()
        expansions: List[str] = []
        for _, exp in acronyms:
            if exp.lower() not in query.lower() and exp not in seen:
                seen.add(exp)
                expansions.append(exp)

        if expansions:
            return f"{query.strip()} {' '.join(expansions)}"
        return query

    def strip_conversational_fillers(self, query: str) -> str:
        """
        Strips conversational query prefixes while preserving key semantic keywords.
        """
        cleaned = query.strip()
        for pat in CONVERSATIONAL_FILLERS:
            cleaned = pat.sub("", cleaned).strip()
        return cleaned

    def preprocess(
        self,
        query: str,
        mode: str = "expand_append",
        strip_fillers: bool = False,
    ) -> str:
        """
        Main query transformation entry point.
        Modes:
          - 'raw': original query
          - 'expand_inline': inline substitution
          - 'expand_append': append at end
          - 'strip_only': only removes conversational fluff
        """
        text = query.strip()
        if strip_fillers:
            text = self.strip_conversational_fillers(text)

        if mode == "raw":
            return text
        elif mode == "expand_inline":
            return self.expand_inline(text)
        elif mode == "expand_append":
            return self.expand_append(text)
        elif mode == "strip_only":
            return text
        else:
            raise ValueError(f"Unknown query preprocessing mode: {mode}")


# Singleton default preprocessor
_default_preprocessor: Optional[QueryPreprocessor] = None


def get_query_preprocessor() -> QueryPreprocessor:
    global _default_preprocessor
    if _default_preprocessor is None:
        _default_preprocessor = QueryPreprocessor()
    return _default_preprocessor


def preprocess_query(
    query: str,
    mode: str = "expand_append",
    strip_fillers: bool = False,
) -> str:
    """Convenience functional interface for query preprocessing."""
    return get_query_preprocessor().preprocess(query, mode=mode, strip_fillers=strip_fillers)
