# BLUF

Your plan is solid and very doable solo. I’d keep the phases and repo layout, but I’d tweak a few things to avoid common RAG pain points: add an **ingestion ledger** (idempotency + versioning), **embedding cache**, **index snapshots**, a tiny **eval harness**, and explicit **contracts** between components. That’ll save you weeks later.

```mermaid
flowchart TD
  subgraph Ingestion
    A[Docling Runner]-->B[Chunker]
    B-->C[Deduper/PII Redactor]
    C-->D[Embedder (cache)]
    D-->E[FAISS Index Writer]
    A-.->L[(Ingestion Ledger)]
    E-.->S[(Index Snapshots)]
  end
  subgraph Serving
    Q[FastAPI /query]-->R[Retriever (FAISS)]
    R-->O[Ollama /generate]
    Q-->M[Metrics + Audit Log]
  end
  subgraph Ops
    K8s[K8s Deployments/Secrets/PVCs]
    G[GitHub Actions/CI]
    P[Prometheus/Grafana]
  end
  E-->R
  M-->P
  G-->K8s
```

---

## Keep (looks great)

* **Phases 1–4** and the **repo layout**. Clean and incremental.
* **Separate pods** for embedder/docling/retriever/ollama with resource limits.
* **JWT + rate limiting**, **Prometheus metrics**, and **audit logs**.

## Adjust (small changes, big payoff)

* **Ingestion ledger**: SQLite/DuckDB table tracking `doc_id`, `content_hash`, `version`, `status`, `chunks`, `embedding_model`. Prevents re-embedding and enables clean re-index.
* **Embedding cache**: Keyed by `(embedding_model, chunk_hash)`. Store vectors in DuckDB or a simple parquet; only write to FAISS if cache miss.
* **Index snapshots**: Periodic `.faiss` + metadata snapshots under `/data/index_snapshots/ts=...`. Add `roll-forward` and `roll-back` commands.
* **Contracts between components**: Define minimal I/O schemas now so you can swap pieces later.

### Minimal contracts (recommend)

* `docling_runner.py` → JSONL of `{doc_id, page, text, mime, sha256, meta}`
* `chunker.py` → JSONL of `{doc_id, chunk_id, text, sha256, order, meta}`
* `embedder.py` → JSONL of `{chunk_id, model, vector, dim, sha256}`
* `vector_store.py`:

  * `upsert(vectors: List[(chunk_id, vector)]) -> index_version`
  * `query(text|vector, k, filters) -> List[(chunk_id, score)]`

## Add (to make it “production-grade”)

* **Dedup + PII pass**: Fast fuzzy dedup (MinHash/SimHash) and optional PII redaction before embedding.
* **Evaluator**: Tiny eval harness (5–10 questions per doc) to score retrieval hit-rate and latency. Run on CI to catch regressions.
* **Backpressure**: Queue for ingestion (e.g., in-process work queue now; Celery/RQ later). Prevents API from stalling under big uploads.
* **Observability details**:

  * Counters: `rag_requests_total`, `ollama_tokens_total`, `retriever_queries_total`
  * Histograms: `retriever_latency_ms`, `ollama_latency_ms`, `embedding_latency_ms`
  * Gauges: `index_size_chunks`, `index_version`
* **Graceful model mgmt** (Ollama): Pin default model per env via env var; expose `/models` in admin UI; stream responses.

---

## Suggested repo tweaks (small)

```
rag-ollama-k8s/
├── apps/
│   ├── backend/
│   │   ├── api/ (routers: upload, query, admin, health)
│   │   ├── core/ (auth, rate_limit, settings)
│   │   └── observability/ (metrics, logging)
│   ├── rag/
│   │   ├── ingestion/ (docling_runner.py, chunker.py, deduper.py, pii.py)
│   │   ├── embeddings/ (embedder.py, cache.py)
│   │   ├── store/ (vector_store.py, snapshots.py, ledger.py)
│   │   └── evals/ (datasets/, run_eval.py)
│   ├── frontend-streamlit/
│   └── frontend-openwebui/
├── deployments/
│   ├── base/ (deployments, services, pvcs, configmaps, secrets)
│   └── overlays/ (dev/, prod/)
├── configs/ (.env.example, kustomization/)
├── scripts/ (make_index_snapshot.sh, restore_snapshot.sh)
├── docker-compose.yml
├── Makefile
└── README.md
```

---

## Kubernetes notes (pragmatic)

* **PVCs**: Separate PVCs for `/data/raw_docs`, `/data/index`, `/data/cache`. Set `ReadWriteOnce` and size explicitly.
* **Probes**: `backend` liveness `/healthz`, readiness `/ready`; `ollama` readiness hit `/api/tags`.
* **Resource requests/limits**: Give **embedder** CPU first; add GPU later via node selector if you upgrade.
* **Secrets**: Use K8s Secret for JWT key; mount as env. ConfigMaps for non-sensitive knobs (chunk size, model, k).
* **Ingress**: Start with NGINX, enable gzip + request body size limits, add rate limit at edge too.

---

## Security quick wins

* **JWT** short TTL + refresh; **signed uploads** (max size, mime allowlist).
* **Rate limiting**: token bucket per JWT + IP. Return 429 with `Retry-After`.
* **Audit**: log `(user_id, action, doc_id, n_tokens, latency, status)`.

---

## Makefile targets (helpful)

```
make dev          # docker compose up + hot reload
make ingest FILE=path.pdf
make reindex      # rebuild FAISS from cache
make snapshot     # save index snapshot
make restore TS=...
make eval         # run tiny eval set, print hitrate/latency
make k8s-dev      # kustomize build overlays/dev | kubectl apply -f -
```

---

## Where to start (my recommendation)

1. **`ledger.py`** (idempotency)
2. **`chunker.py`** (deterministic chunks)
3. **`embedder.py` + `cache.py`** (avoid recompute)
4. **`vector_store.py`** (upsert/query + snapshots)
5. **Backend `/upload` → enqueue → ingestion pipeline → index\`**

If you want, I can scaffold any of these in your layout (with docstrings, pydantic models, and stub tests). Which file do you want first?

