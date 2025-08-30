"""Main CLI application entry point using Typer."""
import sys
import logging
from typing import Optional
from pathlib import Path

import typer
import colorama

from .commands.login import login_command
from .commands.me import me_command
from .commands.chats_ls import chats_ls_command
from .commands.chat_send import chat_send_command
from .commands.chat_tail import chat_tail_command
from .deeplink import open_teams_chat
from .printing import print_error, print_success

# Initialize colorama for Windows color support
colorama.init()

# Create the main Typer app
app = typer.Typer(
    name="teams-cli",
    help="Microsoft Teams CLI for Windows with MSAL authentication",
    no_args_is_help=True
)

# Create subcommand groups
chat_app = typer.Typer(name="chat", help="Chat-related commands")
chats_app = typer.Typer(name="chats", help="Chats listing commands")

app.add_typer(chat_app)
app.add_typer(chats_app)


@app.command()
def login():
    """Start device code authentication flow."""
    exit_code = login_command()
    raise typer.Exit(exit_code)


@app.command()
def me(
    json: bool = typer.Option(
        False, 
        "--json", 
        help="Output raw JSON instead of formatted text"
    )
):
    """Get current user information."""
    exit_code = me_command(output_json=json)
    raise typer.Exit(exit_code)


@chats_app.command("ls")
def chats_ls(
    top: Optional[int] = typer.Option(
        None,
        "--top",
        help="Maximum number of chats to retrieve"
    ),
    json: bool = typer.Option(
        False,
        "--json", 
        help="Output raw JSON instead of formatted table"
    )
):
    """List user's Teams chats."""
    exit_code = chats_ls_command(top=top, output_json=json)
    raise typer.Exit(exit_code)


@chat_app.command("send")
def chat_send(
    chat_id: str = typer.Option(
        ...,
        "--chat",
        help="Teams chat ID to send message to"
    ),
    text: str = typer.Option(
        ...,
        "--text",
        help="Message text content"
    ),
    html: bool = typer.Option(
        False,
        "--html",
        help="Send as HTML content type instead of plain text"
    )
):
    """Send a message to a Teams chat."""
    exit_code = chat_send_command(chat_id=chat_id, text=text, use_html=html)
    raise typer.Exit(exit_code)


@chat_app.command("tail")
def chat_tail(
    chat_id: str = typer.Option(
        ...,
        "--chat",
        help="Teams chat ID to tail"
    ),
    since: Optional[str] = typer.Option(
        None,
        "--since",
        help="Path to custom delta file (overrides default)"
    ),
    timeout_sec: int = typer.Option(
        0,
        "--timeout-sec",
        help="Timeout in seconds (0 means run until Ctrl+C)"
    )
):
    """Stream new messages from a Teams chat using delta queries."""
    exit_code = chat_tail_command(
        chat_id=chat_id,
        since_file=since,
        timeout_sec=timeout_sec
    )
    raise typer.Exit(exit_code)


@app.command()
def open(
    chat_id: str = typer.Option(
        ...,
        "--chat",
        help="Teams chat ID to open"
    ),
    message: Optional[str] = typer.Option(
        None,
        "--message",
        help="Pre-filled message text (URL encoded)"
    )
):
    """Open a Teams chat using deep links."""
    try:
        success = open_teams_chat(chat_id=chat_id, message=message)
        if success:
            print_success("Teams chat opened successfully")
            raise typer.Exit(0)
        else:
            raise typer.Exit(1)
    except Exception as e:
        print_error(f"Failed to open Teams chat: {e}")
        raise typer.Exit(1)


@app.callback()
def main_callback(
    verbose: bool = typer.Option(
        False,
        "--verbose", "-v",
        help="Enable verbose logging"
    ),
    quiet: bool = typer.Option(
        False,
        "--quiet", "-q",
        help="Suppress all output except errors"
    )
):
    """Microsoft Teams CLI for Windows with MSAL authentication."""
    # Configure logging
    if verbose:
        logging.basicConfig(level=logging.DEBUG)
    elif quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        logging.basicConfig(level=logging.WARNING)


def main():
    """Main entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        print_error("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()