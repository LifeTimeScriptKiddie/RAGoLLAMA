"""Configuration management for Teams CLI."""
import json
import os
from pathlib import Path
from typing import List, Dict, Any


class Config:
    """Configuration manager for Teams CLI."""
    
    def __init__(self):
        self._config_data = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from appsettings.json and environment variables."""
        # Load from appsettings.json
        config_file = Path(__file__).parent.parent.parent / "appsettings.json"
        
        if config_file.exists():
            with open(config_file, 'r') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Override with environment variables
        if tenant_id := os.getenv("TENANT_ID"):
            config["tenantId"] = tenant_id
        
        if client_id := os.getenv("CLIENT_ID"):
            config["clientId"] = client_id
        
        if scopes := os.getenv("SCOPES"):
            config["scopes"] = [s.strip() for s in scopes.split(",")]
        
        if graph_base_url := os.getenv("GRAPH_BASE_URL"):
            config["graphBaseUrl"] = graph_base_url
        
        return config
    
    @property
    def tenant_id(self) -> str:
        """Get tenant ID."""
        return self._config_data.get("tenantId", "")
    
    @property
    def client_id(self) -> str:
        """Get client ID."""
        return self._config_data.get("clientId", "")
    
    @property
    def scopes(self) -> List[str]:
        """Get OAuth scopes."""
        return self._config_data.get("scopes", [])
    
    @property
    def graph_base_url(self) -> str:
        """Get Microsoft Graph base URL."""
        return self._config_data.get("graphBaseUrl", "https://graph.microsoft.com/v1.0")
    
    @property
    def authority(self) -> str:
        """Get OAuth authority URL."""
        return f"https://login.microsoftonline.com/{self.tenant_id}"


# Global config instance
config = Config()