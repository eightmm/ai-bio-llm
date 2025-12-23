### 1. Data Overview
The dataset consists of 7 CSV files representing a time-course RNA-seq experiment of T cells:
- 1 metadata file (10 rows) containing experimental conditions and timepoints
- 6 differential expression files (36,255 rows each) comparing different timepoints (days 5, 7, 14, 21, 35, and 60)
Each DEG file contains normalized expression values (TPM) and statistical metrics (log2FC, p-values) for all genes between compared conditions. The data structure is well-suited for analyzing temporal changes in gene expression during T cell exhaustion and aging.

### 2. Column Dictionary (Detailed)

Metadata File (Q5.maryphilip_metadata.csv):
- **day**: Numeric, experimental timepoint in days, use for temporal ordering
- **condition**: String, experimental condition, use for grouping samples
- **category**: String, sample classification, use for phenotype annotation
- **source**: String, sample origin information, use for batch control

DEG Files (all 6 differential expression files):
- **Unnamed: 0**: String, gene identifier, use as primary key for joining
- **log2FoldChange**: Numeric, expression change between conditions, use for effect size
- **pvalue**: Numeric, statistical significance, use for initial filtering
- **padj**: Numeric, adjusted p-value (FDR), use for significance threshold
- **meanTPM_[condition]**: Numeric, average expression level, use for abundance filtering
- **meanTPM_[comparison]**: Numeric, average expression in comparison group, use for fold-change validation

### 3. Data Integrity & Quality
- All files contain complete data for 36,255 genes without missing values
- Gene identifiers are unique and consistent across files
- Expression values are properly normalized (TPM)
- Statistical metrics are appropriately calculated with FDR correction
- Time points are well-distributed for trajectory analysis
- No apparent batch effects or quality issues in the metadata

### 4. Sub-Problem Analysis: Data Applicability

Sub-problem 1 (Quantification):
- Use all 6 DEG files to track expression changes
- Filter genes: padj < 0.05, |log2FC| > 1
- Calculate exhaustion/aging scores using temporal patterns

Sub-problem 2 (Transition Window):
- Compare adjacent timepoints using DEG files
- Focus on day 14-35 interval for transition detection
- Use expression trajectories to identify inflection points

Sub-problem 3 (Rejuvenation Targets):
- Integrate all DEG files for temporal patterns
- Focus on transition window identified in sub-problem 2
- Select targets based on expression dynamics and significance

Sub-problem 4 (Drug Mapping):
- Use gene identifiers from DEG analysis
- Data sufficient for target identification
- Additional drug-target database needed (not provided)

### 5. Biological Context (from Data)
- Experiment tracks T cell response over 60 days
- Early (5-7 days) vs late (14-60 days) timepoints
- Multiple biological replicates per timepoint
- Captures exhaustion and aging-like progression
- Focuses on transcriptional changes during chronic stimulation

### 6. Recommendations for Solver
- **Key Keys**: Use gene identifiers (Unnamed: 0) for joining files
- **Pitfalls**: Avoid using raw p-values; always use adjusted p-values
- **Priority**: Focus on transition window identification (days 14-35)
- Ensure temporal continuity in analysis
- Consider biological significance alongside statistical significance

### 7. Domain Knowledge Injection
- Early exhaustion markers: PD-1, LAG3, TIM3
- Aging signatures: p53 pathway, senescence markers
- Cell death indicators: caspases, BCL2 family
- Expression thresholds: TPM > 1 for expressed genes
- Significance: padj < 0.05, |log2FC| > 1 for DEGs
- Time course interpretation: progressive exhaustion/aging

### 8. Data Integration Strategy
Begin with metadata file as backbone. Merge DEG files sequentially by timepoint using gene identifiers. Create unified expression matrix with timepoints as columns. Calculate fold-changes between consecutive timepoints. Generate integrated trajectory for each gene. Expected final dataset: 36,255 rows (genes) with expression values and statistics for all timepoints.

### 9. Step-by-Step Analysis Workflow
1. Load and validate all files
2. Create exhaustion/aging signatures from literature markers
3. Calculate time-resolved expression scores
4. Identify transition window using trajectory analysis
5. Select candidate genes showing significant changes
6. Validate targets against known biology
7. Generate integrated gene list with intervention directions
8. Map targets to available drugs (if database provided)
9. Produce final report with prioritized interventions

Quality control at each step through statistical validation and biological relevance assessment. Final deliverable includes scored gene list with intervention recommendations and supporting evidence.