"""Console output formatting utilities."""
import json
import shutil
from datetime import datetime
from typing import Any, Dict, List, Optional
from rich.console import Console
from rich.table import Table
from rich.text import Text


console = Console()


def print_json(data: Any, indent: int = 2) -> None:
    """Print data as formatted JSON."""
    print(json.dumps(data, indent=indent, ensure_ascii=False))


def print_user_info(user_data: Dict[str, Any]) -> None:
    """Print user information in a readable format."""
    console.print(f"[green]✓[/green] Signed in successfully")
    console.print(f"Display Name: {user_data.get('displayName', 'N/A')}")
    console.print(f"User Principal Name: {user_data.get('userPrincipalName', 'N/A')}")
    console.print(f"User ID: {user_data.get('id', 'N/A')}")


def print_chats_table(chats_data: Dict[str, Any], output_json: bool = False) -> None:
    """Print chats list in table format or JSON."""
    if output_json:
        print_json(chats_data)
        return
    
    chats = chats_data.get("value", [])
    if not chats:
        console.print("No chats found.")
        return
    
    table = Table(title="Microsoft Teams Chats")
    table.add_column("Chat ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="magenta")
    table.add_column("Topic/Name", style="green")
    table.add_column("Last Message Preview", style="yellow")
    table.add_column("Last Updated", style="blue")
    
    for chat in chats:
        chat_id = chat.get("id", "")[:20] + "..." if len(chat.get("id", "")) > 20 else chat.get("id", "")
        chat_type = chat.get("chatType", "N/A")
        
        # Get topic or construct name from members
        topic = chat.get("topic") or "N/A"
        if topic == "N/A" and chat_type == "oneOnOne":
            # For one-on-one chats, show member names if available
            members = chat.get("members", [])
            if len(members) >= 2:
                names = [m.get("displayName", "Unknown") for m in members[:2]]
                topic = " & ".join(names)
        
        # Get last message preview
        last_message = chat.get("lastMessagePreview", {})
        preview = "N/A"
        if last_message:
            preview = last_message.get("body", {}).get("content", "")[:50]
            if len(preview) > 47:
                preview += "..."
        
        # Format last activity time
        last_updated = "N/A"
        if "lastUpdatedDateTime" in chat:
            try:
                dt = datetime.fromisoformat(chat["lastUpdatedDateTime"].replace("Z", "+00:00"))
                last_updated = dt.strftime("%Y-%m-%d %H:%M")
            except:
                last_updated = chat["lastUpdatedDateTime"]
        
        table.add_row(chat_id, chat_type, topic, preview, last_updated)
    
    console.print(table)
    console.print(f"\nShowing {len(chats)} chats")


def print_message_sent(message_id: str) -> None:
    """Print confirmation that message was sent."""
    console.print(f"[green]✓[/green] Message sent successfully")
    console.print(f"Message ID: {message_id}")


def print_chat_message(
    timestamp: str,
    sender: str,
    content: str,
    message_type: Optional[str] = None
) -> None:
    """Print a chat message in a readable format."""
    # Format timestamp
    try:
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S") + "Z"
    except:
        formatted_time = timestamp
    
    # Clean HTML content for console display
    clean_content = _clean_html_content(content)
    
    # Print message with colors
    time_text = Text(f"[{formatted_time}]", style="dim blue")
    sender_text = Text(f"{sender}:", style="bold green")
    message_text = Text(clean_content, style="white")
    
    console.print(time_text, sender_text, message_text, sep=" ")


def print_error(message: str) -> None:
    """Print error message in red."""
    console.print(f"[red]✗ Error:[/red] {message}")


def print_warning(message: str) -> None:
    """Print warning message in yellow."""
    console.print(f"[yellow]⚠ Warning:[/yellow] {message}")


def print_info(message: str) -> None:
    """Print info message in blue."""
    console.print(f"[blue]ℹ Info:[/blue] {message}")


def print_success(message: str) -> None:
    """Print success message in green."""
    console.print(f"[green]✓[/green] {message}")


def _clean_html_content(content: str) -> str:
    """Clean HTML tags and entities from message content for console display."""
    if not content:
        return ""
    
    import re
    
    # Remove HTML tags
    content = re.sub(r'<[^>]+>', '', content)
    
    # Replace common HTML entities
    replacements = {
        '&lt;': '<',
        '&gt;': '>',
        '&amp;': '&',
        '&quot;': '"',
        '&#39;': "'",
        '&nbsp;': ' ',
    }
    
    for entity, replacement in replacements.items():
        content = content.replace(entity, replacement)
    
    # Clean up extra whitespace
    content = re.sub(r'\s+', ' ', content).strip()
    
    return content


def get_terminal_width() -> int:
    """Get terminal width for formatting."""
    try:
        return shutil.get_terminal_size().columns
    except:
        return 80  # fallback width