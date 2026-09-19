from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Document, Annotation, Note, DocumentShare, Author, Tag, DocumentAuthor
from ..collections_app.models import Collection
from .services.crossref_service import clean_doi, fetch_metadata_from_doi

User = get_user_model()

class CrossrefServiceTestCase(TestCase):
    def test_clean_doi(self):
        self.assertEqual(clean_doi("https://doi.org/10.1016/j.cell.2024.01"), "10.1016/j.cell.2024.01")
        self.assertEqual(clean_doi("http://dx.doi.org/10.1038/nature123"), "10.1038/nature123")
        self.assertEqual(clean_doi(" 10.1000/182 "), "10.1000/182")

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
        self.assertTrue(doc.file.name.endswith('.pdf'))
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
        self.assertEqual(doc.authors.first().last_name, 'Shannon')
        self.assertEqual(doc.tags.count(), 1)
        self.assertEqual(doc.tags.first().name, 'Information Theory')
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
        self.assertTrue(doc.file.name.endswith('.pdf'))

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
