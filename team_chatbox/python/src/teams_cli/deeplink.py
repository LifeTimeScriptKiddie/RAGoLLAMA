"""Microsoft Teams deep link functionality."""
import webbrowser
from typing import Optional
from urllib.parse import quote

from .config import config
from .printing import print_info, print_error


def open_teams_chat(
    chat_id: str,
    message: Optional[str] = None,
    use_desktop: bool = True
) -> bool:
    """
    Open a Microsoft Teams chat using deep links.
    
    Args:
        chat_id: The Teams chat ID to open
        message: Optional pre-filled message text
        use_desktop: Whether to try desktop app first
    
    Returns:
        True if the link was opened successfully, False otherwise
    """
    try:
        if use_desktop:
            # Try Teams desktop protocol first
            desktop_url = _build_desktop_deep_link(chat_id, message)
            print_info(f"Opening Teams desktop app...")
            
            try:
                webbrowser.open(desktop_url)
                return True
            except Exception:
                print_info("Desktop app not available, trying web version...")
        
        # Fall back to web version
        web_url = _build_web_deep_link(chat_id, message)
        print_info(f"Opening Teams in web browser...")
        webbrowser.open(web_url)
        return True
        
    except Exception as e:
        print_error(f"Failed to open Teams chat: {e}")
        return False


def _build_desktop_deep_link(chat_id: str, message: Optional[str] = None) -> str:
    """Build a Microsoft Teams desktop app deep link."""
    # Teams desktop protocol handler
    base_url = f"msteams:/l/chat/0/0"
    params = [f"chatId={quote(chat_id, safe='')}"]
    
    # Add tenant ID if available
    if config.tenant_id and config.tenant_id != "YOUR_TENANT_GUID_OR_DOMAIN":
        params.append(f"tenantId={quote(config.tenant_id, safe='')}")
    
    # Add pre-filled message if provided
    if message:
        params.append(f"message={quote(message, safe='')}")
    
    if params:
        return f"{base_url}?{'&'.join(params)}"
    
    return base_url


def _build_web_deep_link(chat_id: str, message: Optional[str] = None) -> str:
    """Build a Microsoft Teams web app deep link."""
    # Teams web app deep link format
    base_url = "https://teams.microsoft.com/l/chat/0/0"
    params = [f"chatId={quote(chat_id, safe='')}"]
    
    # Add tenant ID if available
    if config.tenant_id and config.tenant_id != "YOUR_TENANT_GUID_OR_DOMAIN":
        params.append(f"tenantId={quote(config.tenant_id, safe='')}")
    
    # Add pre-filled message if provided
    if message:
        params.append(f"message={quote(message, safe='')}")
    
    if params:
        return f"{base_url}?{'&'.join(params)}"
    
    return base_url


def print_deep_link_urls(chat_id: str, message: Optional[str] = None) -> None:
    """Print both desktop and web deep link URLs for manual use."""
    desktop_url = _build_desktop_deep_link(chat_id, message)
    web_url = _build_web_deep_link(chat_id, message)
    
    print_info("Teams Deep Links:")
    print(f"Desktop: {desktop_url}")
    print(f"Web:     {web_url}")