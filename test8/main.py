#!/usr/bin/env python3
"""
Multi-RAG Document Pipeline - Main Entry Point

This is the main entry point for the Multi-RAG Document Pipeline application.
It supports multiple interfaces: CLI, API, Streamlit web interface, and integration
with external tools like OpenWebUI.
"""

import argparse
import sys
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any

# Set up Python path
sys.path.insert(0, str(Path(__file__).parent))

def setup_logging(config: Dict[str, Any]):
    """Set up logging configuration."""
    log_level = config.get("general", {}).get("log_level", "INFO")
    logs_path = Path(config.get("cache", {}).get("logs_path", "/app/logs"))
    logs_path.mkdir(parents=True, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=getattr(logging, log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(logs_path / "application.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured with level: {log_level}")

def load_config(config_path: str = "config/config.json") -> Dict[str, Any]:
    """Load configuration from file."""
    config_file = Path(config_path)
    
    if config_file.exists():
        with open(config_file) as f:
            config = json.load(f)
        print(f"Configuration loaded from {config_path}")
    else:
        # Default configuration
        config = {
            "general": {"log_level": "INFO"},
            "database": {"db_path": "/app/cache/documents.db"},
            "document_processing": {
                "max_chunk_size": 1000,
                "chunk_overlap": 200,
                "supported_formats": [".pdf", ".txt", ".docx", ".pptx", ".jpg", ".png"]
            },
            "embeddings": {"dimension": 384},
            "vector_store": {
                "faiss_index_path": "/app/cache/faiss",
                "index_type": "HNSW"
            },
            "ollama": {
                "ollama_url": "http://localhost:11434",
                "default_model": "llama2"
            },
            "api": {"host": "0.0.0.0", "port": 8000},
            "streamlit": {"host": "0.0.0.0", "port": 8501},
            "cache": {
                "faiss_index_path": "/app/cache/faiss",
                "logs_path": "/app/logs"
            }
        }
        print(f"Using default configuration (config file not found: {config_path})")
    
    # Override with environment variables
    if "OLLAMA_URL" in os.environ:
        config["ollama"]["ollama_url"] = os.environ["OLLAMA_URL"]
    
    if "DB_PATH" in os.environ:
        config["database"]["db_path"] = os.environ["DB_PATH"]
    
    if "FAISS_INDEX_PATH" in os.environ:
        config["vector_store"]["faiss_index_path"] = os.environ["FAISS_INDEX_PATH"]
        config["cache"]["faiss_index_path"] = os.environ["FAISS_INDEX_PATH"]
    
    return config

def run_cli(config: Dict[str, Any], args):
    """Run the CLI interface."""
    from interfaces.cli.main import cli
    
    # Prepare CLI arguments
    cli_args = []
    if args.config:
        cli_args.extend(['--config', args.config])
    
    # Add any additional CLI arguments
    if hasattr(args, 'cli_args') and args.cli_args:
        cli_args.extend(args.cli_args)
    
    # Run CLI
    try:
        cli(cli_args, standalone_mode=False)
    except SystemExit:
        pass

def run_api(config: Dict[str, Any]):
    """Run the FastAPI server."""
    import uvicorn
    from interfaces.api.main import app
    
    api_config = config.get("api", {})
    host = api_config.get("host", "0.0.0.0")
    port = api_config.get("port", 8000)
    
    print(f"Starting API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")

def run_streamlit(config: Dict[str, Any]):
    """Run the Streamlit web interface."""
    import subprocess
    
    streamlit_config = config.get("streamlit", {})
    host = streamlit_config.get("host", "0.0.0.0")
    port = streamlit_config.get("port", 8501)
    
    # Set environment variables for Streamlit
    env = os.environ.copy()
    env["STREAMLIT_SERVER_ADDRESS"] = host
    env["STREAMLIT_SERVER_PORT"] = str(port)
    
    print(f"Starting Streamlit server on {host}:{port}")
    
    # Run Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", 
            "interfaces/streamlit/app.py",
            "--server.address", host,
            "--server.port", str(port)
        ], env=env, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)

def setup_environment(config: Dict[str, Any]):
    """Set up the application environment."""
    # Create necessary directories
    cache_config = config.get("cache", {})
    
    directories = [
        cache_config.get("faiss_index_path", "/app/cache/faiss"),
        cache_config.get("documents_cache_path", "/app/cache/documents"),
        cache_config.get("logs_path", "/app/logs"),
        Path(config.get("database", {}).get("db_path", "/app/cache/documents.db")).parent
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
    
    print("Environment setup complete")

def check_dependencies():
    """Check if required dependencies are available."""
    required_packages = [
        "numpy", "pandas", "scikit-learn", "sentence_transformers",
        "faiss", "PyPDF2", "python-docx", "python-pptx", "Pillow",
        "pytesseract", "python-magic", "fastapi", "uvicorn", 
        "streamlit", "requests", "click", "rich"
    ]
    
    missing_packages = []
    for package in required_packages:
        try:
            __import__(package.replace("-", "_"))
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        print(f"Warning: Missing packages: {', '.join(missing_packages)}")
        print("Install them with: pip install -r requirements.txt")
        return False
    
    return True

def main():
    """Main application entry point."""
    parser = argparse.ArgumentParser(
        description="Multi-RAG Document Pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run CLI interface
  python main.py --interface cli

  # Run API server
  python main.py --interface api

  # Run Streamlit web interface
  python main.py --interface streamlit

  # Run with custom config
  python main.py --interface api --config custom_config.json

  # CLI with specific commands
  python main.py --interface cli -- process document.pdf --method both --compare
        """
    )
    
    parser.add_argument(
        "--interface", "-i",
        choices=["cli", "api", "streamlit"],
        default="cli",
        help="Interface to run (default: cli)"
    )
    
    parser.add_argument(
        "--config", "-c",
        default="config/config.json",
        help="Configuration file path (default: config/config.json)"
    )
    
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Check dependencies and exit"
    )
    
    # Parse known args to separate main args from CLI args
    args, unknown_args = parser.parse_known_args()
    
    # Store CLI args for passing to CLI interface
    args.cli_args = unknown_args
    
    # Check dependencies if requested
    if args.check_deps:
        if check_dependencies():
            print("All dependencies are available")
            sys.exit(0)
        else:
            sys.exit(1)
    
    # Load configuration
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error loading configuration: {e}")
        sys.exit(1)
    
    # Set up logging
    setup_logging(config)
    logger = logging.getLogger(__name__)
    logger.info("Application starting")
    
    # Set up environment
    setup_environment(config)
    
    # Check dependencies (warn but don't exit)
    check_dependencies()
    
    try:
        # Run the selected interface
        if args.interface == "cli":
            run_cli(config, args)
        elif args.interface == "api":
            run_api(config)
        elif args.interface == "streamlit":
            run_streamlit(config)
        else:
            print(f"Unknown interface: {args.interface}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nApplication interrupted by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Application error: {e}", exc_info=True)
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()