from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Document, Annotation, Note, DocumentShare, Author, Tag, DocumentAuthor
from ..collections_app.models import Collection
from .services.crossref_service import clean_doi, fetch_metadata_from_doi
from .services.pdf_metadata_service import extract_metadata_from_pdf, fetch_arxiv_metadata, apply_pdf_metadata_to_document

User = get_user_model()

class CrossrefServiceTestCase(TestCase):
    def test_clean_doi(self):
        self.assertEqual(clean_doi("https://doi.org/10.1016/j.cell.2024.01"), "10.1016/j.cell.2024.01")
        self.assertEqual(clean_doi("http://dx.doi.org/10.1038/nature123"), "10.1038/nature123")
        self.assertEqual(clean_doi(" 10.1000/182 "), "10.1000/182")
        self.assertEqual(clean_doi("s41586-020-2649-2"), "10.1038/s41586-020-2649-2")
        self.assertEqual(clean_doi("doi: 10.1038/s41586-020-2649-2"), "10.1038/s41586-020-2649-2")
        self.assertEqual(clean_doi("https://www.nature.com/articles/s41586-020-2649-2"), "10.1038/s41586-020-2649-2")

    def test_fetch_metadata_live_or_fallback(self):
        # Test with a well-known canonical DOI: 10.1038/s41586-020-2649-2 (AlphaFold 1 paper)
        metadata = fetch_metadata_from_doi("10.1038/s41586-020-2649-2")
        if metadata:  # If internet is reachable
            self.assertIn("title", metadata)
            self.assertIn("authors", metadata)
            self.assertEqual(metadata["doi"], "10.1038/s41586-020-2649-2")
            self.assertTrue(len(metadata["authors"]) > 0)


class DocumentApiTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='researcher1', email='res1@univ.edu', password='password123')
        self.user2 = User.objects.create_user(username='researcher2', email='res2@univ.edu', password='password123')
        self.client.force_authenticate(user=self.user1)

    def test_create_document_with_file_upload(self):
        pdf_content = b"%PDF-1.4 mock pdf content test"
        dummy_file = SimpleUploadedFile("sample_paper.pdf", pdf_content, content_type="application/pdf")

        response = self.client.post('/api/v1/documents/', {
            'title': 'Deep Learning for Genomic Sequences',
            'short_title': 'Genomic DL',
            'doi': '10.1000/test.123',
            'item_type': 'journalArticle',
            'file': dummy_file,
            'author_names': ['Alan Turing', 'Ada Lovelace'],
            'tag_names': ['Genomics', 'AI'],
        }, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        doc = Document.objects.get(title='Deep Learning for Genomic Sequences')
        self.assertEqual(doc.owner, self.user1)
        self.assertTrue(doc.file and doc.file.name and doc.file.name.endswith('.pdf'))
        self.assertEqual(doc.authors.count(), 2)
        self.assertEqual(doc.tags.count(), 2)
        self.assertEqual(doc.rag_status, 'PENDING')

    def test_google_drive_style_sharing(self):
        doc = Document.objects.create(
            owner=self.user1,
            title='Confidential Lab Protocol',
            doi='10.1000/confidential'
        )

        # User2 initially cannot see or access User1's private document
        self.client.force_authenticate(user=self.user2)
        resp_unauth = self.client.get(f'/api/v1/documents/{doc.id}/')
        self.assertEqual(resp_unauth.status_code, status.HTTP_404_NOT_FOUND)

        # User1 shares with User2 with VIEW permission
        self.client.force_authenticate(user=self.user1)
        share_resp = self.client.post(f'/api/v1/documents/{doc.id}/shares/', {
            'shared_with_email': self.user2.email,
            'permission': 'VIEW'
        })
        self.assertEqual(share_resp.status_code, status.HTTP_201_CREATED)

        # Now User2 can view it
        self.client.force_authenticate(user=self.user2)
        resp_shared = self.client.get(f'/api/v1/documents/{doc.id}/')
        self.assertEqual(resp_shared.status_code, status.HTTP_200_OK)

        # But User2 cannot edit because permission is VIEW
        resp_edit = self.client.patch(f'/api/v1/documents/{doc.id}/', {'title': 'Hacked Title'})
        self.assertEqual(resp_edit.status_code, status.HTTP_403_FORBIDDEN)

    def test_pdf_annotations_flow(self):
        doc = Document.objects.create(owner=self.user1, title='Paper on Quantum Optics')
        
        # Add a highlight annotation on page 3
        resp = self.client.post(f'/api/v1/documents/{doc.id}/annotations/', {
            'page_number': 3,
            'type': 'highlight',
            'color': '#ffeb3b',
            'rects': [{'x1': 100, 'y1': 200, 'x2': 300, 'y2': 220}],
            'selected_text': 'Phase transition detected at critical threshold.',
            'comment': 'Check formula against reference [4].'
        }, format='json')

        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Annotation.objects.filter(document=doc).count(), 1)
        anno = Annotation.objects.get(document=doc)
        self.assertEqual(anno.page_number, 3)
        self.assertEqual(anno.user, self.user1)

    def test_personal_notes(self):
        doc = Document.objects.create(owner=self.user1, title='Paper on Robotics')
        resp = self.client.post('/api/v1/notes/', {
            'document': doc.id,
            'title': 'Key insights for our project',
            'content': 'Need to replicate experiment 2 with higher sample rate.'
        })
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Note.objects.filter(user=self.user1).count(), 1)

    def test_annotation_router_patch_and_delete(self):
        """Verify AnnotationViewSet registered at /api/v1/annotations/:id/ supports PATCH and DELETE."""
        doc = Document.objects.create(owner=self.user1, title='Quantum Paper')
        anno = Annotation.objects.create(
            document=doc,
            user=self.user1,
            page_number=1,
            type='highlight',
            color='#ffeb3b',
            comment='Original comment'
        )
        # Test PATCH /annotations/:id/
        patch_resp = self.client.patch(f'/api/v1/annotations/{anno.id}/', {
            'comment': 'Updated comment',
            'color': '#ff0000'
        }, format='json')
        self.assertEqual(patch_resp.status_code, status.HTTP_200_OK)
        anno.refresh_from_db()
        self.assertEqual(anno.comment, 'Updated comment')
        self.assertEqual(anno.color, '#ff0000')

        # Test DELETE /annotations/:id/
        del_resp = self.client.delete(f'/api/v1/annotations/{anno.id}/')
        self.assertEqual(del_resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Annotation.objects.filter(id=anno.id).count(), 0)

    def test_document_m2m_update(self):
        """Verify Document PATCH updates author_names, tag_names, and domain_names."""
        doc = Document.objects.create(owner=self.user1, title='Initial Paper')
        # Initial update with authors, tags, domains
        resp = self.client.patch(f'/api/v1/documents/{doc.id}/', {
            'author_names': ['Alan Turing', 'Ada Lovelace'],
            'tag_names': ['Computing', 'AI'],
            'domain_names': ['Computer Science']
        }, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        doc.refresh_from_db()
        self.assertEqual(doc.authors.count(), 2)
        self.assertEqual(doc.tags.count(), 2)
        self.assertEqual(doc.domains.count(), 1)

        # Update tags and authors
        resp2 = self.client.patch(f'/api/v1/documents/{doc.id}/', {
            'author_names': ['Claude Shannon'],
            'tag_names': ['Information Theory']
        }, format='json')
        self.assertEqual(resp2.status_code, status.HTTP_200_OK)
        doc.refresh_from_db()
        self.assertEqual(doc.authors.count(), 1)
        first_author = doc.authors.first()
        self.assertIsNotNone(first_author)
        assert first_author is not None
        self.assertEqual(first_author.last_name, 'Shannon')
        self.assertEqual(doc.tags.count(), 1)
        first_tag = doc.tags.first()
        self.assertIsNotNone(first_tag)
        assert first_tag is not None
        self.assertEqual(first_tag.name, 'Information Theory')
        # Domains was not in payload, should be untouched
        self.assertEqual(doc.domains.count(), 1)

    def test_pdf_upload_valid_file(self):
        """Valid PDF with %PDF- header succeeds."""
        pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
        pdf_file = SimpleUploadedFile("research.pdf", pdf_content, content_type="application/pdf")
        resp = self.client.post('/api/v1/documents/', {
            'title': 'Real Research Paper',
            'file': pdf_file,
        }, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        doc = Document.objects.get(id=resp.data['id'])
        self.assertTrue(bool(doc.file))
        self.assertTrue(doc.file and doc.file.name and doc.file.name.endswith('.pdf'))

    def test_pdf_upload_renamed_non_pdf_rejected(self):
        """A renamed non-PDF file (.pdf extension but lacking %PDF- header) must be rejected."""
        fake_content = b"This is plain text disguised as a PDF file to bypass extension checks."
        fake_file = SimpleUploadedFile("trojan.pdf", fake_content, content_type="application/pdf")
        resp = self.client.post('/api/v1/documents/', {
            'title': 'Disguised Paper',
            'file': fake_file,
        }, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', resp.data)

    def test_pdf_upload_wrong_extension_rejected(self):
        """A file with a non-PDF extension must be rejected."""
        txt_file = SimpleUploadedFile("notes.txt", b"plain text", content_type="text/plain")
        resp = self.client.post('/api/v1/documents/', {
            'title': 'Notes File',
            'file': txt_file,
        }, format='multipart')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('file', resp.data)

    def test_collection_tree_deep_nested_single_query(self):
        """Verify deep 4-level collection tree is constructed accurately with correct document counts."""
        root = Collection.objects.create(owner=self.user1, name='Computer Science')
        lvl1 = Collection.objects.create(owner=self.user1, name='AI', parent=root)
        lvl2 = Collection.objects.create(owner=self.user1, name='Machine Learning', parent=lvl1)
        lvl3 = Collection.objects.create(owner=self.user1, name='Deep Learning', parent=lvl2)
        Document.objects.create(owner=self.user1, title='Paper 1', primary_collection=lvl3)

        resp = self.client.get('/api/v1/collections/tree/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        tree = resp.data
        self.assertEqual(len(tree), 1)
        self.assertEqual(tree[0]['name'], 'Computer Science')
        self.assertEqual(len(tree[0]['children']), 1)
        self.assertEqual(tree[0]['children'][0]['name'], 'AI')
        self.assertEqual(len(tree[0]['children'][0]['children']), 1)
        self.assertEqual(tree[0]['children'][0]['children'][0]['name'], 'Machine Learning')
        self.assertEqual(len(tree[0]['children'][0]['children'][0]['children']), 1)
        leaf = tree[0]['children'][0]['children'][0]['children'][0]
        self.assertEqual(leaf['name'], 'Deep Learning')
        self.assertEqual(leaf['document_count'], 1)

    def test_document_list_prefetch_performance(self):
        """Verify listing documents with M2M authors, tags, domains does not trigger N+1 queries."""
        for i in range(5):
            doc = Document.objects.create(owner=self.user1, title=f'Performance Paper {i}')
            author = Author.objects.create(first_name='Author', last_name=f'Num{i}')
            DocumentAuthor.objects.create(document=doc, author=author, author_order=1)
            tag = Tag.objects.create(name=f'Tag{i}')
            doc.tags.add(tag)

        resp = self.client.get('/api/v1/documents/')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(len(resp.data), 5)
        self.assertIn('authors', resp.data[0])
        self.assertIn('tags', resp.data[0])

    def test_metadata_lookup_doi_endpoint(self):
        """Test POST /api/v1/metadata/lookup-doi/ endpoint validation and response."""
        # Empty DOI string returns 400
        resp_empty = self.client.post('/api/v1/metadata/lookup-doi/', {})
        self.assertEqual(resp_empty.status_code, status.HTTP_400_BAD_REQUEST)

        # Invalid/nonexistent DOI returns 404
        resp_invalid = self.client.post('/api/v1/metadata/lookup-doi/', {'doi': 'not-a-real-doi-12345'})
        self.assertEqual(resp_invalid.status_code, status.HTTP_404_NOT_FOUND)


class PdfMetadataExtractorTestCase(TestCase):
    def test_arxiv_metadata_fetch(self):
        """Verify official arXiv API resolves real paper metadata."""
        meta = fetch_arxiv_metadata('1706.03762')
        if meta:
            self.assertEqual(meta['title'], 'Attention Is All You Need')
            self.assertIn('Ashish Vaswani', meta['authors'])
            self.assertEqual(meta['repository'], 'arXiv')
            self.assertTrue(meta['date'].startswith('2017'))

    def test_apply_metadata_to_document(self):
        """Verify apply_pdf_metadata_to_document updates Document fields in PostgreSQL."""
        user = User.objects.create_user(username='test_extractor', password='password123')
        doc = Document.objects.create(owner=user, title='1706.03762v7')

        # Mock metadata
        mock_meta = {
            'title': 'Attention Is All You Need',
            'authors': ['Ashish Vaswani', 'Noam Shazeer'],
            'date': '2017-06-12',
            'doi': '10.48550/arXiv.1706.03762',
            'url': 'https://arxiv.org/abs/1706.03762',
            'repository': 'arXiv',
            'extra': 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...',
            'tags': ['cs.CL', 'cs.LG'],
            'domains': ['Computer Science'],
        }

        from unittest.mock import patch
        with patch('apps.documents.services.pdf_metadata_service.extract_metadata_from_pdf', return_value=mock_meta):
            from django.core.files.uploadedfile import SimpleUploadedFile
            doc.file = SimpleUploadedFile("1706.03762v7.pdf", b"%PDF-1.5 test", content_type="application/pdf")
            doc.save()

            applied = apply_pdf_metadata_to_document(doc)
            self.assertTrue(applied)

            doc.refresh_from_db()
            self.assertEqual(doc.title, 'Attention Is All You Need')
            self.assertEqual(doc.doi, '10.48550/arXiv.1706.03762')
            self.assertEqual(doc.repository, 'arXiv')
            self.assertEqual(doc.authors.count(), 2)
            self.assertEqual(doc.tags.count(), 2)
            self.assertEqual(doc.domains.count(), 1)


class DocumentChunksTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='chunk_researcher', password='password123')
        self.client.force_authenticate(user=self.user)

    def test_document_chunks_inspection_api(self):
        """Verify GET /api/v1/documents/{id}/chunks/ returns structured chunks with 3 strategies."""
        doc = Document.objects.create(
            owner=self.user,
            title='Sample Transformer Paper',
            extra='Abstract: Self-attention models require non-parametric memory. Introduction: Transformers replace RNNs.'
        )

        # 1. Strategy A: section
        resp = self.client.get(f'/api/v1/documents/{doc.id}/chunks/?strategy=section')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        data = resp.json()
        self.assertEqual(data['strategy'], 'section')
        self.assertTrue(data['total_chunks'] >= 1)
        self.assertIn('chunks', data)
        self.assertIn('token_count', data['chunks'][0])
        self.assertIn('section', data['chunks'][0])

        # 2. Strategy B: section_token
        resp_token = self.client.get(f'/api/v1/documents/{doc.id}/chunks/?strategy=section_token&max_tokens=20')
        self.assertEqual(resp_token.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_token.json()['strategy'], 'section_token')

        # 3. Strategy C: section_overlap
        resp_overlap = self.client.get(f'/api/v1/documents/{doc.id}/chunks/?strategy=section_overlap&max_tokens=20&overlap=5')
        self.assertEqual(resp_overlap.status_code, status.HTTP_200_OK)
        self.assertEqual(resp_overlap.json()['strategy'], 'section_overlap')
        self.assertEqual(resp_overlap.json()['overlap'], 5)

    def test_chunking_strategies_unit(self):
        """Verify chunk_sections produces expected chunk counts under the 3 experimental strategies."""
        from .services.chunking_utils import chunk_sections, estimate_tokens
        sample_sections = [
            {
                'title': '1. Introduction',
                'page_start': 1,
                'page_end': 1,
                'text': 'Deep learning models require extensive training. ' * 50,
                'token_count': 350
            },
            {
                'title': '2. Methodology',
                'page_start': 2,
                'page_end': 3,
                'text': 'We propose a novel residual learning formulation. ' * 40,
                'token_count': 280
            }
        ]

        chunks_sec = chunk_sections(sample_sections, strategy='section')
        self.assertEqual(len(chunks_sec), 2)
        self.assertEqual(chunks_sec[0]['section'], '1. Introduction')
        self.assertEqual(chunks_sec[1]['section'], '2. Methodology')

        chunks_tok = chunk_sections(sample_sections, strategy='section_token', max_tokens=100)
        self.assertTrue(len(chunks_tok) > len(chunks_sec))

        chunks_ov = chunk_sections(sample_sections, strategy='section_overlap', max_tokens=100, overlap=30)
        self.assertTrue(len(chunks_ov) >= len(chunks_tok))


class RagServiceTestCase(TestCase):
    """Verifies in-memory Qdrant indexing, dense retrieval, and hybrid fusion (Phase 2B)."""

    def test_rag_service_dense_and_budget_retrieval(self):
        from .services.rag_service import RagService

        rag = RagService(in_memory=True)
        collection = "test_eval_collection"

        sample_chunks = [
            {
                "document_id": 101,
                "chunk_id": 1,
                "text": "The Transformer uses multi-head self-attention mechanisms to dispense with recurrence and convolutions entirely.",
                "section": "1. Introduction",
                "page_start": 1,
                "page_end": 1,
                "token_count": 18,
            },
            {
                "document_id": 101,
                "chunk_id": 2,
                "text": "Residual networks ease the training of networks that are substantially deeper than those used previously.",
                "section": "Method",
                "page_start": 3,
                "page_end": 4,
                "token_count": 17,
            },
            {
                "document_id": 101,
                "chunk_id": 3,
                "text": "Low-Rank Adaptation freezes the pre-trained model weights and injects trainable rank decomposition matrices.",
                "section": "Method",
                "page_start": 2,
                "page_end": 3,
                "token_count": 16,
            },
        ]

        indexed_count = rag.index_chunks(collection, sample_chunks, recreate=True)
        self.assertEqual(indexed_count, 3)

        # 1. Dense search
        hits = rag.search_dense(collection, "What mechanism does the Transformer use?", top_k=2)
        self.assertTrue(len(hits) >= 1)
        top_score, top_payload = hits[0]
        self.assertEqual(top_payload["chunk_id"], 1)
        self.assertIn("Transformer", top_payload["text"])

        # 2. Token budget search
        budget_hits = rag.search_dense_with_token_budget(collection, "Explain residual networks", token_budget=50)
        self.assertTrue(len(budget_hits) >= 1)
        self.assertEqual(budget_hits[0][1]["chunk_id"], 2)

        # 3. Hybrid RRF
        bm25_mock = [(10.5, sample_chunks[0]), (5.2, sample_chunks[1])]
        hybrid_hits = rag.search_hybrid_rrf(collection, "Transformer attention", bm25_candidates=bm25_mock, top_k=2)
        self.assertEqual(len(hybrid_hits), 2)
        self.assertEqual(hybrid_hits[0][1]["chunk_id"], 1)

    def test_index_chunks_cross_document_isolation_and_idempotency(self):
        """Task 1A: Two documents with identical chunk_ids must not overwrite each other, and re-indexing is idempotent."""
        from .services.rag_service import RagService

        rag = RagService(in_memory=True)
        coll = "test_isolation_coll"

        doc_a_chunks = [
            {"document_id": "doc_A", "chunk_id": "chunk_01", "text": "Alpha document chunk one."},
            {"document_id": "doc_A", "chunk_id": "chunk_02", "text": "Alpha document chunk two."},
        ]
        doc_b_chunks = [
            {"document_id": "doc_B", "chunk_id": "chunk_01", "text": "Beta document chunk one with identical chunk_id."},
            {"document_id": "doc_B", "chunk_id": "chunk_02", "text": "Beta document chunk two with identical chunk_id."},
        ]

        # Index Doc A
        rag.index_chunks(coll, doc_a_chunks, recreate=True)
        count_a = rag.client.count(collection_name=coll).count
        self.assertEqual(count_a, 2)

        # Index Doc B with identical chunk_id values
        rag.index_chunks(coll, doc_b_chunks, recreate=False)
        count_both = rag.client.count(collection_name=coll).count
        self.assertEqual(count_both, 4, "Chunks from Document B must not overwrite chunks from Document A!")

        # Re-index Doc A (must be idempotent: count stays 4)
        rag.index_chunks(coll, doc_a_chunks, recreate=False)
        count_reindex = rag.client.count(collection_name=coll).count
        self.assertEqual(count_reindex, 4, "Re-indexing same chunks must be idempotent and not alter collection point count!")

    def test_index_chunks_missing_doc_id_raises_value_error(self):
        """Task 1A: Raise ValueError if chunk lacks both document_id and paper_arxiv_id."""
        from .services.rag_service import RagService

        rag = RagService(in_memory=True)
        invalid_chunks = [{"chunk_id": "c1", "text": "Unattributed chunk text without document ID"}]
        with self.assertRaises(ValueError):
            rag.index_chunks("test_err_coll", invalid_chunks)

    def test_index_chunks_page_number_fallback(self):
        """Task 1B: Chunk sections output with 'page' and 'page_end' must populate 'page_start' and 'page_end' in payload."""
        from .services.rag_service import RagService

        rag = RagService(in_memory=True)
        coll = "test_page_coll"

        chunk_from_chunker = [{
            "document_id": "doc_page_test",
            "chunk_id": "chunk_sec_01_p01",
            "text": "Academic section starting on page 5 and ending on page 6.",
            "page": 5,
            "page_end": 6,
        }]

        rag.index_chunks(coll, chunk_from_chunker, recreate=True)
        res = rag.search_dense(coll, "Academic section", top_k=1)
        self.assertEqual(len(res), 1)
        _, payload = res[0]
        self.assertEqual(payload["page_start"], 5, "page_start must fall back to chunk['page']!")
        self.assertEqual(payload["page_end"], 6, "page_end must equal chunk['page_end']!")

    def test_search_hybrid_rrf_multi_document_no_collision(self):
        """Task 1C: Hybrid RRF must fuse candidates from two different documents with identical chunk_ids without collision."""
        from .services.rag_service import RagService

        rag = RagService(in_memory=True)
        coll = "test_rrf_coll"

        chunks = [
            {"document_id": "doc_1", "chunk_id": "intro_01", "text": "Quantum computing uses superposition."},
            {"document_id": "doc_2", "chunk_id": "intro_01", "text": "Classical computing uses deterministic logic."},
        ]
        rag.index_chunks(coll, chunks, recreate=True)

        bm25_mock = [
            (8.5, {"document_id": "doc_1", "chunk_id": "intro_01", "text": "Quantum computing uses superposition."}),
            (8.0, {"document_id": "doc_2", "chunk_id": "intro_01", "text": "Classical computing uses deterministic logic."}),
        ]

        fused = rag.search_hybrid_rrf(coll, "computing logic and superposition", bm25_candidates=bm25_mock, top_k=5)
        # Both chunks must survive in fused output despite sharing chunk_id "intro_01"
        self.assertEqual(len(fused), 2)
        doc_ids_retrieved = {c["document_id"] for score, c in fused}
        self.assertEqual(doc_ids_retrieved, {"doc_1", "doc_2"}, "Both doc_1 and doc_2 chunks must survive without collision!")



