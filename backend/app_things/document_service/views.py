from django.shortcuts import render
from django.http import JsonResponse
from models import Document
from pypdf import PdfReader


def save_metadata_view(request):
    uploaded_file = request.FILES.get("file")

    if not uploaded_file:
        return JsonResponse({"error": "No file provided"}, status=400)

    filename = uploaded_file.name
    content_type = uploaded_file.content_type

    metadata = {
        "filename": filename,
        "content_type": content_type,
        "size": uploaded_file.size,
    }

    if content_type == "application/pdf":
        pdf = PdfReader(uploaded_file)
        # metadata = pdf.metadata
        # metadata = extract_data_from_doc(pdf)

    doc = Document.objects.create(metadata)
    # save_to_db(doc)
    return JsonResponse(metadata)


def content_upload_view(request):
    pass
