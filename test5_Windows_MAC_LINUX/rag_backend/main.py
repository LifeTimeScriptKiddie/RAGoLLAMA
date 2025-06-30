import subprocess
import sys
from pathlib import Path

def run_command(cmd):
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e}")

def setup():
    print("[*] Setting up virtual environment and installing dependencies...")
    venv_path = Path("venv")
    if not venv_path.exists():
        run_command([sys.executable, "-m", "venv", "venv"])

    if sys.platform == "win32":
        pip_exec = "venv\\Scripts\\pip"
        python_exec = "venv\\Scripts\\python"
    else:
        pip_exec = "venv/bin/pip"
        python_exec = "venv/bin/python"

    # Ensure pip exists
    if not Path(pip_exec).exists():
        print("[*] Pip not found in venv. Bootstrapping with ensurepip...")
        run_command([python_exec, "-m", "ensurepip", "--upgrade"])

    run_command([pip_exec, "install", "--upgrade", "pip"])
    run_command([pip_exec, "install", "-r", "requirements.txt"])

    return python_exec

def main():
    python_exec = setup()

    print("[*] Pulling Ollama model...")
    run_command(["ollama", "pull", "mistral"])

    print("[*] Vectorizing documents...")
    run_command([python_exec, "vectorizer.py"])

    print("[*] Launching document processor...")
    run_command([python_exec, "doc_processor.py"])

    print("[*] Uploading to WebUI...")
    run_command([python_exec, "uploader.py"])

if __name__ == "__main__":
    main()
