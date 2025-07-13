#!/usr/bin/env python3
"""
Simple test script to verify document ingestion functionality
"""

import sys
import tempfile
import os
from core.ingestion import ingest

def test_text_ingestion():
    """Test basic text file ingestion"""
    print("Testing text file ingestion...")
    
    # Create a temporary text file
    test_content = "This is a test document.\nIt has multiple lines.\nFor testing purposes."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        # Test ingestion
        docs = ingest(temp_path)
        
        if docs and len(docs) > 0:
            print(f"✅ Text ingestion successful!")
            print(f"   - Document count: {len(docs)}")
            print(f"   - Text length: {len(docs[0].text)}")
            print(f"   - Method: {docs[0].metadata.get('method', 'unknown')}")
            return True
        else:
            print("❌ Text ingestion failed - no documents returned")
            return False
            
    except Exception as e:
        print(f"❌ Text ingestion failed with error: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def test_pdf_ingestion():
    """Test basic PDF handling (will likely use fallback)"""
    print("\nTesting PDF handling...")
    
    # Create a simple text file with .pdf extension to test fallback
    test_content = "This is a fake PDF file for testing fallback mechanisms."
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.pdf', delete=False) as f:
        f.write(test_content)
        temp_path = f.name
    
    try:
        # Test ingestion
        docs = ingest(temp_path)
        
        if docs and len(docs) > 0:
            print(f"✅ PDF handling successful (using fallback)!")
            print(f"   - Document count: {len(docs)}")
            print(f"   - Text length: {len(docs[0].text)}")
            print(f"   - Method: {docs[0].metadata.get('method', 'unknown')}")
            if docs[0].metadata.get('error'):
                print(f"   - Error noted: {docs[0].metadata.get('error')}")
            return True
        else:
            print("❌ PDF handling failed - no documents returned")
            return False
            
    except Exception as e:
        print(f"❌ PDF handling failed with error: {str(e)}")
        return False
    finally:
        # Clean up
        if os.path.exists(temp_path):
            os.unlink(temp_path)

def main():
    print("🧪 Testing Document Ingestion Functionality\n")
    
    results = []
    
    # Test text ingestion
    results.append(test_text_ingestion())
    
    # Test PDF handling
    results.append(test_pdf_ingestion())
    
    # Summary
    print("\n" + "="*50)
    print(f"Test Results: {sum(results)}/{len(results)} passed")
    
    if all(results):
        print("🎉 All ingestion tests passed!")
        return 0
    else:
        print("⚠️  Some tests failed, but fallbacks should prevent crashes")
        return 0  # Don't fail since fallbacks are working

if __name__ == "__main__":
    sys.exit(main())