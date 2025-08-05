"""
CLI Interface for Multi-RAG Document Pipeline

Provides command-line access to document processing, embedding comparison,
and retrieval capabilities.
"""

import click
import json
from pathlib import Path
from typing import Optional
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

from core.document.processor import DocumentProcessor
from core.embedding.docling_embedder import DoclingEmbedder
from core.embedding.microsoft_embedder import MicrosoftEmbedder
from core.vector.faiss_store import FAISSVectorStore
from core.storage.sqlite_manager import SQLiteManager
from core.comparison.comparator import EmbeddingComparator

console = Console()


@click.group()
@click.option('--config', '-c', default='config/config.json', 
              help='Configuration file path')
@click.pass_context
def cli(ctx, config):
    """Multi-RAG Document Pipeline CLI"""
    ctx.ensure_object(dict)
    
    # Load configuration
    config_path = Path(config)
    if config_path.exists():
        with open(config_path) as f:
            ctx.obj['config'] = json.load(f)
    else:
        ctx.obj['config'] = {
            "db_path": "/app/cache/documents.db",
            "faiss_index_path": "/app/cache/faiss",
            "max_chunk_size": 1000,
            "chunk_overlap": 200,
            "dimension": 384,
            "supported_formats": [".pdf", ".txt", ".docx", ".pptx", ".jpg", ".png"]
        }
    
    # Initialize components
    ctx.obj['processor'] = DocumentProcessor(ctx.obj['config'])
    ctx.obj['docling_embedder'] = DoclingEmbedder(ctx.obj['config'])
    ctx.obj['microsoft_embedder'] = MicrosoftEmbedder(ctx.obj['config'])
    ctx.obj['vector_store'] = FAISSVectorStore(ctx.obj['config'])
    ctx.obj['db_manager'] = SQLiteManager(ctx.obj['config'])
    ctx.obj['comparator'] = EmbeddingComparator(ctx.obj['config'])


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--method', '-m', type=click.Choice(['docling', 'microsoft', 'both']), 
              default='both', help='Embedding method to use')
@click.option('--compare', '-c', is_flag=True, 
              help='Compare embedding methods if both are used')
@click.pass_context
def process(ctx, file_path, method, compare):
    """Process a document and generate embeddings"""
    config = ctx.obj['config']
    processor = ctx.obj['processor']
    docling_embedder = ctx.obj['docling_embedder']
    microsoft_embedder = ctx.obj['microsoft_embedder']
    vector_store = ctx.obj['vector_store']
    db_manager = ctx.obj['db_manager']
    comparator = ctx.obj['comparator']
    
    file_path = Path(file_path)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console
    ) as progress:
        
        # Process document
        task1 = progress.add_task("Processing document...", total=None)
        chunks, metadata = processor.process_document(str(file_path))
        progress.update(task1, completed=True)
        
        # Add document to database
        task2 = progress.add_task("Storing document metadata...", total=None)
        document_id = db_manager.add_document(str(file_path), metadata)
        progress.update(task2, completed=True)
        
        embeddings_results = {}
        
        # Generate embeddings
        if method in ['docling', 'both']:
            task3 = progress.add_task("Generating Docling embeddings...", total=None)
            docling_embeddings = docling_embedder.embed_batch(chunks)
            
            # Store embeddings in vector store
            vector_ids = vector_store.add_embeddings(
                docling_embeddings, 
                [{"chunk_index": i, "text": chunk} for i, chunk in enumerate(chunks)],
                str(document_id)
            )
            
            # Store chunks in database
            for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
                db_manager.add_chunk(document_id, i, chunk, "docling", vector_id)
            
            embeddings_results['docling'] = docling_embeddings
            progress.update(task3, completed=True)
        
        if method in ['microsoft', 'both']:
            task4 = progress.add_task("Generating Microsoft embeddings...", total=None)
            microsoft_embeddings = microsoft_embedder.embed_batch(chunks)
            
            # Store embeddings in vector store  
            vector_ids = vector_store.add_embeddings(
                microsoft_embeddings,
                [{"chunk_index": i, "text": chunk} for i, chunk in enumerate(chunks)],
                str(document_id)
            )
            
            # Store chunks in database
            for i, (chunk, vector_id) in enumerate(zip(chunks, vector_ids)):
                db_manager.add_chunk(document_id, i, chunk, "microsoft", vector_id)
            
            embeddings_results['microsoft'] = microsoft_embeddings
            progress.update(task4, completed=True)
        
        # Compare embeddings if requested
        if compare and method == 'both':
            task5 = progress.add_task("Comparing embeddings...", total=None)
            comparison_results = comparator.compare_embeddings(
                embeddings_results['docling'],
                embeddings_results['microsoft'], 
                chunks
            )
            
            # Store comparison results
            db_manager.add_comparison(document_id, comparison_results)
            
            progress.update(task5, completed=True)
            
            # Display comparison summary
            console.print("\n[bold green]Comparison Results[/bold green]")
            console.print(comparator.get_comparison_summary(comparison_results))
    
    # Save vector store
    vector_store.save_index()
    
    console.print(f"\n[bold green]✓[/bold green] Successfully processed {file_path.name}")
    console.print(f"  - Document ID: {document_id}")
    console.print(f"  - Chunks: {len(chunks)}")
    console.print(f"  - Methods: {method}")


@cli.command()
@click.argument('query')
@click.option('--method', '-m', type=click.Choice(['docling', 'microsoft']), 
              default='docling', help='Embedding method to use for search')
@click.option('--top-k', '-k', default=5, help='Number of results to return')
@click.pass_context
def search(ctx, query, method, top_k):
    """Search for similar document chunks"""
    docling_embedder = ctx.obj['docling_embedder']
    microsoft_embedder = ctx.obj['microsoft_embedder']
    vector_store = ctx.obj['vector_store']
    
    # Generate query embedding
    if method == 'docling':
        query_embedding = docling_embedder.embed_text(query)
    else:
        query_embedding = microsoft_embedder.embed_text(query)
    
    # Search vector store
    results = vector_store.search(query_embedding, k=top_k)
    
    if not results:
        console.print("[yellow]No results found[/yellow]")
        return
    
    # Display results
    table = Table(title=f"Search Results for: '{query}'")
    table.add_column("Rank", style="cyan", no_wrap=True)
    table.add_column("Similarity", style="magenta")
    table.add_column("Document", style="green")
    table.add_column("Chunk", style="yellow")
    
    for i, (vector_id, similarity, metadata) in enumerate(results, 1):
        table.add_row(
            str(i),
            f"{similarity:.3f}",
            metadata.get("document_id", "Unknown"),
            metadata.get("text", "")[:100] + "..." if len(metadata.get("text", "")) > 100 else metadata.get("text", "")
        )
    
    console.print(table)


@cli.command()
@click.pass_context
def list_documents(ctx):
    """List all processed documents"""
    db_manager = ctx.obj['db_manager']
    
    documents = db_manager.list_documents()
    
    if not documents:
        console.print("[yellow]No documents found[/yellow]")
        return
    
    table = Table(title="Processed Documents")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("File Name", style="green")
    table.add_column("Type", style="yellow")
    table.add_column("Chunks", style="magenta")
    table.add_column("Processed", style="blue")
    
    for doc in documents:
        table.add_row(
            str(doc["id"]),
            doc["file_name"],
            doc["file_type"],
            str(doc["num_chunks"]),
            doc["processed_at"][:19] if doc["processed_at"] else "Unknown"
        )
    
    console.print(table)


@cli.command()
@click.argument('document_id', type=int)
@click.pass_context
def show_comparison(ctx, document_id):
    """Show comparison results for a document"""
    db_manager = ctx.obj['db_manager']
    comparator = ctx.obj['comparator']
    
    comparison = db_manager.get_comparison(document_id)
    
    if not comparison:
        console.print(f"[red]No comparison found for document {document_id}[/red]")
        return
    
    # Display detailed comparison
    console.print(f"\n[bold]Comparison Results for Document {document_id}[/bold]")
    console.print(f"Best Method: [green]{comparison['best_method']}[/green]")
    console.print(f"Created: {comparison['created_at']}")
    
    # Show metrics table
    results = comparison['comparison_results']
    if isinstance(results, str):
        results = json.loads(results)
    
    console.print(comparator.get_comparison_summary(results))


@cli.command()
@click.pass_context
def stats(ctx):
    """Show system statistics"""
    db_manager = ctx.obj['db_manager']
    vector_store = ctx.obj['vector_store']
    
    db_stats = db_manager.get_stats()
    vector_stats = vector_store.get_stats()
    
    # Database statistics
    console.print("[bold]Database Statistics[/bold]")
    db_table = Table()
    db_table.add_column("Metric", style="cyan")
    db_table.add_column("Value", style="green")
    
    for key, value in db_stats.items():
        db_table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(db_table)
    
    # Vector store statistics
    console.print("\n[bold]Vector Store Statistics[/bold]")
    vector_table = Table()
    vector_table.add_column("Metric", style="cyan")
    vector_table.add_column("Value", style="green")
    
    for key, value in vector_stats.items():
        vector_table.add_row(key.replace("_", " ").title(), str(value))
    
    console.print(vector_table)


if __name__ == '__main__':
    cli()