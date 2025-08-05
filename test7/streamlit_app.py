#!/usr/bin/env python3
"""
Multi-RAG Streamlit Interface

Interactive web interface for the Multi-RAG document pipeline.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import json
import sys
from pathlib import Path
from typing import Dict, Any, List
import io

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from main import MultiRAGPipeline

# Page configuration
st.set_page_config(
    page_title="Multi-RAG Document Pipeline",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .comparison-result {
        background-color: #e8f4fd;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def initialize_pipeline():
    """Initialize the Multi-RAG pipeline."""
    try:
        return MultiRAGPipeline()
    except Exception as e:
        error_msg = str(e)
        if "huggingface.co" in error_msg or "couldn't connect" in error_msg:
            st.error("🌐 **Network Connectivity Issue**")
            st.warning("""
            The system cannot download the required AI models from Hugging Face. This usually happens due to:
            
            1. **No internet connection** in the Docker container
            2. **Firewall restrictions** blocking Hugging Face
            3. **First-time model download** taking time
            
            **Solutions:**
            - Ensure Docker has internet access
            - Wait a few minutes for model download to complete
            - Restart the container: `docker-compose restart streamlit`
            - Check the API service at http://localhost:8000 (it may still work)
            """)
        else:
            st.error(f"Failed to initialize pipeline: {e}")
        
        st.info("💡 **Tip**: You can still use the REST API at http://localhost:8000 even if the web interface has issues.")
        return None


def display_stats(pipeline):
    """Display pipeline statistics."""
    stats = pipeline.get_pipeline_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="📄 Total Documents",
            value=stats.get("database", {}).get("total_documents", 0)
        )
    
    with col2:
        st.metric(
            label="🔢 Total Embeddings",
            value=stats.get("database", {}).get("total_embeddings", 0)
        )
    
    with col3:
        st.metric(
            label="📊 Comparisons",
            value=stats.get("database", {}).get("total_comparisons", 0)
        )
    
    with col4:
        st.metric(
            label="🎯 Vector Store",
            value=stats.get("vector_store", {}).get("total_vectors", 0)
        )


def display_comparison_results(comparison_data: Dict[str, Any]):
    """Display embedding comparison results with visualizations."""
    if not comparison_data:
        st.warning("No comparison data available")
        return
    
    st.subheader("🔍 Embedding Comparison Results")
    
    # Overall assessment
    assessment = comparison_data.get("assessment", {})
    overall_sim = assessment.get("overall_similarity", {})
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📈 Overall Similarity")
        avg_sim = overall_sim.get("average_cosine_similarity", 0)
        st.metric(
            label="Average Cosine Similarity",
            value=f"{avg_sim:.3f}",
            delta=f"{'High' if avg_sim > 0.8 else 'Moderate' if avg_sim > 0.6 else 'Low'} similarity"
        )
        
        consistency = overall_sim.get("similarity_consistency", 0)
        st.metric(
            label="Consistency Score",
            value=f"{consistency:.3f}",
            delta=f"{'Consistent' if consistency < 0.1 else 'Variable'} performance"
        )
    
    with col2:
        st.markdown("### 🎯 Recommendations")
        method_comp = assessment.get("method_comparison", {})
        recommendation = method_comp.get("recommendation", "No recommendation available")
        
        st.markdown(f"""
        <div class="comparison-result">
            <strong>Recommendation:</strong><br>
            {recommendation}
        </div>
        """, unsafe_allow_html=True)
    
    # Pairwise similarities visualization
    pairwise_sims = comparison_data.get("pairwise_similarities", [])
    if pairwise_sims:
        st.markdown("### 📊 Pairwise Similarity Analysis")
        
        # Create DataFrame for visualization
        sim_df = pd.DataFrame(pairwise_sims)
        
        # Similarity distribution
        fig_hist = px.histogram(
            sim_df, 
            x="cosine_similarity",
            title="Distribution of Cosine Similarities",
            nbins=20
        )
        st.plotly_chart(fig_hist, use_container_width=True)
        
        # Similarity trends
        if len(sim_df) > 1:
            fig_line = px.line(
                sim_df,
                x="chunk_index",
                y=["cosine_similarity", "pearson_correlation"],
                title="Similarity Trends Across Document Chunks"
            )
            st.plotly_chart(fig_line, use_container_width=True)
    
    # Cross-method similarities
    cross_method = comparison_data.get("cross_method_similarities", {})
    if cross_method.get("similarity_matrix"):
        st.markdown("### 🎨 Cross-Method Similarity Matrix")
        
        sim_matrix = np.array(cross_method["similarity_matrix"])
        
        fig_heatmap = px.imshow(
            sim_matrix,
            title="Cross-Method Similarity Heatmap",
            color_continuous_scale="Blues",
            aspect="auto"
        )
        fig_heatmap.update_layout(
            xaxis_title="Microsoft RAG Chunks",
            yaxis_title="Docling Chunks"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)
    
    # Statistical analysis
    stats_analysis = comparison_data.get("statistical_analysis", {})
    if stats_analysis:
        st.markdown("### 📈 Statistical Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Docling Statistics**")
            docling_stats = stats_analysis.get("docling_stats", {})
            st.json(docling_stats)
        
        with col2:
            st.markdown("**Microsoft RAG Statistics**")
            microsoft_stats = stats_analysis.get("microsoft_stats", {})
            st.json(microsoft_stats)
    
    # Chunk analysis
    chunk_analysis = comparison_data.get("chunk_analysis", [])
    if chunk_analysis:
        st.markdown("### 📝 Per-Chunk Analysis")
        
        chunk_df = pd.DataFrame(chunk_analysis)
        
        # Similarity by chunk
        fig_chunk = px.bar(
            chunk_df,
            x="chunk_index",
            y="cosine_similarity",
            title="Cosine Similarity by Chunk",
            hover_data=["text_length", "text_preview"]
        )
        st.plotly_chart(fig_chunk, use_container_width=True)
        
        # Show detailed chunk data
        with st.expander("Detailed Chunk Analysis"):
            st.dataframe(chunk_df)


def process_document_page(pipeline):
    """Document processing page."""
    st.header("📄 Document Processing")
    
    uploaded_file = st.file_uploader(
        "Choose a document file",
        type=['pdf', 'txt', 'docx', 'pptx', 'jpg', 'jpeg', 'png'],
        help="Upload a document to process through the Multi-RAG pipeline"
    )
    
    compare_methods = st.checkbox(
        "Compare embedding methods",
        value=True,
        help="Perform comparison between Docling and Microsoft RAG embeddings"
    )
    
    if uploaded_file is not None:
        # Display file info
        st.write(f"**File:** {uploaded_file.name}")
        st.write(f"**Size:** {uploaded_file.size:,} bytes")
        st.write(f"**Type:** {uploaded_file.type}")
        
        if st.button("Process Document", type="primary"):
            with st.spinner("Processing document..."):
                try:
                    # Save uploaded file temporarily
                    import tempfile
                    import shutil
                    
                    temp_dir = Path(tempfile.mkdtemp())
                    temp_file = temp_dir / uploaded_file.name
                    
                    with open(temp_file, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    
                    # Process document
                    result = pipeline.process_document(str(temp_file), compare_methods=compare_methods)
                    
                    # Clean up
                    shutil.rmtree(temp_dir)
                    
                    st.success("Document processed successfully!")
                    
                    # Display results
                    st.subheader("📊 Processing Results")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Status", result.get("status", "unknown"))
                    with col2:
                        st.metric("Docling Embeddings", result.get("docling_embeddings", 0))
                    with col3:
                        st.metric("Microsoft Embeddings", result.get("microsoft_embeddings", 0))
                    
                    # Show document details
                    if "document" in result:
                        with st.expander("Document Details"):
                            st.json(result["document"])
                    
                    # Show comparison results
                    if "comparison" in result:
                        display_comparison_results(result["comparison"])
                    
                except Exception as e:
                    st.error(f"Processing failed: {e}")


def search_documents_page(pipeline):
    """Document search page."""
    st.header("🔍 Document Search")
    
    # Search form
    with st.form("search_form"):
        query_text = st.text_area(
            "Enter your search query:",
            placeholder="What are you looking for?",
            height=100
        )
        
        col1, col2 = st.columns(2)
        with col1:
            method = st.selectbox(
                "Embedding Method:",
                ["docling", "microsoft"],
                help="Choose which embedding method to use for search"
            )
        
        with col2:
            limit = st.slider(
                "Number of results:",
                min_value=1,
                max_value=20,
                value=5
            )
        
        search_button = st.form_submit_button("Search", type="primary")
    
    if search_button and query_text:
        with st.spinner("Searching..."):
            try:
                results = pipeline.search_similar(
                    query_text=query_text,
                    method=method,
                    k=limit
                )
                
                if results:
                    st.subheader(f"📋 Found {len(results)} results")
                    
                    for i, result in enumerate(results, 1):
                        with st.expander(f"Result {i} - Similarity: {result['similarity']:.3f}"):
                            doc = result["document"]
                            
                            col1, col2 = st.columns([2, 1])
                            
                            with col1:
                                st.write(f"**File:** {doc['file_name']}")
                                st.write(f"**Type:** {doc['file_type']}")
                                st.write(f"**Size:** {doc['file_size']:,} bytes")
                                st.write(f"**Chunks:** {doc['num_chunks']}")
                                st.write(f"**Processed:** {doc['processed_at']}")
                            
                            with col2:
                                st.metric("Similarity Score", f"{result['similarity']:.3f}")
                                st.metric("Method Used", result['method_used'])
                            
                            # Show chunk metadata
                            if result.get("chunk_metadata"):
                                st.json(result["chunk_metadata"])
                else:
                    st.warning("No matching documents found.")
                    
            except Exception as e:
                st.error(f"Search failed: {e}")


def documents_management_page(pipeline):
    """Documents management page."""
    st.header("📚 Document Management")
    
    # Get documents list
    try:
        documents = pipeline.db_manager.list_documents(limit=100)
        
        if not documents:
            st.info("No documents found. Upload some documents to get started!")
            return
        
        # Convert to DataFrame for display
        df = pd.DataFrame(documents)
        
        # Display summary
        st.subheader("📊 Documents Overview")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Documents", len(df))
        with col2:
            avg_chunks = df["num_chunks"].mean() if "num_chunks" in df else 0
            st.metric("Avg. Chunks", f"{avg_chunks:.1f}")
        with col3:
            total_size = df["file_size"].sum() if "file_size" in df else 0
            st.metric("Total Size", f"{total_size / 1024 / 1024:.1f} MB")
        
        # File type distribution
        if "file_type" in df:
            fig_pie = px.pie(
                df, 
                names="file_type", 
                title="Document Types Distribution"
            )
            st.plotly_chart(fig_pie, use_container_width=True)
        
        # Documents table
        st.subheader("📋 Documents List")
        
        # Select columns to display
        display_columns = ["id", "file_name", "file_type", "file_size", "num_chunks", "processed_at"]
        available_columns = [col for col in display_columns if col in df.columns]
        
        # Format the dataframe
        display_df = df[available_columns].copy()
        if "file_size" in display_df:
            display_df["file_size"] = display_df["file_size"].apply(lambda x: f"{x / 1024:.1f} KB")
        
        # Show table with selection
        selected_rows = st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True
        )
        
        # Document actions
        st.subheader("📋 Document Actions")
        
        doc_id = st.selectbox(
            "Select document for actions:",
            options=df["id"].tolist(),
            format_func=lambda x: f"ID {x}: {df[df['id'] == x]['file_name'].iloc[0]}"
        )
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("View Details"):
                document = pipeline.db_manager.get_document(doc_id)
                embeddings = pipeline.db_manager.get_embeddings(doc_id)
                comparison = pipeline.db_manager.get_comparison(doc_id)
                
                st.json({
                    "document": document,
                    "embeddings_count": len(embeddings),
                    "has_comparison": comparison is not None
                })
        
        with col2:
            if st.button("View Comparison"):
                comparison = pipeline.db_manager.get_comparison(doc_id)
                if comparison:
                    display_comparison_results(comparison["comparison_results"])
                else:
                    st.warning("No comparison available for this document.")
        
        with col3:
            if st.button("Export Data"):
                document = pipeline.db_manager.get_document(doc_id)
                embeddings = pipeline.db_manager.get_embeddings(doc_id)
                comparison = pipeline.db_manager.get_comparison(doc_id)
                
                export_data = {
                    "document": document,
                    "embeddings": embeddings,
                    "comparison": comparison
                }
                
                # Create download button
                json_str = json.dumps(export_data, indent=2, default=str)
                st.download_button(
                    label="Download JSON",
                    data=json_str,
                    file_name=f"document_{doc_id}_export.json",
                    mime="application/json"
                )
        
    except Exception as e:
        st.error(f"Failed to load documents: {e}")


def analytics_page(pipeline):
    """Analytics and insights page."""
    st.header("📊 Analytics & Insights")
    
    try:
        stats = pipeline.get_pipeline_stats()
        
        # Overall statistics
        display_stats(pipeline)
        
        # Get documents for analysis
        documents = pipeline.db_manager.list_documents(limit=100)
        
        if documents:
            df = pd.DataFrame(documents)
            
            # Processing timeline
            if "processed_at" in df:
                st.subheader("📈 Processing Timeline")
                df["processed_date"] = pd.to_datetime(df["processed_at"]).dt.date
                timeline_data = df.groupby("processed_date").size().reset_index()
                timeline_data.columns = ["Date", "Documents"]
                
                fig_timeline = px.line(
                    timeline_data,
                    x="Date",
                    y="Documents",
                    title="Documents Processed Over Time"
                )
                st.plotly_chart(fig_timeline, use_container_width=True)
            
            # File size distribution
            if "file_size" in df:
                st.subheader("📏 File Size Distribution")
                fig_size = px.histogram(
                    df,
                    x="file_size",
                    title="File Size Distribution",
                    nbins=20
                )
                fig_size.update_xaxis(title="File Size (bytes)")
                st.plotly_chart(fig_size, use_container_width=True)
            
            # Chunks analysis
            if "num_chunks" in df:
                st.subheader("🔢 Chunks Analysis")
                fig_chunks = px.box(
                    df,
                    y="num_chunks",
                    title="Number of Chunks per Document"
                )
                st.plotly_chart(fig_chunks, use_container_width=True)
        
        # Model information
        st.subheader("🤖 Model Information")
        
        models_info = stats.get("models", {})
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Docling Model**")
            docling_info = models_info.get("docling", {})
            st.json(docling_info)
        
        with col2:
            st.markdown("**Microsoft RAG Model**")
            microsoft_info = models_info.get("microsoft", {})
            st.json(microsoft_info)
        
    except Exception as e:
        st.error(f"Failed to load analytics: {e}")


def main():
    """Main Streamlit application."""
    st.title("🔍 Multi-RAG Document Pipeline")
    st.markdown("Cross-platform pipeline for comparing Docling vs Microsoft RAG embeddings")
    
    # Initialize pipeline
    pipeline = initialize_pipeline()
    
    if pipeline is None:
        st.error("Failed to initialize pipeline. Please check the configuration.")
        return
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Choose a page:",
        [
            "📄 Process Documents",
            "🔍 Search Documents", 
            "📚 Manage Documents",
            "📊 Analytics"
        ]
    )
    
    # Display current stats in sidebar
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📈 Quick Stats")
    try:
        stats = pipeline.get_pipeline_stats()
        st.sidebar.metric("Documents", stats.get("database", {}).get("total_documents", 0))
        st.sidebar.metric("Embeddings", stats.get("database", {}).get("total_embeddings", 0))
        st.sidebar.metric("Comparisons", stats.get("database", {}).get("total_comparisons", 0))
    except:
        st.sidebar.warning("Stats unavailable")
    
    # Route to appropriate page
    if page == "📄 Process Documents":
        process_document_page(pipeline)
    elif page == "🔍 Search Documents":
        search_documents_page(pipeline)
    elif page == "📚 Manage Documents":
        documents_management_page(pipeline)
    elif page == "📊 Analytics":
        analytics_page(pipeline)


if __name__ == "__main__":
    main()