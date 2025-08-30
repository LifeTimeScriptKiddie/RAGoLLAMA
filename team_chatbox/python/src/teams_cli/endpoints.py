"""Microsoft Graph API endpoint URL builders."""
from typing import Optional
from urllib.parse import quote

from .config import config


def me_endpoint() -> str:
    """Get /me endpoint URL."""
    return "/me"


def me_chats_endpoint(top: Optional[int] = None) -> str:
    """Get /me/chats endpoint URL with optional $top parameter."""
    url = "/me/chats"
    if top:
        url += f"?$top={top}"
    return url


def chat_messages_endpoint(chat_id: str) -> str:
    """Get /chats/{chatId}/messages endpoint URL."""
    return f"/chats/{quote(chat_id, safe='')}/messages"


def chat_messages_delta_endpoint(chat_id: str) -> str:
    """Get /chats/{chatId}/messages/delta endpoint URL."""
    return f"/chats/{quote(chat_id, safe='')}/messages/delta"


def delta_link_to_url(delta_link: str) -> str:
    """Convert a delta link to a full URL or return as-is if already absolute."""
    if delta_link.startswith("http"):
        return delta_link
    
    # If it's a relative URL, prepend the Graph base URL
    if delta_link.startswith("/"):
        return f"{config.graph_base_url}{delta_link}"
    
    # If it's just a query string, append to base URL
    if delta_link.startswith("?"):
        return f"{config.graph_base_url}/me/chats{delta_link}"
    
    return delta_link


def build_teams_chat_deep_link(
    chat_id: str,
    message: Optional[str] = None,
    tenant_id: Optional[str] = None
) -> str:
    """Build a Microsoft Teams deep link for a chat."""
    # Use configured tenant ID if not provided
    if not tenant_id:
        tenant_id = config.tenant_id
    
    # Base deep link format for Teams
    base_url = f"https://teams.microsoft.com/l/chat/0/0"
    
    # Add chat ID as a parameter
    params = [f"chatId={quote(chat_id, safe='')}"]
    
    # Add tenant ID if available
    if tenant_id and tenant_id != "YOUR_TENANT_GUID_OR_DOMAIN":
        params.append(f"tenantId={quote(tenant_id, safe='')}")
    
    # Add pre-filled message if provided
    if message:
        params.append(f"message={quote(message, safe='')}")
    
    # Construct full URL
    if params:
        return f"{base_url}?{'&'.join(params)}"
    
    return base_url


def build_teams_desktop_deep_link(chat_id: str) -> str:
    """Build a Microsoft Teams desktop app deep link."""
    # Teams desktop protocol handler
    return f"msteams:/l/chat/0/0?chatId={quote(chat_id, safe='')}"