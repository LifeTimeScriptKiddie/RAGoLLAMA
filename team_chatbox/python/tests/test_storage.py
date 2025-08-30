"""Unit tests for storage utilities."""
import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, Mock
import os

from teams_cli.storage import (
    get_app_data_dir,
    get_delta_file_path,
    save_delta_link,
    load_delta_link,
    save_app_settings,
    load_app_settings,
    clear_app_data
)


@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path, ignore_errors=True)


def test_get_app_data_dir_windows():
    with patch('os.name', 'nt'):
        with patch('os.getenv', return_value='C:\\Users\\test\\AppData\\Local'):
            result = get_app_data_dir()
            expected = Path('C:\\Users\\test\\AppData\\Local\\teams-cli')
            assert result == expected


def test_get_app_data_dir_fallback():
    with patch('os.name', 'posix'):
        with patch('pathlib.Path.home', return_value=Path('/home/test')):
            result = get_app_data_dir()
            expected = Path('/home/test/.teams-cli')
            assert result == expected


def test_get_delta_file_path():
    chat_id = "19:test-chat-id@thread.v2"
    
    with patch('teams_cli.storage.get_app_data_dir') as mock_get_dir:
        mock_dir = Path('/test/teams-cli')
        mock_get_dir.return_value = mock_dir
        
        result = get_delta_file_path(chat_id)
        
        # Should sanitize the chat ID for filename
        expected = mock_dir / "delta-19test-chat-idthreadv2.txt"
        assert result == expected


def test_save_and_load_delta_link(temp_dir):
    chat_id = "test-chat-123"
    delta_link = "https://graph.microsoft.com/v1.0/me/chats/delta?token=abc123"
    
    with patch('teams_cli.storage.get_app_data_dir', return_value=temp_dir):
        # Save delta link
        save_delta_link(chat_id, delta_link)
        
        # Load delta link
        result = load_delta_link(chat_id)
        
        assert result == delta_link


def test_load_delta_link_not_found(temp_dir):
    with patch('teams_cli.storage.get_app_data_dir', return_value=temp_dir):
        result = load_delta_link("nonexistent-chat")
        assert result is None


def test_load_delta_link_file_error(temp_dir):
    chat_id = "test-chat-123"
    
    with patch('teams_cli.storage.get_app_data_dir', return_value=temp_dir):
        # Create a directory with the same name as the expected file
        delta_file = get_delta_file_path(chat_id)
        delta_file.mkdir(parents=True)
        
        # Should handle the error gracefully
        result = load_delta_link(chat_id)
        assert result is None


def test_save_and_load_app_settings(temp_dir):
    settings = {
        "last_used_chat": "test-chat-123",
        "theme": "dark",
        "notifications": True
    }
    
    with patch('teams_cli.storage.get_app_data_dir', return_value=temp_dir):
        # Save settings
        save_app_settings(settings)
        
        # Load settings
        result = load_app_settings()
        
        assert result == settings


def test_load_app_settings_not_found(temp_dir):
    with patch('teams_cli.storage.get_app_data_dir', return_value=temp_dir):
        result = load_app_settings()
        assert result == {}


def test_save_app_settings_error(temp_dir):
    settings = {"test": "value"}
    
    # Mock the app data dir to return a non-writable location
    with patch('teams_cli.storage.get_app_data_dir', return_value=Path('/invalid/path')):
        with patch('builtins.print') as mock_print:
            save_app_settings(settings)
            # Should print warning but not raise exception
            mock_print.assert_called_once()
            assert "Warning: Could not save settings" in str(mock_print.call_args)


def test_clear_app_data(temp_dir):
    # Create some test data
    with patch('teams_cli.storage.get_app_data_dir', return_value=temp_dir):
        save_delta_link("test-chat", "test-delta-link")
        save_app_settings({"test": "value"})
        
        # Verify data exists
        assert (temp_dir / "settings.json").exists()
        assert any(temp_dir.glob("delta-*.txt"))
        
        # Clear data
        clear_app_data()
        
        # Verify data is gone
        assert not temp_dir.exists()


def test_clear_app_data_error():
    # Test clearing non-existent directory
    with patch('teams_cli.storage.get_app_data_dir', return_value=Path('/nonexistent/path')):
        with patch('builtins.print') as mock_print:
            clear_app_data()
            # Should not raise exception, but may print warning
            # (depending on implementation details)


def test_delta_file_path_sanitization():
    # Test various problematic chat IDs
    test_cases = [
        ("19:test@thread.v2", "delta-19testthreadv2.txt"),
        ("chat-with/slashes", "delta-chat-withslashes.txt"),
        ("chat:with:colons", "delta-chatwithcolons.txt"),
        ("chat with spaces", "delta-chatwithspaces.txt"),
        ("chat<with>brackets", "delta-chatwithbrackets.txt"),
        ("chat|with|pipes", "delta-chatwithpipes.txt"),
        ("normal-chat-123", "delta-normal-chat-123.txt")
    ]
    
    with patch('teams_cli.storage.get_app_data_dir') as mock_get_dir:
        mock_dir = Path('/test')
        mock_get_dir.return_value = mock_dir
        
        for chat_id, expected_filename in test_cases:
            result = get_delta_file_path(chat_id)
            assert result.name == expected_filename
            assert result.parent == mock_dir


def test_save_delta_link_with_whitespace(temp_dir):
    chat_id = "test-chat"
    delta_link = "  https://graph.microsoft.com/delta?token=abc  \n"
    
    with patch('teams_cli.storage.get_app_data_dir', return_value=temp_dir):
        save_delta_link(chat_id, delta_link)
        result = load_delta_link(chat_id)
        
        # Should strip whitespace when saving and loading
        assert result == delta_link.strip()