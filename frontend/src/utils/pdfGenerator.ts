import type { Document } from '../types';

/**
 * Escapes characters for PDF literal text strings: \( \) \\
 * Keeps printable ASCII for standard PDF Type-1 fonts (Helvetica, etc.).
 */
/**
 * Cleans XML/HTML tags and entities from input strings.
 */
function cleanText(str: string): string {
  return (str || '')
    .replace(/<[^>]*>/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/\s+/g, ' ')
    .trim();
}

/**
 * Escapes characters for PDF literal text strings: \( \) \\
 * Keeps printable ASCII for standard PDF Type-1 fonts (Helvetica, etc.).
 */
function escapePdfText(str: string): string {
  return cleanText(str)
    .replace(/\\/g, '\\\\')
    .replace(/\(/g, '\\(')
    .replace(/\)/g, '\\)')
    .replace(/[^\x20-\x7E]/g, ' ');
}

/**
 * Wraps text into lines that do not exceed maxChars.
 */
function wrapText(text: string, maxChars = 80): string[] {
  const words = cleanText(text).split(/\s+/);
  const lines: string[] = [];
  let currentLine = '';

  for (const w of words) {
    if (!w) continue;
    if ((currentLine + ' ' + w).trim().length <= maxChars) {
      currentLine = (currentLine + ' ' + w).trim();
    } else {
      if (currentLine) lines.push(currentLine);
      currentLine = w;
    }
  }
  if (currentLine) lines.push(currentLine);
  return lines;
}

/**
 * Encodes a string to Latin-1 bytes for PDF output without relying on Node.js Buffer.
 */
function stringToLatin1Bytes(str: string): Uint8Array {
  const bytes = new Uint8Array(str.length);
  for (let i = 0; i < str.length; i++) {
    bytes[i] = str.charCodeAt(i) & 0xff;
  }
  return bytes;
}

/**
 * Dynamically generates a valid, tailored, multi-page academic PDF (PDF 1.4)
 * for any given scientific document.
 * Includes Title, Authors, DOI, Abstract, Metadata Cards, Methodology, Benchmarks Table & References.
 */
export function generateAcademicPdf(doc: Document): Uint8Array {
  const title = cleanText(doc.title) || 'Academic Paper Title';
  const authors = cleanText(doc.creator || (doc.metadata?.authors?.join(', ') || 'Unknown Author'));
  const doi = cleanText(doc.metadata?.doi || '10.xxxx/xxxx');
  const repo = cleanText(doc.metadata?.repository || 'Open Research Repository');
  const date = cleanText(doc.metadata?.date || '2026');
  const license = cleanText(doc.metadata?.license || 'Open Access');
  const itemType = cleanText(doc.metadata?.itemType || 'Journal Article');
  const tags = cleanText(doc.metadata?.tags?.join(', ') || 'Scientific Computing, AI');
  const extra = cleanText(doc.metadata?.extra || 'Peer-reviewed academic research with empirical validation.');

  // ---------------- Page 1 Content Stream ----------------
  let p1 = '';

  // Top Banner Bar (Dark Blue)
  p1 += '0.08 0.18 0.36 rg\n';
  p1 += '50 782 495 24 re f\n';
  p1 += 'BT /F2 8.5 Tf 1 1 1 rg 60 790 Td (JOURNAL OF ADVANCED SCIENTIFIC RESEARCH & INFORMATICS  --  VOL. 28, NO. 4) Tj ET\n';

  // Document Title (Bold 15pt, Dark Slate)
  p1 += 'BT /F2 15 Tf 0.1 0.12 0.18 rg 50 740 Td\n';
  const titleLines = wrapText(title, 55);
  p1 += `(${escapePdfText(titleLines[0] || title)}) Tj\n`;
  if (titleLines[1]) {
    p1 += `0 -20 Td (${escapePdfText(titleLines[1])}) Tj\n`;
  }
  if (titleLines[2]) {
    p1 += `0 -20 Td (${escapePdfText(titleLines[2])}) Tj\n`;
  }
  p1 += 'ET\n';

  let currentY = titleLines.length > 2 ? 670 : titleLines.length > 1 ? 690 : 710;

  // Authors (10.5pt)
  p1 += `BT /F1 10.5 Tf 0.2 0.25 0.35 rg 50 ${currentY} Td (${escapePdfText(authors)}) Tj ET\n`;
  currentY -= 16;
  p1 += `BT /F3 8.5 Tf 0.45 0.45 0.5 rg 50 ${currentY} Td (Department of Computational Science & Biomedical Engineering  |  Published: ${escapePdfText(date)}) Tj ET\n`;
  currentY -= 18;

  // Horizontal separator line
  p1 += `0.8 0.82 0.88 RG 1 w 50 ${currentY} m 545 ${currentY} l S\n`;
  currentY -= 16;

  // Metadata Card Box
  p1 += `0.95 0.96 0.98 rg 50 ${currentY - 36} 495 40 re f\n`;
  p1 += `0.85 0.88 0.94 RG 0.5 w 50 ${currentY - 36} 495 40 re S\n`;
  p1 += `BT /F2 8.5 Tf 0.2 0.25 0.35 rg 60 ${currentY - 14} Td (DOI:) Tj /F1 8.5 Tf 30 0 Td (https://doi.org/${escapePdfText(doi)}) Tj ET\n`;
  p1 += `BT /F2 8.5 Tf 0.2 0.25 0.35 rg 60 ${currentY - 28} Td (Repository:) Tj /F1 8.5 Tf 55 0 Td (${escapePdfText(repo)}) Tj /F2 8.5 Tf 120 0 Td (License:) Tj /F1 8.5 Tf 45 0 Td (${escapePdfText(license)}) Tj /F2 8.5 Tf 100 0 Td (Type:) Tj /F1 8.5 Tf 35 0 Td (${escapePdfText(itemType)}) Tj ET\n`;
  currentY -= 54;

  // Abstract Header
  p1 += `BT /F2 11 Tf 0.1 0.15 0.25 rg 50 ${currentY} Td (ABSTRACT) Tj ET\n`;
  currentY -= 14;

  // Abstract Paragraph (Italic / Regular)
  const abstractText = `${title}. This paper presents a principled computational investigation into ${tags}. ${extra} By synthesizing multimodal empirical representations and rigorously benchmarking against baseline formulations, our experimental framework achieves state-of-the-art accuracy, low inference latency, and robust convergence properties across diverse scientific domains.`;
  const abstractLines = wrapText(abstractText, 85);
  p1 += `BT /F3 9.5 Tf 0.2 0.2 0.2 rg 50 ${currentY} Td\n`;
  abstractLines.slice(0, 7).forEach((l, idx) => {
    if (idx === 0) p1 += `(${escapePdfText(l)}) Tj\n`;
    else p1 += `0 -13 Td (${escapePdfText(l)}) Tj\n`;
  });
  p1 += 'ET\n';
  currentY -= (Math.min(abstractLines.length, 7) * 13 + 12);

  // Keywords
  p1 += `BT /F2 9 Tf 0.2 0.25 0.35 rg 50 ${currentY} Td (Keywords: ) Tj /F1 9 Tf 50 0 Td (${escapePdfText(tags)}) Tj ET\n`;
  currentY -= 22;

  // Section 1: Introduction
  p1 += `BT /F2 11 Tf 0.1 0.15 0.25 rg 50 ${currentY} Td (1. INTRODUCTION) Tj ET\n`;
  currentY -= 15;

  const introText1 = `Recent advancements in computational methodologies have dramatically expanded our capacity to model complex phenomena in scientific documentation and research intelligence. In the context of ${title}, traditional approaches frequently suffer from scalability bottlenecks, semantic ambiguity, and high variance under out-of-distribution domain shifts.`;
  const introLines1 = wrapText(introText1, 85);
  p1 += `BT /F1 9.5 Tf 0.2 0.2 0.2 rg 50 ${currentY} Td\n`;
  introLines1.forEach((l, idx) => {
    if (idx === 0) p1 += `(${escapePdfText(l)}) Tj\n`;
    else p1 += `0 -13 Td (${escapePdfText(l)}) Tj\n`;
  });
  p1 += 'ET\n';
  currentY -= (introLines1.length * 13 + 10);

  const introText2 = `To address these challenges, we introduce an integrated algorithmic pipeline tailored specifically for ${tags}. Our design philosophy centers on three core pillars: (i) robust data-driven representation extraction, (ii) high-throughput vector indexing with verifiable provenance, and (iii) interactive human-in-the-loop annotation validation.`;
  const introLines2 = wrapText(introText2, 85);
  p1 += `BT /F1 9.5 Tf 0.2 0.2 0.2 rg 50 ${currentY} Td\n`;
  introLines2.slice(0, 5).forEach((l, idx) => {
    if (idx === 0) p1 += `(${escapePdfText(l)}) Tj\n`;
    else p1 += `0 -13 Td (${escapePdfText(l)}) Tj\n`;
  });
  p1 += 'ET\n';

  // Footer Page 1
  p1 += 'BT /F1 8.5 Tf 0.5 0.5 0.5 rg 50 35 Td (Scientific Document Manager - Academic Archive) Tj 440 0 Td (Page 1 of 2) Tj ET\n';

  // ---------------- Page 2 Content Stream ----------------
  let p2 = '';
  p2 += `BT /F3 8.5 Tf 0.5 0.5 0.5 rg 50 805 Td (${escapePdfText(titleLines[0] || title)} - ${escapePdfText(authors)}) Tj 380 0 Td (Page 2 of 2) Tj ET\n`;
  p2 += '0.8 0.82 0.88 RG 0.5 w 50 798 m 545 798 l S\n';

  let p2Y = 770;
  // Section 2: Methodology
  p2 += `BT /F2 11 Tf 0.1 0.15 0.25 rg 50 ${p2Y} Td (2. ARCHITECTURE & METHODOLOGY) Tj ET\n`;
  p2Y -= 15;

  const methodText = `The proposed framework establishes a dual-stage execution loop. The primary ingestion module computes structured vector embeddings across normalized coordinate spaces, allowing real-time PDF canvas highlighting and spatial text selection. Let the document embedding space be represented by D in R^(N x d), where each bounding box coordinate (x, y, w, h) maps directly to the normalized viewport.`;
  const methodLines = wrapText(methodText, 85);
  p2 += `BT /F1 9.5 Tf 0.2 0.2 0.2 rg 50 ${p2Y} Td\n`;
  methodLines.forEach((l, idx) => {
    if (idx === 0) p2 += `(${escapePdfText(l)}) Tj\n`;
    else p2 += `0 -13 Td (${escapePdfText(l)}) Tj\n`;
  });
  p2 += 'ET\n';
  p2Y -= (methodLines.length * 13 + 14);

  // Benchmarks Section
  p2 += `BT /F2 11 Tf 0.1 0.15 0.25 rg 50 ${p2Y} Td (3. EXPERIMENTAL BENCHMARKS & EVALUATION) Tj ET\n`;
  p2Y -= 15;

  // Table Box
  p2 += `0.96 0.97 0.99 rg 50 ${p2Y - 70} 495 70 re f\n`;
  p2 += `0.85 0.88 0.94 RG 0.5 w 50 ${p2Y - 70} 495 70 re S\n`;
  p2 += `BT /F2 8.5 Tf 0.15 0.2 0.3 rg 60 ${p2Y - 16} Td (Table 1: Quantitative Comparison on ${escapePdfText(tags.slice(0, 30))}) Tj ET\n`;
  p2 += `BT /F2 8 Tf 0.2 0.2 0.2 rg 60 ${p2Y - 32} Td (Model / Configuration) Tj 140 0 Td (Accuracy (AUROC)) Tj 120 0 Td (F1-Score) Tj 100 0 Td (Latency (ms)) Tj ET\n`;
  p2 += `BT /F1 8 Tf 0.3 0.3 0.3 rg 60 ${p2Y - 46} Td (Baseline Standard Heuristic) Tj 140 0 Td (0.841) Tj 120 0 Td (0.812) Tj 100 0 Td (148 ms) Tj ET\n`;
  p2 += `BT /F2 8 Tf 0.1 0.45 0.2 rg 60 ${p2Y - 60} Td (Proposed Method (Ours)) Tj 140 0 Td (0.974 (+13.3%)) Tj 120 0 Td (0.961 (+14.9%)) Tj 100 0 Td (24 ms (6.1x)) Tj ET\n`;
  p2Y -= 88;

  // Section 4: Conclusion
  p2 += `BT /F2 11 Tf 0.1 0.15 0.25 rg 50 ${p2Y} Td (4. CONCLUSION & COLLABORATION WORKFLOW) Tj ET\n`;
  p2Y -= 15;

  const concText = `We demonstrated that integrating structured metadata extraction with in-canvas PDF annotation and Google Drive-style collaboration permissions provides superior research velocity. Future work will integrate retrieval-augmented generation (RAG) directly into the viewing pane for interactive cross-paper question answering.`;
  const concLines = wrapText(concText, 85);
  p2 += `BT /F1 9.5 Tf 0.2 0.2 0.2 rg 50 ${p2Y} Td\n`;
  concLines.forEach((l, idx) => {
    if (idx === 0) p2 += `(${escapePdfText(l)}) Tj\n`;
    else p2 += `0 -13 Td (${escapePdfText(l)}) Tj\n`;
  });
  p2 += 'ET\n';
  p2Y -= (concLines.length * 13 + 16);

  // References
  p2 += `BT /F2 10 Tf 0.1 0.15 0.25 rg 50 ${p2Y} Td (REFERENCES) Tj ET\n`;
  p2Y -= 14;
  p2 += `BT /F1 8 Tf 0.3 0.3 0.3 rg 50 ${p2Y} Td ([1] ${escapePdfText(authors)} (${escapePdfText(date)}). "${escapePdfText(title)}". ${escapePdfText(repo)}. https://doi.org/${escapePdfText(doi)}) Tj ET\n`;
  p2Y -= 13;
  p2 += `BT /F1 8 Tf 0.3 0.3 0.3 rg 50 ${p2Y} Td ([2] Vaswani, A., et al. (2017). "Attention Is All You Need". Advances in Neural Information Processing Systems (NeurIPS), 30.) Tj ET\n`;
  p2Y -= 13;
  p2 += `BT /F1 8 Tf 0.3 0.3 0.3 rg 50 ${p2Y} Td ([3] Devlin, J., et al. (2019). "BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding". NAACL-HLT.) Tj ET\n`;

  // Footer Page 2
  p2 += 'BT /F1 8.5 Tf 0.5 0.5 0.5 rg 50 35 Td (Scientific Document Manager - Academic Archive) Tj 440 0 Td (Page 2 of 2) Tj ET\n';

  // ---------------- Assemble Complete PDF 1.4 Object Graph ----------------
  const p1BytesLength = p1.length;
  const p2BytesLength = p2.length;

  const objects: string[] = [];
  objects[1] = '<< /Type /Catalog /Pages 2 0 R >>';
  objects[2] = '<< /Type /Pages /Kids [3 0 R 4 0 R] /Count 2 >>';
  objects[3] = '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R >> >> /Contents 8 0 R >>';
  objects[4] = '<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Resources << /Font << /F1 5 0 R /F2 6 0 R /F3 7 0 R >> >> /Contents 9 0 R >>';
  objects[5] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>';
  objects[6] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold >>';
  objects[7] = '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Oblique >>';
  objects[8] = `<< /Length ${p1BytesLength} >>\nstream\n${p1}\nendstream`;
  objects[9] = `<< /Length ${p2BytesLength} >>\nstream\n${p2}\nendstream`;

  let pdf = '%PDF-1.4\n%\xE2\xE3\xCF\xD3\n';
  const xrefOffsets: number[] = [0];

  for (let i = 1; i <= 9; i++) {
    xrefOffsets[i] = pdf.length;
    pdf += `${i} 0 obj\n${objects[i]}\nendobj\n`;
  }

  const startXref = pdf.length;
  pdf += 'xref\n0 10\n0000000000 65535 f \n';
  for (let i = 1; i <= 9; i++) {
    pdf += `${String(xrefOffsets[i]).padStart(10, '0')} 00000 n \n`;
  }

  pdf += `trailer\n<< /Size 10 /Root 1 0 R >>\nstartxref\n${startXref}\n%%EOF\n`;

  return stringToLatin1Bytes(pdf);
}
