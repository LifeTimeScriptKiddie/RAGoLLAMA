"""Authentication module using MSAL device code flow."""
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

import keyring
from msal import PublicClientApplication

from .config import config

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Authentication related errors."""
    pass


class TokenManager:
    """Manages OAuth tokens using MSAL and keyring storage."""
    
    KEYRING_SERVICE = "teams-cli"
    
    def __init__(self):
        self.app = PublicClientApplication(
            client_id=config.client_id,
            authority=config.authority
        )
        self._cached_token: Optional[Dict[str, Any]] = None
        self._account_name: Optional[str] = None
    
    def get_access_token(self) -> str:
        """Get a valid access token, refreshing if necessary."""
        if not config.tenant_id or not config.client_id:
            raise AuthenticationError(
                "Missing configuration. Please set tenantId and clientId in appsettings.json "
                "or via TENANT_ID and CLIENT_ID environment variables."
            )
        
        # Try to use cached token first
        if self._cached_token and self._is_token_valid(self._cached_token):
            return self._cached_token["access_token"]
        
        # Try to load token from keyring
        if self._account_name:
            stored_token = self._load_token_from_keyring(self._account_name)
            if stored_token and self._is_token_valid(stored_token):
                self._cached_token = stored_token
                return stored_token["access_token"]
        
        # Try silent refresh if we have refresh token
        if stored_token and "refresh_token" in stored_token:
            refreshed_token = self._refresh_token(stored_token)
            if refreshed_token:
                self._cached_token = refreshed_token
                self._save_token_to_keyring(self._account_name, refreshed_token)
                return refreshed_token["access_token"]
        
        # If all else fails, need new device flow
        raise AuthenticationError(
            "No valid token available. Please run 'teams-cli login' first."
        )
    
    def login(self) -> Dict[str, Any]:
        """Perform device code authentication flow."""
        if not config.tenant_id or not config.client_id:
            raise AuthenticationError(
                "Missing configuration. Please set tenantId and clientId in appsettings.json "
                "or via TENANT_ID and CLIENT_ID environment variables."
            )
        
        flow = self.app.initiate_device_flow(scopes=config.scopes)
        
        if "user_code" not in flow:
            raise AuthenticationError("Failed to create device flow")
        
        print(flow["message"])
        
        # Wait for user to complete device flow
        token_response = self.app.acquire_token_by_device_flow(flow)
        
        if "error" in token_response:
            error_desc = token_response.get("error_description", token_response.get("error"))
            raise AuthenticationError(f"Authentication failed: {error_desc}")
        
        # Get user info
        user_info = self._get_user_info(token_response["access_token"])
        upn = user_info.get("userPrincipalName", "unknown_user")
        
        # Cache token
        self._cached_token = token_response
        self._account_name = upn
        
        # Save to keyring
        self._save_token_to_keyring(upn, token_response)
        
        return user_info
    
    def _is_token_valid(self, token: Dict[str, Any]) -> bool:
        """Check if token is still valid."""
        if not token or "access_token" not in token:
            return False
        
        # Check expiration (with 5 minute buffer)
        if "expires_in" in token:
            expires_at = token.get("_expires_at", 0)
            if expires_at == 0:
                # Calculate expiration if not cached
                expires_at = datetime.now().timestamp() + token["expires_in"]
                token["_expires_at"] = expires_at
            
            return datetime.now().timestamp() < (expires_at - 300)  # 5 min buffer
        
        return True
    
    def _refresh_token(self, token: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Attempt to refresh the access token."""
        if "refresh_token" not in token:
            return None
        
        try:
            accounts = self.app.get_accounts()
            if accounts:
                # Try silent token acquisition
                result = self.app.acquire_token_silent(
                    scopes=config.scopes,
                    account=accounts[0]
                )
                if result and "access_token" in result:
                    return result
        except Exception as e:
            logger.debug(f"Token refresh failed: {e}")
        
        return None
    
    def _load_token_from_keyring(self, account_name: str) -> Optional[Dict[str, Any]]:
        """Load token from keyring storage."""
        try:
            token_json = keyring.get_password(self.KEYRING_SERVICE, account_name)
            if token_json:
                return json.loads(token_json)
        except Exception as e:
            logger.debug(f"Failed to load token from keyring: {e}")
        
        return None
    
    def _save_token_to_keyring(self, account_name: str, token: Dict[str, Any]) -> None:
        """Save token to keyring storage."""
        try:
            # Add expiration timestamp for local tracking
            if "expires_in" in token and "_expires_at" not in token:
                token["_expires_at"] = datetime.now().timestamp() + token["expires_in"]
            
            keyring.set_password(
                self.KEYRING_SERVICE,
                account_name,
                json.dumps(token)
            )
        except Exception as e:
            logger.warning(f"Failed to save token to keyring: {e}")
            # Fall back to local file if keyring fails
            self._save_token_to_file(account_name, token)
    
    def _save_token_to_file(self, account_name: str, token: Dict[str, Any]) -> None:
        """Fallback: save token to local file."""
        try:
            from .storage import get_app_data_dir
            token_file = get_app_data_dir() / f"token-{account_name}.json"
            token_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(token_file, 'w') as f:
                json.dump(token, f)
            
            # Set restrictive permissions on Windows
            import stat
            token_file.chmod(stat.S_IREAD | stat.S_IWRITE)
            
        except Exception as e:
            logger.error(f"Failed to save token to file: {e}")
    
    def _get_user_info(self, access_token: str) -> Dict[str, Any]:
        """Get user information from Microsoft Graph."""
        import requests
        
        headers = {"Authorization": f"Bearer {access_token}"}
        response = requests.get(f"{config.graph_base_url}/me", headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            raise AuthenticationError(f"Failed to get user info: {response.status_code}")


# Global token manager instance
token_manager = TokenManager()