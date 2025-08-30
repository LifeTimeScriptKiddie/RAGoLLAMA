"""Microsoft Graph API client with retry logic and error handling."""
import time
import random
import logging
from typing import Any, Dict, Optional, Union

import requests

from .auth import token_manager, AuthenticationError
from .config import config

logger = logging.getLogger(__name__)


class GraphAPIError(Exception):
    """Microsoft Graph API related errors."""
    pass


class GraphClient:
    """HTTP client wrapper for Microsoft Graph API with retry logic."""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "teams-cli/1.0.0",
            "Accept": "application/json",
            "Content-Type": "application/json"
        })
        self._auth_retry_attempted = False
    
    def request(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Make HTTP request with authentication and retry logic."""
        if not url.startswith("http"):
            url = f"{config.graph_base_url}{url}"
        
        return self._request_with_retry(method, url, json_data, params)
    
    def _request_with_retry(
        self,
        method: str,
        url: str,
        json_data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Internal method to handle requests with retry logic."""
        max_retries = 5
        
        try:
            # Get access token and set auth header
            access_token = token_manager.get_access_token()
            self.session.headers.update({"Authorization": f"Bearer {access_token}"})
        except AuthenticationError:
            if not self._auth_retry_attempted:
                self._auth_retry_attempted = True
                raise GraphAPIError(
                    "Authentication failed. Please run 'teams-cli login' first."
                )
            raise
        
        try:
            response = self.session.request(
                method=method,
                url=url,
                json=json_data,
                params=params,
                timeout=30
            )
            
            # Handle different response codes
            if response.status_code == 200:
                return response.json() if response.content else {}
            elif response.status_code == 201:
                return response.json() if response.content else {}
            elif response.status_code == 204:
                return {}
            elif response.status_code == 401:
                # Authentication failed - try to refresh token once
                if not self._auth_retry_attempted and retry_count == 0:
                    logger.debug("Received 401, attempting token refresh")
                    self._auth_retry_attempted = True
                    # Clear cached token to force refresh
                    token_manager._cached_token = None
                    return self._request_with_retry(method, url, json_data, params, 1)
                else:
                    raise GraphAPIError(
                        "Authentication failed. Please run 'teams-cli login' again."
                    )
            elif response.status_code == 429:
                # Rate limiting - respect Retry-After header
                if retry_count < max_retries:
                    retry_after = int(response.headers.get("Retry-After", "60"))
                    logger.warning(f"Rate limited. Waiting {retry_after} seconds...")
                    time.sleep(retry_after)
                    return self._request_with_retry(method, url, json_data, params, retry_count + 1)
                else:
                    raise GraphAPIError("Rate limit exceeded. Max retries reached.")
            elif 500 <= response.status_code < 600:
                # Server errors - exponential backoff with jitter
                if retry_count < max_retries:
                    wait_time = (2 ** retry_count) + random.uniform(0, 1)
                    logger.warning(f"Server error {response.status_code}. Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    return self._request_with_retry(method, url, json_data, params, retry_count + 1)
                else:
                    raise GraphAPIError(f"Server error {response.status_code}. Max retries reached.")
            else:
                # Other client errors
                error_msg = f"HTTP {response.status_code}: {response.text}"
                try:
                    error_json = response.json()
                    if "error" in error_json:
                        error_detail = error_json["error"]
                        if isinstance(error_detail, dict):
                            error_msg = error_detail.get("message", error_msg)
                        else:
                            error_msg = str(error_detail)
                except:
                    pass
                
                raise GraphAPIError(error_msg)
        
        except requests.exceptions.RequestException as e:
            if retry_count < max_retries and any(
                err in str(e).lower() 
                for err in ["timeout", "connection", "network"]
            ):
                wait_time = (2 ** retry_count) + random.uniform(0, 1)
                logger.warning(f"Network error: {e}. Retrying in {wait_time:.1f}s...")
                time.sleep(wait_time)
                return self._request_with_retry(method, url, json_data, params, retry_count + 1)
            else:
                raise GraphAPIError(f"Network error: {e}")
    
    def get(self, url: str, params: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Make GET request."""
        return self.request("GET", url, params=params)
    
    def post(self, url: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make POST request."""
        return self.request("POST", url, json_data=json_data)
    
    def put(self, url: str, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Make PUT request."""
        return self.request("PUT", url, json_data=json_data)
    
    def delete(self, url: str) -> Dict[str, Any]:
        """Make DELETE request."""
        return self.request("DELETE", url)


# Global graph client instance
graph_client = GraphClient()