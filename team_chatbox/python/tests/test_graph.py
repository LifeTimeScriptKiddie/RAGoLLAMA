"""Unit tests for Microsoft Graph client."""
import pytest
from unittest.mock import Mock, patch, MagicMock
import requests
import time

from teams_cli.graph import GraphClient, GraphAPIError


@pytest.fixture
def mock_token_manager():
    with patch('teams_cli.graph.token_manager') as mock_tm:
        mock_tm.get_access_token.return_value = "test_access_token"
        yield mock_tm


@pytest.fixture
def mock_config():
    with patch('teams_cli.graph.config') as mock_config:
        mock_config.graph_base_url = "https://graph.microsoft.com/v1.0"
        yield mock_config


@pytest.fixture
def graph_client():
    return GraphClient()


def test_successful_get_request(graph_client, mock_token_manager, mock_config):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"value": "test"}
    mock_response.content = b'{"value": "test"}'
    
    with patch.object(graph_client.session, 'request', return_value=mock_response):
        result = graph_client.get("/me")
    
    assert result == {"value": "test"}
    mock_token_manager.get_access_token.assert_called_once()


def test_successful_post_request(graph_client, mock_token_manager, mock_config):
    mock_response = Mock()
    mock_response.status_code = 201
    mock_response.json.return_value = {"id": "created"}
    mock_response.content = b'{"id": "created"}'
    
    with patch.object(graph_client.session, 'request', return_value=mock_response):
        result = graph_client.post("/chats/123/messages", {"body": {"content": "test"}})
    
    assert result == {"id": "created"}


def test_204_no_content_response(graph_client, mock_token_manager, mock_config):
    mock_response = Mock()
    mock_response.status_code = 204
    mock_response.content = b''
    
    with patch.object(graph_client.session, 'request', return_value=mock_response):
        result = graph_client.delete("/item/123")
    
    assert result == {}


def test_401_authentication_retry(graph_client, mock_token_manager, mock_config):
    # First call returns 401, second call succeeds
    mock_response_401 = Mock()
    mock_response_401.status_code = 401
    
    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"value": "success"}
    mock_response_200.content = b'{"value": "success"}'
    
    with patch.object(graph_client.session, 'request', side_effect=[mock_response_401, mock_response_200]):
        result = graph_client.get("/me")
    
    assert result == {"value": "success"}
    # Token should be requested twice (initial + retry)
    assert mock_token_manager.get_access_token.call_count == 2


def test_401_authentication_failure_after_retry(graph_client, mock_token_manager, mock_config):
    mock_response = Mock()
    mock_response.status_code = 401
    
    with patch.object(graph_client.session, 'request', return_value=mock_response):
        with pytest.raises(GraphAPIError, match="Authentication failed"):
            graph_client.get("/me")


def test_429_rate_limiting_with_retry_after(graph_client, mock_token_manager, mock_config):
    # First call returns 429 with Retry-After, second call succeeds
    mock_response_429 = Mock()
    mock_response_429.status_code = 429
    mock_response_429.headers = {"Retry-After": "1"}
    
    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"value": "success"}
    mock_response_200.content = b'{"value": "success"}'
    
    with patch.object(graph_client.session, 'request', side_effect=[mock_response_429, mock_response_200]):
        with patch('time.sleep') as mock_sleep:
            result = graph_client.get("/me")
    
    assert result == {"value": "success"}
    mock_sleep.assert_called_once_with(1)


def test_429_rate_limiting_max_retries_exceeded(graph_client, mock_token_manager, mock_config):
    mock_response = Mock()
    mock_response.status_code = 429
    mock_response.headers = {"Retry-After": "1"}
    
    with patch.object(graph_client.session, 'request', return_value=mock_response):
        with patch('time.sleep'):
            with pytest.raises(GraphAPIError, match="Rate limit exceeded"):
                graph_client.get("/me")


def test_500_server_error_with_exponential_backoff(graph_client, mock_token_manager, mock_config):
    # First call returns 500, second call succeeds
    mock_response_500 = Mock()
    mock_response_500.status_code = 500
    
    mock_response_200 = Mock()
    mock_response_200.status_code = 200
    mock_response_200.json.return_value = {"value": "success"}
    mock_response_200.content = b'{"value": "success"}'
    
    with patch.object(graph_client.session, 'request', side_effect=[mock_response_500, mock_response_200]):
        with patch('time.sleep') as mock_sleep:
            result = graph_client.get("/me")
    
    assert result == {"value": "success"}
    # Should have slept for exponential backoff (2^0 + random)
    mock_sleep.assert_called_once()
    sleep_time = mock_sleep.call_args[0][0]
    assert 1.0 <= sleep_time <= 2.0  # Base 1 second + up to 1 second jitter


def test_500_server_error_max_retries_exceeded(graph_client, mock_token_manager, mock_config):
    mock_response = Mock()
    mock_response.status_code = 500
    
    with patch.object(graph_client.session, 'request', return_value=mock_response):
        with patch('time.sleep'):
            with pytest.raises(GraphAPIError, match="Server error 500"):
                graph_client.get("/me")


def test_400_client_error_no_retry(graph_client, mock_token_manager, mock_config):
    mock_response = Mock()
    mock_response.status_code = 400
    mock_response.text = "Bad Request"
    mock_response.json.return_value = {
        "error": {
            "message": "Invalid request"
        }
    }
    
    with patch.object(graph_client.session, 'request', return_value=mock_response):
        with pytest.raises(GraphAPIError, match="Invalid request"):
            graph_client.get("/me")


def test_network_error_with_retry(graph_client, mock_token_manager, mock_config):
    # First call raises network error, second succeeds
    network_error = requests.exceptions.ConnectionError("Network timeout")
    
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"value": "success"}
    mock_response.content = b'{"value": "success"}'
    
    with patch.object(graph_client.session, 'request', side_effect=[network_error, mock_response]):
        with patch('time.sleep') as mock_sleep:
            result = graph_client.get("/me")
    
    assert result == {"value": "success"}
    mock_sleep.assert_called_once()


def test_network_error_max_retries_exceeded(graph_client, mock_token_manager, mock_config):
    network_error = requests.exceptions.ConnectionError("Network timeout")
    
    with patch.object(graph_client.session, 'request', side_effect=network_error):
        with patch('time.sleep'):
            with pytest.raises(GraphAPIError, match="Network error"):
                graph_client.get("/me")


def test_relative_url_conversion(graph_client, mock_token_manager, mock_config):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"value": "test"}
    mock_response.content = b'{"value": "test"}'
    
    with patch.object(graph_client.session, 'request', return_value=mock_response) as mock_request:
        graph_client.get("/me")
    
    # Verify the URL was converted to absolute
    call_args = mock_request.call_args
    assert call_args[1]['url'] == "https://graph.microsoft.com/v1.0/me"


def test_absolute_url_passthrough(graph_client, mock_token_manager, mock_config):
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"value": "test"}
    mock_response.content = b'{"value": "test"}'
    
    absolute_url = "https://graph.microsoft.com/v1.0/me/chats/delta?token=abc"
    
    with patch.object(graph_client.session, 'request', return_value=mock_response) as mock_request:
        graph_client.get(absolute_url)
    
    # Verify the URL was passed through unchanged
    call_args = mock_request.call_args
    assert call_args[1]['url'] == absolute_url