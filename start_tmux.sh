#!/bin/bash

SESSION="rag_session"
VENV_ACTIVATE="./venv/bin/activate"
PYTHON_CMD="streamlit run streamlit_app.py"

# Create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "🔧 Creating virtual environment..."
    python3 -m venv venv
fi

# Create tmux session
tmux new-session -d -s $SESSION

# Pane 0: start ollama
tmux send-keys -t $SESSION:0 'ollama serve' C-m

# Split the window vertically (pane 1)
tmux split-window -h -t $SESSION:0

# Activate venv and start Python app in pane 1
tmux send-keys -t $SESSION:0.1 "source $VENV_ACTIVATE && pip install --upgrade pip && pip install -r requirements.txt && $PYTHON_CMD" C-m

# Attach to the tmux session
tmux attach -t $SESSION
