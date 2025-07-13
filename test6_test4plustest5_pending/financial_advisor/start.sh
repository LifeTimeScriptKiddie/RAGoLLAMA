#!/bin/bash

# Start the Financial Advisor application with both Streamlit and Knowledge Base API

echo "🚀 Starting Financial Advisor Suite..."

# Set Python path
export PYTHONPATH=/app

# Start Knowledge Base API in background
echo "📚 Starting Knowledge Base API on port 8502..."
cd /app && python -m uvicorn core.webui_integration:app --host 0.0.0.0 --port 8502 --reload &

# Wait a moment for the API to start
sleep 3

# Start Streamlit
echo "🌐 Starting Streamlit interface on port 8501..."
streamlit run /app/financial_advisor/app.py --server.port 8501 --server.address 0.0.0.0

# Keep the script running
wait