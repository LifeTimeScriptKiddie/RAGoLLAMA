from prometheus_client import Counter, Histogram, Gauge
import time

# Counters
rag_requests_total = Counter("rag_requests_total", "Total RAG requests", ["endpoint"])
ollama_tokens_total = Counter("ollama_tokens_total", "Total tokens processed by Ollama")
retriever_queries_total = Counter("retriever_queries_total", "Total retriever queries")
documents_uploaded_total = Counter("documents_uploaded_total", "Total documents uploaded")

# Histograms (latency metrics)
retriever_latency_ms = Histogram("retriever_latency_ms", "Retriever query latency in milliseconds")
ollama_latency_ms = Histogram("ollama_latency_ms", "Ollama generation latency in milliseconds")
embedding_latency_ms = Histogram("embedding_latency_ms", "Embedding generation latency in milliseconds")
query_latency_ms = Histogram("query_latency_ms", "End-to-end query latency in milliseconds")

# Gauges
index_size_chunks = Gauge("index_size_chunks", "Number of chunks in the index")
index_version = Gauge("index_version", "Current index version")

class Metrics:
    """Metrics collection helper."""
    
    def increment(self, metric_name: str, labels: dict = None):
        """Increment a counter metric."""
        if metric_name == "rag_requests_total" and labels:
            rag_requests_total.labels(**labels).inc()
        elif metric_name == "documents_uploaded_total":
            documents_uploaded_total.inc()
        elif metric_name == "queries_total":
            rag_requests_total.labels(endpoint="query").inc()
        # Add more as needed
    
    def histogram(self, metric_name: str, value: float):
        """Record a histogram metric."""
        if metric_name == "query_latency_ms":
            query_latency_ms.observe(value)
        elif metric_name == "retriever_latency_ms":
            retriever_latency_ms.observe(value)
        elif metric_name == "ollama_latency_ms":
            ollama_latency_ms.observe(value)
        elif metric_name == "embedding_latency_ms":
            embedding_latency_ms.observe(value)
    
    def gauge(self, metric_name: str, value: float):
        """Set a gauge metric."""
        if metric_name == "index_size_chunks":
            index_size_chunks.set(value)
        elif metric_name == "index_version":
            index_version.set(value)

metrics = Metrics()