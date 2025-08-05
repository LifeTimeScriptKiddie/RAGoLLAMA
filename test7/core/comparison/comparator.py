"""
Embedding Comparison Module

Compares embeddings from different methods and provides detailed analysis.
"""

from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import logging
from sklearn.metrics.pairwise import cosine_similarity
from scipy.spatial.distance import euclidean
from scipy.stats import pearsonr, spearmanr
import json

logger = logging.getLogger(__name__)


class EmbeddingComparator:
    """Compares embeddings from different methods and provides analysis."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize embedding comparator.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.similarity_threshold = config.get("similarity_threshold", 0.8)
        self.analysis_metrics = config.get("analysis_metrics", [
            "cosine_similarity", "euclidean_distance", "pearson_correlation", "spearman_correlation"
        ])
    
    def compare_embeddings(self, docling_embeddings: List[np.ndarray], 
                          microsoft_embeddings: List[np.ndarray],
                          chunk_texts: List[str]) -> Dict[str, Any]:
        """
        Compare embeddings from Docling and Microsoft RAG methods.
        
        Args:
            docling_embeddings: List of Docling embeddings
            microsoft_embeddings: List of Microsoft RAG embeddings
            chunk_texts: Original text chunks for reference
            
        Returns:
            Comprehensive comparison results
        """
        if len(docling_embeddings) != len(microsoft_embeddings):
            raise ValueError("Embedding lists must have the same length")
        
        if len(docling_embeddings) != len(chunk_texts):
            raise ValueError("Number of embeddings must match number of text chunks")
        
        logger.info(f"Comparing {len(docling_embeddings)} embedding pairs")
        
        try:
            results = {
                "summary": self._create_summary(docling_embeddings, microsoft_embeddings),
                "pairwise_similarities": self._calculate_pairwise_similarities(docling_embeddings, microsoft_embeddings),
                "cross_method_similarities": self._calculate_cross_method_similarities(docling_embeddings, microsoft_embeddings),
                "statistical_analysis": self._perform_statistical_analysis(docling_embeddings, microsoft_embeddings),
                "clustering_analysis": self._analyze_clustering(docling_embeddings, microsoft_embeddings),
                "dimensional_analysis": self._analyze_dimensions(docling_embeddings, microsoft_embeddings),
                "chunk_analysis": self._analyze_by_chunks(docling_embeddings, microsoft_embeddings, chunk_texts)
            }
            
            # Add overall assessment
            results["assessment"] = self._create_assessment(results)
            
            logger.info("Embedding comparison completed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error comparing embeddings: {e}")
            raise
    
    def _create_summary(self, docling_embeddings: List[np.ndarray], 
                       microsoft_embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """Create a summary of the comparison."""
        docling_dims = [emb.shape[0] for emb in docling_embeddings]
        microsoft_dims = [emb.shape[0] for emb in microsoft_embeddings]
        
        return {
            "num_embeddings": len(docling_embeddings),
            "docling_dimensions": {
                "min": min(docling_dims),
                "max": max(docling_dims),
                "avg": np.mean(docling_dims),
                "consistent": len(set(docling_dims)) == 1
            },
            "microsoft_dimensions": {
                "min": min(microsoft_dims),
                "max": max(microsoft_dims),
                "avg": np.mean(microsoft_dims),
                "consistent": len(set(microsoft_dims)) == 1
            },
            "dimension_compatibility": docling_dims[0] == microsoft_dims[0] if docling_dims and microsoft_dims else False
        }
    
    def _calculate_pairwise_similarities(self, docling_embeddings: List[np.ndarray], 
                                       microsoft_embeddings: List[np.ndarray]) -> List[Dict[str, float]]:
        """Calculate pairwise similarities between corresponding embeddings."""
        similarities = []
        
        for i, (doc_emb, ms_emb) in enumerate(zip(docling_embeddings, microsoft_embeddings)):
            pair_similarity = {}
            
            # Cosine similarity
            if "cosine_similarity" in self.analysis_metrics:
                cosine_sim = cosine_similarity(doc_emb.reshape(1, -1), ms_emb.reshape(1, -1))[0][0]
                pair_similarity["cosine_similarity"] = float(cosine_sim)
            
            # Euclidean distance
            if "euclidean_distance" in self.analysis_metrics:
                euclidean_dist = euclidean(doc_emb, ms_emb)
                pair_similarity["euclidean_distance"] = float(euclidean_dist)
            
            # Pearson correlation
            if "pearson_correlation" in self.analysis_metrics:
                try:
                    pearson_corr, _ = pearsonr(doc_emb, ms_emb)
                    pair_similarity["pearson_correlation"] = float(pearson_corr) if not np.isnan(pearson_corr) else 0.0
                except:
                    pair_similarity["pearson_correlation"] = 0.0
            
            # Spearman correlation
            if "spearman_correlation" in self.analysis_metrics:
                try:
                    spearman_corr, _ = spearmanr(doc_emb, ms_emb)
                    pair_similarity["spearman_correlation"] = float(spearman_corr) if not np.isnan(spearman_corr) else 0.0
                except:
                    pair_similarity["spearman_correlation"] = 0.0
            
            pair_similarity["chunk_index"] = i
            similarities.append(pair_similarity)
        
        return similarities
    
    def _calculate_cross_method_similarities(self, docling_embeddings: List[np.ndarray], 
                                           microsoft_embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """Calculate similarities between all Docling and Microsoft embeddings."""
        # Convert to matrices
        docling_matrix = np.vstack(docling_embeddings)
        microsoft_matrix = np.vstack(microsoft_embeddings)
        
        # Calculate cross-similarity matrix
        cross_similarity = cosine_similarity(docling_matrix, microsoft_matrix)
        
        return {
            "similarity_matrix": cross_similarity.tolist(),
            "avg_cross_similarity": float(np.mean(cross_similarity)),
            "max_cross_similarity": float(np.max(cross_similarity)),
            "min_cross_similarity": float(np.min(cross_similarity)),
            "diagonal_similarities": [float(cross_similarity[i, i]) for i in range(min(cross_similarity.shape))],
            "avg_diagonal_similarity": float(np.mean([cross_similarity[i, i] for i in range(min(cross_similarity.shape))]))
        }
    
    def _perform_statistical_analysis(self, docling_embeddings: List[np.ndarray], 
                                    microsoft_embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """Perform statistical analysis on the embeddings."""
        # Flatten embeddings for analysis
        docling_flat = np.hstack(docling_embeddings)
        microsoft_flat = np.hstack(microsoft_embeddings)
        
        analysis = {
            "docling_stats": {
                "mean": float(np.mean(docling_flat)),
                "std": float(np.std(docling_flat)),
                "min": float(np.min(docling_flat)),
                "max": float(np.max(docling_flat)),
                "l2_norm_avg": float(np.mean([np.linalg.norm(emb) for emb in docling_embeddings]))
            },
            "microsoft_stats": {
                "mean": float(np.mean(microsoft_flat)),
                "std": float(np.std(microsoft_flat)),
                "min": float(np.min(microsoft_flat)),
                "max": float(np.max(microsoft_flat)),
                "l2_norm_avg": float(np.mean([np.linalg.norm(emb) for emb in microsoft_embeddings]))
            }
        }
        
        # Compare distributions
        try:
            from scipy.stats import ks_2samp
            ks_stat, ks_pvalue = ks_2samp(docling_flat, microsoft_flat)
            analysis["distribution_comparison"] = {
                "ks_statistic": float(ks_stat),
                "ks_pvalue": float(ks_pvalue),
                "distributions_similar": ks_pvalue > 0.05
            }
        except ImportError:
            logger.warning("scipy not available for distribution comparison")
        
        return analysis
    
    def _analyze_clustering(self, docling_embeddings: List[np.ndarray], 
                          microsoft_embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """Analyze clustering behavior of embeddings."""
        try:
            from sklearn.cluster import KMeans
            from sklearn.metrics import silhouette_score
            
            if len(docling_embeddings) < 3:
                return {"note": "Not enough samples for clustering analysis"}
            
            n_clusters = min(3, len(docling_embeddings) // 2)
            
            # Cluster Docling embeddings
            docling_matrix = np.vstack(docling_embeddings)
            docling_kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            docling_labels = docling_kmeans.fit_predict(docling_matrix)
            docling_silhouette = silhouette_score(docling_matrix, docling_labels)
            
            # Cluster Microsoft embeddings
            microsoft_matrix = np.vstack(microsoft_embeddings)
            microsoft_kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            microsoft_labels = microsoft_kmeans.fit_predict(microsoft_matrix)
            microsoft_silhouette = silhouette_score(microsoft_matrix, microsoft_labels)
            
            # Compare clustering results
            label_agreement = np.mean(docling_labels == microsoft_labels)
            
            return {
                "n_clusters": n_clusters,
                "docling_silhouette": float(docling_silhouette),
                "microsoft_silhouette": float(microsoft_silhouette),
                "cluster_label_agreement": float(label_agreement),
                "docling_labels": docling_labels.tolist(),
                "microsoft_labels": microsoft_labels.tolist()
            }
            
        except ImportError:
            logger.warning("sklearn not available for clustering analysis")
            return {"note": "sklearn not available for clustering analysis"}
    
    def _analyze_dimensions(self, docling_embeddings: List[np.ndarray], 
                          microsoft_embeddings: List[np.ndarray]) -> Dict[str, Any]:
        """Analyze dimensional properties of embeddings."""
        try:
            from sklearn.decomposition import PCA
            
            if len(docling_embeddings) < 2:
                return {"note": "Not enough samples for dimensional analysis"}
            
            # Perform PCA
            docling_matrix = np.vstack(docling_embeddings)
            microsoft_matrix = np.vstack(microsoft_embeddings)
            
            n_components = min(10, docling_matrix.shape[0] - 1, docling_matrix.shape[1])
            
            docling_pca = PCA(n_components=n_components)
            docling_transformed = docling_pca.fit_transform(docling_matrix)
            
            microsoft_pca = PCA(n_components=n_components)
            microsoft_transformed = microsoft_pca.fit_transform(microsoft_matrix)
            
            return {
                "docling_explained_variance": docling_pca.explained_variance_ratio_.tolist(),
                "microsoft_explained_variance": microsoft_pca.explained_variance_ratio_.tolist(),
                "docling_cumulative_variance": np.cumsum(docling_pca.explained_variance_ratio_).tolist(),
                "microsoft_cumulative_variance": np.cumsum(microsoft_pca.explained_variance_ratio_).tolist(),
                "intrinsic_dimensionality_estimate": {
                    "docling": int(np.sum(np.cumsum(docling_pca.explained_variance_ratio_) < 0.95) + 1),
                    "microsoft": int(np.sum(np.cumsum(microsoft_pca.explained_variance_ratio_) < 0.95) + 1)
                }
            }
            
        except ImportError:
            logger.warning("sklearn not available for dimensional analysis")
            return {"note": "sklearn not available for dimensional analysis"}
    
    def _analyze_by_chunks(self, docling_embeddings: List[np.ndarray], 
                          microsoft_embeddings: List[np.ndarray],
                          chunk_texts: List[str]) -> List[Dict[str, Any]]:
        """Analyze embeddings for each text chunk."""
        chunk_analyses = []
        
        for i, (doc_emb, ms_emb, text) in enumerate(zip(docling_embeddings, microsoft_embeddings, chunk_texts)):
            chunk_analysis = {
                "chunk_index": i,
                "text_length": len(text),
                "text_preview": text[:100] + "..." if len(text) > 100 else text,
                "docling_norm": float(np.linalg.norm(doc_emb)),
                "microsoft_norm": float(np.linalg.norm(ms_emb)),
                "cosine_similarity": float(cosine_similarity(doc_emb.reshape(1, -1), ms_emb.reshape(1, -1))[0][0]),
                "embedding_difference_norm": float(np.linalg.norm(doc_emb - ms_emb)),
                "relative_difference": float(np.linalg.norm(doc_emb - ms_emb) / (np.linalg.norm(doc_emb) + np.linalg.norm(ms_emb)))
            }
            
            chunk_analyses.append(chunk_analysis)
        
        return chunk_analyses
    
    def _create_assessment(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Create an overall assessment of the comparison."""
        pairwise_sims = results["pairwise_similarities"]
        cross_method = results["cross_method_similarities"]
        
        avg_cosine_similarity = np.mean([sim["cosine_similarity"] for sim in pairwise_sims])
        similarity_consistency = np.std([sim["cosine_similarity"] for sim in pairwise_sims])
        
        assessment = {
            "overall_similarity": {
                "average_cosine_similarity": float(avg_cosine_similarity),
                "similarity_consistency": float(similarity_consistency),
                "high_similarity": avg_cosine_similarity > self.similarity_threshold,
                "consistent_performance": similarity_consistency < 0.1
            },
            "method_comparison": {
                "methods_are_similar": avg_cosine_similarity > self.similarity_threshold,
                "prefer_docling": "Docling shows more consistent embeddings" if similarity_consistency < 0.05 else None,
                "prefer_microsoft": "Microsoft RAG shows more consistent embeddings" if similarity_consistency < 0.05 else None,
                "recommendation": self._get_recommendation(avg_cosine_similarity, similarity_consistency)
            },
            "quality_metrics": {
                "embedding_alignment": cross_method["avg_diagonal_similarity"],
                "cross_method_coherence": cross_method["avg_cross_similarity"],
                "dimensional_efficiency": results.get("dimensional_analysis", {}).get("intrinsic_dimensionality_estimate", {})
            }
        }
        
        return assessment
    
    def _get_recommendation(self, avg_similarity: float, consistency: float) -> str:
        """Generate a recommendation based on comparison results."""
        if avg_similarity > 0.9 and consistency < 0.05:
            return "Both methods produce highly similar and consistent embeddings. Choose based on performance requirements."
        elif avg_similarity > 0.8 and consistency < 0.1:
            return "Methods produce similar embeddings with good consistency. Both are viable options."
        elif avg_similarity > 0.7:
            return "Methods show moderate similarity. Consider ensemble approaches or choose based on specific use case."
        elif avg_similarity > 0.5:
            return "Methods show some similarity but significant differences. Evaluate based on downstream task performance."
        else:
            return "Methods produce quite different embeddings. Choose based on specific requirements and validation testing."
    
    def export_comparison_report(self, comparison_results: Dict[str, Any], output_path: str):
        """Export comparison results to a JSON report."""
        try:
            import json
            with open(output_path, 'w') as f:
                json.dump(comparison_results, f, indent=2, default=str)
            logger.info(f"Comparison report exported to {output_path}")
        except Exception as e:
            logger.error(f"Error exporting report: {e}")
            raise