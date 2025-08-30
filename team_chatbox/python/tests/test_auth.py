"""Unit tests for authentication module."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import json
from datetime import datetime, timedelta

from teams_cli.auth import TokenManager, AuthenticationError


@pytest.fixture
def mock_config():
    with patch('teams_cli.auth.config') as mock_config:
        mock_config.tenant_id = "test-tenant"
        mock_config.client_id = "test-client-id"
        mock_config.authority = "https://login.microsoftonline.com/test-tenant"
        mock_config.scopes = ["Chat.ReadBasic", "Chat.ReadWrite"]
        mock_config.graph_base_url = "https://graph.microsoft.com/v1.0"
        yield mock_config


@pytest.fixture
def token_manager(mock_config):
    with patch('teams_cli.auth.PublicClientApplication') as mock_pca:
        mock_app = Mock()
        mock_pca.return_value = mock_app
        
        tm = TokenManager()
        tm.app = mock_app
        return tm


def test_token_manager_initialization(mock_config):
    with patch('teams_cli.auth.PublicClientApplication') as mock_pca:
        mock_app = Mock()
        mock_pca.return_value = mock_app
        
        tm = TokenManager()
        
        mock_pca.assert_called_once_with(
            client_id="test-client-id",
            authority="https://login.microsoftonline.com/test-tenant"
        )


def test_is_token_valid_with_valid_token(token_manager):
    # Token that expires in 10 minutes
    future_timestamp = datetime.now().timestamp() + 600
    token = {
        "access_token": "valid_token",
        "expires_in": 3600,
        "_expires_at": future_timestamp
    }
    
    assert token_manager._is_token_valid(token) is True


def test_is_token_valid_with_expired_token(token_manager):
    # Token that expired 10 minutes ago
    past_timestamp = datetime.now().timestamp() - 600
    token = {
        "access_token": "expired_token",
        "expires_in": 3600,
        "_expires_at": past_timestamp
    }
    
    assert token_manager._is_token_valid(token) is False


def test_is_token_valid_with_near_expiry_token(token_manager):
    # Token that expires in 2 minutes (within 5 minute buffer)
    near_future_timestamp = datetime.now().timestamp() + 120
    token = {
        "access_token": "near_expiry_token",
        "expires_in": 3600,
        "_expires_at": near_future_timestamp
    }
    
    assert token_manager._is_token_valid(token) is False


def test_login_success(token_manager):
    # Mock device flow
    mock_flow = {
        "user_code": "ABC123",
        "message": "Go to https://microsoft.com/devicelogin and enter ABC123"
    }
    token_manager.app.initiate_device_flow.return_value = mock_flow
    
    # Mock successful token acquisition
    mock_token = {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600
    }
    token_manager.app.acquire_token_by_device_flow.return_value = mock_token
    
    # Mock user info response
    mock_user_info = {
        "userPrincipalName": "test@example.com",
        "displayName": "Test User"
    }
    
    with patch('teams_cli.auth.requests.get') as mock_get:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_info
        mock_get.return_value = mock_response
        
        with patch.object(token_manager, '_save_token_to_keyring'):
            result = token_manager.login()
    
    assert result == mock_user_info
    assert token_manager._cached_token == mock_token
    assert token_manager._account_name == "test@example.com"


def test_login_device_flow_failure(token_manager):
    # Mock device flow failure
    token_manager.app.initiate_device_flow.return_value = {}
    
    with pytest.raises(AuthenticationError, match="Failed to create device flow"):
        token_manager.login()


def test_login_token_acquisition_failure(token_manager):
    # Mock successful device flow
    mock_flow = {
        "user_code": "ABC123",
        "message": "Go to https://microsoft.com/devicelogin and enter ABC123"
    }
    token_manager.app.initiate_device_flow.return_value = mock_flow
    
    # Mock failed token acquisition
    mock_error_response = {
        "error": "invalid_grant",
        "error_description": "User cancelled authentication"
    }
    token_manager.app.acquire_token_by_device_flow.return_value = mock_error_response
    
    with pytest.raises(AuthenticationError, match="Authentication failed"):
        token_manager.login()


def test_get_access_token_with_cached_valid_token(token_manager):
    # Set up valid cached token
    future_timestamp = datetime.now().timestamp() + 600
    token_manager._cached_token = {
        "access_token": "cached_token",
        "expires_in": 3600,
        "_expires_at": future_timestamp
    }
    
    result = token_manager.get_access_token()
    assert result == "cached_token"


def test_get_access_token_missing_config(token_manager):
    with patch('teams_cli.auth.config') as mock_config:
        mock_config.tenant_id = ""
        mock_config.client_id = ""
        
        with pytest.raises(AuthenticationError, match="Missing configuration"):
            token_manager.get_access_token()


def test_refresh_token_success(token_manager):
    # Mock accounts and silent token acquisition
    mock_account = {"username": "test@example.com"}
    token_manager.app.get_accounts.return_value = [mock_account]
    
    mock_refreshed_token = {
        "access_token": "refreshed_token",
        "refresh_token": "new_refresh_token",
        "expires_in": 3600
    }
    token_manager.app.acquire_token_silent.return_value = mock_refreshed_token
    
    old_token = {"refresh_token": "old_refresh_token"}
    result = token_manager._refresh_token(old_token)
    
    assert result == mock_refreshed_token


def test_refresh_token_failure(token_manager):
    # Mock no accounts
    token_manager.app.get_accounts.return_value = []
    
    old_token = {"refresh_token": "old_refresh_token"}
    result = token_manager._refresh_token(old_token)
    
    assert result is None


@patch('teams_cli.auth.keyring')
def test_save_token_to_keyring(mock_keyring, token_manager):
    token = {
        "access_token": "test_token",
        "expires_in": 3600
    }
    
    token_manager._save_token_to_keyring("test@example.com", token)
    
    mock_keyring.set_password.assert_called_once()
    args = mock_keyring.set_password.call_args[0]
    assert args[0] == "teams-cli"
    assert args[1] == "test@example.com"
    
    # Verify JSON contains the token data
    saved_data = json.loads(args[2])
    assert saved_data["access_token"] == "test_token"
    assert "_expires_at" in saved_data


@patch('teams_cli.auth.keyring')
def test_load_token_from_keyring(mock_keyring, token_manager):
    stored_token = {
        "access_token": "stored_token",
        "refresh_token": "stored_refresh",
        "expires_in": 3600
    }
    mock_keyring.get_password.return_value = json.dumps(stored_token)
    
    result = token_manager._load_token_from_keyring("test@example.com")
    
    assert result == stored_token
    mock_keyring.get_password.assert_called_once_with("teams-cli", "test@example.com")


@patch('teams_cli.auth.keyring')
def test_load_token_from_keyring_not_found(mock_keyring, token_manager):
    mock_keyring.get_password.return_value = None
    
    result = token_manager._load_token_from_keyring("test@example.com")
    
    assert result is None