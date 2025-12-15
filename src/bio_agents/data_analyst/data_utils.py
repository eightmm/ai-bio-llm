"""
Data Utils Module
Handles file resolution, loading, and parsing operations.
Combines functionality of former FileResolver and DataLoader.
"""

import os
import re
import json
import logging
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple, Any

logger = logging.getLogger(__name__)


class FileResolver:
    """Resolves DB_list references to actual file paths"""

    def __init__(self, data_dir: Union[str, Path]):
        """
        Initialize FileResolver

        Args:
            data_dir: Root directory containing data files
        """
        self.data_dir = Path(data_dir)
        if not self.data_dir.exists():
            # If default data dir doesn't exist, try to find a data folder
            # but raising error is safer if config is expected to be correct
            logger.warning(f"Data directory does not exist: {data_dir}")

        # Build file index for fast lookup
        self._file_index = self._build_file_index()

    def _build_file_index(self) -> Dict[str, Any]:
        """Build index of all data files for fast lookup"""
        index = {
            'by_name': {},      # filename -> [paths]
            'by_folder': {},    # folder_name -> [paths]
            'by_pattern': []    # all files for pattern matching
        }

        supported_extensions = {'.csv', '.tsv', '.txt', '.tab', '.xlsx', '.xls', '.json', '.parquet'}

        if not self.data_dir.exists():
            return index

        for root, dirs, files in os.walk(self.data_dir):
            root_path = Path(root)
            folder_name = root_path.name

            for filename in files:
                file_path = root_path / filename
                ext = file_path.suffix.lower()

                if ext in supported_extensions:
                    # Index by filename
                    name_lower = filename.lower()
                    if name_lower not in index['by_name']:
                        index['by_name'][name_lower] = []
                    index['by_name'][name_lower].append(file_path)

                    # Index by folder
                    if folder_name not in index['by_folder']:
                        index['by_folder'][folder_name] = []
                    index['by_folder'][folder_name].append(file_path)

                    # Add to pattern list
                    index['by_pattern'].append(file_path)

        logger.info(f"Built file index: {len(index['by_pattern'])} files indexed")
        return index

    def resolve(self, db_list: str) -> List[Dict[str, str]]:
        """
        Resolve DB_list string to actual file paths

        Args:
            db_list: DB_list string from Brain module
                     Examples: "genelist.csv", "Q1 features", "Q1 features, genelist.csv"

        Returns:
            List of dicts with file information:
            [{"path": "/full/path", "name": "filename", "match_type": "exact|folder|pattern"}]
        """
        if not db_list or not db_list.strip():
            return []

        results = []

        # Split by comma for multiple references
        references = [ref.strip() for ref in db_list.split(',')]

        for ref in references:
            ref = ref.strip()
            if not ref:
                continue

            # Try different resolution strategies
            resolved = self._resolve_single(ref)
            results.extend(resolved)

        # Remove duplicates while preserving order
        seen = set()
        unique_results = []
        for r in results:
            if r['path'] not in seen:
                seen.add(r['path'])
                unique_results.append(r)

        logger.info(f"Resolved '{db_list}' to {len(unique_results)} files")
        return unique_results

    def _resolve_single(self, ref: str) -> List[Dict[str, str]]:
        """Resolve a single reference string"""
        results = []

        # Strategy 1: Exact filename match
        exact_matches = self._match_exact(ref)
        if exact_matches:
            results.extend(exact_matches)
            return results

        # Strategy 2: Folder/pattern match (e.g., "Q1 features" -> Q1.features folder)
        folder_matches = self._match_folder(ref)
        if folder_matches:
            results.extend(folder_matches)
            return results

        # Strategy 3: Fuzzy pattern match
        pattern_matches = self._match_pattern(ref)
        if pattern_matches:
            results.extend(pattern_matches)
            return results

        logger.warning(f"Could not resolve reference: {ref}")
        return results

    def _match_exact(self, ref: str) -> List[Dict[str, str]]:
        """Match exact filename"""
        ref_lower = ref.lower()
        results = []

        # Direct lookup
        if ref_lower in self._file_index['by_name']:
            for path in self._file_index['by_name'][ref_lower]:
                results.append({
                    'path': str(path),
                    'name': path.name,
                    'match_type': 'exact'
                })

        # Try with common prefixes (Q1., Q5., etc.)
        if not results:
            for prefix in ['Q1.', 'Q2.', 'Q3.', 'Q4.', 'Q5.']:
                prefixed = f"{prefix}{ref}".lower()
                if prefixed in self._file_index['by_name']:
                    for path in self._file_index['by_name'][prefixed]:
                        results.append({
                            'path': str(path),
                            'name': path.name,
                            'match_type': 'exact_prefixed'
                        })

        return results

    def _match_folder(self, ref: str) -> List[Dict[str, str]]:
        """Match folder name pattern"""
        results = []

        # Normalize reference: "Q1 features" -> patterns like "Q1.features", "Q1_features"
        ref_normalized = ref.lower().replace(' ', '.').replace('_', '.')

        for folder_name, paths in self._file_index['by_folder'].items():
            folder_normalized = folder_name.lower().replace(' ', '.').replace('_', '.')

            # Check if folder matches
            if ref_normalized in folder_normalized or folder_normalized in ref_normalized:
                for path in paths:
                    results.append({
                        'path': str(path),
                        'name': path.name,
                        'match_type': 'folder'
                    })

        return results

    def _match_pattern(self, ref: str) -> List[Dict[str, str]]:
        """Match using fuzzy pattern"""
        results = []

        # Extract keywords from reference
        keywords = re.findall(r'\w+', ref.lower())
        if not keywords:
            return []

        for path in self._file_index['by_pattern']:
            path_str = str(path).lower()

            # Check if all keywords are in the path
            if all(kw in path_str for kw in keywords):
                results.append({
                    'path': str(path),
                    'name': path.name,
                    'match_type': 'pattern'
                })

        return results
    
    def refresh_index(self) -> None:
        """Refresh the file index (call after adding new files)"""
        self._file_index = self._build_file_index()


class DataLoader:
    """Handles loading and parsing of various data file formats"""

    SUPPORTED_FORMATS = {
        '.csv': 'csv',
        '.tsv': 'tsv',
        '.txt': 'text',
        '.tab': 'tsv',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.json': 'json',
        '.parquet': 'parquet'
    }

    # Encodings to try in order
    ENCODINGS = ['utf-8-sig', 'utf-8', 'latin1', 'cp949', 'euc-kr']

    def __init__(self, max_sample_rows: int = 1000):
        """
        Initialize DataLoader

        Args:
            max_sample_rows: Maximum rows to load for sampling
        """
        self.max_sample_rows = max_sample_rows

    def load_file(
        self,
        file_path: Union[str, Path],
        sample: bool = True,
        n_rows: Optional[int] = None
    ) -> Tuple[pd.DataFrame, Dict]:
        """
        Load a data file into DataFrame

        Args:
            file_path: Path to the file
            sample: Whether to sample (default True for large files)
            n_rows: Number of rows to load (None = all or sample)

        Returns:
            Tuple of (DataFrame, metadata dict)
        """
        file_path = Path(file_path)
        ext = file_path.suffix.lower()

        if ext not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported file format: {ext}")

        format_type = self.SUPPORTED_FORMATS[ext]

        logger.info(f"Loading file: {file_path} (format: {format_type})")

        # Get file size
        file_size = file_path.stat().st_size

        # Determine rows to load
        if n_rows is None and sample:
            n_rows = self.max_sample_rows

        # Load based on format
        try:
            if format_type == 'csv':
                df, encoding = self._load_csv(file_path, n_rows)
            elif format_type == 'tsv':
                df, encoding = self._load_tsv(file_path, n_rows)
            elif format_type == 'text':
                df, encoding = self._load_text(file_path, n_rows)
            elif format_type == 'excel':
                df = self._load_excel(file_path, n_rows)
                encoding = 'binary'
            elif format_type == 'json':
                df = self._load_json(file_path, n_rows)
                encoding = 'utf-8'
            elif format_type == 'parquet':
                df = self._load_parquet(file_path, n_rows)
                encoding = 'binary'
            else:
                raise ValueError(f"Unknown format type: {format_type}")

            # Count total rows (efficiently)
            total_rows = self._count_total_rows(file_path, format_type)

            metadata = {
                'file_path': str(file_path),
                'file_name': file_path.name,
                'format': format_type,
                'encoding': encoding if 'encoding' in dir() else 'unknown',
                'file_size_bytes': file_size,
                'file_size_mb': round(file_size / 1024 / 1024, 2),
                'total_rows': total_rows,
                'loaded_rows': len(df),
                'columns': self._get_column_info(df),
                'is_sampled': len(df) < total_rows if total_rows else False
            }

            logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
            return df, metadata

        except Exception as e:
            logger.error(f"Error loading file {file_path}: {str(e)}")
            raise

    def _load_csv(self, file_path: Path, n_rows: Optional[int]) -> Tuple[pd.DataFrame, str]:
        """Load CSV file with encoding detection"""
        for encoding in self.ENCODINGS:
            try:
                df = pd.read_csv(
                    file_path,
                    encoding=encoding,
                    nrows=n_rows,
                    low_memory=False
                )
                return df, encoding
            except UnicodeDecodeError:
                continue
            except Exception as e:
                # Try next encoding for encoding-related errors
                if 'codec' in str(e).lower():
                    continue
                raise

        raise ValueError(f"Could not decode {file_path} with supported encodings")

    def _load_tsv(self, file_path: Path, n_rows: Optional[int]) -> Tuple[pd.DataFrame, str]:
        """Load TSV file with encoding detection"""
        for encoding in self.ENCODINGS:
            try:
                df = pd.read_csv(
                    file_path,
                    sep='\t',
                    encoding=encoding,
                    nrows=n_rows,
                    low_memory=False
                )
                return df, encoding
            except UnicodeDecodeError:
                continue
            except Exception as e:
                if 'codec' in str(e).lower():
                    continue
                raise

        raise ValueError(f"Could not decode {file_path} with supported encodings")

    def _load_text(self, file_path: Path, n_rows: Optional[int]) -> Tuple[pd.DataFrame, str]:
        """Load text file - try TSV first, then CSV"""
        # First try TSV
        try:
            return self._load_tsv(file_path, n_rows)
        except Exception:
            pass

        # Then try CSV
        try:
            return self._load_csv(file_path, n_rows)
        except Exception:
            pass

        # Fallback: load as single column
        for encoding in self.ENCODINGS:
            try:
                with open(file_path, 'r', encoding=encoding) as f:
                    lines = []
                    for i, line in enumerate(f):
                        if n_rows and i >= n_rows:
                            break
                        lines.append(line.strip())
                df = pd.DataFrame({'content': lines})
                return df, encoding
            except UnicodeDecodeError:
                continue

        raise ValueError(f"Could not read text file {file_path}")

    def _load_excel(self, file_path: Path, n_rows: Optional[int]) -> pd.DataFrame:
        """Load Excel file"""
        df = pd.read_excel(file_path, nrows=n_rows)
        return df

    def _load_json(self, file_path: Path, n_rows: Optional[int]) -> pd.DataFrame:
        """Load JSON file"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # Handle different JSON structures
        if isinstance(data, list):
            df = pd.DataFrame(data)
        elif isinstance(data, dict):
            # Try to find the data array
            if any(isinstance(v, list) for v in data.values()):
                for key, value in data.items():
                    if isinstance(value, list) and len(value) > 0:
                        df = pd.DataFrame(value)
                        break
            else:
                df = pd.DataFrame([data])
        else:
            df = pd.DataFrame({'value': [data]})

        if n_rows:
            df = df.head(n_rows)

        return df

    def _load_parquet(self, file_path: Path, n_rows: Optional[int]) -> pd.DataFrame:
        """Load Parquet file"""
        if n_rows:
            df = pd.read_parquet(file_path).head(n_rows)
        else:
            df = pd.read_parquet(file_path)
        return df

    def _count_total_rows(self, file_path: Path, format_type: str) -> int:
        """Efficiently count total rows in file"""
        try:
            if format_type in ['csv', 'tsv', 'text']:
                if os.path.exists(file_path):
                     # Count lines efficiently
                    try:
                        with open(file_path, 'rb') as f:
                            return sum(1 for _ in f) - 1  # Subtract header
                    except Exception:
                         return -1 # Fallback
            elif format_type == 'excel':
                 # Expensive to count without loading
                 return -1
            elif format_type == 'parquet':
                try:
                    import pyarrow.parquet as pq
                    return pq.read_metadata(file_path).num_rows
                except ImportError:
                    return -1
            elif format_type == 'json':
                 # Must load to count
                 return -1
        except Exception as e:
            logger.warning(f"Could not count rows: {e}")
            return -1

        return -1

    def get_sample_data(
        self,
        df: pd.DataFrame,
        n_rows: int = 5
    ) -> List[List]:
        """
        Get sample data as list of lists for JSON output
        """
        sample_df = df.head(n_rows)
        return sample_df.values.tolist()

    def _get_column_info(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generate detailed column information matching DataExecutor expectations
        """
        info = []
        for col in df.columns:
            try:
                series = df[col]
                # specific handling for numpy types to ensure json serializability if needed later
                dtype = str(series.dtype)
                
                col_info = {
                    'name': str(col),
                    'dtype': dtype,
                    'non_null_count': int(series.count()),
                    'unique_count': int(series.nunique()),
                    'sample_values': series.dropna().unique()[:5].tolist()
                }
                info.append(col_info)
            except Exception as e:
                # Fallback for any column processing errors
                info.append({
                    'name': str(col),
                    'dtype': 'unknown',
                    'non_null_count': 0,
                    'unique_count': 0,
                    'sample_values': []
                })
        return info
