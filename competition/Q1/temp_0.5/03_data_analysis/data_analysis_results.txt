### 1. Data Overview
- reference.fa: Single FASTA file containing one transcript sequence (toy_gene)
- reads.fastq.gz: 400 single-end reads, 50nt length, containing sequence and quality information
- protocol.md: Text file containing experimental protocol with sections for steps, reagents, and QC
- trimmed.fastq: 400 adapter-trimmed reads derived from the original FASTQ file

### 2. Column Dictionary (Detailed)

**reference.fa**
- id: String, transcript identifier, use for mapping reference
- sequence: String, nucleotide sequence, use for read alignment
- length: Numeric, sequence length, use for coordinate validation

**reads.fastq.gz & trimmed.fastq**
- id: String, read identifier with UMI information, use for tracking reads
- sequence: String, nucleotide sequence, use for alignment and UMI extraction
- quality: String, Phred quality scores, use for QC filtering
- length: Numeric, read length, use for size distribution analysis
- avg_quality: Numeric, mean quality score, use for quality filtering

**protocol.md**
- line_num: Numeric, line number in protocol, use for reference
- type: String, section type (step/reagent/note), use for parsing
- level: Numeric, heading level, use for structure
- content: String, protocol text content, use for analysis
- raw: String, original markdown formatting, use for reference

### 3. Data Integrity & Quality
- All files present and readable
- FASTQ quality scores appear acceptable (no systematic degradation)
- Reference sequence is complete and properly formatted
- Protocol file contains complete experimental workflow
- No missing values in key fields
- Read IDs are unique within FASTQ files
- UMI information preserved in read headers

### 4. Sub-Problem Analysis: Data Applicability

**Sub-problem 1 (Incident A)**
- Requires: protocol.md
- Data sufficient for protocol analysis
- Focus on cleanup/purification steps

**Sub-problem 2 (Incident B)**
- Requires: protocol.md
- Data sufficient for identifying operator-dependent steps
- Review bead handling instructions

**Sub-problem 3 (Incident C)**
- Requires: protocol.md, reads.fastq.gz, reference.fa
- Data sufficient for fragment size and periodicity analysis
- Analyze length distribution and mapping patterns

**Sub-problem 4 (Incident D)**
- Requires: reads.fastq.gz, protocol.md
- Data sufficient for UMI analysis
- Extract and analyze UMI patterns

**Sub-problem 5 (Incident E)**
- Requires: protocol.md
- Data sufficient for oligo specification analysis
- Review adapter/ligation requirements

**Sub-problem 6 (Data Analysis)**
- Requires: all files
- Data sufficient for complete analysis
- Generate position-wise counts and QC metrics

### 5. Biological Context (from Data)
- Single transcript ribosome profiling experiment
- Contains UMI-based deduplication capability
- Expected footprint size ~28-34nt
- Coding sequence present in reference transcript
- Translation-specific features (3-nt periodicity) expected

### 6. Recommendations for Solver
- Key Keys: Use read IDs for tracking through pipeline
- Pitfalls: 
  - Verify UMI extraction before deduplication
  - Consider soft-clipping in position counting
  - Account for both strands in alignment
- Priority: Establish correct read processing workflow before detailed QC

### 7. Domain Knowledge Injection
- Ribosome footprints should show strong 3-nt periodicity
- UMI diversity should scale with library complexity
- Protected fragment size distribution should be narrow
- Adapter contamination produces characteristic patterns
- P-site offset typically 12-13nt from 5' end

### 8. Data Integration Strategy
Process reads.fastq.gz through adapter trimming to generate trimmed.fastq. Align trimmed reads to reference.fa sequence. Extract UMIs during processing and append to read names. Generate both raw and deduplicated position-wise counts. Integrate protocol information to validate each step. Expected final output includes position-wise counts for the single transcript with and without UMI deduplication.

### 9. Step-by-Step Analysis Workflow
1. Initial QC of raw reads
2. Extract UMIs and trim adapters
3. Align to reference transcript
4. Generate raw position-wise counts
5. Perform UMI-based deduplication
6. Generate deduplicated counts
7. Calculate QC metrics (length distribution, periodicity)
8. Compare raw vs deduplicated signals
9. Generate visualization and QC report
10. Validate against protocol specifications
11. Document all parameters and decisions
12. Prepare final counts files and summary report