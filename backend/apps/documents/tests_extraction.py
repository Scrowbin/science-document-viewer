"""Tests for the layout-based PDF title/author extraction (manual_pdf_parser) and the tier-2
metadata mapping + online enrichment (data_extractor).

SimpleTestCase only: no database access. Synthetic PDFs are built in memory with PyMuPDF.
Run: python manage.py test apps.documents.tests_extraction -v 2
"""
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

import pymupdf as fitz
from django.test import SimpleTestCase, override_settings

from apps.documents.data_extractor import data_extractor as de
from apps.documents.data_extractor import manual_pdf_parser as mp

ARXIV_FETCH = "apps.documents.services.pdf_metadata_service.fetch_arxiv_metadata"
CROSSREF_FETCH = "apps.documents.services.crossref_service.fetch_metadata_from_doi"


class _PdfMixin:
    """Builds one-page synthetic PDFs. Each item is (point, text) or (point, text, insert_text kwargs)."""

    def setUp(self):
        super().setUp()
        self.tmpdir = tempfile.mkdtemp(prefix="extract_test_")
        self.addCleanup(shutil.rmtree, self.tmpdir, ignore_errors=True)

    def build_doc(self, items, metadata=None):
        doc = fitz.open()
        page = doc.new_page()  # A4-ish: 595 x 842
        for item in items:
            point, text = item[0], item[1]
            kwargs = item[2] if len(item) > 2 else {}
            page.insert_text(point, text, **kwargs)
        if metadata:
            doc.set_metadata(metadata)
        return doc

    def build_pdf(self, items, metadata=None, name="paper.pdf"):
        doc = self.build_doc(items, metadata)
        path = os.path.join(self.tmpdir, name)
        doc.save(path)
        doc.close()
        return path

    def layout(self, items):
        doc = self.build_doc(items)
        self.addCleanup(doc.close)
        return mp.layout_title_authors(doc[0])

    def page_lines(self, items):
        doc = self.build_doc(items)
        self.addCleanup(doc.close)
        return mp._page_lines(doc[0])


# ─── Pure text helpers ──────────────────────────────────────────────────────────────


class AccentAndLigatureTests(SimpleTestCase):
    def test_spacing_accent_with_space_before_letter(self):
        self.assertEqual(mp._fix_accents("Bok´ anyi"), "Bokányi")

    def test_dotless_i_and_j_recombined(self):
        self.assertEqual(mp._fix_accents("Mart´ınez"), "Martínez")
        self.assertEqual(mp._fix_accents("ˆȷ"), "ĵ")

    def test_other_accents(self):
        self.assertEqual(mp._fix_accents("Ca˜nas"), "Cañas")
        self.assertEqual(mp._fix_accents("Fran¸cois"), "François")
        self.assertEqual(mp._fix_accents("Dvoˇr´ak"), "Dvořák")
        self.assertEqual(mp._fix_accents("Erd˝os"), "Erdős")

    def test_result_is_nfc(self):
        out = mp._fix_accents("Gr¨onroos")
        self.assertEqual(len(out), len("Grönroos"))  # one precomposed code point, not o + U+0308

    def test_ligatures(self):
        self.assertEqual(mp._fix_accents("ﬂow eﬀect oﬃce baﬄe ﬁnal"), "flow effect office baffle final")

    def test_lone_accent_left_alone(self):
        self.assertEqual(mp._fix_accents("value ´ 5"), "value ´ 5")
        self.assertEqual(mp._fix_accents("plain text"), "plain text")

    def test_is_accent_only(self):
        self.assertTrue(mp._is_accent_only("¨"))
        self.assertTrue(mp._is_accent_only(" ´ "))
        self.assertTrue(mp._is_accent_only("́"))
        self.assertFalse(mp._is_accent_only("a"))
        self.assertFalse(mp._is_accent_only("´a"))


class TitleCaseTests(SimpleTestCase):
    def test_mixed_case_unchanged(self):
        self.assertEqual(mp._smart_title_case("Attention Is All You Need"), "Attention Is All You Need")
        self.assertEqual(mp._smart_title_case("BERT for NLP"), "BERT for NLP")

    def test_small_words_lowercase_except_first(self):
        self.assertEqual(mp._smart_title_case("THE ART OF WAR IN THE MODERN AGE"),
                         "The Art of War in the Modern Age")

    def test_acronym_before_colon_kept_only_if_short_and_early(self):
        self.assertEqual(mp._smart_title_case("TRANSFORMERS: NEURAL MODELS"), "Transformers: Neural Models")
        self.assertEqual(mp._smart_title_case("BERT: PRE-TRAINING OF DEEP BIDIRECTIONAL TRANSFORMERS"),
                         "BERT: Pre-Training of Deep Bidirectional Transformers")
        # Colon word at position >= 3 is not treated as an acronym.
        self.assertEqual(mp._smart_title_case("A NEW DEEP GAN: RESULTS"), "A New Deep Gan: Results")

    # Regression (was a bug; _smart_title_case, manual_pdf_parser.py:429): a small word right after a colon
    # is lower-cased ("BERT: a Robustly ..."); title-case styles (APA, Chicago) capitalise the
    # first word of a subtitle.
    def test_first_word_after_colon_capitalised(self):
        self.assertEqual(mp._smart_title_case("ROBERTA: A ROBUSTLY OPTIMIZED BERT PRETRAINING APPROACH"),
                         "ROBERTA: A Robustly Optimized Bert Pretraining Approach")

    def test_acronyms_seen_in_mixed_case_text_keep_capitals(self):
        lines = [{"text": "WE PRESENT BERT AND GPT-4 RESULTS"},
                 {"text": "We fine-tune BERT and GPT-4 on SQuAD."}]
        acronyms = mp._page_acronyms(lines)
        self.assertTrue({"BERT", "GPT-4"} <= acronyms)
        self.assertNotIn("WE", acronyms)  # the all-caps line itself is not evidence
        self.assertEqual(mp._smart_title_case("ROBERTA: A ROBUSTLY OPTIMIZED BERT PRETRAINING APPROACH", acronyms),
                         "ROBERTA: A Robustly Optimized BERT Pretraining Approach")


class JoinTitleLinesTests(SimpleTestCase):
    def test_compound_prefixes_keep_hyphen(self):
        self.assertEqual(mp._join_title_lines(["Self-", "Supervised Learning"]), "Self-Supervised Learning")
        self.assertEqual(mp._join_title_lines(["Fine-", "tuning Models"]), "Fine-tuning Models")
        self.assertEqual(mp._join_title_lines(["Multi-", "Task Agents"]), "Multi-Task Agents")

    def test_hyphen_before_digit_kept(self):
        self.assertEqual(mp._join_title_lines(["Detecting COVID-", "19 in X-Rays"]), "Detecting COVID-19 in X-Rays")

    def test_three_lines_and_plain_join(self):
        self.assertEqual(mp._join_title_lines(["Graph Neural", "Net-", "works at Scale"]),
                         "Graph Neural Networks at Scale")

    def test_empty_and_single(self):
        self.assertEqual(mp._join_title_lines([]), "")
        self.assertEqual(mp._join_title_lines(["Only One Line"]), "Only One Line")


class AuthorNameHelperTests(SimpleTestCase):
    def test_clean_author_name_strips_markers_digits_and_punctuation(self):
        self.assertEqual(mp._clean_author_name("Ada Lovelace1,2∗"), "Ada Lovelace")
        self.assertEqual(mp._clean_author_name(" †Alan  Turing‡, "), "Alan Turing")
        self.assertEqual(mp._clean_author_name("Grace Hopper§¶ ."), "Grace Hopper")
        self.assertEqual(mp._clean_author_name("12"), "")

    def test_roman_numeral_sections_rejected(self):
        for heading in ("II. Methods", "III. Results", "IV. Discussion", "XII. Appendix"):
            self.assertFalse(mp._looks_like_name(heading), heading)

    def test_single_letter_initial_is_a_name(self):
        # "X. Li" / "V. Kumar" are real initials; single-letter Roman numerals stay accepted.
        self.assertTrue(mp._looks_like_name("X. Li"))
        self.assertTrue(mp._looks_like_name("V. Kumar"))

    def test_particles_and_compound_names(self):
        self.assertTrue(mp._looks_like_name("Vincent van der Berg"))
        self.assertTrue(mp._looks_like_name("Ludwig von Mises"))
        self.assertTrue(mp._looks_like_name("Jean-Pierre O'Neil"))
        self.assertTrue(mp._looks_like_name("J.-P. Sartre"))
        self.assertTrue(mp._looks_like_name("Zoë Ångström"))
        self.assertTrue(mp._looks_like_name("Nguyễn Văn An"))

    def test_rejections(self):
        self.assertFalse(mp._looks_like_name("Smith"))  # one token
        self.assertFalse(mp._looks_like_name("A B C D E F"))  # six tokens
        self.assertFalse(mp._looks_like_name("J. K."))  # initials only
        self.assertFalse(mp._looks_like_name("deep learning"))
        self.assertFalse(mp._looks_like_name("Ada lovelace"))
        self.assertFalse(mp._looks_like_name("Ada Lovelace (2020)"))
        self.assertFalse(mp._looks_like_name("Aaaaaaaaaaaaaaaaaaaaaaaaaaaaaa Bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"))


class PlausibleMetadataTitleTests(SimpleTestCase):
    def test_rejected(self):
        for t in (None, "", "Microsoft Word - draft.docx", "Microsoft Word - My Thesis Final",
                  "untitled document here", "Template for IEEE papers", "Slide deck for talk",
                  "c6_thermalspec_thf_2.eps", "Single", "Two Words", "x" * 301 + " a b c",
                  "report final version.pdf"):
            self.assertIsNone(mp._plausible_metadata_title(t), t)

    def test_accepted_and_stripped(self):
        self.assertEqual(mp._plausible_metadata_title("  Deep Residual Learning for Image Recognition "),
                         "Deep Residual Learning for Image Recognition")


class KeywordTests(SimpleTestCase):
    def test_separators_and_dedupe(self):
        text = "Keywords: alpha; beta · gamma • delta, alpha.\n1. INTRODUCTION\nBody."
        self.assertEqual(mp.extract_keywords(text), ["alpha", "beta", "gamma", "delta"])

    def test_index_terms_and_wrapped_lines(self):
        text = "Index Terms—graph neural\nnetworks, retrieval\n\nThis paragraph is body.\nI. INTRODUCTION\n"
        self.assertEqual(mp.extract_keywords(text), ["graph neural networks", "retrieval"])

    def test_length_and_word_caps(self):
        too_long = "a" * 61
        seven_words = "one two three four five six seven"
        six_words = "one two three four five six"
        text = f"Keywords: ok, {too_long}, {seven_words}, {six_words}, {'b' * 60}\n1. INTRODUCTION\n"
        self.assertEqual(mp.extract_keywords(text), ["ok", six_words, "b" * 60])

    def test_at_most_ten(self):
        kws = [f"kw{i}" for i in range(14)]
        text = "Keywords: " + ", ".join(kws) + "\n1. INTRODUCTION\n"
        self.assertEqual(mp.extract_keywords(text), kws[:10])

    def test_stops_at_metadata_labels(self):
        text = "Keywords: OCR, vision License: CC BY 4.0, other\n1. INTRODUCTION\n"
        self.assertEqual(mp.extract_keywords(text), ["OCR", "vision"])
        text = "Keywords: OCR, vision DOI 10.1/x\n1. INTRODUCTION\n"
        self.assertEqual(mp.extract_keywords(text), ["OCR", "vision"])

    def test_no_keyword_label(self):
        self.assertEqual(mp.extract_keywords("Abstract. Nothing here.\n1. INTRODUCTION\n"), [])

    # Regression (was a bug; extract_keywords, manual_pdf_parser.py:174-181): the match requires a following
    # "I. INTRODUCTION" / "1. INTRODUCTION" heading. LaTeX article-class papers number the
    # heading "1 Introduction" (no dot), so their keyword block is never found.
    def test_keywords_found_without_dotted_introduction_heading(self):
        text = "Keywords: retrieval, embeddings\n\n1 Introduction\nBody text."
        self.assertEqual(mp.extract_keywords(text), ["retrieval", "embeddings"])

    # Regression (was a bug; extract_keywords, manual_pdf_parser.py:189-194): the block is cut at the bare word
    # "abstract" anywhere, so a real keyword such as "abstract interpretation" truncates the list.
    def test_keyword_containing_the_word_abstract(self):
        text = "Keywords: program analysis, abstract interpretation, static analysis\n1. INTRODUCTION\n"
        self.assertEqual(mp.extract_keywords(text),
                         ["program analysis", "abstract interpretation", "static analysis"])


# ─── Layout extraction on synthetic PDFs ────────────────────────────────────────────


class PageLinesTests(_PdfMixin, SimpleTestCase):
    def test_vertical_text_dropped(self):
        lines = self.page_lines([
            ((20, 500), "arXiv:2101.01234v2 [cs.CL] 4 Jan 2021", {"fontsize": 20, "rotate": 90}),
            ((72, 90), "A Horizontal Title Line", {"fontsize": 18}),
        ])
        self.assertEqual([ln["text"] for ln in lines], ["A Horizontal Title Line"])

    def test_superscript_markers_dropped_and_names_separated(self):
        lines = self.page_lines([
            ((72, 150), "Ada Lovelace", {"fontsize": 11}),
            ((138, 145), "1,*", {"fontsize": 7}),
            ((152, 150), "Alan Turing", {"fontsize": 11}),
        ])
        self.assertEqual(len(lines), 1)
        self.assertNotIn("1", lines[0]["text"])
        self.assertNotIn("*", lines[0]["text"])
        self.assertEqual(lines[0]["text"], "Ada Lovelace Alan Turing")
        self.assertEqual(lines[0]["size"], 11.0)

    def test_subscript_kept(self):
        lines = self.page_lines([
            ((72, 150), "Al", {"fontsize": 14}),
            ((84.5, 153), "2", {"fontsize": 9}),
            ((89.5, 150), "O", {"fontsize": 14}),
            ((99.5, 153), "3", {"fontsize": 9}),
            ((104.5, 150), " Thin Films", {"fontsize": 14}),
        ])
        self.assertEqual(len(lines), 1)
        self.assertIn("2", lines[0]["text"])
        self.assertIn("3", lines[0]["text"])

    def test_adjacent_spans_in_different_fonts_stay_one_line(self):
        lines = self.page_lines([
            ((72, 150), "Graph", {"fontsize": 12}),
            ((106, 150), "Networks", {"fontsize": 12, "fontname": "tiro"}),
        ])
        self.assertEqual([ln["text"] for ln in lines], ["GraphNetworks"])

    def test_spacing_accent_span_glued(self):
        lines = self.page_lines([
            ((72, 150), "Bok", {"fontsize": 12}),
            ((93, 150), "´", {"fontsize": 12}),
            ((97, 150), "anyi Ervin", {"fontsize": 12}),
        ])
        self.assertEqual(lines[0]["text"], "Bokányi Ervin")

    def test_bold_flag_and_sorting(self):
        lines = self.page_lines([
            ((72, 200), "Lower line", {"fontsize": 11}),
            ((72, 100), "Upper bold line", {"fontsize": 11, "fontname": "hebo"}),
        ])
        self.assertEqual([ln["text"] for ln in lines], ["Upper bold line", "Lower line"])
        self.assertTrue(lines[0]["bold"])
        self.assertFalse(lines[1]["bold"])


class _FakePage:
    """Stands in for a PyMuPDF page: get_text("dict") returns a hand-made structure, so the span
    logic is tested without PyMuPDF's own space insertion between spans."""

    def __init__(self, lines):
        self._data = {"blocks": [{"lines": lines}]}

    def get_text(self, kind):
        assert kind == "dict"
        return self._data


def _span(text, x0, x1, size=10.0, baseline=100.0, flags=0):
    return {"text": text, "size": size, "flags": flags, "origin": (x0, baseline),
            "bbox": (x0, baseline - size, x1, baseline + 2)}


def _line(spans, direction=(1, 0)):
    return {"dir": direction, "spans": spans,
            "bbox": (spans[0]["bbox"][0], 90, spans[-1]["bbox"][2], 102)}


class PageLinesSpanLogicTests(SimpleTestCase):
    def texts(self, *lines):
        return [ln["text"] for ln in mp._page_lines(_FakePage(list(lines)))]

    def test_gap_between_spans_is_a_word_break(self):
        self.assertEqual(self.texts(_line([_span("Graph", 0, 30), _span("Networks", 32, 80)])), ["Graph Networks"])
        self.assertEqual(self.texts(_line([_span("Graph", 0, 30), _span("Networks", 31, 80)])), ["GraphNetworks"])

    def test_superscript_by_flag_dropped(self):
        self.assertEqual(self.texts(_line([_span("Ada Lovelace", 0, 60), _span("12", 60, 64, flags=1),
                                           _span("Alan Turing", 64, 120)])), ["Ada Lovelace Alan Turing"])

    def test_small_raised_span_dropped_small_lowered_kept(self):
        raised = _line([_span("Ada Lovelace", 0, 60), _span("†", 60, 63, size=6, baseline=95),
                        _span("Alan Turing", 63, 120)])
        lowered = _line([_span("Al", 0, 10), _span("2", 10, 13, size=6, baseline=102), _span("O", 13, 20),
                         _span("3", 20, 23, size=6, baseline=102), _span(" Films", 23, 50)])
        self.assertEqual(self.texts(raised), ["Ada Lovelace Alan Turing"])
        self.assertEqual(self.texts(lowered), ["Al2O3 Films"])

    def test_raised_accent_span_glued_not_dropped(self):
        line = _line([_span("Gr", 0, 10), _span("¨", 12, 15, size=6, baseline=96, flags=1),
                      _span("onroos", 15, 50)])
        self.assertEqual(self.texts(line), ["Grönroos"])

    def test_non_horizontal_lines_dropped(self):
        self.assertEqual(self.texts(_line([_span("Upward", 0, 30)], (0, -1)),
                                    _line([_span("Upside down", 0, 30)], (-1, 0)),
                                    _line([_span("Kept Line", 0, 30)])), ["Kept Line"])

    def test_whitespace_only_spans_and_lines_skipped(self):
        self.assertEqual(self.texts(_line([_span("  ", 0, 5)]), _line([_span("Text", 0, 20), _span(" ", 20, 22)])),
                         ["Text"])

    def test_size_is_main_span_size(self):
        lines = mp._page_lines(_FakePage([_line([_span("A", 0, 10, size=20), _span("Longer body text", 10, 90, size=9.96)])]))
        self.assertEqual(lines[0]["size"], 10.0)


class LayoutTitleAuthorsTests(_PdfMixin, SimpleTestCase):
    def test_arxiv_style_first_page(self):
        title, authors = self.layout([
            ((20, 500), "arXiv:2101.01234v2 [cs.CL] 4 Jan 2021", {"fontsize": 20, "rotate": 90}),
            ((72, 90), "Scalable Multi-Lan-", {"fontsize": 20}),
            ((72, 114), "guage Retrieval for Science", {"fontsize": 20}),
            ((72, 150), "Ada Lovelace", {"fontsize": 11}),
            ((140, 145), "1", {"fontsize": 7}),
            ((150, 150), ", Alan Turing", {"fontsize": 11}),
            ((222, 145), "2*", {"fontsize": 7}),
            ((232, 150), " and Grace Hopper", {"fontsize": 11}),
            ((72, 166), "1 University of Somewhere, ada@uni.edu", {"fontsize": 9}),
            ((72, 178), "2 Institute of Things, alan@inst.org", {"fontsize": 9}),
            ((72, 210), "Abstract", {"fontsize": 11}),
            ((72, 226), "Jane Doe Should Not Appear", {"fontsize": 11}),
        ])
        self.assertEqual(title, "Scalable Multi-Language Retrieval for Science")
        self.assertEqual(authors, ["Ada Lovelace", "Alan Turing", "Grace Hopper"])

    def test_compound_hyphen_kept_across_lines(self):
        title, _ = self.layout([
            ((72, 90), "Self-", {"fontsize": 20}),
            ((72, 114), "Supervised Pre-Training at Scale", {"fontsize": 20}),
        ])
        self.assertEqual(title, "Self-Supervised Pre-Training at Scale")

    def test_author_separators(self):
        _, authors = self.layout([
            ((72, 90), "A Title About Separators", {"fontsize": 20}),
            ((72, 130), "Ada Lovelace & Alan Turing; Grace Hopper", {"fontsize": 11}),
            ((72, 146), "Barbara Liskov · Donald Knuth | Edsger Dijkstra", {"fontsize": 11}),
            ((72, 162), "Ludwig van Beethoven and Marie Curie", {"fontsize": 11}),
            ((72, 190), "Abstract—This paper studies separators.", {"fontsize": 9}),
        ])
        self.assertEqual(authors, ["Ada Lovelace", "Alan Turing", "Grace Hopper", "Barbara Liskov",
                                   "Donald Knuth", "Edsger Dijkstra", "Ludwig van Beethoven", "Marie Curie"])

    def test_affiliation_and_email_lines_skipped(self):
        _, authors = self.layout([
            ((72, 90), "A Title About Affiliations", {"fontsize": 20}),
            ((72, 130), "Ada Lovelace", {"fontsize": 11}),
            ((72, 146), "Department of Computer Science", {"fontsize": 11}),
            ((72, 162), "Stanford University", {"fontsize": 11}),
            ((72, 178), "Google Research", {"fontsize": 11}),
            ((72, 194), "ada.lovelace@example.com", {"fontsize": 11}),
            ((72, 210), "Alan Turing", {"fontsize": 11}),
        ])
        self.assertEqual(authors, ["Ada Lovelace", "Alan Turing"])

    def test_unlabelled_abstract_stops_author_scan(self):
        _, authors = self.layout([
            ((72, 90), "A Title Without Abstract Label", {"fontsize": 20}),
            ((72, 130), "Ada Lovelace", {"fontsize": 11}),
            ((72, 160), "we propose a method that improves the retrieval of scientific documents across many",
             {"fontsize": 10}),
            ((72, 172), "Jane Doe", {"fontsize": 10}),
        ])
        self.assertEqual(authors, ["Ada Lovelace"])

    def test_introduction_stops_author_scan(self):
        _, authors = self.layout([
            ((72, 90), "A Title Before Introduction", {"fontsize": 20}),
            ((72, 130), "Ada Lovelace", {"fontsize": 11}),
            ((72, 160), "1 Introduction", {"fontsize": 12}),
            ((72, 180), "Jane Doe", {"fontsize": 10}),
        ])
        self.assertEqual(authors, ["Ada Lovelace"])

    def test_ieee_bold_title_then_regular_authors_same_size(self):
        title, authors = self.layout([
            ((72, 90), "Robust Control of Power Grids", {"fontsize": 14, "fontname": "hebo"}),
            ((72, 108), "John Smith, Mary Major", {"fontsize": 14}),
        ])
        self.assertEqual(title, "Robust Control of Power Grids")
        self.assertEqual(authors, ["John Smith", "Mary Major"])

    def test_all_caps_title_title_cased(self):
        title, _ = self.layout([
            ((72, 90), "LORA: LOW-RANK ADAPTATION OF", {"fontsize": 17}),
            ((72, 112), "LARGE LANGUAGE MODELS", {"fontsize": 17}),
            ((72, 140), "Edward Hu", {"fontsize": 10}),
        ])
        self.assertEqual(title, "LORA: Low-Rank Adaptation of Large Language Models")

    def test_boilerplate_first_lines_skipped(self):
        title, authors = self.layout([
            ((72, 50), "Noname manuscript No.", {"fontsize": 22}),
            ((72, 72), "Preprint", {"fontsize": 22}),
            ((72, 110), "Learning Sparse Codes for Images", {"fontsize": 18}),
            ((72, 140), "Ada Lovelace", {"fontsize": 11}),
        ])
        self.assertEqual(title, "Learning Sparse Codes for Images")
        self.assertEqual(authors, ["Ada Lovelace"])

    def test_title_prefix_removed(self):
        title, _ = self.layout([((72, 90), "Title: Sparse Codes for Images", {"fontsize": 18})])
        self.assertEqual(title, "Sparse Codes for Images")

    def test_too_short_largest_line_falls_to_next_size(self):
        title, _ = self.layout([
            ((72, 60), "Nature", {"fontsize": 26}),
            ((72, 110), "Sparse Codes for Natural Images", {"fontsize": 18}),
        ])
        self.assertEqual(title, "Sparse Codes for Natural Images")

    def test_text_in_lower_page_ignored(self):
        title, authors = self.layout([((72, 700), "A Big Footer Banner Text", {"fontsize": 30})])
        self.assertIsNone(title)
        self.assertEqual(authors, [])

    def test_blank_page(self):
        self.assertEqual(self.layout([]), (None, []))

    def test_title_run_stops_at_gap(self):
        title, _ = self.layout([
            ((72, 90), "Sparse Codes for Images", {"fontsize": 18}),
            ((72, 300), "Section Heading At Same Size", {"fontsize": 18}),
        ])
        self.assertEqual(title, "Sparse Codes for Images")

    def test_larger_lines_after_title_not_authors(self):
        _, authors = self.layout([
            ((72, 90), "Sparse Codes for Images", {"fontsize": 18}),
            ((72, 130), "Ada Lovelace", {"fontsize": 11}),
            # Larger than the title, but below the title zone (lower 40% of the page).
            ((72, 600), "Jane Doe", {"fontsize": 30}),
        ])
        self.assertEqual(authors, ["Ada Lovelace"])


class AutoExtractMetadataTests(_PdfMixin, SimpleTestCase):
    BODY_LOW = [((72, 600), "this is lowercase body text with no title at all", {"fontsize": 10})]

    def test_layout_title_wins_over_metadata(self):
        path = self.build_pdf([
            ((72, 90), "Layout Title Wins Here", {"fontsize": 20}),
            ((72, 130), "Ada Lovelace", {"fontsize": 11}),
        ], metadata={"title": "Some Metadata Title Value", "author": "Meta Person"})
        out = mp.auto_extract_metadata(path)
        self.assertEqual(out["title"], "Layout Title Wins Here")
        self.assertEqual(out["authors"], ["Ada Lovelace"])

    def test_metadata_title_used_when_no_layout_title(self):
        path = self.build_pdf(self.BODY_LOW, metadata={"title": "Deep Metadata Title Here",
                                                       "author": "Ada Lovelace and Alan Turing; Grace Hopper"})
        out = mp.auto_extract_metadata(path)
        self.assertEqual(out["title"], "Deep Metadata Title Here")
        self.assertEqual(out["authors"], ["Ada Lovelace", "Alan Turing", "Grace Hopper"])

    def test_rejected_metadata_title_falls_back_to_text(self):
        for bad in ("Microsoft Word - draft.docx", "c6_thermalspec_thf_2.eps"):
            path = self.build_pdf(self.BODY_LOW, metadata={"title": bad})
            out = mp.auto_extract_metadata(path)
            self.assertEqual(out["title"], "this is lowercase body text with no title at all", bad)

    def test_metadata_author_used_when_layout_finds_no_authors(self):
        path = self.build_pdf([((72, 90), "A Title With No Author Line", {"fontsize": 20})],
                              metadata={"author": "Ada Lovelace, x, Alan Turing"})
        out = mp.auto_extract_metadata(path)
        self.assertEqual(out["authors"], ["Ada Lovelace", "Alan Turing"])

    def test_identifiers_and_keywords(self):
        path = self.build_pdf([
            ((72, 90), "A Title With Identifiers", {"fontsize": 20}),
            ((72, 130), "Ada Lovelace", {"fontsize": 11}),
            ((72, 160), "DOI: 10.1145/3292500.3330701.", {"fontsize": 9}),
            ((72, 175), "Keywords: retrieval, embeddings", {"fontsize": 9}),
            ((72, 200), "1. INTRODUCTION", {"fontsize": 11}),
        ])
        out = mp.auto_extract_metadata(path)
        self.assertEqual(out["doi"], "10.1145/3292500.3330701")
        self.assertEqual(out["keywords"], ["retrieval", "embeddings"])

    def test_unreadable_file_returns_none(self):
        path = os.path.join(self.tmpdir, "broken.pdf")
        with open(path, "wb") as f:
            f.write(b"not a pdf at all")
        self.assertIsNone(mp.auto_extract_metadata(path))


# ─── data_extractor: identifiers, URLs, matching, enrichment ─────────────────────────


class PageOneIdentifierTests(SimpleTestCase):
    def test_arxiv_id(self):
        self.assertEqual(de._page_one_arxiv_id("arXiv:2101.01234v2 [cs.CL] 4 Jan 2021"), "2101.01234")
        self.assertEqual(de._page_one_arxiv_id("ARXIV : 1706.03762"), "1706.03762")
        self.assertEqual(de._page_one_arxiv_id("see arXiv:0704.0001 too"), "0704.0001")

    def test_arxiv_id_absent(self):
        self.assertIsNone(de._page_one_arxiv_id("1706.03762 without prefix"))
        self.assertIsNone(de._page_one_arxiv_id(""))
        self.assertIsNone(de._page_one_arxiv_id(None))

    def test_doi_trailing_punctuation(self):
        self.assertEqual(de._page_one_doi("DOI: 10.1145/3292500.3330701."), "10.1145/3292500.3330701")
        self.assertEqual(de._page_one_doi("(doi 10.1000/xyz123)."), "10.1000/xyz123")
        self.assertEqual(de._page_one_doi("10.1016/S0140-6736(20)30183-5;"), "10.1016/S0140-6736(20)30183-5")

    def test_doi_absent(self):
        self.assertIsNone(de._page_one_doi("no identifier"))
        self.assertIsNone(de._page_one_doi(None))


class BestUrlTests(SimpleTestCase):
    def test_priority(self):
        urls = ["https://example.org/paper"]
        self.assertEqual(de._best_url(urls, "10.1/x", "2101.01234"), "https://doi.org/10.1/x")
        self.assertEqual(de._best_url(urls, "", "2101.01234"), "https://arxiv.org/abs/2101.01234")
        self.assertEqual(de._best_url(urls, "", None), "https://example.org/paper")

    def test_noise_filtered(self):
        urls = ["https://orcid.org/0000-0001", "http://creativecommons.org/licenses/by/4.0",
                "mailto:a@b.c", "https://github.com/me/repo/issues", "https://twitter.com/me",
                "https://x.com/me", "https://github.com/me/repo"]
        self.assertEqual(de._best_url(urls, "", None), "https://github.com/me/repo")
        self.assertEqual(de._best_url(urls[:-1], "", None), "")
        self.assertEqual(de._best_url([], None, None), "")


class SamePaperTests(SimpleTestCase):
    def test_empty_titles(self):
        self.assertFalse(de._same_paper("", "Attention Is All You Need"))
        self.assertFalse(de._same_paper("Attention Is All You Need", None))
        self.assertFalse(de._same_paper("AI", "AI"))  # no word of 3+ characters

    def test_thresholds(self):
        self.assertTrue(de._same_paper("Attention Is All You Need", "attention is all you need."))
        # 2 of 4 words shared = 0.5 -> same
        self.assertTrue(de._same_paper("alpha beta gamma delta", "alpha beta epsilon zeta"))
        # 1 of 4 -> different
        self.assertFalse(de._same_paper("alpha beta gamma delta", "alpha omega epsilon zeta"))

    def test_ratio_uses_shorter_title(self):
        self.assertTrue(de._same_paper("Deep Residual Learning", "Deep Residual Learning for Image Recognition"))


@override_settings(METADATA_ONLINE_LOOKUP=True)
class EnrichOnlineTests(SimpleTestCase):
    LOCAL = {"title": "Attention Is All You Need", "short_title": "Attention Is All You Need",
             "authors": ["Ashish Vaswani"], "date": "2017", "doi": "", "url": "", "extra": "local abstract",
             "repository": "arXiv", "tags": ["NLP"]}

    def test_lookup_disabled(self):
        with override_settings(METADATA_ONLINE_LOOKUP=False), \
                patch(ARXIV_FETCH) as ax, patch(CROSSREF_FETCH) as cr:
            out = de._enrich_online(dict(self.LOCAL), "1706.03762", "10.1/x")
        ax.assert_not_called()
        cr.assert_not_called()
        self.assertEqual(out, self.LOCAL)

    def test_no_identifier_no_call(self):
        with patch(ARXIV_FETCH) as ax, patch(CROSSREF_FETCH) as cr:
            out = de._enrich_online(dict(self.LOCAL), None, None)
        ax.assert_not_called()
        cr.assert_not_called()
        self.assertNotIn("metadata_source", out)

    def test_arxiv_none_then_crossref(self):
        record = {"title": "Attention is all you need", "authors": ["Ashish Vaswani", "Noam Shazeer"],
                  "date": "2017-12-04", "doi": "10.5555/3295222", "repository": "NeurIPS"}
        with patch(ARXIV_FETCH, return_value=None) as ax, patch(CROSSREF_FETCH, return_value=record) as cr:
            out = de._enrich_online(dict(self.LOCAL), "1706.03762", "10.5555/3295222")
        ax.assert_called_once_with("1706.03762", timeout=5)
        cr.assert_called_once_with("10.5555/3295222", timeout=5)
        self.assertEqual(out["authors"], ["Ashish Vaswani", "Noam Shazeer"])
        self.assertEqual(out["doi"], "10.5555/3295222")
        self.assertEqual(out["metadata_source"], "Crossref")

    def test_arxiv_hit_skips_crossref(self):
        record = {"title": "Attention Is All You Need", "repository": "arXiv", "extra": "online abstract"}
        with patch(ARXIV_FETCH, return_value=record), patch(CROSSREF_FETCH) as cr:
            out = de._enrich_online(dict(self.LOCAL), "1706.03762", "10.1/x")
        cr.assert_not_called()
        self.assertEqual(out["metadata_source"], "arXiv")
        self.assertEqual(out["extra"], "online abstract")

    def test_fetch_raises_keeps_local(self):
        with patch(ARXIV_FETCH, side_effect=ConnectionError("down")), \
                patch(CROSSREF_FETCH) as cr, patch("builtins.print"):
            out = de._enrich_online(dict(self.LOCAL), "1706.03762", "10.1/x")
        self.assertEqual(out, self.LOCAL)
        cr.assert_not_called()  # documented: any failure keeps the local result
        with patch(CROSSREF_FETCH, side_effect=TimeoutError()), patch("builtins.print"):
            out = de._enrich_online(dict(self.LOCAL), None, "10.1/x")
        self.assertEqual(out, self.LOCAL)

    def test_mismatched_or_titleless_record_keeps_local(self):
        for record in ({"title": "Protein Folding With Diffusion", "authors": ["X Y"]},
                       {"title": "", "authors": ["X Y"]}, {"authors": ["X Y"]}, {}):
            with patch(CROSSREF_FETCH, return_value=record):
                out = de._enrich_online(dict(self.LOCAL), None, "10.1/x")
            self.assertEqual(out, self.LOCAL, record)

    def test_html_stripped_and_whitespace_collapsed(self):
        local = dict(self.LOCAL, title="Al2O3 Thin Films Grown by Atomic Layer Deposition")
        record = {"title": "Al<sub>2</sub>O<sub>3</sub> thin films grown by\n <i>atomic</i> layer deposition",
                  "short_title": "<b>Al2O3</b>  films", "authors": ["A <b>B</b>"]}
        with patch(CROSSREF_FETCH, return_value=record):
            out = de._enrich_online(local, None, "10.1/x")
        self.assertEqual(out["title"], "Al2O3 thin films grown by atomic layer deposition")
        self.assertEqual(out["short_title"], "Al2O3 films")
        self.assertEqual(out["authors"], ["A <b>B</b>"])  # lists are copied as-is

    def test_tags_kept_unless_empty(self):
        record = {"title": "Attention Is All You Need", "tags": ["Transformers"]}
        with patch(CROSSREF_FETCH, return_value=record):
            kept = de._enrich_online(dict(self.LOCAL), None, "10.1/x")
            filled = de._enrich_online(dict(self.LOCAL, tags=[]), None, "10.1/x")
        self.assertEqual(kept["tags"], ["NLP"])
        self.assertEqual(filled["tags"], ["Transformers"])

    def test_empty_online_values_do_not_overwrite(self):
        record = {"title": "Attention Is All You Need", "authors": [], "date": "", "extra": ""}
        with patch(CROSSREF_FETCH, return_value=record):
            out = de._enrich_online(dict(self.LOCAL), None, "10.1/x")
        self.assertEqual(out["authors"], ["Ashish Vaswani"])
        self.assertEqual(out["date"], "2017")
        self.assertEqual(out["extra"], "local abstract")

    def test_input_not_mutated_and_unknown_keys_ignored(self):
        local = dict(self.LOCAL)
        record = {"title": "Attention Is All You Need", "authors": ["New Person"], "publisher": "ACM",
                  "item_type": "conferencePaper", "language": "en"}
        with patch(CROSSREF_FETCH, return_value=record):
            out = de._enrich_online(local, None, "10.1/x")
        self.assertEqual(local, self.LOCAL)
        self.assertNotIn("publisher", out)
        self.assertEqual(out["item_type"], "conferencePaper")
        self.assertEqual(out["language"], "en")

    def test_arxiv_record_without_arxiv_repository_labelled_crossref(self):
        record = {"title": "Attention Is All You Need", "repository": ""}
        with patch(ARXIV_FETCH, return_value=record):
            out = de._enrich_online(dict(self.LOCAL), "1706.03762", None)
        self.assertEqual(out["metadata_source"], "Crossref")


@override_settings(USE_GROBID=False, METADATA_ONLINE_LOOKUP=False)
class DataExtractorEndToEndTests(_PdfMixin, SimpleTestCase):
    def _arxiv_pdf(self, stamp):
        return self.build_pdf([
            ((20, 500), stamp, {"fontsize": 20, "rotate": 90}),
            ((72, 90), "Scalable Retrieval for Scientific Papers", {"fontsize": 20}),
            ((72, 130), "Ada Lovelace and Alan Turing", {"fontsize": 11}),
            ((72, 160), "Abstract", {"fontsize": 11}),
        ])

    def test_arxiv_id_gives_year_repository_and_url(self):
        out = de.data_extractor(self._arxiv_pdf("arXiv:2101.01234v2"))
        self.assertEqual(out["title"], "Scalable Retrieval for Scientific Papers")
        self.assertEqual(out["short_title"], out["title"])
        self.assertEqual(out["authors"], ["Ada Lovelace", "Alan Turing"])
        self.assertEqual(out["date"], "2021")
        self.assertEqual(out["repository"], "arXiv")
        self.assertEqual(out["url"], "https://arxiv.org/abs/2101.01234")
        self.assertEqual(out["doi"], "")
        self.assertNotIn("metadata_source", out)

    # Regression (was a bug; data_extractor.py:181-183 + manual_pdf_parser.extract_year): the page-1 year comes from
    # extract_year first, whose YEAR_RE matches the "1912" of the arXiv id "1912.01234". Every
    # 2019 (19MM.*) and 2020 (20MM.*) arXiv id therefore yields a year 1901-1912 / 2001-2012
    # instead of 2019 / 2020 when the stamp is the first year-like text on page 1.
    def test_arxiv_id_year_not_misread_from_id_digits(self):
        out = de.data_extractor(self._arxiv_pdf("arXiv:1912.01234v1"))
        self.assertEqual(out["date"], "2019")

    def test_local_upload_with_doi_and_keywords(self):
        path = self.build_pdf([
            ((72, 90), "Robust Control of Power Grids", {"fontsize": 20}),
            ((72, 130), "John Smith", {"fontsize": 11}),
            ((72, 160), "Abstract: We study grids.", {"fontsize": 9}),
            ((72, 175), "Keywords: control, grids", {"fontsize": 9}),
            ((72, 190), "DOI: 10.1109/TPWRS.2020.1234567", {"fontsize": 9}),
            ((72, 220), "1. INTRODUCTION", {"fontsize": 11}),
        ])
        out = de.data_extractor(path)
        self.assertEqual(out["repository"], "Local Upload")
        self.assertEqual(out["doi"], "10.1109/TPWRS.2020.1234567")
        self.assertEqual(out["url"], "https://doi.org/10.1109/TPWRS.2020.1234567")
        self.assertEqual(out["tags"], ["control", "grids"])
        self.assertEqual(out["extra"], "We study grids.")

    def test_long_title_short_title_truncated(self):
        long_words = " ".join(["Retrieval"] * 6)
        path = self.build_pdf([
            ((40, 90), long_words, {"fontsize": 14}),
            ((40, 110), long_words, {"fontsize": 14}),
        ])
        out = de.data_extractor(path)
        self.assertGreater(len(out["title"]), 100)
        self.assertEqual(out["short_title"], out["title"][:100])

    def test_page_one_ids_passed_to_enrichment(self):
        record = {"title": "Scalable Retrieval for Scientific Papers", "authors": ["Ada Lovelace"],
                  "repository": "arXiv", "date": "2021-01-04"}
        with override_settings(METADATA_ONLINE_LOOKUP=True), patch(ARXIV_FETCH, return_value=record) as ax:
            out = de.data_extractor(self._arxiv_pdf("arXiv:2101.01234v2"))
        ax.assert_called_once_with("2101.01234", timeout=5)
        self.assertEqual(out["metadata_source"], "arXiv")
        self.assertEqual(out["date"], "2021-01-04")

    def test_no_title_returns_none(self):
        path = self.build_pdf([])
        self.assertIsNone(de.data_extractor(path))
