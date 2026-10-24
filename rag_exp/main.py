from dataclasses import dataclass, field
from typing import Callable, List, Dict, Any
import argparse

from chunking import fixed_size_chunker, recursive_chunker, semantic_chunker
from eval import dataset_passthrough, evaluate_chunk_strategy, qasper_passthrough
from ranx import evaluate
from langchain_huggingface import HuggingFaceEmbeddings

# Registry mapping string names to actual chunker functions
CHUNKER_REGISTRY: Dict[str, Callable] = {
    "fixed": fixed_size_chunker,
    "recursive": recursive_chunker,
    "semantic": semantic_chunker,
}

# Registry mapping dataset names to dataset passthrough functions
DATASET_REGISTRY: Dict[str, Callable] = {
    "qasper": qasper_passthrough,
    "beir/fiqa/test": lambda: dataset_passthrough("beir/fiqa/test"),
    "cord19/trec-covid": lambda: dataset_passthrough("cord19/trec-covid"),
}


@dataclass
class Config:
    chunking_strategy: str = "fixed"
    embedding_model: str = "ibm-granite/granite-embedding-125m-english"
    dataset: str = "qasper"
    batch_size: int = 128
    metrics: List[str] = field(
        default_factory=lambda: ["precision@5", "recall@5", "f1@5", "ndcg@5"]
    )

    @classmethod
    def from_args(cls) -> "Config":
        parser = argparse.ArgumentParser(
            description="Evaluate chunking strategies on IR datasets."
        )
        parser.add_argument(
            "--chunker",
            type=str,
            default="fixed",
            choices=list(CHUNKER_REGISTRY.keys()),
            help="Chunking strategy to apply",
        )
        parser.add_argument(
            "--model",
            type=str,
            default="ibm-granite/granite-embedding-125m-english",
            help="HuggingFace embedding model name or path",
        )
        parser.add_argument(
            "--dataset",
            type=str,
            default="qasper",
            help="Dataset identifier (e.g., 'qasper', 'beir/fiqa/test')",
        )
        parser.add_argument(
            "--batch-size",
            type=int,
            default=128,
            help="Batch size for embedding encoding",
        )
        parser.add_argument(
            "--metrics",
            nargs="+",
            default=["precision@5", "recall@5", "f1@5", "ndcg@5"],
            help="Evaluation metrics list",
        )

        args = parser.parse_args()
        return cls(
            chunking_strategy=args.chunker,
            embedding_model=args.model,
            dataset=args.dataset,
            batch_size=args.batch_size,
            metrics=args.metrics,
        )


def main(cfg: Config) -> None:
    # 1. Initialize Embedding Model
    embed_model = HuggingFaceEmbeddings(
        model_name=cfg.embedding_model,
        encode_kwargs={"batch_size": cfg.batch_size},
    )

    # 2. Resolve Dataset Loader
    if cfg.dataset in DATASET_REGISTRY:
        docs, qrels, queries = DATASET_REGISTRY[cfg.dataset]()
    else:
        docs, qrels, queries = dataset_passthrough(cfg.dataset)

    # 3. Resolve Chunker Strategy
    chunker = CHUNKER_REGISTRY.get(cfg.chunking_strategy)
    if chunker is None:
        raise ValueError(
            f"Unsupported chunking strategy '{cfg.chunking_strategy}'. "
            f"Available: {list(CHUNKER_REGISTRY.keys())}"
        )

    # 4. Run Evaluation
    run = evaluate_chunk_strategy(chunker, docs, queries, embed_model)

    print(
        f"--- Strategy: {cfg.chunking_strategy} | Model: {cfg.embedding_model} | Dataset: {cfg.dataset} ---"
    )
    results = evaluate(qrels, run, cfg.metrics)
    print(results)


if __name__ == "__main__":
    config = Config.from_args()
    main(config)
