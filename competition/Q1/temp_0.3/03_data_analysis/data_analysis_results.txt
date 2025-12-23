### 1. Data Overview
- protocol.md: A structured protocol document with line numbers, content type, hierarchical level, and content text. Contains experimental protocol details.
- reference.fa: Single transcript FASTA file with 1 sequence record containing ID, sequence, and length information.
- reads.fastq.gz: Raw sequencing data with 400 reads, containing standard FASTQ format (ID, sequence, quality scores, length metrics).
- trimmed.fastq: Processed version of reads with 400 entries, including original FASTQ fields plus extracted UMI sequences.

### 2. Column Dictionary (Detailed)

protocol.md:
- **line_num**: Numeric, Line number in protocol, Use for reference tracking
- **type**: String, Section type (header/step/note), Use for protocol structure parsing
- **level**: Numeric, Hierarchical depth, Use for protocol organization
- **content**: String, Protocol step text, Use for procedure analysis
- **raw**: String, Original markdown formatting, Use for display formatting

reference.fa:
- **id**: String, Transcript identifier, Use for sequence mapping
- **sequence**: String, Nucleotide sequence, Use for read alignment
- **length**: Numeric, Sequence length, Use for coordinate validation

reads.fastq.gz:
- **id**: String, Read identifier, Use for tracking reads
- **sequence**: String, Raw read sequence, Use for alignment/UMI extraction
- **quality**: String, Base quality scores, Use for QC filtering
- **length**: Numeric, Read length, Use for size distribution analysis
- **avg_quality**: Numeric, Mean quality score, Use for quality filtering

trimmed.fastq:
- **id**: String, Read identifier, Use for read tracking
- **sequence**: String, Processed read sequence, Use for alignment
- **quality**: String, Base quality scores, Use for QC
- **length**: Numeric, Trimmed read length, Use for size filtering
- **avg_quality**: Numeric, Mean quality score, Use for quality filtering
- **umi**: String, Extracted UMI sequence, Use for deduplication

### 3. Data Integrity & Quality
- All files are complete with no missing values
- Read IDs are unique within FASTQ files
- Protocol content appears well-structured with consistent formatting
- Reference sequence is complete and properly formatted
- UMI extraction appears successful with valid sequences

### 4. Sub-Problem Analysis: Data Applicability

1. Incident A (Library Quality):
- Uses: protocol.md
- Sufficient: Yes, protocol details available for analysis
- Strategy: Review cleanup/precipitation steps

2. Incident B (PCR Success):
- Uses: protocol.md
- Sufficient: Yes, protocol details available
- Strategy: Analyze bead cleanup steps

3. Incident C (Fragment Size):
- Uses: protocol.md, reads.fastq.gz
- Sufficient: Yes, can analyze size distributions
- Strategy: Examine nuclease digestion protocol and read lengths

4. Incident D (UMI Issues):
- Uses: protocol.md, reads.fastq.gz, trimmed.fastq
- Sufficient: Yes, UMI data available
- Strategy: Analyze UMI diversity and extraction accuracy

5. Incident E (Ligation):
- Uses: protocol.md, reads.fastq.gz
- Sufficient: Yes, can analyze adapter presence
- Strategy: Review ligation chemistry and read starts

6. Pilot Analysis:
- Uses: All files
- Sufficient: Yes, complete dataset available
- Strategy: Full pipeline from FASTQ to position counts

### 5. Biological Context (from Data)
- Single transcript ribosome profiling experiment
- Expected footprint size range: 28-34 nucleotides
- UMI-based deduplication system
- Coding sequence analysis capability
- Single-end 50nt sequencing format

### 6. Recommendations for Solver
- Key Keys: Use read IDs for tracking through pipeline
- Pitfalls: Ensure correct UMI extraction before trimming
- Priority: Validate read structure and UMI extraction first

### 7. Domain Knowledge Injection
- Ribosome footprint characteristics (28-34nt protected fragments)
- 3-nucleotide periodicity expectations in coding regions
- UMI complexity requirements (4^N unique sequences)
- Library size distribution patterns
- PCR duplication rates in Ribo-seq

### 8. Data Integration Strategy
Process reads.fastq.gz through UMI extraction to create trimmed.fastq, then align to reference.fa. Track read positions and UMIs for deduplication. Maintain read ID relationships throughout processing. Expect ~400 initial reads with some loss during QC and alignment. Join protocol steps with experimental observations using section numbers.

### 9. Step-by-Step Analysis Workflow
1. Protocol Analysis:
- Parse protocol.md for critical steps
- Map to incident reports
- Identify potential failure points

2. Read Processing:
- Extract UMIs from reads.fastq.gz
- Trim adapters
- Quality filter
- Generate length distributions

3. Alignment:
- Map to reference.fa
- Calculate 5' positions
- Track UMI associations

4. Position Counting:
- Generate raw counts
- Perform UMI-based deduplication
- Create position-wise counts

5. QC Analysis:
- Length distribution plots
- UMI complexity analysis
- Periodicity calculation
- Coverage visualization

6. Report Generation:
- Combine all metrics
- Create visualization plots
- Write interpretations
- List follow-up recommendations