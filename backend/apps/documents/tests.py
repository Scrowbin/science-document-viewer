from django.test import TestCase
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from .models import Document, Annotation, Note, DocumentShare
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
