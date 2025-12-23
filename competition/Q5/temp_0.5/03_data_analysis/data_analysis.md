### 1. Data Overview
The dataset consists of 7 files representing time-course RNA-seq analysis of T cells:
- 1 metadata file (Q5.maryphilip_metadata.csv) with 10 rows containing experimental conditions
- 6 differential expression files comparing different timepoints (5, 7, 14, 21, 35, and 60 days)
- Each DEG file contains 36,255 genes with expression values (TPM), fold changes, and statistical metrics
- Files follow a consistent format with same number of columns and comparable metrics

### 2. Column Dictionary (Detailed)

Metadata File Columns:
- **day**: String - Timepoint of sample collection - Use for temporal ordering
- **condition**: String - Experimental condition - Use for grouping samples
- **category**: String - Sample classification - Use for phenotype association
- **source**: String - Sample origin - Use for batch control

DEG Files Common Columns:
- **Unnamed: 0**: String - Gene identifier - Use as primary join key
- **log2FoldChange**: Numeric - Expression change between conditions - Use for effect size
- **pvalue**: Numeric - Statistical significance - Use for initial filtering
- **padj**: Numeric - Multiple-testing corrected p-value - Use for significance threshold
- **meanTPM_[condition]**: Numeric - Average expression level - Use for abundance filtering

### 3. Data Integrity & Quality
- Gene identifiers are consistent across all DEG files
- No missing values in key statistical columns
- TPM values properly normalized
- Consistent number of genes (36,255) across all comparisons
- Clear temporal progression in sample comparisons
- Statistical metrics properly calculated with adjusted p-values

### 4. Sub-Problem Analysis: Data Applicability

Sub-problem 1 (Quantify Programs):
- Use all DEG files to track expression changes
- Sufficient data for both exhaustion and aging scores
- Filter genes: padj < 0.05, |log2FC| > 1

Sub-problem 2 (Transition Window):
- Compare adjacent timepoints using DEG files
- Sufficient temporal resolution (5-60 days)
- Focus on day 14-35 transition files

Sub-problem 3 (Rejuvenation Targets):
- Use transition window DEG files
- Compare expression patterns across all timepoints
- Filter for consistent trends

Sub-problem 4 (Drug Mapping):
- Gene identifiers present for mapping
- Expression data sufficient for direction prediction
- Missing drug-target dataset noted in files

### 5. Biological Context (from Data)
- Time course spans early (day 5) to late (day 60) T cell responses
- Early vs Late (E vs L) comparisons at days 5 and 7
- Later timepoints compared to day 14 baseline
- Captures progression from activation to exhaustion
- Temporal resolution suitable for transition detection

### 6. Recommendations for Solver
- **Key Keys**: Use Unnamed: 0 column as gene identifier
- **Pitfalls**: Avoid direct day 5 to day 60 comparisons
- **Priority**: Focus on day 14-35 transition period
- Use TPM values for abundance filtering
- Consider both up and down-regulated genes

### 7. Domain Knowledge Injection
- Early activation markers (CD69, CD25) expected in day 5-7
- Exhaustion markers (PD-1, LAG3, TIM3) in intermediate timepoints
- Aging/senescence markers (p21, p16) in later timepoints
- TPM > 1 indicates reliable expression
- Consider cell death markers after day 35

### 8. Data Integration Strategy
Integrate files sequentially by timepoint:
1. Start with day 5 vs day 7 comparison
2. Add day 14 data using gene identifiers
3. Incorporate day 21, 35, and 60 comparisons
4. Maintain gene-centric organization
5. Create temporal profiles for each gene
6. Expected ~36,000 genes with complete profiles

### 9. Step-by-Step Analysis Workflow
1. Load and validate all DEG files
2. Create gene-centric temporal profiles
3. Calculate exhaustion scores using early timepoints
4. Derive aging scores from later timepoints
5. Identify transition window (day 14-35)
6. Extract candidate intervention targets
7. Validate targets against known biology
8. Generate comprehensive gene profiles
9. Document expression patterns and statistics
10. Prepare final target recommendations