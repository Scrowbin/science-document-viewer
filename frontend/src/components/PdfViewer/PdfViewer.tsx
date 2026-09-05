import React, { useState } from 'react';
import styles from './PdfViewer.module.css';
import type { Document } from '../../types';
import {
  FaHighlighter,
  FaNoteSticky,
  FaAngleLeft,
  FaAngleRight,
  FaMagnifyingGlassMinus,
  FaMagnifyingGlassPlus,
  FaExpand,
} from 'react-icons/fa6';

export interface PdfViewerProps {
  document: Document;
}

export const PdfViewer: React.FC<PdfViewerProps> = ({ document }) => {
  const [highlightActive, setHighlightActive] = useState(false);
  const [noteActive, setNoteActive] = useState(false);
  const [zoomLevel, setZoomLevel] = useState(100);

  return (
    <div className={styles.pdfViewerWrapper}>
      {/* Top Annotation Toolbar */}
      <div className={styles.pdfToolbar}>
        <div className={styles.pdfToolbarGroup}>
          <button
            type="button"
            className={`${styles.pdfToolBtn} ${highlightActive ? styles.pdfToolBtnActive : ''}`}
            onClick={() => setHighlightActive((prev) => !prev)}
            title="Highlight Text Tool"
          >
            <FaHighlighter />
            <span>Highlight</span>
          </button>
          <button
            type="button"
            className={`${styles.pdfToolBtn} ${noteActive ? styles.pdfToolBtnActive : ''}`}
            onClick={() => setNoteActive((prev) => !prev)}
            title="Add Sticky Note"
          >
            <FaNoteSticky />
            <span>Note</span>
          </button>
        </div>

        <div className={styles.pdfToolbarGroup}>
          <button type="button" className={styles.pdfToolBtn} title="Previous Page">
            <FaAngleLeft />
          </button>
          <span className={styles.pdfPageIndicator}>Page 1 of 14</span>
          <button type="button" className={styles.pdfToolBtn} title="Next Page">
            <FaAngleRight />
          </button>
        </div>

        <div className={styles.pdfToolbarGroup}>
          <button
            type="button"
            className={styles.pdfToolBtn}
            onClick={() => setZoomLevel((z) => Math.max(75, z - 10))}
            title="Zoom Out"
          >
            <FaMagnifyingGlassMinus />
          </button>
          <span className={styles.pdfPageIndicator}>{zoomLevel}%</span>
          <button
            type="button"
            className={styles.pdfToolBtn}
            onClick={() => setZoomLevel((z) => Math.min(150, z + 10))}
            title="Zoom In"
          >
            <FaMagnifyingGlassPlus />
          </button>
          <button
            type="button"
            className={styles.pdfToolBtn}
            onClick={() => setZoomLevel(100)}
            title="Fit to Width"
          >
            <FaExpand />
            <span>Fit</span>
          </button>
        </div>
      </div>

      {/* PDF Content Area */}
      <div className={styles.pdfBody}>
        {/* Scrollable PDF Paper Canvas */}
        <div className={styles.pdfCanvasScrollArea}>
          <div
            className={styles.pdfPageCanvas}
            style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: 'top center' }}
          >
            <div className={styles.pdfArticleHeader}>
              <div className={styles.pdfArticleTitle}>{document.metadata.title}</div>
              <div className={styles.pdfArticleAuthors}>
                {document.metadata.authors.join(', ')}
              </div>
              <div className={styles.pdfArticleMeta}>
                {document.metadata.repository} • DOI: {document.metadata.doi} • {document.metadata.date}
              </div>
            </div>

            <div className={styles.pdfAbstractBox}>
              <strong>Abstract — </strong>
              Scientific and computational precision in medical artificial intelligence requires
              rigorous multi-centric evaluation. Here, we present a standardized approach validating
              architectures against out-of-distribution shifts, showing statistically significant
              improvement in accuracy, recall, and interpretability over baseline benchmarks.
            </div>

            <div className={styles.pdfTwoColumns}>
              <div>
                <div className={styles.pdfSectionHeading}>1. Introduction</div>
                <p>
                  High-throughput acquisition of scientific imaging datasets presents both an
                  immense clinical opportunity and substantial analytical challenges. Prior
                  computational pipelines suffer from dataset shifts, variance in acquisition
                  protocols, and lack of reproducible fact-checking constraints.
                </p>
                <p>
                  <span className={styles.pdfHighlight}>
                    In this investigation, we introduce an end-to-end framework integrating multimodal
                    representations with clinical diagnostic prior distributions.
                  </span>
                </p>
                <div className={styles.pdfSectionHeading}>2. Methodology</div>
                <p>
                  Our architecture leverages transformer-based self-attention mechanisms with
                  sparse kernel representations. Each layer applies normalization and residual
                  projections to maintain gradient stability across deep hierarchies.
                </p>
              </div>

              <div>
                <div className={styles.pdfFigureBox}>
                  <strong>[Figure 1: Architectural Pipeline]</strong>
                  <br />
                  Schematic overview of latent feature alignment across multimodal clinical modalities.
                </div>
                <div className={styles.pdfSectionHeading}>3. Experimental Results</div>
                <p>
                  Across three independent validation cohorts comprising 14,200 patient cases, our
                  proposed system outperformed existing state-of-the-art benchmarks by 4.8% AUROC
                  (p &lt; 0.001) while decreasing computational latency by 32%.
                </p>
                <div className={styles.pdfSectionHeading}>4. Discussion</div>
                <p>
                  These empirical findings substantiate the hypothesis that structured attention
                  priors significantly enhance generalizability across heterogeneous radiological
                  institutions.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Side Note / Annotations Panel */}
        <div className={styles.pdfNotesSidebar}>
          <div className={styles.pdfNotesTitle}>Annotations & Notes</div>
          <div className={styles.pdfNoteCard}>
            <div className={styles.pdfNoteCardHeader}>
              <span>Highlight • Page 1</span>
              <span>10:42 AM</span>
            </div>
            <div className={styles.pdfNoteQuote}>
              "In this investigation, we introduce an end-to-end framework integrating multimodal
              representations..."
            </div>
            <div className={styles.pdfNoteText}>
              Crucial methodology finding to reference in our upcoming literature review.
            </div>
          </div>

          <div className={styles.pdfNoteCard}>
            <div className={styles.pdfNoteCardHeader}>
              <span>Sticky Note • Figure 1</span>
              <span>Yesterday</span>
            </div>
            <div className={styles.pdfNoteText}>
              Check comparison metrics against the 2025 baseline benchmark in Table 2.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PdfViewer;
