#!/usr/bin/env python
"""
Test script to verify snapshotter functionality.
"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend', 'evidence'))
from snapshot import snapshotter

def test_snapshotter():
    print("Testing snapshotter...")

    test_url = "https://example.com"
    result = snapshotter.snapshot(test_url)
    print(f"Snapshot result for {test_url}: {result}")

    # Test is_snapshot_available
    if result:
        available = snapshotter.is_snapshot_available(test_url, result)
        print(f"Is snapshot available? {available}")

    return result is not None

if __name__ == "__main__":
    success = test_snapshotter()
    print(f"Test {'PASSED' if success else 'FAILED'}")
    exit(0 if success else 1)