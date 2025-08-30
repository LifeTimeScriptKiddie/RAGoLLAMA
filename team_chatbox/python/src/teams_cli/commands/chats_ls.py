"""Chats list command implementation."""
from typing import Optional

from ..graph import graph_client, GraphAPIError
from ..endpoints import me_chats_endpoint
from ..printing import print_chats_table, print_error


def chats_ls_command(top: Optional[int] = None, output_json: bool = False) -> int:
    """
    Execute the chats ls command to list user's chats.
    
    Args:
        top: Maximum number of chats to retrieve
        output_json: Whether to output raw JSON instead of formatted table
    
    Returns:
        0 on success, 1 on error
    """
    try:
        # Get chats from Microsoft Graph
        chats_data = graph_client.get(me_chats_endpoint(top=top))
        
        # Print results
        print_chats_table(chats_data, output_json=output_json)
        
        return 0
        
    except GraphAPIError as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Unexpected error retrieving chats: {e}")
        return 1