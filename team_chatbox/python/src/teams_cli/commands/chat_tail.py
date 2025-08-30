"""Chat tail command implementation for streaming messages."""
import time
import signal
import sys
from typing import Optional, Dict, Any, List
from pathlib import Path

from ..graph import graph_client, GraphAPIError
from ..endpoints import chat_messages_delta_endpoint, delta_link_to_url
from ..storage import load_delta_link, save_delta_link
from ..printing import print_chat_message, print_error, print_info, print_warning


class TailInterrupted(Exception):
    """Exception raised when tail operation is interrupted."""
    pass


def chat_tail_command(
    chat_id: str,
    since_file: Optional[str] = None,
    timeout_sec: int = 0
) -> int:
    """
    Execute the chat tail command to stream new messages from a chat.
    
    Args:
        chat_id: The Teams chat ID to tail
        since_file: Optional path to custom delta file (overrides default)
        timeout_sec: Timeout in seconds (0 means run until interrupted)
    
    Returns:
        0 on success, 1 on error
    """
    # Set up signal handler for graceful interruption
    def signal_handler(signum, frame):
        raise TailInterrupted()
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        delta_link = _load_or_initialize_delta_link(chat_id, since_file)
        
        print_info(f"Tailing chat {chat_id[:20]}...")
        print_info("Press Ctrl+C to stop")
        print()
        
        start_time = time.time()
        
        while True:
            # Check timeout
            if timeout_sec > 0 and (time.time() - start_time) >= timeout_sec:
                print_info("Timeout reached. Stopping tail operation.")
                break
            
            # Get new messages using delta
            messages, new_delta_link = _get_delta_messages(delta_link)
            
            # Print new messages
            if messages:
                for message in messages:
                    _print_message(message)
            
            # Update delta link
            if new_delta_link and new_delta_link != delta_link:
                delta_link = new_delta_link
                _save_delta_link_with_fallback(chat_id, delta_link, since_file)
            
            # Wait before next poll (with some backoff for rate limiting)
            time.sleep(2)
        
        return 0
        
    except TailInterrupted:
        print_info("\nTail operation interrupted by user.")
        return 0
    except GraphAPIError as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Unexpected error during tail operation: {e}")
        return 1


def _load_or_initialize_delta_link(
    chat_id: str,
    since_file: Optional[str] = None
) -> str:
    """Load existing delta link or initialize with first delta call."""
    # Try to load existing delta link
    if since_file:
        # Load from custom file
        try:
            since_path = Path(since_file)
            if since_path.exists():
                with open(since_path, 'r', encoding='utf-8') as f:
                    delta_link = f.read().strip()
                    if delta_link:
                        return delta_link
        except Exception as e:
            print_warning(f"Could not load delta from {since_file}: {e}")
    else:
        # Load from default storage
        delta_link = load_delta_link(chat_id)
        if delta_link:
            return delta_link
    
    # Initialize with first delta call
    print_info("Initializing delta tracking...")
    endpoint = chat_messages_delta_endpoint(chat_id)
    
    try:
        response = graph_client.get(endpoint)
        delta_link = response.get("@odata.deltaLink", "")
        
        if delta_link:
            _save_delta_link_with_fallback(chat_id, delta_link, since_file)
            print_info("Delta tracking initialized.")
        
        # Print any existing messages from initial call
        messages = response.get("value", [])
        if messages:
            print_info(f"Found {len(messages)} recent messages:")
            for message in messages:
                _print_message(message)
        
        return delta_link
        
    except GraphAPIError as e:
        raise GraphAPIError(f"Failed to initialize delta tracking: {e}")


def _get_delta_messages(delta_link: str) -> tuple[List[Dict[str, Any]], str]:
    """
    Get new messages using delta link.
    
    Returns:
        Tuple of (messages list, new delta link)
    """
    if not delta_link:
        return [], ""
    
    try:
        url = delta_link_to_url(delta_link)
        response = graph_client.get(url)
        
        messages = response.get("value", [])
        new_delta_link = response.get("@odata.deltaLink", delta_link)
        
        return messages, new_delta_link
        
    except GraphAPIError as e:
        # If delta link is invalid, we might need to reinitialize
        if "400" in str(e) or "invalid" in str(e).lower():
            print_warning("Delta link expired or invalid. Reinitializing...")
            return [], ""
        raise


def _print_message(message: Dict[str, Any]) -> None:
    """Print a single chat message."""
    try:
        # Extract message details
        message_id = message.get("id", "")
        created_time = message.get("createdDateTime", "")
        
        # Get sender information
        sender_info = message.get("from", {})
        sender = "Unknown"
        if sender_info:
            user_info = sender_info.get("user", {})
            sender = user_info.get("displayName") or user_info.get("userPrincipalName", "Unknown")
        
        # Get message content
        body = message.get("body", {})
        content = body.get("content", "")
        
        # Skip empty messages or system messages
        if not content.strip():
            return
        
        # Print the message
        print_chat_message(created_time, sender, content)
        
    except Exception as e:
        print_warning(f"Error printing message: {e}")


def _save_delta_link_with_fallback(
    chat_id: str,
    delta_link: str,
    custom_file: Optional[str] = None
) -> None:
    """Save delta link with fallback options."""
    if custom_file:
        # Save to custom file
        try:
            custom_path = Path(custom_file)
            custom_path.parent.mkdir(parents=True, exist_ok=True)
            with open(custom_path, 'w', encoding='utf-8') as f:
                f.write(delta_link)
        except Exception as e:
            print_warning(f"Could not save delta to {custom_file}: {e}")
            # Fall back to default storage
            save_delta_link(chat_id, delta_link)
    else:
        # Save to default storage
        save_delta_link(chat_id, delta_link)