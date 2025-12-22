"""
Test script for DataLoader functionality
Tests various file formats including FASTA, FASTQ, CSV, etc.
"""

import sys
from pathlib import Path
from data_utils import DataLoader, FileResolver

def test_dataloader():
    """Test DataLoader with various file formats"""
    
    # Initialize
    data_dir = Path("../../../problems/problem_1")  # Adjust path as needed
    resolver = FileResolver(data_dir)
    loader = DataLoader(max_sample_rows=10)  # Load only 10 rows for testing
    
    print("=" * 80)
    print("DataLoader Test Suite")
    print("=" * 80)
    print(f"Data directory: {data_dir.absolute()}")
    print()
    
    # Test 1: List all indexed files
    print("📁 Indexed files:")
    print("-" * 80)
    file_count = len(resolver._file_index['by_pattern'])
    print(f"Total files indexed: {file_count}")
    for i, file_path in enumerate(resolver._file_index['by_pattern'][:5], 1):
        print(f"  {i}. {file_path.name}")
    if file_count > 5:
        print(f"  ... and {file_count - 5} more files")
    print()
    
    # Test 2: File resolution
    print("🔍 Testing file resolution:")
    print("-" * 80)
    test_queries = [
        "genelist",
        "features",
        "*.csv",
        "Q1",
    ]
    
    for query in test_queries:
        print(f"Query: '{query}'")
        resolved = resolver.resolve(query)
        if resolved:
            for file_info in resolved[:3]:  # Show first 3 matches
                print(f"  ✓ Found: {file_info['name']} ({file_info['match_type']})")
        else:
            print(f"  ✗ No files found")
        print()
    
    # Test 3: Load different file formats
    print("📊 Testing file loading:")
    print("-" * 80)
    
    # Find files to test
    test_files = resolver._file_index['by_pattern'][:5]
    
    for file_path in test_files:
        ext = DataLoader._get_effective_ext(file_path)
        format_type = loader.SUPPORTED_FORMATS.get(ext, 'unknown')
        
        print(f"\nFile: {file_path.name}")
        print(f"  Extension: {ext}")
        print(f"  Format: {format_type}")
        
        if format_type == 'unknown':
            print(f"  ⚠️  Unsupported format")
            continue
        
        try:
            df, metadata = loader.load_file(file_path, sample=True, n_rows=5)
            
            print(f"  ✓ Loaded successfully")
            print(f"    - Total rows: {metadata['total_rows']}")
            print(f"    - Loaded rows: {metadata['loaded_rows']}")
            print(f"    - Columns: {len(metadata['columns'])}")
            print(f"    - File size: {metadata['file_size_mb']} MB")
            print(f"    - Encoding: {metadata['encoding']}")
            
            # Show column info
            if metadata['columns']:
                print(f"    - Column names: {[col['name'] for col in metadata['columns'][:5]]}")
            
            # Show sample data for small datasets
            if len(df) <= 3:
                print(f"    - Sample data:")
                print(df.to_string(index=False).replace('\n', '\n      '))
            
        except Exception as e:
            print(f"  ✗ Error: {type(e).__name__}: {e}")
    
    print()
    print("=" * 80)
    print("Test completed!")
    print("=" * 80)


def test_specific_format(file_pattern: str):
    """Test loading a specific file pattern"""
    data_dir = Path("../../../problems")
    resolver = FileResolver(data_dir)
    loader = DataLoader(max_sample_rows=10)
    
    print(f"\n🔍 Testing specific pattern: '{file_pattern}'")
    print("-" * 80)
    
    resolved = resolver.resolve(file_pattern)
    
    if not resolved:
        print(f"❌ No files found matching '{file_pattern}'")
        return
    
    for file_info in resolved:
        print(f"\n📄 {file_info['name']}")
        print(f"   Path: {file_info['path']}")
        print(f"   Match type: {file_info['match_type']}")
        
        try:
            df, metadata = loader.load_file(file_info['path'], sample=True, n_rows=5)
            
            print(f"   ✓ Loaded: {metadata['loaded_rows']} rows, {len(df.columns)} columns")
            print(f"   Format: {metadata['format']}")
            print(f"   Columns: {list(df.columns)}")
            
            if len(df) > 0:
                print(f"\n   First few rows:")
                print(df.head(3).to_string(index=False).replace('\n', '\n   '))
            
        except Exception as e:
            print(f"   ✗ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific file pattern
        pattern = sys.argv[1]
        test_specific_format(pattern)
    else:
        # Run full test suite
        test_dataloader()
