from fastapi import FastAPI
from prometheus_client import make_asgi_app
from apps.backend.api import upload, query, admin, auth
from apps.backend.core.settings import settings

app = FastAPI(
    title="RAG-Ollama Backend",
    description="RAG system with Ollama integration",
    version="1.0.0"
)

# Include routers
app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(query.router)
app.include_router(admin.router)

# Add Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)

@app.get("/")
async def root():
    return {"message": "RAG-Ollama Backend API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=True
    )