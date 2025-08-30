#!/usr/bin/env python3
"""
Evaluation harness for RAG system.

Runs evaluation questions against the RAG system and measures:
- Retrieval hit rate (are expected sources retrieved?)
- Response latency
- Answer relevance (placeholder for now)
"""

import json
import asyncio
import time
from pathlib import Path
from typing import List, Dict, Any
import sys
import os

# Add project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from apps.backend.services.rag_service import get_rag_service

class RAGEvaluator:
    """Evaluator for RAG system performance."""
    
    def __init__(self, questions_file: str = None):
        self.rag_service = get_rag_service()
        
        if questions_file is None:
            questions_file = Path(__file__).parent / "datasets" / "sample_questions.json"
        
        with open(questions_file, 'r') as f:
            self.questions = json.load(f)
    
    async def evaluate_question(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """Evaluate a single question."""
        
        start_time = time.time()
        
        # Query the RAG system
        result = await self.rag_service.query(
            query_text=question["question"],
            k=10  # Get more results for evaluation
        )
        
        latency = time.time() - start_time
        
        # Evaluate retrieval hit rate
        retrieved_sources = [s.get("metadata", {}).get("doc_id", "") for s in result["sources"]]
        expected_keywords = question.get("expected_sources", [])
        
        # Simple keyword matching for hit rate
        hits = 0
        for keyword in expected_keywords:
            for source_id in retrieved_sources:
                if keyword.lower() in source_id.lower():
                    hits += 1
                    break
        
        hit_rate = hits / max(1, len(expected_keywords)) if expected_keywords else 0.0
        
        return {
            "question_id": question["id"],
            "question": question["question"],
            "category": question["category"],
            "difficulty": question["difficulty"],
            "answer": result["answer"],
            "sources_count": len(result["sources"]),
            "latency_seconds": latency,
            "hit_rate": hit_rate,
            "retrieved_sources": retrieved_sources[:5],  # Top 5 for logging
            "expected_sources": expected_keywords,
            "rag_latency_ms": result["latency_ms"]
        }
    
    async def run_evaluation(self) -> Dict[str, Any]:
        """Run full evaluation suite."""
        
        print(f"Starting evaluation with {len(self.questions)} questions...")
        
        results = []
        total_latency = 0
        total_hit_rate = 0
        category_stats = {}
        
        for i, question in enumerate(self.questions, 1):
            print(f"Evaluating question {i}/{len(self.questions)}: {question['id']}")
            
            try:
                result = await self.evaluate_question(question)
                results.append(result)
                
                total_latency += result["latency_seconds"]
                total_hit_rate += result["hit_rate"]
                
                # Category stats
                category = result["category"]
                if category not in category_stats:
                    category_stats[category] = {"count": 0, "total_hit_rate": 0, "total_latency": 0}
                
                category_stats[category]["count"] += 1
                category_stats[category]["total_hit_rate"] += result["hit_rate"]
                category_stats[category]["total_latency"] += result["latency_seconds"]
                
                print(f"  Hit rate: {result['hit_rate']:.2f}, Latency: {result['latency_seconds']:.2f}s")
                
            except Exception as e:
                print(f"  Error: {e}")
                results.append({
                    "question_id": question["id"],
                    "error": str(e),
                    "hit_rate": 0.0,
                    "latency_seconds": 0.0
                })
        
        # Calculate overall metrics
        total_questions = len(results)
        avg_hit_rate = total_hit_rate / max(1, total_questions)
        avg_latency = total_latency / max(1, total_questions)
        
        # Category averages
        for category, stats in category_stats.items():
            count = stats["count"]
            stats["avg_hit_rate"] = stats["total_hit_rate"] / max(1, count)
            stats["avg_latency"] = stats["total_latency"] / max(1, count)
        
        summary = {
            "total_questions": total_questions,
            "avg_hit_rate": avg_hit_rate,
            "avg_latency_seconds": avg_latency,
            "category_breakdown": category_stats,
            "timestamp": time.time()
        }
        
        return {
            "summary": summary,
            "detailed_results": results
        }
    
    def print_results(self, evaluation_results: Dict[str, Any]):
        """Pretty print evaluation results."""
        
        summary = evaluation_results["summary"]
        
        print("\n" + "="*60)
        print("RAG EVALUATION RESULTS")
        print("="*60)
        
        print(f"Total Questions: {summary['total_questions']}")
        print(f"Average Hit Rate: {summary['avg_hit_rate']:.2%}")
        print(f"Average Latency: {summary['avg_latency_seconds']:.2f}s")
        
        print("\nCategory Breakdown:")
        print("-" * 40)
        for category, stats in summary["category_breakdown"].items():
            print(f"{category:15} | {stats['count']:2d} questions | "
                  f"Hit Rate: {stats['avg_hit_rate']:.2%} | "
                  f"Latency: {stats['avg_latency']:.2f}s")
        
        print("\nDetailed Results:")
        print("-" * 60)
        for result in evaluation_results["detailed_results"]:
            if "error" in result:
                print(f"{result['question_id']:6} | ERROR: {result['error']}")
            else:
                print(f"{result['question_id']:6} | Hit Rate: {result['hit_rate']:.2%} | "
                      f"Latency: {result['latency_seconds']:.2f}s | "
                      f"Sources: {result['sources_count']}")
        
        print("\n" + "="*60)
    
    def save_results(self, evaluation_results: Dict[str, Any], output_file: str = None):
        """Save evaluation results to JSON file."""
        
        if output_file is None:
            timestamp = int(time.time())
            output_file = f"eval_results_{timestamp}.json"
        
        output_path = Path(output_file)
        
        with open(output_path, 'w') as f:
            json.dump(evaluation_results, f, indent=2)
        
        print(f"Results saved to: {output_path}")

async def main():
    """Main evaluation function."""
    
    # Check if RAG system is ready
    try:
        evaluator = RAGEvaluator()
        print("RAG Evaluator initialized successfully")
    except Exception as e:
        print(f"Failed to initialize RAG evaluator: {e}")
        print("Make sure the backend services are running.")
        return 1
    
    try:
        # Run evaluation
        results = await evaluator.run_evaluation()
        
        # Print results
        evaluator.print_results(results)
        
        # Save results
        evaluator.save_results(results)
        
        # Return exit code based on performance
        hit_rate = results["summary"]["avg_hit_rate"]
        if hit_rate < 0.5:
            print(f"\nWARNING: Low hit rate ({hit_rate:.2%}). Consider improving retrieval.")
            return 1
        else:
            print(f"\nEvaluation completed successfully! Hit rate: {hit_rate:.2%}")
            return 0
            
    except Exception as e:
        print(f"Evaluation failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)