"""
Management command to rebuild and reindex document vectors under a selected chunking strategy.
Supports both 'section_overlap' (flat) and 'hierarchical' (small-to-big) chunking strategies.
"""
import logging
import os
from pathlib import Path
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.documents.models import Document
from apps.documents.services.chunkers import chunk_hierarchical
from apps.documents.services.chunking_utils import (
    chunk_document,
    chunk_sections,
    extract_sections_from_pdf,
)
from apps.documents.services.rag_service import RagService, reindex_document

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Reindex document vectors in Qdrant and local cache under a specified chunking strategy."

    def add_arguments(self, parser):
        parser.add_argument(
            "--strategy",
            type=str,
            default=getattr(settings, "CHUNKING_STRATEGY", "hierarchical"),
            choices=["hierarchical", "section_overlap", "section", "section_token"],
            help="Chunking strategy to apply ('hierarchical' or 'section_overlap').",
        )
        parser.add_argument(
            "--doc-id",
            type=int,
            default=None,
            help="Specific Document primary key to re-index.",
        )
        parser.add_argument(
            "--all",
            action="store_true",
            help="Re-index all active documents that have uploaded PDF files.",
        )
        parser.add_argument(
            "--qdrant-collection",
            type=str,
            default=None,
            help="Optional Qdrant collection name to index into (defaults to 'doc_{doc_id}').",
        )

    def handle(self, *args: Any, **options: Any) -> None:
        strategy = options["strategy"]
        doc_id = options["doc_id"]
        reindex_all = options["all"]
        custom_coll = options["qdrant_collection"]

        if not doc_id and not reindex_all:
            raise CommandError("Please provide either --doc-id <ID> or --all to specify documents to re-index.")

        if doc_id:
            qs = Document.objects.filter(id=doc_id)
            if not qs.exists():
                raise CommandError(f"Document with ID {doc_id} does not exist.")
        else:
            qs = Document.objects.filter(file__isnull=False).exclude(file="")

        docs = list(qs)
        self.stdout.write(
            self.style.NOTICE(
                f"Starting re-indexing for {len(docs)} document(s) with strategy: {strategy}..."
            )
        )

        rag_service = RagService.get_instance()
        success_count = 0
        total_chunks = 0
        total_parents = 0

        for doc in docs:
            if not doc.file or not os.path.exists(doc.file.path):
                self.stdout.write(self.style.WARNING(f"Skipping Doc {doc.id}: file missing at {doc.file}"))
                continue

            file_path = doc.file.path
            coll_name = custom_coll or f"doc_{doc.id}"

            try:
                # 1. Update in-memory DocumentRAG instance
                reindex_document(doc.id, file_path, strategy=strategy)

                # 2. Index into persistent Qdrant collection with strategy metadata
                sections = extract_sections_from_pdf(file_path)
                paper_id = doc.archive_id or doc.doi or f"doc_{doc.id}"

                if strategy == "hierarchical":
                    chunks_data = chunk_hierarchical(
                        sections, child_max_tokens=200, child_overlap=40, paper_id=paper_id
                    )
                else:
                    chunks_data = chunk_sections(
                        sections, strategy=strategy, max_tokens=400, overlap=80
                    )

                # Inject relational and ownership identifiers
                for c in chunks_data:
                    c["document_id"] = str(doc.id)
                    c["paper_arxiv_id"] = str(doc.archive_id or doc.doi or "")
                    c["paper_title"] = doc.title

                indexed_count = rag_service.index_chunks(
                    collection_name=coll_name,
                    chunks=chunks_data,
                    recreate=True,
                )

                parents_coll = f"{coll_name}_parents"
                p_count = (
                    rag_service.client.count(collection_name=parents_coll).count
                    if rag_service.client.collection_exists(parents_coll)
                    else 0
                )

                # Update database status
                doc.rag_status = "INDEXED"
                doc.save(update_fields=["rag_status"])

                success_count += 1
                total_chunks += indexed_count
                total_parents += p_count

                self.stdout.write(
                    self.style.SUCCESS(
                        f"  [OK] Doc {doc.id} ({doc.title[:40]}...): indexed {indexed_count} chunks "
                        f"({p_count} unique parents) in '{coll_name}'"
                    )
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"  [FAIL] Doc {doc.id} failed: {e}"))
                doc.rag_status = "FAILED"
                doc.save(update_fields=["rag_status"])

        self.stdout.write(
            self.style.SUCCESS(
                f"\nRe-indexing Complete! Successfully processed {success_count}/{len(docs)} documents. "
                f"Total chunks indexed: {total_chunks}, Total parent sections: {total_parents}."
            )
        )
