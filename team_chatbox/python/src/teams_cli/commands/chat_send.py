"""Chat send command implementation."""
from typing import Dict, Any

from ..graph import graph_client, GraphAPIError
from ..endpoints import chat_messages_endpoint
from ..printing import print_message_sent, print_error


def chat_send_command(
    chat_id: str,
    text: str,
    use_html: bool = False
) -> int:
    """
    Execute the chat send command to send a message to a chat.
    
    Args:
        chat_id: The Teams chat ID to send message to
        text: The message text content
        use_html: Whether to send as HTML content type
    
    Returns:
        0 on success, 1 on error
    """
    try:
        # Prepare message body
        message_body = _build_message_body(text, use_html)
        
        # Send message via Microsoft Graph
        endpoint = chat_messages_endpoint(chat_id)
        response = graph_client.post(endpoint, message_body)
        
        # Extract message ID from response
        message_id = response.get("id", "unknown")
        print_message_sent(message_id)
        
        return 0
        
    except GraphAPIError as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Unexpected error sending message: {e}")
        return 1


def _build_message_body(text: str, use_html: bool = False) -> Dict[str, Any]:
    """
    Build the message body for Microsoft Graph API.
    
    Args:
        text: The message text content
        use_html: Whether to use HTML content type
    
    Returns:
        Message body dictionary for Graph API
    """
    content_type = "html" if use_html else "text"
    
    return {
        "body": {
            "contentType": content_type,
            "content": text
        }
    }