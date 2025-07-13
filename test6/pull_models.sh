#!/bin/bash

# Script to pull optimized Ollama models for the Financial Advisor Suite
# Optimized for systems with 5.5GB memory - total models: ~6GB

echo "🤖 Pulling optimized Ollama models..."
echo "📊 Memory-optimized collection for 5.5GB systems"
echo "This may take some time depending on your internet connection."
echo ""

# Function to pull a model with error handling
pull_model() {
    local model=$1
    echo "📦 Pulling $model..."
    
    # Check if model is already pulled
    if docker exec ollama_test6 ollama list | grep -q "$model"; then
        echo "✅ $model already exists, skipping"
        return 0
    fi
    
    # Use gtimeout if available (brew install coreutils), otherwise regular pull
    if command -v gtimeout &> /dev/null; then
        if gtimeout 900 docker exec ollama_test6 ollama pull "$model"; then
            echo "✅ Successfully pulled $model"
        else
            echo "❌ Failed to pull $model (timeout or error)"
            echo "💡 You can continue manually with: docker exec ollama_test6 ollama pull $model"
        fi
    else
        if docker exec ollama_test6 ollama pull "$model"; then
            echo "✅ Successfully pulled $model"
        else
            echo "❌ Failed to pull $model"
            echo "💡 You can continue manually with: docker exec ollama_test6 ollama pull $model"
        fi
    fi
    echo ""
}

# Check if container is running
if ! docker ps | grep -q "ollama_test6"; then
    echo "❌ Ollama container is not running. Please start with 'docker compose up -d'"
    exit 1
fi

echo "📋 Available models before pulling:"
docker exec ollama_test6 ollama list
echo ""

# Pull optimized models in order of preference (smallest to largest)
echo "🚀 Starting optimized model downloads..."
echo "📈 Models ordered by size: 397MB → 637MB → 1.3GB → 1.6GB → 2.2GB"
echo ""

# Ultra-lightweight models (fast responses)
echo "⚡ Phase 1: Ultra-lightweight models"
pull_model "qwen2.5:0.5b"      # 397MB - Ultra-fast responses
pull_model "tinyllama:latest"  # 637MB - Lightweight general tasks

# Balanced models (recommended default)
echo "🎯 Phase 2: Balanced performance models"
pull_model "llama3.2:1b"       # 1.3GB - Best balance (RECOMMENDED DEFAULT)

# Specialized models
echo "🔧 Phase 3: Specialized models"
pull_model "codegemma:2b"      # 1.6GB - Coding/technical documentation

# Capable models (best performance)
echo "💪 Phase 4: High-performance models"
pull_model "phi3:latest"       # 2.2GB - Most capable responses

# Large models (commented out - too big for 5.5GB systems)
echo "⚠️  Large models (disabled for memory optimization):"
echo "   # mistral:7b-instruct-q4_0  # 4.1GB - Too large for 5.5GB systems"
echo "   # gemma:latest              # 5.0GB - Too large for 5.5GB systems"
echo "   # llama3.1:latest           # 4.7GB - Too large for 5.5GB systems"

echo "📋 Available models after pulling:"
docker exec ollama_test6 ollama list
echo ""

echo "🎉 Optimized model collection complete!"
echo "💡 Total: 5 models (~6.1GB) - Perfect for 5.5GB memory systems"
echo ""
echo "🎯 Model Usage Guide:"
echo "   • qwen2.5:0.5b (397MB)   - Ultra-fast responses, simple queries"
echo "   • tinyllama (637MB)      - Lightweight general tasks" 
echo "   • llama3.2:1b (1.3GB)   - RECOMMENDED DEFAULT - Best balance"
echo "   • codegemma:2b (1.6GB)   - Programming & technical questions"
echo "   • phi3 (2.2GB)          - Most capable, complex analysis"
echo ""
echo "🚀 Your Financial Advisor Suite is ready with optimized LLM capabilities!"
echo ""
echo "📝 To pull additional models manually:"
echo "   docker exec ollama_test6 ollama pull <model-name>"
echo ""
echo "💾 Memory tip: Only one model runs at a time, so all models fit in 5.5GB systems"
echo "🔗 Browse more models: https://ollama.com/library"