from typing import Dict, List, Any, Optional
from .ollama_client import ollama_client
from .turbo_rag import turbo_rag
import json
import sqlite3
import pandas as pd

class CAGEngine:
    """Context-Aware Generation Engine"""
    
    def __init__(self, model_name: str = None):
        # Use best available model instead of hardcoded one
        self.requested_model = model_name or "llama3.2:latest"
        self.conversation_history = []
        self.user_profile = {}
        
    def update_user_profile(self, profile_data: Dict[str, Any]):
        """Update user profile for personalization"""
        self.user_profile.update(profile_data)
    
    def get_financial_context(self, db_path: str = "/app/data/finance.db") -> str:
        """Get financial context from database"""
        try:
            conn = sqlite3.connect(db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            # Check if transactions table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'")
            if not cursor.fetchone():
                return "No financial data available."
            
            # Get recent transactions summary
            df = pd.read_sql("SELECT * FROM transactions ORDER BY date DESC LIMIT 20", conn)
            
            if df.empty:
                return "No transaction data available."
            
            # Generate summary
            total_spending = df[df['amount'].astype(float) < 0]['amount'].astype(float).sum()
            total_income = df[df['amount'].astype(float) > 0]['amount'].astype(float).sum()
            
            summary = f"""
Recent Financial Summary:
- Total Spending (last 20 transactions): ${abs(total_spending):,.2f}
- Total Income (last 20 transactions): ${total_income:,.2f}
- Net: ${total_income + total_spending:,.2f}
- Most common categories: {df['bucket'].value_counts().head(3).to_dict()}
"""
            conn.close()
            return summary
            
        except Exception as e:
            return f"Error accessing financial data: {str(e)}"
    
    def generate_context_aware_response(self, query: str, context_type: str = "general") -> Dict[str, Any]:
        """Generate context-aware response based on query type"""
        
        # Get base RAG response
        rag_response = turbo_rag.query(query)
        
        # Build context based on type
        context_parts = []
        
        if context_type == "financial":
            financial_context = self.get_financial_context()
            context_parts.append(f"Financial Context:\n{financial_context}")
        
        if self.user_profile:
            profile_context = f"User Profile: {json.dumps(self.user_profile, indent=2)}"
            context_parts.append(profile_context)
        
        if self.conversation_history:
            recent_history = self.conversation_history[-3:]  # Last 3 exchanges
            history_context = "Recent conversation:\n" + "\n".join([
                f"User: {h['user']}\nAssistant: {h['assistant']}" 
                for h in recent_history
            ])
            context_parts.append(history_context)
        
        # Combine contexts
        full_context = "\n\n".join(context_parts)
        
        # Generate enhanced response
        enhanced_prompt = f"""You are a personal financial advisor and assistant. Use the following context to provide a comprehensive, personalized response.

{full_context}

Retrieved Information:
{rag_response['answer']}

User Query: {query}

Provide a detailed, personalized response that:
1. Addresses the user's specific question
2. Incorporates relevant financial context if applicable
3. Provides actionable advice
4. Maintains conversation continuity

Response:"""
        
        enhanced_answer = ollama_client.generate(self.requested_model, enhanced_prompt)
        
        # Update conversation history
        self.conversation_history.append({
            "user": query,
            "assistant": enhanced_answer,
            "context_type": context_type
        })
        
        # Keep only last 10 exchanges
        if len(self.conversation_history) > 10:
            self.conversation_history = self.conversation_history[-10:]
        
        return {
            "answer": enhanced_answer,
            "rag_sources": rag_response["sources"],
            "confidence": rag_response["confidence"],
            "context_type": context_type,
            "financial_context_used": context_type == "financial"
        }
    
    def classify_query_type(self, query: str) -> str:
        """Classify query to determine appropriate context"""
        financial_keywords = [
            "budget", "spending", "income", "tax", "investment", "stock", 
            "expense", "money", "financial", "bank", "transaction", "save"
        ]
        
        query_lower = query.lower()
        if any(keyword in query_lower for keyword in financial_keywords):
            return "financial"
        
        return "general"
    
    def clear_history(self):
        """Clear conversation history"""
        self.conversation_history = []

# Global instance
cag_engine = CAGEngine()