import requests
import logging
import os
from typing import Optional, List, Dict
from config import OPEN_WEBUI_URL, HEADERS

#crontab -e
#0 2 * * * /usr/bin/python3 /app/uploader.py >> /app/docs/upload.log 2>&1

# Set paths
DOCS_FOLDER = os.getenv("UPLOAD_FOLDER_PATH", "./docs")
LOG_PATH = os.path.join(DOCS_FOLDER, "upload.log")

# Configure logging to file
os.makedirs(DOCS_FOLDER, exist_ok=True)
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# Supported file extensions
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

    # Check if it already exists
    existing = list_knowledge_bases()
    for kb in existing:
        if kb.get("name") == kb_name:
            logging.info(f"Using existing knowledge base: {kb_name}")
            return kb.get("id")

    # Create new
    url = f"{OPEN_WEBUI_URL}/api/knowledge"
    payload = {"name": kb_name, "description": kb_desc}
    try:
        res = requests.post(url, headers=HEADERS, json=payload, timeout=10)
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

    url = f"{OPEN_WEBUI_URL}/api/knowledge/{knowledge_id}/documents"
    try:
        with open(filepath, "rb") as f:
            files = {"file": f}
            headers = {"Authorization": HEADERS.get("Authorization", "")}
            res = requests.post(url, headers=headers, files=files, timeout=30)
            res.raise_for_status()
            return res.json()
    except requests.RequestException as e:
        logging.error(f"Upload failed for '{filepath}': {e}")
        return None


def sync_folder_to_knowledge(folder_path: str, knowledge_id: str) -> None:
    if not os.path.isdir(folder_path):
        logging.error(f"Invalid folder path: {folder_path}")
        return

    all_files = [
        f for f in os.listdir(folder_path)
        if os.path.isfile(os.path.join(folder_path, f)) and f.lower().endswith(SUPPORTED_EXTENSIONS)
    ]

    if not all_files:
        logging.warning(f"No supported files found in {folder_path}")
        return

    uploaded, failed = 0, []

    for filename in all_files:
        full_path = os.path.join(folder_path, filename)
        result = upload_file(knowledge_id, full_path)
        if result:
            uploaded += 1
            logging.info(f"[+] Uploaded: {filename}")
        else:
            failed.append(filename)

    logging.info("\n=== Upload Summary ===")
    logging.info(f"Total files found: {len(all_files)}")
    logging.info(f"Successfully uploaded: {uploaded}")
    if failed:
        logging.warning(f"Failed uploads: {failed}")


if __name__ == "__main__":
    logging.info("📁 Starting sync of ./docs to Open WebUI...")
    kb_id = get_or_create_default_kb()

    if not kb_id:
        logging.error("❌ Could not find or create a knowledge base. Exiting.")
        exit(1)

    sync_folder_to_knowledge(DOCS_FOLDER, kb_id)
    logging.info("✅ Sync complete.")