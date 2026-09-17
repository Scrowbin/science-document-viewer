import re
import requests
from typing import Dict, Any, Optional

def clean_doi(doi: str) -> str:
    """Normalize DOI string by stripping URL prefixes and whitespace."""
    if not doi:
        return ""
    doi = doi.strip()
    doi = re.sub(r'^https?://(dx\.)?doi\.org/', '', doi, flags=re.IGNORECASE)
    return doi.strip()

def strip_html_tags(text: str) -> str:
    """Remove XML/HTML tags often present in Crossref abstracts."""
    if not text:
        return ""
    return re.sub(r'<[^>]+>', '', text).strip()

def fetch_metadata_from_doi(raw_doi: str, timeout: int = 10) -> Optional[Dict[str, Any]]:
    """
    Fetch comprehensive academic metadata from Crossref REST API.
    Does not require an API key.
    """
    doi = clean_doi(raw_doi)
    if not doi:
        return None

    url = f"https://api.crossref.org/works/{doi}"
    headers = {
        'User-Agent': 'ScientificDocumentManager/1.0 (mailto:contact@scidocmanager.org)'
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        if response.status_code != 200:
            return None

        data = response.json()
        item = data.get('message', {})

        # Extract title
        titles = item.get('title', [])
        title = titles[0] if titles else 'Untitled Document'

        # Extract short title
        short_titles = item.get('short-title', [])
        short_title = short_titles[0] if short_titles else ''

        # Extract authors
        authors = []
        for author in item.get('author', []):
            given = author.get('given', '').strip()
            family = author.get('family', '').strip()
            name = f"{given} {family}".strip() if given or family else author.get('name', '').strip()
            if name:
                authors.append({
                    'first_name': given,
                    'last_name': family or name
                })

        # Extract journal / repository
        containers = item.get('container-title', [])
        repository = containers[0] if containers else item.get('publisher', '')

        # Extract publication date
        published = item.get('published-print') or item.get('published-online') or item.get('created') or {}
        date_parts = published.get('date-parts', [[]])[0]
        year = str(date_parts[0]) if len(date_parts) > 0 else '2026'
        month = f"{date_parts[1]:02d}" if len(date_parts) > 1 else '01'
        day = f"{date_parts[2]:02d}" if len(date_parts) > 2 else '01'
        iso_date = f"{year}-{month}-{day}"

        # Extract abstract
        abstract = strip_html_tags(item.get('abstract', ''))

        # Extract licenses
        licenses = item.get('license', [])
        license_name = licenses[0].get('URL', 'Open Access') if licenses else 'Open Access'

        # Extract subjects / tags
        subjects = item.get('subject', [])

        return {
            'title': title,
            'short_title': short_title,
            'authors': authors,
            'repository': repository,
            'doi': doi,
            'url': item.get('URL', f"https://doi.org/{doi}"),
            'date': iso_date,
            'item_type': item.get('type', 'journal-article'),
            'language': item.get('language', 'en'),
            'license': license_name,
            'extra': abstract,
            'tags': subjects[:5],
            'domains': [repository] if repository else ['General Science'],
        }

    except Exception as e:
        print(f"Error fetching metadata from Crossref for DOI {doi}: {e}")
        return None
