"""
title: Financial Advisor Knowledge Base
author: Claude Code
author_url: https://claude.ai/code
funding_url: https://github.com/anthropics/claude-code
version: 1.0.0
license: MIT
"""

import requests
import json
from typing import Dict, Any, Optional
from pydantic import BaseModel

class Tools:
    def __init__(self):
        # URL to our Financial Advisor knowledge base API
        self.knowledge_base_url = "http://financial_advisor:8502"
    
    def search_financial_knowledge(self, query: str, limit: int = 3) -> str:
        """
        Search the Financial Advisor knowledge base for relevant information.
        
        Args:
            query (str): The search query
            limit (int): Maximum number of results to return (default: 3)
            
        Returns:
            str: Formatted search results or error message
        """
        try:
            response = requests.get(
                f"{self.knowledge_base_url}/search",
                params={"query": query, "limit": limit},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])
                
                if not results:
                    return "No relevant information found in the Financial Advisor knowledge base."
                
                # Format the results
                formatted_results = []
                for i, result in enumerate(results, 1):
                    content = result.get("content", "")[:500]  # Limit content length
                    score = result.get("score", 0.0)
                    formatted_results.append(f"**Result {i}** (Score: {score:.3f}):\n{content}...")
                
                return f"**Financial Advisor Knowledge Base Search Results for: '{query}'**\n\n" + "\n\n".join(formatted_results)
            
            else:
                return f"Error searching knowledge base: HTTP {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"Connection error to Financial Advisor knowledge base: {str(e)}"
        except Exception as e:
            return f"Error searching Financial Advisor knowledge base: {str(e)}"
    
    def get_knowledge_base_info(self) -> str:
        """
        Get information about the Financial Advisor knowledge base.
        
        Returns:
            str: Knowledge base statistics and information
        """
        try:
            response = requests.get(f"{self.knowledge_base_url}/knowledge", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                
                return f"""**Financial Advisor Knowledge Base Information:**

📚 **Name:** {data.get('name', 'Unknown')}
📝 **Description:** {data.get('description', 'No description')}
📊 **Total Documents:** {data.get('total_documents', 0)}
✅ **Successfully Processed:** {data.get('successful_documents', 0)}
❌ **Errors:** {data.get('error_documents', 0)}
🕒 **Last Updated:** {data.get('updated_at', 'Unknown')}

The knowledge base contains cybersecurity and financial documents that have been processed and embedded for search."""
            
            else:
                return f"Error getting knowledge base info: HTTP {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"Connection error to Financial Advisor knowledge base: {str(e)}"
        except Exception as e:
            return f"Error getting knowledge base info: {str(e)}"
    
    def refresh_knowledge_base(self) -> str:
        """
        Refresh the knowledge base by scanning for new documents.
        
        Returns:
            str: Results of the refresh operation
        """
        try:
            response = requests.post(f"{self.knowledge_base_url}/refresh", timeout=30)
            
            if response.status_code == 200:
                data = response.json()
                results = data.get("results", {})
                
                return f"""**Knowledge Base Refresh Complete:**

📁 **Found:** {results.get('total_found', 0)} documents
✅ **Processed:** {results.get('processed', 0)} documents  
⏭️ **Skipped:** {results.get('skipped', 0)} documents
❌ **Errors:** {results.get('errors', 0)} documents
🔄 **Cyber Docs:** {results.get('cyber_docs', 0)}
💰 **Financial Docs:** {results.get('financial_docs', 0)}
📄 **General Docs:** {results.get('general_docs', 0)}

Refresh completed at: {data.get('timestamp', 'Unknown')}"""
            
            else:
                return f"Error refreshing knowledge base: HTTP {response.status_code}"
                
        except requests.exceptions.RequestException as e:
            return f"Connection error to Financial Advisor knowledge base: {str(e)}"
        except Exception as e:
            return f"Error refreshing knowledge base: {str(e)}"


class UserValves(BaseModel):
    """User-configurable settings for the Financial Advisor Knowledge Base function."""
    
    financial_kb_enabled: bool = True
    max_search_results: int = 3
    include_scores: bool = True


class Pipe:
    """Financial Advisor Knowledge Base integration for Open WebUI"""
    
    class Valves(BaseModel):
        """System valves for configuration"""
        name: str = "Financial Advisor Knowledge Base"
        
    def __init__(self):
        self.valves = self.Valves()
        self.tools = Tools()

    async def on_startup(self):
        """Called when the function is loaded"""
        print("Financial Advisor Knowledge Base function loaded successfully")

    async def on_shutdown(self):
        """Called when the function is unloaded"""
        print("Financial Advisor Knowledge Base function unloaded")

    def pipe(self, prompt: str = None, **kwargs) -> str:
        """
        Main function processing - automatically enhance prompts with knowledge base search
        """
        if not prompt:
            return "No prompt provided"
        
        # Check if the prompt is asking for financial or cybersecurity information
        financial_keywords = [
            "financial", "finance", "investment", "stock", "tax", "budget", "saving", "money",
            "portfolio", "retirement", "debt", "credit", "expense", "income", "wealth"
        ]
        
        cyber_keywords = [
            "cyber", "security", "malware", "hacking", "penetration", "vulnerability",
            "threat", "attack", "defense", "encryption", "firewall", "virus", "breach"
        ]
        
        prompt_lower = prompt.lower()
        
        # Search knowledge base if relevant keywords are found
        if any(keyword in prompt_lower for keyword in financial_keywords + cyber_keywords):
            # Extract key terms for search
            search_query = prompt[:200]  # Use first 200 chars as search query
            kb_results = self.tools.search_financial_knowledge(search_query)
            
            # Enhance the prompt with knowledge base context
            enhanced_prompt = f"""Context from Financial Advisor Knowledge Base:
{kb_results}

User Question: {prompt}

Please provide a comprehensive answer using the context above when relevant, but also use your general knowledge. If the context doesn't contain relevant information, please say so and provide a helpful response anyway."""
            
            return enhanced_prompt
        
        # For non-financial/cyber questions, return original prompt
        return prompt

# Required for Open WebUI function loading
tools = Tools()