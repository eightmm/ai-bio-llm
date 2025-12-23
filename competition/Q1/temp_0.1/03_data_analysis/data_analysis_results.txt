### 1. Data Overview
- protocol.md: Text file containing the Ribo-seq experimental protocol with sections, steps, and instructions
- reference.fa: FASTA file containing a single transcript sequence (toy_gene) for alignment
- reads.fastq.gz: Compressed FASTQ file with 400 single-end reads, 50nt length, containing UMI and adapter sequences
- trimmed.fastq: Processed FASTQ file after adapter/UMI extraction, containing 400 cleaned reads ready for alignment

### 2. Column Dictionary (Detailed)

protocol.md:
- **line_num**: Numeric, Line number in protocol, Use for step reference
- **type**: String, Section type (header/step/note), Use for protocol structure
- **level**: Numeric, Heading/indentation level, Use for protocol hierarchy
- **content**: String, Protocol instruction text, Use for procedure details
- **raw**: String, Raw markdown text, Use for formatting reference

reference.fa:
- **id**: String, Transcript identifier (toy_gene), Use for alignment reference
- **sequence**: String, Nucleotide sequence, Use for read mapping
- **length**: Numeric, Sequence length, Use for coordinate validation

reads.fastq.gz:
- **id**: String, Read identifier with instrument/flow cell info, Use for tracking
- **sequence**: String, Raw read sequence with UMI/adapters, Use for processing
- **quality**: String, Base quality scores, Use for QC filtering
- **length**: Numeric, Read length (50nt), Use for size verification
- **avg_quality**: Numeric, Mean quality score, Use for read filtering

trimmed.fastq:
- **id**: String, Modified read ID with UMI info, Use for deduplication
- **sequence**: String, Cleaned read sequence, Use for alignment
- **quality**: String, Trimmed quality scores, Use for mapping QC
- **length**: Numeric, Post-trim length, Use for footprint size filtering
- **avg_quality**: Numeric, Post-trim mean quality, Use for QC

### 3. Data Integrity & Quality
- All files present and readable
- Reference sequence is complete and single-transcript
- FASTQ reads maintain paired ID/sequence/quality structure
- No missing or corrupted entries detected
- UMI sequences appear intact in read headers
- Quality scores within expected Illumina range

### 4. Sub-Problem Analysis: Data Applicability

1. Incident A (Messy libraries):
- Uses protocol.md for cleanup step analysis
- Sufficient for protocol forensics
- Focus on cleanup/purification steps

2. Incident B (PCR variability):
- Uses protocol.md for operator-sensitive steps
- Sufficient for identifying critical points
- Analyze bead handling instructions

3. Incident C (Footprint size):
- Uses protocol.md for digestion/size selection
- Uses reads.fastq.gz for length distribution
- Sufficient for diagnosis

4. Incident D (UMI issues):
- Uses reads.fastq.gz for UMI extraction
- Uses protocol.md for adapter structure
- Sufficient for UMI analysis

5. Incident E (Ligation failure):
- Uses protocol.md for oligo specifications
- Uses reads.fastq.gz for adapter presence
- Sufficient for diagnosis

6. Pilot Analysis:
- Uses all files for complete workflow
- Sufficient for basic Ribo-seq metrics
- Enables footprint counting and QC

### 5. Biological Context (from Data)
- Single transcript experimental system
- Ribosome footprint data with UMI deduplication
- Short read (50nt) Illumina sequencing
- Expected footprint size ~28-34nt
- Single-end read structure

### 6. Recommendations for Solver
- Key Keys: Use read IDs with UMI tags for deduplication
- Pitfalls: Avoid mixing raw/trimmed reads in analysis
- Priority: UMI extraction and adapter removal critical first step

### 7. Domain Knowledge Injection
- Ribosome footprints should show 3-nucleotide periodicity
- UMI complexity should reflect library complexity
- Adapter dimer products typically 40-50bp
- Expected mapping primarily to coding regions
- P-site offset typically 12nt from 5' end

### 8. Data Integration Strategy
Process reads.fastq.gz through UMI extraction and adapter trimming to create cleaned reads. Align cleaned reads to reference.fa using appropriate short-read aligner. Generate raw counts using 5' end positions. Perform UMI-aware deduplication using read start positions and UMI sequences. Create parallel count tables for raw and deduplicated data.

### 9. Step-by-Step Analysis Workflow
1. Extract UMIs and trim adapters from reads.fastq.gz
2. Perform quality filtering on trimmed reads
3. Align processed reads to reference.fa
4. Generate raw 5' end position counts
5. Perform UMI-based deduplication
6. Create deduplicated position counts
7. Generate QC metrics (length distribution, mapping stats)
8. Produce visualization of footprint positions
9. Compare raw vs deduplicated counts
10. Generate comprehensive HTML report with all metrics