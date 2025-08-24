#!/bin/bash

# RattGoLLAMA Model Download Script
# Downloads popular models for Ollama

set -e

echo "🦙 RattGoLLAMA Model Downloader"
echo "================================"

# Check if Ollama container is running
if ! docker compose ps ollama | grep -q "Up"; then
    echo "❌ Error: Ollama container is not running"
    echo "Please start the system first: docker compose up -d"
    exit 1
fi

echo "📥 Downloading additional models..."

# Popular chat models
MODELS=(
    "llama3.1:8b"           # Latest Llama 3.1 8B
    "llama3.1:70b"          # Latest Llama 3.1 70B (large)
    "qwen2.5:7b"            # Qwen2.5 - excellent coding
    "deepseek-coder:6.7b"   # DeepSeek Coder
    "starcoder2:3b"         # StarCoder2 for coding
    "vicuna:7b"             # Vicuna chat model
    "dolphin-mixtral:8x7b"  # Dolphin Mixtral
    "neural-chat:7b"        # Neural Chat
    "orca-mini:3b"          # Orca Mini (small and fast)
    "tinydolphin:1.1b"      # Tiny model for testing
)

# Function to download model
download_model() {
    local model=$1
    echo "⬇️  Downloading $model..."
    if docker compose exec ollama ollama pull "$model"; then
        echo "✅ Successfully downloaded $model"
    else
        echo "❌ Failed to download $model"
    fi
    echo ""
}

echo "Select models to download:"
echo "1) Essential models (recommended)"
echo "2) All models (large download ~50GB+)"
echo "3) Custom selection"
echo "4) List available models"

read -p "Choose option (1-4): " choice

case $choice in
    1)
        # Essential models - good balance of capability and size
        ESSENTIAL_MODELS=(
            "llama3.1:8b"
            "qwen2.5:7b" 
            "deepseek-coder:6.7b"
            "orca-mini:3b"
            "tinydolphin:1.1b"
        )
        echo "📦 Downloading essential models..."
        for model in "${ESSENTIAL_MODELS[@]}"; do
            download_model "$model"
        done
        ;;
    2)
        echo "📦 Downloading all models (this will take a while)..."
        for model in "${MODELS[@]}"; do
            download_model "$model"
        done
        ;;
    3)
        echo "Available models:"
        for i in "${!MODELS[@]}"; do
            echo "$((i+1))) ${MODELS[i]}"
        done
        echo ""
        read -p "Enter model numbers separated by spaces (e.g., 1 3 5): " selections
        
        for num in $selections; do
            if [[ $num -ge 1 && $num -le ${#MODELS[@]} ]]; then
                model="${MODELS[$((num-1))]}"
                download_model "$model"
            else
                echo "❌ Invalid selection: $num"
            fi
        done
        ;;
    4)
        echo "📋 Currently available models:"
        docker compose exec ollama ollama list
        echo ""
        echo "🌐 Browse more models at: https://ollama.com/library"
        ;;
    *)
        echo "❌ Invalid option"
        exit 1
        ;;
esac

echo ""
echo "✨ Model download complete!"
echo "📋 View downloaded models: docker compose exec ollama ollama list"
echo "🌐 Access Open WebUI at: http://localhost:3001"
echo "🎯 Access main interface at: http://localhost:8080"