# SYSTEM
You are an expert bioinformatics data analyst. Generate clean, working Python code.

# USER
You are an expert bioinformatics data analyst.
Generate complete, executable Python code (Pandas/SciPy based) to analyze the provided data files.

## Sub-Problem Context
**Goal**: {sub_problem_title}
**Description**: {sub_problem_description}
{plan_context}

## Data Context
**(File is already loaded as `df`)**
- **Filename**: `{file_name}`
- **Rows**: {total_rows}
- **Columns**:
{columns}

**Column Sampling**:
{column_info}

**Sample Data**:
{sample_data}

## Analysis Requirements
Your code must:
1.  **Analyze**: Perform statistical summaries, checks, or transformations relevant to the Sub-Problem.
2.  **Inspect**: Check for missing values or key integrity.
3.  **Summarize**: Create a JSON-serializable `result` dictionary.

The `result` dictionary MUST strictly follow this structure:
```python
result = {{
    "file": "{file_name}",
    "type": "gene_expression|metadata|gene_list|other",
    "rows": 12345,
    "columns": [
        {{
            "name": "col_name_1",
            "type": "float64",
            "bio": "Log2 Normalized Expression",
            "use": "Primary metric for differential analysis"
        }},
        ... (top 5-10 key columns)
    ],
    "keys": ["key_column_name"],
    "summary": "Brief biological summary of findings (e.g., '150 significant DE key genes found')",
    "stats": {{ "mean_expression": 12.5, "missing_values": 0, ... }},
    "integration": {{
        "join_key": "suggested_join_key",
        "strategy": "how to join this with other files"
    }}
}}
```

**CRITICAL RULES**:
- Assume `df` matches the sample data structure.
- **Do NOT** load the file again. It is already loaded as `df`.
- Avoid defining helper functions that reference `df` from outer scope. Prefer direct, top-level code that reads/writes `result`.
- If you absolutely must reference the original file location, use `file_path` (provided) rather than hardcoding filenames.
- **Do NOT** print anything.
- Use only standard libraries (pandas as pd, numpy as np).
- Handle potential NaN/null values gracefully.
- Variable `result` MUST be defined at the end.

## Example Output Structure
```python
# Analysis logic here...
stats = df.describe().to_dict()

result = {{
    "file": "example.csv",
    "type": "gene_list",
    "rows": 100,
    "columns": [
        {{
            "name": "gene_name",
            "type": "object",
            "bio": "Official gene symbol",
            "use": "Identifier"
        }}
    ],
    "keys": ["gene_name"],
    "summary": "100 genes identified as relevant markers",
    "stats": stats,
    "integration": {{ "join_key": "gene_name", "strategy": "inner" }}
}}
```

Output ONLY Python code, no explanations.

# FIX_USER
Your previous code raised an error. Please fix it.

Previous Code:
```python
{previous_code}
```

Error:
{error_message}

File Info:
- Filename: {file_name}
- Columns: {column_info}

Common issues to check:
1. Column name typos - use exact column names from the list above
2. Data type mismatches - check if numeric operations are on numeric columns
3. Missing values - handle NaN properly
4. Index issues - ensure proper DataFrame indexing

Requirements:
- The code must assign a dictionary to a variable named `result`
- The result dict must contain: file, type, rows, columns, keys, summary, stats, integration
- Use only pandas (pd) and numpy (np) - they are pre-imported

Output ONLY the corrected Python code, no explanations.
