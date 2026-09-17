/**
 * Minimal valid academic PDF binary content for testing and fallback rendering
 * when a document does not have an uploaded physical file yet.
 */
export const SAMPLE_ACADEMIC_PDF_RAW = `%PDF-1.4
1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj
2 0 obj << /Type /Pages /Kids [3 0 R 6 0 R] /Count 2 >> endobj
3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R /Resources << /Font << /F1 5 0 R /F2 7 0 R >> >> >> endobj
4 0 obj << /Length 440 >> stream
BT
/F1 20 Tf
50 730 Td
(Scientific Document Manager: Automated Extraction and Verification) Tj
/F2 11 Tf
0 -26 Td
(Authors: Dr. Sarah Jenkins, Alan Turing, Ada Lovelace) Tj
0 -18 Td
(Stanford AI & Medicine Lab | Open Science Foundation) Tj
/F1 13 Tf
0 -35 Td
(1. Abstract) Tj
/F2 10 Tf
0 -18 Td
(Recent advances in transformer-based language models and multimodal dense retrievers) Tj
0 -14 Td
(have unlocked unprecedented capabilities in processing long-form biomedical literature.) Tj
0 -14 Td
(In this investigation, we introduce an end-to-end framework integrating multimodal) Tj
0 -14 Td
(representations with clinical diagnostic prior distributions.) Tj
/F1 13 Tf
0 -30 Td
(2. Methodology & Architecture) Tj
/F2 10 Tf
0 -18 Td
(Our neural pipeline maps scientific abstracts and full-text paragraphs into normalized) Tj
0 -14 Td
(dense vector spaces using contrastive loss functions and self-attention kernels.) Tj
ET
endstream
endobj
5 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >> endobj
6 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 8 0 R /Resources << /Font << /F1 5 0 R /F2 7 0 R >> >> >> endobj
7 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj
8 0 obj << /Length 380 >> stream
BT
/F1 16 Tf
50 730 Td
(3. Experimental Results & Discussion) Tj
/F2 10 Tf
0 -26 Td
(We evaluated our proposed system across 14,200 peer-reviewed articles indexed on Crossref.) Tj
0 -16 Td
(The model achieved 96.4% precision in extracting author attributions and citation keys.) Tj
0 -16 Td
(Furthermore, real-time PDF annotation synchronization demonstrated sub-50ms latency.) Tj
/F1 13 Tf
0 -36 Td
(4. Conclusion & Future Directions) Tj
/F2 10 Tf
0 -18 Td
(In-canvas PDF highlights and Google Drive-style permission sharing provide an essential) Tj
0 -14 Td
(foundation for next-generation collaborative scientific research.) Tj
ET
endstream
endobj
xref
0 9
0000000000 65535 f 
0000000009 00000 n 
0000000058 00000 n 
0000000122 00000 n 
0000000252 00000 n 
0000000746 00000 n 
0000000818 00000 n 
0000000948 00000 n 
0000001015 00000 n 
trailer << /Size 9 /Root 1 0 R >>
startxref
1449
%%EOF`;

/**
 * Returns an ArrayBuffer representation of the sample PDF.
 */
export function getSamplePdfArrayBuffer(): ArrayBuffer {
  const encoder = new TextEncoder();
  return encoder.encode(SAMPLE_ACADEMIC_PDF_RAW).buffer;
}
