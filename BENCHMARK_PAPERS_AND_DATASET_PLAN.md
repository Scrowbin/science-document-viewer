# Day 1: Evaluation Benchmark Dataset & Recommended Papers

> **Document Purpose:** Guidelines, recommended scientific papers, and gold-standard Ground-Truth Question-Answer-Evidence benchmark dataset for empirical evaluation of the Scientific Document Retrieval (RAG) system.

---

## 1. Selection Criteria for Evaluation Benchmark Papers

To make the evaluation scientifically rigorous, recognizable to defense committee members, and reproducible, papers must fulfill:
1. **Open-Access & Canonical:** Freely accessible on arXiv / open repositories with unambiguous DOIs.
2. **Clear Hierarchical Sectioning:** Standard academic layout (Abstract, Introduction, Related Work, Methodology/Architecture, Experiments, Results, Discussion).
3. **Multi-Column Formatting:** Tests layout-aware PyMuPDF reading order without cross-column bridging.
4. **Mix of Factoid, Quantitative, and Conceptual Information:** Allows testing various query complexities.

---

## 2. Recommended Papers (The Core 4)

### Paper 1: Attention Is All You Need (Vaswani et al., 2017)
* **arXiv ID:** [`arXiv:1706.03762`](https://arxiv.org/abs/1706.03762)
* **DOI:** `10.48550/arXiv.1706.03762`
* **Domain:** Deep Learning / Natural Language Processing
* **Key Sections:**
  * `1. Introduction`
  * `3. Model Architecture` (`3.1 Encoder and Decoder Stacks`, `3.2 Attention`, `3.3 Position-wise Feed-Forward Networks`, `3.4 Embeddings and Softmax`, `3.5 Positional Encoding`)
  * `4. Why Self-Attention`
  * `5. Training` (`5.1 Training Data and Batching`, `5.2 Hardware and Schedule`, `5.3 Optimizer`, `5.4 Regularization`)
  * `6. Results`

### Paper 2: Deep Residual Learning for Image Recognition (He et al., 2015)
* **arXiv ID:** [`arXiv:1512.03385`](https://arxiv.org/abs/1512.03385)
* **DOI:** `10.1109/CVPR.2016.90`
* **Domain:** Computer Vision / Convolutional Networks
* **Key Sections:**
  * `1. Introduction`
  * `3. Deep Residual Learning` (`3.1 Residual Learning`, `3.2 Identity Mapping by Shortcuts`, `3.3 Network Architectures`)
  * `4. Experiments` (`4.1 ImageNet Classification`, `4.2 CIFAR-10 and Analysis`)

### Paper 3: LoRA: Low-Rank Adaptation of Large Language Models (Hu et al., 2021)
* **arXiv ID:** [`arXiv:2106.09685`](https://arxiv.org/abs/2106.09685)
* **DOI:** `10.48550/arXiv.2106.09685`
* **Domain:** Parameter-Efficient Fine-Tuning (PEFT) / LLM Systems
* **Key Sections:**
  * `1. Introduction`
  * `2. Problem Formulation`
  * `3. Aren't Existing Solutions Good Enough?`
  * `4. Our Method` (`4.1 Low-Rank Parametrized Update Matrices`, `4.2 Applying LoRA to Transformer`, `4.3 Practical Benefits and Limitations`)
  * `5. Empirical Experiments`

### Paper 4: Retrieval-Augmented Generation for Knowledge-Intensive NLP Tasks (Lewis et al., 2020)
* **arXiv ID:** [`arXiv:2005.11401`](https://arxiv.org/abs/2005.11401)
* **DOI:** `10.48550/arXiv.2005.11401`
* **Domain:** Information Retrieval / RAG Architectures (direct thesis topic match)
* **Key Sections:**
  * `1. Introduction`
  * `2. Methods` (`2.1 Models: RAG-Sequence, RAG-Token`, `2.2 Retriever: DPR`, `2.3 Generator: BART`)
  * `3. Experiments` (`3.1 Open-domain Question Answering`, `3.2 Abstractive QA`)

---

## 3. Seed Benchmark Dataset (16 Curated Question-Answer-Evidence Pairs)

The benchmark is formally serialized in [`backend/data/eval_benchmark_seed.json`](file:///c:/DACNTT/backend/data/eval_benchmark_seed.json) and follows the schema:

| Field | Type | Description |
| :--- | :--- | :--- |
| `id` | String | Unique query identifier (e.g. `Q_ATTN_01`) |
| `paper_arxiv_id` | String | Associated research paper identifier |
| `paper_title` | String | Standard academic title |
| `question` | String | The realistic natural language query |
| `question_type` | Enum | `factoid` \| `architecture` \| `quantitative` \| `methodology` |
| `expected_answer` | String | Ground-truth gold answer |
| `target_section` | String | Primary section heading containing the supporting text |
| `target_page` | Integer | 1-indexed PDF page where evidence appears |
| `evidence_keywords` | Array[String]| Salient lexical tokens expected in the retrieved chunk |

### Detailed Evaluation Pairs:

#### Paper 1: Attention Is All You Need
1. **Q_ATTN_01 (Quantitative):**
   * *Question:* "What is the dimensionality ($d_{model}$) of the input and output vectors across all layers in the base Transformer model?"
   * *Target Section:* `3.1 Encoder and Decoder Stacks`
   * *Target Page:* 3
   * *Expected Answer:* "$d_{model} = 512$"
   * *Keywords:* `["d_model", "512", "encoder", "decoder", "sub-layers"]`

2. **Q_ATTN_02 (Architecture):**
   * *Question:* "Why does the Scaled Dot-Product Attention divide the dot product of queries and keys by the square root of $d_k$?"
   * *Target Section:* `3.2.1 Scaled Dot-Product Attention`
   * *Target Page:* 4
   * *Expected Answer:* "For large values of $d_k$, the dot products grow large in magnitude, pushing the softmax function into regions with extremely small gradients. Scaling by $\frac{1}{\sqrt{d_k}}$ counteracts this effect."
   * *Keywords:* `["square root", "sqrt(d_k)", "softmax", "gradients", "magnitude"]`

3. **Q_ATTN_03 (Methodology):**
   * *Question:* "What optimizer and learning rate warmup schedule were utilized during training?"
   * *Target Section:* `5.3 Optimizer`
   * *Target Page:* 7
   * *Expected Answer:* "Adam optimizer ($\beta_1=0.9, \beta_2=0.98, \epsilon=10^{-9}$) with 4000 warmup steps, increasing the learning rate linearly then decaying proportionally to the inverse square root of the step number."
   * *Keywords:* `["Adam", "beta_1", "4000", "warmup_steps", "inverse square root"]`

4. **Q_ATTN_04 (Factoid):**
   * *Question:* "What positional encoding formulation did the authors select to allow the model to extrapolate to sequence lengths unseen during training?"
   * *Target Section:* `3.5 Positional Encoding`
   * *Target Page:* 6
   * *Expected Answer:* "Sine and cosine functions of different frequencies ($PE_{(pos, 2i)} = \sin(pos/10000^{2i/d_{model}})$ and $PE_{(pos, 2i+1)} = \cos(pos/10000^{2i/d_{model}})$)."
   * *Keywords:* `["sine", "cosine", "frequencies", "extrapolate", "positional encoding"]`

---

#### Paper 2: Deep Residual Learning for Image Recognition
5. **Q_RES_01 (Methodology):**
   * *Question:* "What formulation expresses the residual mapping function $\mathcal{F}(x, \{W_i\})$ with identity shortcut connections?"
   * *Target Section:* `3.2 Identity Mapping by Shortcuts`
   * *Target Page:* 3
   * *Expected Answer:* "$y = \mathcal{F}(x, \{W_i\}) + x$, where $x$ and $y$ are the input and output vectors of the considered layers."
   * *Keywords:* `["identity mapping", "shortcuts", "F(x, {Wi})", "+ x"]`

6. **Q_RES_02 (Architecture):**
   * *Question:* "How does the 'bottleneck' building block design in 50/101/152-layer ResNets reduce parameter complexity?"
   * *Target Section:* `3.3 Network Architectures`
   * *Target Page:* 4
   * *Expected Answer:* "By using a stack of 3 layers: $1\times 1, 3\times 3, \text{and } 1\times 1$ convolutions, where the $1\times 1$ layers reduce and subsequently restore (increase) dimensions, leaving the $3\times 3$ layer a bottleneck."
   * *Keywords:* `["bottleneck", "1x1", "3x3", "reduce dimensions", "restore dimensions"]`

7. **Q_RES_03 (Quantitative):**
   * *Question:* "What top-5 error rate did the ensemble of ResNets achieve on the ImageNet test set?"
   * *Target Section:* `4.1 ImageNet Classification`
   * *Target Page:* 5
   * *Expected Answer:* "ResNet achieved a 3.57% top-5 error rate on the ImageNet test set, winning 1st place in the ILSVRC 2015 competition."
   * *Keywords:* `["3.57%", "top-5 error", "ImageNet", "ILSVRC 2015"]`

8. **Q_RES_04 (Factoid):**
   * *Question:* "What is the degradation problem observed when plain deep networks increase in depth?"
   * *Target Section:* `1. Introduction`
   * *Target Page:* 1
   * *Expected Answer:* "With network depth increasing, accuracy becomes saturated and then degrades rapidly; this degradation is not caused by overfitting, as training error also increases."
   * *Keywords:* `["degradation problem", "saturation", "training error", "not caused by overfitting"]`

---

#### Paper 3: LoRA: Low-Rank Adaptation
9. **Q_LORA_01 (Methodology):**
   * *Question:* "How does LoRA decompose the weight update matrix $\Delta W \in \mathbb{R}^{d \times k}$ during adaptation?"
   * *Target Section:* `4.1 Low-Rank Parametrized Update Matrices`
   * *Target Page:* 3
   * *Expected Answer:* "By decomposing $\Delta W$ into the product of two low-rank matrices $B \times A$, where $B \in \mathbb{R}^{d \times r}, A \in \mathbb{R}^{r \times k}$, with rank $r \ll \min(d, k)$."
   * *Keywords:* `["low-rank", "B * A", "rank r", "BA", "parameterized update"]`

10. **Q_LORA_02 (Architecture):**
    * *Question:* "How are matrices $A$ and $B$ initialized before training begins?"
    * *Target Section:* `4.1 Low-Rank Parametrized Update Matrices`
    * *Target Page:* 3
    * *Expected Answer:* "$A$ is initialized with a random Gaussian distribution, and $B$ is initialized to zero, ensuring $\Delta W = BA = 0$ at the start of training."
    * *Keywords:* `["Gaussian distribution", "initialized to zero", "Delta W = 0"]`

11. **Q_LORA_03 (Quantitative):**
    * *Question:* "By how much does LoRA reduce the number of trainable parameters compared to full fine-tuning of GPT-3 175B?"
    * *Target Section:* `1. Introduction`
    * *Target Page:* 2
    * *Expected Answer:* "LoRA can reduce the number of trainable parameters by 10,000 times (e.g. from 175B to ~17.5M) and reduce GPU memory requirement by 3 times."
    * *Keywords:* `["10,000 times", "3 times", "trainable parameters", "GPT-3 175B"]`

12. **Q_LORA_04 (Factoid):**
    * *Question:* "Does LoRA introduce any inference latency overhead compared to the fully fine-tuned model?"
    * *Target Section:* `4.1 Low-Rank Parametrized Update Matrices`
    * *Target Page:* 4
    * *Expected Answer:* "No. When deployed in production, the adapted weights can be directly combined with $W = W_0 + BA$, introducing zero additional inference latency."
    * *Keywords:* `["inference latency", "zero additional latency", "W = W_0 + BA", "combined"]`

---

#### Paper 4: Retrieval-Augmented Generation (Lewis et al., 2020)
13. **Q_RAG_01 (Architecture):**
    * *Question:* "What two distinct formulations of RAG models are introduced in the paper?"
    * *Target Section:* `2.1 Models`
    * *Target Page:* 2
    * *Expected Answer:* "RAG-Sequence (which uses the same retrieved passages to generate the entire sequence) and RAG-Token (which can attend to different passages across different generated tokens)."
    * *Keywords:* `["RAG-Sequence", "RAG-Token", "same document", "different tokens"]`

14. **Q_RAG_02 (Methodology):**
    * *Question:* "What neural retrieval mechanism and generator architecture are combined in the RAG system?"
    * *Target Section:* `2.2 Retriever: DPR`
    * *Target Page:* 3
    * *Expected Answer:* "Dense Passage Retriever (DPR) with a bi-encoder architecture based on BERT, combined with BART as the sequence-to-sequence generator."
    * *Keywords:* `["Dense Passage Retriever", "DPR", "BART", "bi-encoder"]`

15. **Q_RAG_03 (Quantitative):**
    * *Question:* "What passage retrieval corpus was indexed for the open-domain QA experiments?"
    * *Target Section:* `2.2 Retriever: DPR`
    * *Target Page:* 3
    * *Expected Answer:* "The December 2018 Wikipedia dump split into 21 million 100-word disjoint passages."
    * *Keywords:* `["December 2018", "Wikipedia dump", "21 million", "100-word passages"]`

16. **Q_RAG_04 (Comparative):**
    * *Question:* "Why does RAG achieve higher factual accuracy than purely parametric models like T5 or GPT-3?"
    * *Target Section:* `1. Introduction`
    * *Target Page:* 1
    * *Expected Answer:* "Because knowledge is stored explicitly in external non-parametric memory and retrieved dynamically, allowing verifiable citations and easier updating without retraining."
    * *Keywords:* `["non-parametric memory", "parametric", "verifiable", "updating without retraining"]`

---

## 4. Evaluation Execution Procedure

1. **Step 1:** Upload the target PDF into the Document Manager.
2. **Step 2:** Trigger chunking via `GET /api/v1/documents/{id}/chunks/?strategy={strategy}` for each strategy:
   * `section`
   * `section_token`
   * `section_overlap`
3. **Step 3:** Run the automated evaluation harness:
   ```bash
   python backend/scripts/evaluate_retrieval.py --benchmark backend/data/eval_benchmark_seed.json
   ```
4. **Step 4:** Record the comparative metrics: **Hit Rate@1**, **Hit Rate@3**, **Hit Rate@5**, **MRR**, and **Latency**.
