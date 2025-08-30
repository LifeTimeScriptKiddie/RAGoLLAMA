"""Login command implementation."""
from ..auth import token_manager, AuthenticationError
from ..printing import print_user_info, print_error


def login_command() -> int:
    """
    Execute the login command using device code flow.
    
    Returns:
        0 on success, 1 on error
    """
    try:
        print("Starting Microsoft Teams login using device code flow...")
        user_info = token_manager.login()
        print_user_info(user_info)
        return 0
        
    except AuthenticationError as e:
        print_error(str(e))
        return 1
    except Exception as e:
        print_error(f"Unexpected error during login: {e}")
        return 1