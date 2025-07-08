import os
import sqlite3
import hashlib
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from .ingestion import ingest
from .vector_store import add as vector_add
import threading
import time
import schedule

logger = logging.getLogger(__name__)

class DocumentManager:
    """Manages automatic document loading and monitoring"""
    
    def __init__(self, docs_path: str = "/app/docs", db_path: str = "/app/data/documents.db"):
        self.docs_path = Path(docs_path)
        self.db_path = db_path
        self.docs_path.mkdir(parents=True, exist_ok=True)
        self.init_db()
        self.scheduler_running = False
        
    def init_db(self):
        """Initialize document tracking database"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT UNIQUE NOT NULL,
            filepath TEXT NOT NULL,
            file_hash TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            last_modified TIMESTAMP NOT NULL,
            processed_at TIMESTAMP NOT NULL,
            status TEXT NOT NULL,
            error_message TEXT,
            metadata TEXT
        )
        ''')
        
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS processing_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP NOT NULL,
            action TEXT NOT NULL,
            filename TEXT,
            status TEXT NOT NULL,
            message TEXT
        )
        ''')
        
        conn.commit()
        conn.close()
        
    def calculate_file_hash(self, filepath: Path) -> str:
        """Calculate SHA256 hash of file"""
        hash_sha256 = hashlib.sha256()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating hash for {filepath}: {str(e)}")
            return ""
    
    def log_processing_event(self, action: str, filename: str = None, status: str = "success", message: str = ""):
        """Log processing events"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
        INSERT INTO processing_log (timestamp, action, filename, status, message)
        VALUES (?, ?, ?, ?, ?)
        ''', (datetime.now().isoformat(), action, filename, status, message))
        
        conn.commit()
        conn.close()
    
    def is_document_processed(self, filepath: Path) -> bool:
        """Check if document has been processed and is up to date"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        # Get file stats
        try:
            stat = filepath.stat()
            current_hash = self.calculate_file_hash(filepath)
            
            cursor.execute('''
            SELECT file_hash, file_size, last_modified, status 
            FROM documents 
            WHERE filename = ?
            ''', (filepath.name,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                stored_hash, stored_size, stored_modified, status = result
                # Check if file has changed
                if (stored_hash == current_hash and 
                    stored_size == stat.st_size and 
                    status == "success"):
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking document status for {filepath}: {str(e)}")
            conn.close()
            return False
    
    def process_document(self, filepath: Path) -> bool:
        """Process a single document"""
        try:
            logger.info(f"Processing document: {filepath.name}")
            
            # Ingest document
            docs = ingest(str(filepath))
            
            if not docs:
                raise Exception("No documents returned from ingestion")
            
            # Add to vector store
            texts = []
            for doc in docs:
                if hasattr(doc, 'text') and doc.text:
                    texts.append(doc.text)
            
            if texts:
                vector_add(texts)
                logger.info(f"Added {len(texts)} text chunks to vector store")
            else:
                raise Exception("No text content found in document")
            
            # Update database
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            stat = filepath.stat()
            file_hash = self.calculate_file_hash(filepath)
            
            # Store document metadata
            doc_metadata = {
                "text_chunks": len(texts),
                "processing_method": docs[0].metadata.get("method", "unknown") if docs else "unknown",
                "file_type": filepath.suffix.lower()
            }
            
            cursor.execute('''
            INSERT OR REPLACE INTO documents 
            (filename, filepath, file_hash, file_size, last_modified, processed_at, status, error_message, metadata)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filepath.name,
                str(filepath),
                file_hash,
                stat.st_size,
                datetime.fromtimestamp(stat.st_mtime).isoformat(),
                datetime.now().isoformat(),
                "success",
                None,
                json.dumps(doc_metadata)
            ))
            
            conn.commit()
            conn.close()
            
            self.log_processing_event("process_document", filepath.name, "success", 
                                    f"Processed {len(texts)} text chunks")
            
            return True
            
        except Exception as e:
            error_msg = f"Error processing {filepath.name}: {str(e)}"
            logger.error(error_msg)
            
            # Log error to database
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            cursor = conn.cursor()
            
            try:
                stat = filepath.stat()
                file_hash = self.calculate_file_hash(filepath)
                
                cursor.execute('''
                INSERT OR REPLACE INTO documents 
                (filename, filepath, file_hash, file_size, last_modified, processed_at, status, error_message, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    filepath.name,
                    str(filepath),
                    file_hash,
                    stat.st_size,
                    datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    datetime.now().isoformat(),
                    "error",
                    str(e),
                    json.dumps({"error": True})
                ))
                
                conn.commit()
            except Exception as db_error:
                logger.error(f"Error logging to database: {str(db_error)}")
            finally:
                conn.close()
            
            self.log_processing_event("process_document", filepath.name, "error", str(e))
            
            return False
    
    def scan_and_process_documents(self) -> Dict[str, Any]:
        """Scan docs folder and process new/modified documents"""
        logger.info(f"Scanning documents in {self.docs_path}")
        
        results = {
            "total_found": 0,
            "processed": 0,
            "skipped": 0,
            "errors": 0,
            "files_processed": [],
            "files_skipped": [],
            "files_errors": []
        }
        
        # Supported file extensions
        supported_extensions = {'.pdf', '.txt', '.md', '.docx', '.doc'}
        
        try:
            # Find all supported files
            all_files = []
            for ext in supported_extensions:
                all_files.extend(self.docs_path.glob(f'**/*{ext}'))
            
            results["total_found"] = len(all_files)
            
            self.log_processing_event("scan_start", message=f"Found {len(all_files)} documents")
            
            for filepath in all_files:
                if self.is_document_processed(filepath):
                    logger.info(f"Skipping already processed document: {filepath.name}")
                    results["skipped"] += 1
                    results["files_skipped"].append(filepath.name)
                    continue
                
                if self.process_document(filepath):
                    results["processed"] += 1
                    results["files_processed"].append(filepath.name)
                else:
                    results["errors"] += 1
                    results["files_errors"].append(filepath.name)
            
            self.log_processing_event("scan_complete", 
                                    message=f"Processed: {results['processed']}, Skipped: {results['skipped']}, Errors: {results['errors']}")
            
            logger.info(f"Document scan complete. Processed: {results['processed']}, Skipped: {results['skipped']}, Errors: {results['errors']}")
            
        except Exception as e:
            logger.error(f"Error during document scan: {str(e)}")
            self.log_processing_event("scan_error", message=str(e), status="error")
            
        return results
    
    def get_document_status(self) -> List[Dict[str, Any]]:
        """Get status of all tracked documents"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT filename, filepath, file_size, last_modified, processed_at, status, error_message, metadata
        FROM documents
        ORDER BY processed_at DESC
        ''')
        
        documents = []
        for row in cursor.fetchall():
            filename, filepath, file_size, last_modified, processed_at, status, error_message, metadata = row
            
            doc_info = {
                "filename": filename,
                "filepath": filepath,
                "file_size": file_size,
                "last_modified": last_modified,
                "processed_at": processed_at,
                "status": status,
                "error_message": error_message,
                "metadata": json.loads(metadata) if metadata else {}
            }
            documents.append(doc_info)
        
        conn.close()
        return documents
    
    def get_processing_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent processing log entries"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT timestamp, action, filename, status, message
        FROM processing_log
        ORDER BY timestamp DESC
        LIMIT ?
        ''', (limit,))
        
        logs = []
        for row in cursor.fetchall():
            timestamp, action, filename, status, message = row
            logs.append({
                "timestamp": timestamp,
                "action": action,
                "filename": filename,
                "status": status,
                "message": message
            })
        
        conn.close()
        return logs
    
    def start_scheduler(self):
        """Start the scheduled document processing"""
        if self.scheduler_running:
            return
        
        # Schedule daily processing at 2 AM
        schedule.every().day.at("02:00").do(self.scheduled_processing)
        
        self.scheduler_running = True
        
        def run_scheduler():
            while self.scheduler_running:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        
        # Start scheduler in background thread
        scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        scheduler_thread.start()
        
        logger.info("Document scheduler started - will process documents daily at 2:00 AM")
    
    def scheduled_processing(self):
        """Scheduled processing function"""
        logger.info("Starting scheduled document processing at 2 AM")
        self.log_processing_event("scheduled_processing", message="Starting scheduled scan")
        
        results = self.scan_and_process_documents()
        
        self.log_processing_event("scheduled_processing", 
                                status="success",
                                message=f"Scheduled processing complete: {results['processed']} processed, {results['errors']} errors")
    
    def startup_processing(self):
        """Process documents at startup"""
        logger.info("Starting initial document processing at startup")
        self.log_processing_event("startup_processing", message="Starting startup scan")
        
        results = self.scan_and_process_documents()
        
        self.log_processing_event("startup_processing", 
                                status="success",
                                message=f"Startup processing complete: {results['processed']} processed, {results['errors']} errors")
        
        return results

# Global instance
document_manager = DocumentManager()