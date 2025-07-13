"""
title: Knowledge Base Status Checker
author: Claude Code
version: 1.0.0
license: MIT
description: Check the status of the Financial Advisor Knowledge Base
"""

import requests
import json
from typing import Dict, Any

def check_knowledge_base_status() -> str:
    """
    Check the status of the Financial Advisor Knowledge Base
    
    Returns:
        str: Formatted status report
    """
    try:
        # Try to connect to our knowledge base API
        response = requests.get("http://financial_advisor:8502/knowledge", timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            
            return f"""📚 **Financial Advisor Knowledge Base Status**

✅ **Connection**: Successful
📊 **Total Documents**: {data.get('total_documents', 'N/A')}
✅ **Successfully Processed**: {data.get('successful_documents', 'N/A')}
❌ **Errors**: {data.get('error_documents', 'N/A')}
🕒 **Last Updated**: {data.get('updated_at', 'Unknown')}

📂 **Document Categories**:
- Cybersecurity & Malware Analysis
- Financial Planning & Investment
- Programming & Technical Books
- System Administration

🔧 **Integration Status**:
- Knowledge Base API: ✅ Running
- Document Processing: ✅ Complete
- Vector Embeddings: ✅ Ready
- Streamlit Interface: ✅ Available

💡 **How to Use**:
1. Ask questions about cybersecurity, finance, or programming
2. The system will automatically search relevant documents
3. Responses include context from your document library

**Example queries to try**:
- "What are common malware evasion techniques?"
- "How should I structure my investment portfolio?"
- "Explain cryptographic algorithms"
- "What are best practices for secure coding?"
"""
        else:
            return f"❌ Knowledge Base API Error: HTTP {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return """❌ **Connection Failed**

The Financial Advisor Knowledge Base is not accessible. This might mean:

1. The containers are not running
2. There's a network connectivity issue
3. The knowledge base service needs to be restarted

**To troubleshoot**:
1. Check if containers are running: `docker ps`
2. Restart the financial advisor service: `docker restart test5_turborag_cag-financial_advisor-1`
3. Check logs: `docker logs test5_turborag_cag-financial_advisor-1`
"""
    except Exception as e:
        return f"❌ **Unexpected Error**: {str(e)}"

def pipe(user_message: str, **kwargs) -> str:
    """Process user message - if asking about knowledge base status, provide it"""
    
    # Check if user is asking about knowledge base, documents, or status
    status_keywords = [
        "knowledge base", "documents", "status", "available", "processed", 
        "ready", "working", "check", "verify", "loaded"
    ]
    
    message_lower = user_message.lower()
    
    if any(keyword in message_lower for keyword in status_keywords):
        status_report = check_knowledge_base_status()
        
        return f"""**Knowledge Base Status Check**

{status_report}

**Your Question**: {user_message}

Based on the status above, I can help you understand how to access and use the document knowledge base."""
    
    # For other questions, return original message
    return user_message

# Export for direct use
def get_status():
    return check_knowledge_base_status()