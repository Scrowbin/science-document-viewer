"""
Management command to rebuild and reindex document vectors under a selected chunking strategy.
Supports both 'section_overlap' (flat) and 'hierarchical' (small-to-big) chunking strategies.
"""
import logging
import os
from typing import Any

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from ...models import Document
from ...services.rag_service import RagService, reindex_document

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
            help=(
                "Deprecated and ignored: production ingestion always writes to 'doc_{doc_id}' "
                "(+ 'doc_{doc_id}_parents'), the collections chat/summarize read from."
            ),
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

        if custom_coll:
            self.stdout.write(
                self.style.WARNING(
                    f"--qdrant-collection={custom_coll} is ignored: documents are indexed into 'doc_{{id}}'."
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
            coll_name = f"doc_{doc.id}"

            try:
                # Single pass: reindex_document() runs the production ingestion (chunk_seq-ordered
                # chunks, paper id "doc_{id}", chunking_strategy payload) into 'doc_{id}' and its
                # companion '_parents' collection, and refreshes the in-memory DocumentRAG cache.
                # (A second index_chunks(recreate=True) pass used to overwrite that collection
                # without chunk_seq and with a different paper id; it has been removed.)
                rag = reindex_document(doc.id, file_path, strategy=strategy)
                indexed_count = len(rag.documents) if rag is not None else 0
                if indexed_count <= 0:
                    raise RuntimeError("re-indexing produced no chunks")

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
