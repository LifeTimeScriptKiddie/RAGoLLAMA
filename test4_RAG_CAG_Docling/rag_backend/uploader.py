import requests
import logging
import os
from typing import Optional, List, Dict
from config import OPEN_WEBUI_URL, HEADERS

# Constants
DOCS_FOLDER = os.getenv("UPLOAD_FOLDER_PATH", "./docs")
LOG_PATH = os.path.join(DOCS_FOLDER, "upload.log")
RECORD_PATH = os.path.join(DOCS_FOLDER, "uploaded_files.txt")

# Ensure docs folder exists
os.makedirs(DOCS_FOLDER, exist_ok=True)

# Configure logging
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Supported file types
SUPPORTED_EXTENSIONS = (
    ".pdf", ".md", ".docx", ".txt", ".html", ".csv", ".epub",
    ".jpg", ".jpeg", ".png", ".gif", ".webp"
)

def list_knowledge_bases() -> List[Dict]:
    url = f"{OPEN_WEBUI_URL}/api/knowledge"
    try:
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        return res.json()
    except requests.RequestException as e:
        logging.error(f"Error listing knowledge bases: {e}")
        return []

def get_or_create_default_kb() -> Optional[str]:
    kb_name = os.getenv("DEFAULT_KB_NAME", "AutoKB")
    kb_desc = os.getenv("DEFAULT_KB_DESC", "Uploaded by uploader.py")
    existing = list_knowledge_bases()
    for kb in existing:
        if kb.get("name") == kb_name:
            logging.info(f"Using existing knowledge base: {kb_name}")
            return kb.get("id")
    try:
        res = requests.post(
            f"{OPEN_WEBUI_URL}/api/knowledge",
            headers=HEADERS,
            json={"name": kb_name, "description": kb_desc},
            timeout=10
        )
        res.raise_for_status()
        new_kb = res.json()
        logging.info(f"Created new knowledge base: {kb_name}")
        return new_kb.get("id")
    except requests.RequestException as e:
        logging.error(f"Failed to create knowledge base '{kb_name}': {e}")
        return None

def upload_file(knowledge_id: str, filepath: str) -> Optional[Dict]:
    if not os.path.isfile(filepath):
        logging.warning(f"File not found: {filepath}")
        return None

    ext = os.path.splitext(filepath)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        logging.warning(f"Unsupported file type skipped: {filepath}")
        return None

    try:
        with open(filepath, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": HEADERS.get("Authorization", "")}
            res = requests.post(
                f"{OPEN_WEBUI_URL}/api/knowledge/{knowledge_id}/documents",
                headers=headers,
                files=files,
                timeout=30
            )
            res.raise_for_status()
            return res.json()
    except requests.RequestException as e:
        logging.error(f"Upload failed for '{filepath}': {e}")
        return None

def load_uploaded_file_list() -> set:
    if not os.path.exists(RECORD_PATH):
        return set()
    with open(RECORD_PATH, "r") as f:
        return set(line.strip() for line in f.readlines())

def save_uploaded_file(filepath: str):
    with open(RECORD_PATH, "a") as f:
        f.write(filepath + "\n")

def sync_folder_to_knowledge(folder_path: str, knowledge_id: str) -> None:
    if not os.path.isdir(folder_path):
        logging.error(f"Invalid folder: {folder_path}")
        return

    uploaded_files = load_uploaded_file_list()

    all_files = [
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f))
        and f.lower().endswith(SUPPORTED_EXTENSIONS)
        and f not in uploaded_files
    ]

    if not all_files:
        logging.info(f"No new files to upload in {folder_path}")
        return

    uploaded, failed = 0, []

    for filename in all_files:
        full_path = os.path.join(folder_path, filename)
        result = upload_file(knowledge_id, full_path)
        if result:
            uploaded += 1
            logging.info(f"[+] Uploaded: {filename}")
            save_uploaded_file(filename)
        else:
            failed.append(filename)

    logging.info("\n=== Upload Summary ===")
    logging.info(f"New files found: {len(all_files)}")
    logging.info(f"Successfully uploaded: {uploaded}")
    if failed:
        logging.warning(f"Failed uploads: {failed}")

if __name__ == "__main__":
    logging.info("📁 Starting upload of new documents in ./docs")
    kb_id = get_or_create_default_kb()
    if not kb_id:
        logging.error("❌ Failed to retrieve or create knowledge base.")
        exit(1)
    sync_folder_to_knowledge(DOCS_FOLDER, kb_id)
    logging.info("✅ Sync complete.")