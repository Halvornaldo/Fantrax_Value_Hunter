#!/usr/bin/env python
"""Debug script to test CSV import issue"""

import sys
import traceback

# Test 1: Check if the file can be read properly
print("=== Testing file reading ===")
try:
    with open('test_ffp.csv', 'rb') as f:
        raw_content = f.read()
        print(f"Raw content size: {len(raw_content)} bytes")
        
        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        for encoding in encodings:
            try:
                decoded = raw_content.decode(encoding)
                print(f"✓ {encoding}: Successfully decoded ({len(decoded)} chars)")
                lines = decoded.strip().split('\n')
                print(f"  Lines: {len(lines)}")
                
                # Check for Arsenal line
                for i, line in enumerate(lines):
                    if 'arsenal' in line.lower() and 'predicted lineup' in line.lower():
                        print(f"  Arsenal found at line {i+1}")
                        break
            except Exception as e:
                print(f"✗ {encoding}: {e}")
except Exception as e:
    print(f"Error reading file: {e}")
    traceback.print_exc()

print("\n=== Testing Flask-style file reading ===")
try:
    # Simulate Flask file upload
    class MockFile:
        def __init__(self, path):
            self.file = open(path, 'rb')
            self.filename = path
        
        def read(self):
            return self.file.read()
        
        def close(self):
            self.file.close()
    
    file = MockFile('test_ffp.csv')
    
    # Try to read like Flask does
    try:
        csv_content = file.read().decode('utf-8')
        lines = csv_content.strip().split('\n')
        print(f"✓ UTF-8 decode successful: {len(lines)} lines")
    except UnicodeDecodeError as e:
        print(f"✗ UTF-8 decode failed: {e}")
        
        # Try with error handling
        file = MockFile('test_ffp.csv')
        csv_content = file.read().decode('utf-8', errors='ignore')
        lines = csv_content.strip().split('\n')
        print(f"✓ UTF-8 with errors='ignore': {len(lines)} lines")
    
    file.close()
    
except Exception as e:
    print(f"Error in Flask simulation: {e}")
    traceback.print_exc()

print("\n=== Testing with Python CSV module ===")
try:
    import csv
    from io import StringIO
    
    with open('test_ffp.csv', 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()
        lines = content.strip().split('\n')
        
        # Parse header
        csv_reader = csv.reader(StringIO(lines[0]))
        header = next(csv_reader)
        print(f"Header columns: {len(header)}")
        print(f"First 3 columns: {header[:3]}")
        
        # Find Arsenal
        for i, line in enumerate(lines):
            if 'arsenal' in line.lower() and 'predicted lineup' in line.lower():
                csv_reader = csv.reader(StringIO(line))
                data = next(csv_reader)
                print(f"Arsenal line {i+1}: {len(data)} columns")
                print(f"First 5 values: {data[:5]}")
                break
                
except Exception as e:
    print(f"Error with CSV module: {e}")
    traceback.print_exc()