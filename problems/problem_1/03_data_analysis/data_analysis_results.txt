### 1. Data Overview

The provided dataset consists of four CSV files capturing gene-level expression and annotation information across multiple T cell types and activation states in mouse (Ensembl IDs with ENSMUSG prefix).  

The first file, Q1.genelist.csv, contains 36,727 rows and two columns: Ensembl gene IDs and corresponding gene names. This serves as the master annotation table and reference index for all downstream integration. It is well-suited as the central gene identifier resource for the entire analysis.

The second file, Q1.features(nCD4).csv, contains 42,644 rows and 13 columns. It includes TPM expression values for naive CD4 T cells and a detailed activation time course (0.5h to 72h), along with precomputed mean resting and mean activated TPM values. This file provides high-resolution temporal expression dynamics for CD4 T cell activation and is directly usable for expression-based similarity calculations and resting-versus-activated contrasts.

The third file, Q1.features(nCD8).csv, includes 36,727 rows and 8 columns. It contains TPM expression values for naive CD8 T cells and selected activation time points (4h, 12h, 24h), as well as mean resting and mean activated TPM values. While the temporal resolution is lower than CD4, it is sufficient to compare resting versus activated expression patterns in CD8 T cells.

The fourth file, Q1.features(CD4 subtypes).csv, contains 26,260 rows and 12 columns. It provides expression values across multiple CD4 T helper subsets (Th0, Th1, Th2, Th9, Th17, Treg), along with naive and memory states. It also includes derived metrics such as resting mean TPM, activated mean TPM, and resting versus activated log2 fold change. This file is particularly valuable for identifying genes associated with resting (naive/memory) versus differentiated or activated CD4 states.

Collectively, these datasets are highly usable for constructing gene–gene similarity measures based on expression patterns across resting and activated T cell states, and for prioritizing genes relevant to naive and memory T cell regulation.

---

### 2. Column Dictionary (Detailed)

**File: Q1.genelist.csv**  
The “ensembl” column is a string representing the Ensembl gene identifier (ENSMUSG format), serving as the primary unique gene key. It should be used for all joins across files.  
The “gene_name” column is a string containing the common gene symbol. Biologically, it provides interpretability and linkage to known immunological functions. It should be used for reporting, annotation, and LLM-based functional summaries, but not as a join key due to potential duplication or ambiguity.

**File: Q1.features(nCD4).csv**  
The “ensembl” column is a string Ensembl gene ID and should be used as the join key.  
The “gene_name” column is a string gene symbol used for interpretation.  
The “naive” column is numeric TPM expression in naive CD4 T cells, representing resting state baseline expression.  
The “0.5h”, “1h”, “2h”, “4h”, “6h”, “12h”, “24h”, “48h”, and “72h” columns are numeric TPM values capturing a CD4 T cell activation time course following stimulation, reflecting early, intermediate, and late activation programs.  
The “mean_resting_TPM” column is numeric and summarizes expression across resting conditions (primarily naive). It should be used to rank genes by resting expression.  
The “mean_activated_TPM” column is numeric and summarizes expression across activated time points. It is useful for computing resting-versus-activated contrasts and similarity patterns.

**File: Q1.features(nCD8).csv**  
The “ensembl” column is a string Ensembl gene ID for joining.  
The “gene_name” column is a string gene symbol.  
The “naive” column is numeric TPM expression in naive CD8 T cells, representing resting expression.  
The “4h”, “12h”, and “24h” columns are numeric TPM values reflecting CD8 T cell activation at selected time points.  
The “mean_resting_tpm” column is numeric and summarizes resting expression.  
The “mean_activated_tpm” column is numeric and summarizes activated expression. These columns are recommended for resting-versus-activated comparisons in CD8 T cells.

**File: Q1.features(CD4 subtypes).csv**  
The “ensembl” column is a string Ensembl gene ID and join key.  
The “gene_name” column is a string gene symbol.  
The “naive” column is numeric TPM expression in naive CD4 T cells.  
The “Th0”, “Th1”, “Th17”, “Th2”, “Th9”, and “Treg” columns are numeric TPM values for differentiated CD4 T helper subsets, representing distinct functional states.  
The “memory” column is numeric TPM expression in memory CD4 T cells, a key resting-like state.  
The “meanTPM” column is numeric and represents overall mean expression across conditions.  
The “resting_mean_TPM” column is numeric and summarizes naive and memory expression, ideal for identifying resting T cell genes.  
The “activated_mean_TPM” column is numeric and summarizes activated/helper subset expression.  
The “resting_vs_activated_log2FC” column is numeric and quantifies differential expression between resting and activated states, directly useful for prioritizing resting T cell regulators.

---

### 3. Data Integrity & Quality

Ensembl gene IDs appear consistently across all files and are suitable as unique identifiers, although row counts differ between files, indicating that not all genes are present in every dataset. Gene names may not be unique and should not be used as primary keys. There is no explicit indication of missing values in the summaries, but expression matrices of this size typically include zero or near-zero TPM values for lowly expressed genes, which should be interpreted cautiously. Differences in column naming conventions, such as “mean_resting_TPM” versus “mean_resting_tpm”, require normalization during integration. Overall, the data quality is sufficient for large-scale similarity analysis, with standard preprocessing needed.

---

### 4. Sub-Problem Analysis: Data Applicability

**Sub-problem 1: Integrated Strategy for T Cell Gene Functional Similarity Scoring**  
This sub-problem requires integration of expression similarity, LLM-derived functional summaries, phylogenetic knowledge, and protein structure similarity. The expression-based component is fully supported by Q1.features(nCD4).csv, Q1.features(nCD8).csv, and Q1.features(CD4 subtypes).csv using TPM values, resting versus activated means, and log2 fold changes. The genelist file provides the necessary gene identifiers and names for LLM-based functional summarization and knowledge-based phylogenetic grouping. While no direct phylogenetic or protein structure data are included, the gene identifiers enable external annotation using public databases, making the data sufficient as an input backbone. Filtering strategies should include focusing on genes with high resting_mean_TPM and significant resting_vs_activated_log2FC to prioritize resting T cell regulators before computing similarity scores.

---

### 5. Biological Context (from Data)

The datasets cover mouse CD4 and CD8 T cells across naive, memory, and multiple activated or differentiated states. Resting T cells are represented by naive and memory conditions, while activation is captured through time-course stimulation (0.5h to 72h) and differentiation into Th1, Th2, Th17, Th9, and Treg subsets. Early activation time points reflect immediate-early signaling and transcriptional responses, whereas later time points and helper subsets represent stable effector programs. This biological breadth allows comparison of quiescent versus active transcriptional programs central to T cell homeostasis.

---

### 6. Recommendations for Solver

The optimal join key across all files is the “ensembl” gene ID. Gene names should be used only for interpretation and reporting. A major pitfall is inconsistent column naming across files, which must be harmonized before analysis. Another risk is overinterpreting low TPM values; filtering for sufficiently expressed genes in resting states is critical. The most critical analysis step is robust expression-based similarity calculation focused on resting conditions, as this anchors the identification of naive and memory T cell regulatory gene pairs.

---

### 7. Domain Knowledge Injection

Genes such as CCR7, IL7R, LTB, MALAT1, and TCF7 are classical markers of naive and memory T cells and are likely present among highly expressed resting genes. Early activation markers like CD69 and immediate-early transcription factors are expected to peak at 0.5–4h, while cytokines and effector molecules increase later. TPM values represent normalized transcript abundance; values above 1–5 TPM in resting cells generally indicate biologically meaningful expression. Log2 fold changes can be used to distinguish quiescence-associated genes from activation-induced genes.

---

### 8. Data Integration Strategy (Natural Language)

Integration should begin with Q1.genelist.csv as the central reference table. Each feature file should be left-joined to the genelist using the Ensembl gene ID to preserve annotation consistency. Column name harmonization should be applied to resting and activated mean TPM fields. Genes missing from certain datasets should be retained with partial data rather than excluded, as absence may reflect cell-type specificity. After integration, the expected row count will approximate the union of genes across all files, likely around 40,000 genes with varying completeness.

---

### 9. Step-by-Step Analysis Workflow (Natural Language)

First, load all four datasets and standardize column names, ensuring Ensembl IDs are consistent. Second, merge feature files with the genelist to create a unified gene-centric table. Third, identify resting T cell–relevant genes by filtering for high resting_mean_TPM and positive resting_vs_activated_log2FC in CD4 and CD8 contexts. Fourth, compute expression-based similarity between genes using correlation or distance metrics across resting and activation conditions. Fifth, generate LLM-based functional summaries for prioritized genes using gene names and known immunological roles, and organize them into functional or phylogenetic families. Sixth, incorporate external protein domain and structure annotations for the top 300 resting-expressed genes to estimate structural similarity. Finally, integrate expression similarity, functional/phylogenetic similarity, and structural similarity into a composite Functional Similarity Score, perform quality checks for biological plausibility, and output ranked gene pairs predicted to regulate naive and memory T cell states.