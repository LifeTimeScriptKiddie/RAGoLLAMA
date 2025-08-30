"""Me command implementation."""
from ..graph import graph_client, GraphAPIError
from ..endpoints import me_endpoint
from ..printing import print_user_info, print_json, print_error


def me_command(output_json: bool = False) -> int:
    """
    Execute the me command to get current user information.
    
    Args:
        output_json: Whether to output raw JSON instead of formatted text
    
    Returns:
        0 on success, 1 on error
    """
    try:
        user_data = graph_client.get(me_endpoint())
        
        if output_json:
            print_json(user_data)
        else:
            print_user_info(user_data)
        
        return 0
        
    except GraphAPIError as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Unexpected error retrieving user info: {e}")
        return 1